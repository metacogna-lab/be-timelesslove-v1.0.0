"""
JWT encoding and decoding utilities for custom authentication scheme.

Provides functions to create, validate, and decode JWT tokens with custom claims
for user roles and family unit context.
"""

from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from uuid import uuid4
import os

from jose import jwt, JWTError
from pydantic import BaseModel
from app.config import get_settings


class TokenClaims(BaseModel):
    """JWT token claims structure."""
    sub: str  # User ID
    role: str  # User role (adult, teen, child, grandparent, pet)
    family_unit_id: str  # Family unit UUID
    iat: int  # Issued at timestamp
    exp: int  # Expiration timestamp
    jti: str  # JWT ID
    type: str  # Token type (access or refresh)


class JWTConfig:
    """JWT configuration from environment variables."""

    def __init__(self):
        secret_key = os.getenv("JWT_SECRET_KEY", "test_jwt_secret_key_minimum_32_bytes_long")
        if not secret_key:
            raise ValueError("JWT_SECRET_KEY environment variable is required")
        self.secret_key = secret_key

        self.algorithm = os.getenv("JWT_ALGORITHM", "HS256")
        self.access_token_expire_minutes = int(
            os.getenv("JWT_ACCESS_TOKEN_EXPIRE_MINUTES", "15")
        )
        self.refresh_token_expire_days = int(
            os.getenv("JWT_REFRESH_TOKEN_EXPIRE_DAYS", "7")
        )
    
    @property
    def access_token_expire_seconds(self) -> int:
        """Access token expiration in seconds."""
        return self.access_token_expire_minutes * 60
    
    @property
    def refresh_token_expire_seconds(self) -> int:
        """Refresh token expiration in seconds."""
        return self.refresh_token_expire_days * 24 * 60 * 60


# Global JWT config instance
_jwt_config: Optional[JWTConfig] = None


def get_jwt_config() -> JWTConfig:
    """Get or create JWT configuration instance."""
    global _jwt_config
    if _jwt_config is None:
        _jwt_config = JWTConfig()
    return _jwt_config


def create_access_token(
    user_id: str,
    role: str,
    family_unit_id: str,
    config: Optional[JWTConfig] = None
) -> str:
    """
    Create a JWT access token with user claims.
    
    Args:
        user_id: User UUID from user_profiles.id
        role: User role (adult, teen, child, grandparent, pet)
        family_unit_id: Family unit UUID
        config: Optional JWT config (uses global if not provided)
    
    Returns:
        Encoded JWT access token string
    """
    if config is None:
        config = get_jwt_config()
    
    now = datetime.utcnow()
    expire = now + timedelta(seconds=config.access_token_expire_seconds)
    
    claims = {
        "sub": user_id,
        "role": role,
        "family_unit_id": family_unit_id,
        "iat": int(now.timestamp()),
        "exp": int(expire.timestamp()),
        "jti": str(uuid4()),
        "type": "access"
    }
    
    return jwt.encode(claims, config.secret_key, algorithm=config.algorithm)


def create_refresh_token(
    user_id: str,
    role: str,
    family_unit_id: str,
    config: Optional[JWTConfig] = None
) -> str:
    """
    Create a JWT refresh token with user claims.
    
    Args:
        user_id: User UUID from user_profiles.id
        role: User role
        family_unit_id: Family unit UUID
        config: Optional JWT config (uses global if not provided)
    
    Returns:
        Encoded JWT refresh token string
    """
    if config is None:
        config = get_jwt_config()
    
    now = datetime.utcnow()
    expire = now + timedelta(seconds=config.refresh_token_expire_seconds)
    
    claims = {
        "sub": user_id,
        "role": role,
        "family_unit_id": family_unit_id,
        "iat": int(now.timestamp()),
        "exp": int(expire.timestamp()),
        "jti": str(uuid4()),
        "type": "refresh"
    }
    
    return jwt.encode(claims, config.secret_key, algorithm=config.algorithm)


def decode_token(
    token: str,
    config: Optional[JWTConfig] = None,
    expected_type: Optional[str] = None
) -> Dict[str, Any]:
    """
    Decode and validate a JWT token.
    
    Args:
        token: JWT token string
        config: Optional JWT config (uses global if not provided)
        expected_type: Expected token type ("access" or "refresh")
    
    Returns:
        Decoded token claims dictionary
    
    Raises:
        JWTError: If token is invalid, expired, or malformed
        ValueError: If token type doesn't match expected_type
    """
    if config is None:
        config = get_jwt_config()
    
    try:
        payload = jwt.decode(
            token,
            config.secret_key,
            algorithms=[config.algorithm]
        )
    except JWTError as e:
        raise JWTError(f"Invalid token: {str(e)}")
    
    # Validate token type if specified
    if expected_type and payload.get("type") != expected_type:
        raise ValueError(
            f"Token type mismatch. Expected '{expected_type}', "
            f"got '{payload.get('type')}'"
        )
    
    # Validate required claims
    required_claims = ["sub", "role", "family_unit_id", "iat", "exp", "jti", "type"]
    missing_claims = [claim for claim in required_claims if claim not in payload]
    if missing_claims:
        raise ValueError(f"Missing required claims: {missing_claims}")
    
    return payload


def get_token_claims(token: str) -> Optional[TokenClaims]:
    """
    Get token claims as a validated Pydantic model.
    
    Args:
        token: JWT token string
    
    Returns:
        TokenClaims model if valid, None if invalid
    """
    try:
        payload = decode_token(token)
        return TokenClaims(**payload)
    except (JWTError, ValueError):
        return None


def is_token_expired(token: str) -> bool:
    """
    Check if a token is expired without full validation.

    Args:
        token: JWT token string

    Returns:
        True if token is expired, False otherwise
    """
    try:
        payload = decode_token(token)
        exp = payload.get("exp")
        if exp is None:
            return True
        return datetime.utcnow().timestamp() > exp
    except (JWTError, ValueError):
        return True


def decode_supabase_token(token: str) -> Dict[str, Any]:
    """
    Decode and validate a Supabase JWT token.

    Args:
        token: Supabase JWT token string

    Returns:
        Decoded Supabase token payload

    Raises:
        JWTError: If token is invalid, expired, or malformed
    """
    settings = get_settings()

    try:
        payload = jwt.decode(
            token,
            settings.supabase_jwt_secret,
            algorithms=["HS256"],
            audience="authenticated"
        )
    except JWTError as e:
        raise JWTError(f"Invalid Supabase token: {str(e)}")

    return payload


async def get_family_unit_id(user_id: str) -> Optional[str]:
    """
    Fetch family_unit_id from database for a given user_id.

    Args:
        user_id: User UUID from Supabase auth

    Returns:
        Family unit UUID as string, or None if not found
    """
    from app.db.supabase import get_supabase_service_client

    try:
        client = get_supabase_service_client()
        response = client.table("user_profiles").select("family_unit_id").eq("id", user_id).single().execute()

        if response.data and response.data.get("family_unit_id"):
            return str(response.data["family_unit_id"])

        return None
    except Exception:
        return None


def decode_supabase_token_to_claims(token: str, family_unit_id: Optional[str] = None) -> TokenClaims:
    """
    Decode Supabase JWT and convert to TokenClaims structure.

    Args:
        token: Supabase JWT token string
        family_unit_id: Optional family_unit_id (fetched from DB if not provided)

    Returns:
        TokenClaims model with mapped Supabase claims

    Raises:
        JWTError: If token is invalid or expired
        ValueError: If required claims are missing
    """
    payload = decode_supabase_token(token)

    # Extract user ID
    user_id = payload.get("sub")
    if not user_id:
        raise ValueError("Missing 'sub' claim in Supabase token")

    # Extract role from user_metadata or use default
    role = "adult"  # Default role
    if "user_metadata" in payload and isinstance(payload["user_metadata"], dict):
        role = payload["user_metadata"].get("role", "adult")
    elif "app_metadata" in payload and isinstance(payload["app_metadata"], dict):
        role = payload["app_metadata"].get("role", "adult")

    # Use provided family_unit_id or empty string (will be fetched by caller)
    if family_unit_id is None:
        family_unit_id = ""

    # Get timestamps
    exp = payload.get("exp", int(datetime.utcnow().timestamp()) + 3600)
    iat = payload.get("iat", int(datetime.utcnow().timestamp()))

    return TokenClaims(
        sub=user_id,
        role=role,
        family_unit_id=family_unit_id,
        iat=iat,
        exp=exp,
        jti=payload.get("jti", str(uuid4())),
        type="access"
    )

