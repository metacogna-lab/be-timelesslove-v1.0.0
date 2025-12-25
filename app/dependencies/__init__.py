"""
FastAPI dependencies for authentication, database access, and request context.
"""

from typing import Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from app.db.supabase import get_supabase_client, get_supabase_service_client
from app.utils.jwt import (
    decode_token,
    decode_supabase_token_to_claims,
    get_family_unit_id,
    TokenClaims
)
from app.config import get_settings
from supabase import Client
from jose import JWTError


security = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> TokenClaims:
    """
    Dependency to get current authenticated user from JWT token.
    Supports both custom JWT tokens and Supabase JWT tokens.

    Args:
        credentials: HTTP Bearer token credentials

    Returns:
        TokenClaims with user information

    Raises:
        HTTPException: If token is invalid or expired
    """
    token = credentials.credentials

    # Try custom JWT first
    try:
        claims = decode_token(token, expected_type="access")
        return TokenClaims(**claims)
    except (JWTError, ValueError, Exception):
        # Custom JWT failed, try Supabase JWT
        pass

    # Try Supabase JWT
    try:
        # Decode Supabase token
        token_claims = decode_supabase_token_to_claims(token)

        # Fetch family_unit_id from database
        family_id = await get_family_unit_id(token_claims.sub)

        if family_id:
            token_claims.family_unit_id = family_id
        else:
            # User doesn't have a family unit yet (might be during onboarding)
            # Allow the request but with empty family_unit_id
            pass

        return token_claims
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid or expired token: {str(e)}",
            headers={"WWW-Authenticate": "Bearer"},
        )


async def get_current_user_model(
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """
    Dependency to get current authenticated user as CurrentUser model.
    Supports both custom JWT tokens and Supabase JWT tokens.

    This is a convenience dependency for endpoints that prefer CurrentUser over TokenClaims.

    Args:
        credentials: HTTP Bearer token credentials

    Returns:
        CurrentUser model with user information

    Raises:
        HTTPException: If token is invalid or expired
    """
    from app.models.user import CurrentUser

    # Use get_current_user to handle both token types
    token_claims = await get_current_user(credentials)
    return CurrentUser.from_token_claims(token_claims)


def get_db() -> Client:
    """
    Dependency to get Supabase client.

    Returns:
        Supabase client instance
    """
    return get_supabase_client()


def get_service_db() -> Client:
    """
    Dependency to get Supabase service client (bypasses RLS).

    Returns:
        Supabase service client instance
    """
    return get_supabase_service_client()
