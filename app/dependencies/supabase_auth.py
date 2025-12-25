"""
Supabase JWT verification dependency for frontend-issued tokens.

This module provides a "Proxy Auth Pattern" where the frontend handles
authentication via Supabase GoTrue, and the backend verifies the JWT
without managing login/signup flows.

Use this for routes that accept tokens from the React frontend.
"""

from typing import Optional, Dict, Any
from fastapi import Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import jwt, JWTError
from pydantic import BaseModel
from app.config import get_settings
import httpx


security = HTTPBearer()


class SupabaseUser(BaseModel):
    """Supabase authenticated user model."""

    id: str  # Supabase auth.users.id (UUID)
    email: Optional[str] = None
    role: Optional[str] = None  # From JWT aud claim
    app_metadata: Dict[str, Any] = {}
    user_metadata: Dict[str, Any] = {}
    aud: str = "authenticated"

    # Custom claims from your app
    family_unit_id: Optional[str] = None
    user_role: Optional[str] = None  # adult, teen, child, grandparent, pet


class SupabaseJWTVerifier:
    """Verify Supabase-issued JWTs using the project's JWT secret."""

    def __init__(self):
        self.settings = get_settings()
        self.jwt_secret = self.settings.jwt_secret_key
        self.algorithm = self.settings.jwt_algorithm
        self._jwks_cache: Optional[Dict] = None

    async def get_jwks(self) -> Dict:
        """
        Fetch JWKS from Supabase for JWT verification.

        Note: Supabase uses HS256 by default, so JWKS may not be needed.
        This method is here for future RS256 support.
        """
        if self._jwks_cache:
            return self._jwks_cache

        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.settings.supabase_url}/auth/v1/.well-known/jwks.json"
                )
                response.raise_for_status()
                self._jwks_cache = response.json()
                return self._jwks_cache
        except Exception as e:
            # Fallback: Supabase uses HS256 with JWT_SECRET by default
            return {}

    def verify_token(self, token: str) -> Dict[str, Any]:
        """
        Verify Supabase JWT token.

        Args:
            token: JWT token from Authorization header

        Returns:
            Decoded JWT payload

        Raises:
            JWTError: If token is invalid, expired, or malformed
        """
        try:
            # Supabase uses HS256 with JWT_SECRET from project settings
            payload = jwt.decode(
                token,
                self.jwt_secret,
                algorithms=[self.algorithm],
                audience="authenticated",  # Supabase default audience
            )
            return payload
        except JWTError as e:
            raise JWTError(f"Invalid Supabase token: {str(e)}")


# Global verifier instance
_verifier: Optional[SupabaseJWTVerifier] = None


def get_verifier() -> SupabaseJWTVerifier:
    """Get or create JWT verifier instance."""
    global _verifier
    if _verifier is None:
        _verifier = SupabaseJWTVerifier()
    return _verifier


async def verify_supabase_token(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> SupabaseUser:
    """
    FastAPI dependency to verify Supabase-issued JWT tokens.

    This is the "Proxy Auth Pattern" - frontend handles login via Supabase,
    backend verifies the token and extracts user information.

    Args:
        credentials: HTTP Bearer token from Authorization header

    Returns:
        SupabaseUser model with authenticated user info

    Raises:
        HTTPException: If token is invalid or expired (401)

    Usage:
        @router.get("/protected")
        async def protected_route(
            user: SupabaseUser = Depends(verify_supabase_token)
        ):
            return {"user_id": user.id, "email": user.email}
    """
    token = credentials.credentials
    verifier = get_verifier()

    try:
        payload = verifier.verify_token(token)

        # Extract Supabase standard claims
        user_id = payload.get("sub")
        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token: missing user ID",
                headers={"WWW-Authenticate": "Bearer"},
            )

        # Build SupabaseUser model
        user = SupabaseUser(
            id=user_id,
            email=payload.get("email"),
            role=payload.get("role"),
            app_metadata=payload.get("app_metadata", {}),
            user_metadata=payload.get("user_metadata", {}),
            aud=payload.get("aud", "authenticated"),
            # Custom app claims
            family_unit_id=payload.get("family_unit_id"),
            user_role=payload.get("user_role"),
        )

        return user

    except JWTError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Token verification failed: {str(e)}",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Authentication error: {str(e)}",
            headers={"WWW-Authenticate": "Bearer"},
        )


async def optional_supabase_token(
    request: Request,
) -> Optional[SupabaseUser]:
    """
    Optional Supabase token verification.

    Returns None if no token is provided or if token is invalid.
    Useful for endpoints that have different behavior for authenticated vs anonymous users.

    Usage:
        @router.get("/content")
        async def get_content(
            user: Optional[SupabaseUser] = Depends(optional_supabase_token)
        ):
            if user:
                return {"message": f"Hello {user.email}"}
            return {"message": "Hello anonymous user"}
    """
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        return None

    token = auth_header.replace("Bearer ", "")
    verifier = get_verifier()

    try:
        payload = verifier.verify_token(token)
        user_id = payload.get("sub")

        if not user_id:
            return None

        return SupabaseUser(
            id=user_id,
            email=payload.get("email"),
            role=payload.get("role"),
            app_metadata=payload.get("app_metadata", {}),
            user_metadata=payload.get("user_metadata", {}),
            aud=payload.get("aud", "authenticated"),
            family_unit_id=payload.get("family_unit_id"),
            user_role=payload.get("user_role"),
        )
    except:
        return None


# Alias for backward compatibility with existing code
get_supabase_user = verify_supabase_token
