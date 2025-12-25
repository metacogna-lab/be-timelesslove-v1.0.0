"""
FastAPI dependencies for Role-Based Access Control (RBAC).
"""

from typing import List, Optional
from fastapi import Depends, HTTPException, status
from app.dependencies import get_current_user, get_current_user_model
from app.utils.jwt import TokenClaims
from app.models.user import CurrentUser
from typing import Union
from app.services.rbac import (
    can_manage_family,
    can_invite_members,
    can_provision_children,
    can_create_pets,
    can_delete_content,
    can_edit_content,
    validate_family_access
)


def require_roles(*allowed_roles: str):
    """
    Dependency factory to require specific role(s) for endpoint access.
    
    Args:
        *allowed_roles: One or more allowed roles
        
    Usage:
        @router.get("/endpoint")
        async def endpoint(
            current_user: TokenClaims = Depends(require_roles("adult", "grandparent"))
        ):
            ...
    """
    async def role_checker(
        current_user: TokenClaims = Depends(get_current_user)
    ) -> TokenClaims:
        if current_user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Operation requires one of these roles: {', '.join(allowed_roles)}"
            )
        return current_user
    return role_checker


def require_adult(
    current_user: TokenClaims = Depends(get_current_user)
) -> TokenClaims:
    """
    Dependency to require adult role.
    
    Usage:
        @router.get("/endpoint")
        async def endpoint(current_user: TokenClaims = Depends(require_adult)):
            ...
    """
    if current_user.role != "adult":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Operation requires adult role"
        )
    return current_user


def require_adult_or_grandparent(
    current_user: TokenClaims = Depends(get_current_user)
) -> TokenClaims:
    """
    Dependency to require adult or grandparent role.
    
    Usage:
        @router.get("/endpoint")
        async def endpoint(current_user: TokenClaims = Depends(require_adult_or_grandparent)):
            ...
    """
    if current_user.role not in ("adult", "grandparent"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Operation requires adult or grandparent role"
        )
    return current_user


def require_family_member(
    family_unit_id: str,
    current_user: TokenClaims = Depends(get_current_user)
) -> TokenClaims:
    """
    Dependency to ensure user is in the same family unit as the resource.
    
    Args:
        family_unit_id: The family unit ID to check
        current_user: Current authenticated user
        
    Usage:
        @router.get("/memories/{memory_id}")
        async def get_memory(
            memory_id: UUID,
            family_unit_id: str = Query(...),
            current_user: TokenClaims = Depends(require_family_member)
        ):
            ...
    """
    if not validate_family_access(str(current_user.family_unit_id), family_unit_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied: Resource belongs to different family unit"
        )
    return current_user


def require_content_owner_or_adult(
    owner_user_id: Optional[str] = None,
    current_user: TokenClaims = Depends(get_current_user)
) -> TokenClaims:
    """
    Dependency to ensure user owns the content or is an adult.
    
    Args:
        owner_user_id: The user ID who owns the content
        current_user: Current authenticated user
        
    Usage:
        @router.delete("/memories/{memory_id}")
        async def delete_memory(
            memory_id: UUID,
            memory: Memory = Depends(get_memory),
            current_user: TokenClaims = Depends(require_content_owner_or_adult)
        ):
            ...
    """
    is_owner = owner_user_id and str(current_user.user_id) == owner_user_id
    
    if not can_delete_content(current_user.role, is_owner):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied: You do not have permission to delete this content"
        )
    return current_user


def require_content_editor(
    owner_user_id: Optional[str] = None,
    current_user: TokenClaims = Depends(get_current_user)
) -> TokenClaims:
    """
    Dependency to ensure user can edit the content.
    
    Args:
        owner_user_id: The user ID who owns the content
        current_user: Current authenticated user
        
    Usage:
        @router.put("/memories/{memory_id}")
        async def update_memory(
            memory_id: UUID,
            memory: Memory = Depends(get_memory),
            current_user: TokenClaims = Depends(require_content_editor)
        ):
            ...
    """
    is_owner = owner_user_id and str(current_user.user_id) == owner_user_id
    
    if not can_edit_content(current_user.role, is_owner):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied: You do not have permission to edit this content"
        )
    return current_user


def require_family_manager(
    current_user: TokenClaims = Depends(get_current_user)
) -> TokenClaims:
    """
    Dependency to require role that can manage family unit.
    
    Usage:
        @router.put("/family/{family_id}")
        async def update_family(
            family_id: UUID,
            current_user: TokenClaims = Depends(require_family_manager)
        ):
            ...
    """
    if not can_manage_family(current_user.role):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Operation requires family management permissions"
        )
    return current_user


def require_invite_permission(
    current_user: TokenClaims = Depends(get_current_user)
) -> TokenClaims:
    """
    Dependency to require role that can invite family members.
    
    Usage:
        @router.post("/invites")
        async def create_invite(
            current_user: TokenClaims = Depends(require_invite_permission)
        ):
            ...
    """
    if not can_invite_members(current_user.role):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Operation requires permission to invite family members"
        )
    return current_user


def require_child_provision_permission(
    current_user: TokenClaims = Depends(get_current_user)
) -> TokenClaims:
    """
    Dependency to require role that can provision child accounts.
    
    Usage:
        @router.post("/auth/provision-child")
        async def provision_child(
            current_user: TokenClaims = Depends(require_child_provision_permission)
        ):
            ...
    """
    if not can_provision_children(current_user.role):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Operation requires permission to provision child accounts"
        )
    return current_user


def require_pet_creation_permission(
    current_user: TokenClaims = Depends(get_current_user)
) -> TokenClaims:
    """
    Dependency to require role that can create pet profiles.
    
    Usage:
        @router.post("/auth/register-pet")
        async def register_pet(
            current_user: TokenClaims = Depends(require_pet_creation_permission)
        ):
            ...
    """
    if not can_create_pets(current_user.role):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Operation requires permission to create pet profiles"
        )
    return current_user


def exclude_pets_for_current_user(
    current_user: CurrentUser = Depends(get_current_user_model)
) -> CurrentUser:
    """
    Dependency to exclude pet role from endpoint (pets are read-only).
    
    Works with CurrentUser model (for feed endpoints).
    
    Usage:
        @router.post("/memories")
        async def create_memory(
            current_user: CurrentUser = Depends(exclude_pets_for_current_user)
        ):
            ...
    """
    if current_user.role == "pet":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Pets cannot perform this operation"
        )
    return current_user


def exclude_pets(
    current_user: TokenClaims = Depends(get_current_user)
) -> TokenClaims:
    """
    Dependency to exclude pet role from endpoint (pets are read-only).
    
    Works with TokenClaims model (for standard endpoints).
    
    Usage:
        @router.post("/memories")
        async def create_memory(
            current_user: TokenClaims = Depends(exclude_pets)
        ):
            ...
    """
    if current_user.role == "pet":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Pets cannot perform this operation"
        )
    return current_user

