"""
User service for user profile operations.
"""

from typing import Optional
from uuid import UUID, uuid4
from supabase import Client
from app.db.supabase import get_supabase_client, get_supabase_service_client
from app.models.user import UserProfile


async def create_user_profile(
    user_id: UUID,
    role: str,
    display_name: str,
    family_unit_id: Optional[UUID] = None,
    is_family_creator: bool = False,
    preferences: Optional[dict] = None
) -> UserProfile:
    """
    Create a user profile in the database.
    
    Args:
        user_id: User UUID (from auth.users)
        role: User role
        display_name: User's display name
        family_unit_id: Family unit UUID (required if not family creator)
        is_family_creator: Whether this user is creating a new family
        preferences: User preferences dict
    
    Returns:
        Created UserProfile
    """
    service_client = get_supabase_service_client()
    
    profile_data = {
        "id": str(user_id),
        "role": role,
        "display_name": display_name,
        "is_family_creator": is_family_creator,
        "preferences": preferences or {}
    }
    
    if family_unit_id:
        profile_data["family_unit_id"] = str(family_unit_id)
    
    result = service_client.table("user_profiles").insert(profile_data).execute()
    
    if not result.data:
        raise ValueError("Failed to create user profile")
    
    return UserProfile(**result.data[0])


async def get_user_profile(user_id: UUID) -> Optional[UserProfile]:
    """
    Get user profile by ID.
    
    Args:
        user_id: User UUID
    
    Returns:
        UserProfile if found, None otherwise
    """
    client = get_supabase_client()
    
    result = client.table("user_profiles").select("*").eq("id", str(user_id)).single().execute()
    
    if not result.data:
        return None
    
    return UserProfile(**result.data)


async def get_user_profile_by_email(email: str) -> Optional[UserProfile]:
    """
    Get user profile by email (via auth.users lookup).
    
    Args:
        email: User email
    
    Returns:
        UserProfile if found, None otherwise
    """
    service_client = get_supabase_service_client()
    
    # Get auth user by email
    auth_users = service_client.auth.admin.list_users()
    auth_user = None
    for user in auth_users.users:
        if user.email == email:
            auth_user = user
            break
    
    if not auth_user:
        return None
    
    return await get_user_profile(UUID(auth_user.id))


async def check_user_exists(email: str) -> bool:
    """
    Check if a user with the given email already exists.
    
    Args:
        email: Email to check
    
    Returns:
        True if user exists, False otherwise
    """
    service_client = get_supabase_service_client()
    
    try:
        auth_users = service_client.auth.admin.list_users()
        for user in auth_users.users:
            if user.email == email:
                return True
        return False
    except Exception:
        return False

