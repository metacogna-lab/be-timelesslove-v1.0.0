"""
Role-Based Access Control (RBAC) utilities and decorators.
"""

from typing import Callable, Optional
from functools import wraps
from fastapi import HTTPException, status
from app.utils.jwt import TokenClaims


def require_role(*allowed_roles: str):
    """
    Decorator to require specific role(s) for endpoint access.
    
    Args:
        *allowed_roles: One or more allowed roles
    
    Usage:
        @require_role("adult")
        async def endpoint(current_user: TokenClaims = Depends(get_current_user)):
            ...
    """
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Find current_user in kwargs
            current_user: Optional[TokenClaims] = None
            for key, value in kwargs.items():
                if isinstance(value, TokenClaims):
                    current_user = value
                    break
            
            if not current_user:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Current user not found in request context"
                )
            
            if current_user.role not in allowed_roles:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Operation requires one of these roles: {', '.join(allowed_roles)}"
                )
            
            return await func(*args, **kwargs)
        return wrapper
    return decorator


def require_adult(func: Callable):
    """Decorator to require adult role."""
    return require_role("adult")(func)


def require_family_member(func: Callable):
    """
    Decorator to ensure user is in the same family unit as the resource.
    
    Usage:
        @require_family_member
        async def endpoint(family_unit_id: str, current_user: TokenClaims = Depends(get_current_user)):
            ...
    """
    @wraps(func)
    async def wrapper(*args, **kwargs):
        # Find current_user and family_unit_id in kwargs
        current_user: Optional[TokenClaims] = None
        family_unit_id: Optional[str] = None
        
        for key, value in kwargs.items():
            if isinstance(value, TokenClaims):
                current_user = value
            elif key == "family_unit_id" and isinstance(value, str):
                family_unit_id = value
        
        if not current_user:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Current user not found in request context"
            )
        
        if family_unit_id and current_user.family_unit_id != family_unit_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied: Resource belongs to different family unit"
            )
        
        return await func(*args, **kwargs)
    return wrapper


def can_manage_family(role: str) -> bool:
    """
    Check if a role can manage family unit.
    
    Args:
        role: User role
    
    Returns:
        True if role can manage family, False otherwise
    """
    return role in ("adult", "grandparent")


def can_invite_members(role: str) -> bool:
    """
    Check if a role can invite family members.
    
    Args:
        role: User role
    
    Returns:
        True if role can invite, False otherwise
    """
    return role in ("adult", "grandparent")


def can_provision_children(role: str) -> bool:
    """
    Check if a role can provision child accounts.
    
    Args:
        role: User role
    
    Returns:
        True if role can provision children, False otherwise
    """
    return role == "adult"


def can_create_pets(role: str) -> bool:
    """
    Check if a role can create pet profiles.
    
    Args:
        role: User role
    
    Returns:
        True if role can create pets, False otherwise
    """
    return role in ("adult", "grandparent")


def can_delete_content(role: str, is_owner: bool = False) -> bool:
    """
    Check if a role can delete content.
    
    Args:
        role: User role
        is_owner: Whether user owns the content
    
    Returns:
        True if role can delete, False otherwise
    """
    if role == "adult":
        return True  # Adults can delete any content
    if role in ("teen", "grandparent") and is_owner:
        return True  # Can delete own content
    return False  # Children and pets cannot delete


def can_edit_content(role: str, is_owner: bool = False) -> bool:
    """
    Check if a role can edit content.
    
    Args:
        role: User role
        is_owner: Whether user owns the content
    
    Returns:
        True if role can edit, False otherwise
    """
    if role == "pet":
        return False  # Pets cannot edit
    if role == "child" and not is_owner:
        return False  # Children can only edit own content
    return True  # All other roles can edit (with ownership restrictions)


def validate_family_access(
    user_family_unit_id: str,
    resource_family_unit_id: str
) -> bool:
    """
    Validate that user has access to resource in same family unit.
    
    Args:
        user_family_unit_id: User's family unit ID
        resource_family_unit_id: Resource's family unit ID
    
    Returns:
        True if access allowed, False otherwise
    """
    return user_family_unit_id == resource_family_unit_id

