"""
Authentication service for JWT token generation and validation.
"""

from typing import Optional
from uuid import UUID
from supabase import Client
from app.utils.jwt import create_access_token, create_refresh_token, decode_token, TokenClaims
from app.db.supabase import get_supabase_service_client


async def generate_tokens(
    user_id: str,
    role: str,
    family_unit_id: str
) -> tuple[str, str]:
    """
    Generate access and refresh tokens for a user.
    
    Args:
        user_id: User UUID
        role: User role
        family_unit_id: Family unit UUID
    
    Returns:
        Tuple of (access_token, refresh_token)
    """
    access_token = create_access_token(user_id, role, family_unit_id)
    refresh_token = create_refresh_token(user_id, role, family_unit_id)
    
    # Store refresh token in database
    await store_refresh_token(refresh_token, user_id)
    
    return access_token, refresh_token


async def store_refresh_token(refresh_token: str, user_id: str) -> None:
    """
    Store refresh token in database for revocation tracking.
    
    Args:
        refresh_token: Refresh token string
        user_id: User UUID
    """
    try:
        claims = decode_token(refresh_token, expected_type="refresh")
        service_client = get_supabase_service_client()
        
        from datetime import datetime
        expires_at = datetime.fromtimestamp(claims["exp"])
        
        service_client.table("user_sessions").insert({
            "user_id": user_id,
            "refresh_token_jti": claims["jti"],
            "expires_at": expires_at.isoformat(),
        }).execute()
    except Exception as e:
        # Log error but don't fail token generation
        print(f"Warning: Failed to store refresh token: {e}")


async def revoke_refresh_token(refresh_token: str) -> bool:
    """
    Revoke a refresh token.
    
    Args:
        refresh_token: Refresh token to revoke
    
    Returns:
        True if token was revoked, False if not found
    """
    try:
        claims_dict = decode_token(refresh_token, expected_type="refresh")
        service_client = get_supabase_service_client()
        
        from datetime import datetime
        result = service_client.table("user_sessions").update({
            "revoked_at": datetime.utcnow().isoformat()
        }).eq("refresh_token_jti", claims_dict["jti"]).execute()
        
        return len(result.data) > 0
    except Exception:
        return False


async def validate_refresh_token(refresh_token: str) -> Optional[TokenClaims]:
    """
    Validate a refresh token and check if it's revoked.
    
    Args:
        refresh_token: Refresh token to validate
    
    Returns:
        TokenClaims if valid, None if invalid or revoked
    """
    try:
        claims_dict = decode_token(refresh_token, expected_type="refresh")
        service_client = get_supabase_service_client()
        
        # Check if token is revoked
        session = service_client.table("user_sessions").select("*").eq(
            "refresh_token_jti", claims_dict["jti"]
        ).single().execute()
        
        if session.data and session.data.get("revoked_at"):
            return None
        
        return TokenClaims(**claims_dict)
    except Exception:
        return None

