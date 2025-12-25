"""
Tests for Supabase JWT authentication (Proxy Auth Pattern).

Tests verify that:
1. Frontend-issued Supabase tokens are correctly verified
2. Invalid/expired tokens are rejected
3. User information is correctly extracted from JWT claims
4. Optional authentication works for public endpoints
"""

import pytest
from datetime import datetime, timedelta
from jose import jwt
from fastapi import HTTPException
from app.dependencies.supabase_auth import (
    verify_supabase_token,
    optional_supabase_token,
    SupabaseUser,
    SupabaseJWTVerifier,
)
from app.utils.jwt import get_jwt_config


class TestSupabaseJWTVerifier:
    """Test Supabase JWT verification logic."""

    def test_verify_valid_token(self, mock_settings):
        """Test verification of a valid Supabase token."""
        config = get_jwt_config()
        verifier = SupabaseJWTVerifier()

        # Create a valid Supabase-style token
        from datetime import timezone
        now = datetime.now(timezone.utc)
        payload = {
            "sub": "550e8400-e29b-41d4-a716-446655440000",
            "email": "test@example.com",
            "role": "authenticated",
            "aud": "authenticated",
            "iat": int(now.timestamp()),
            "exp": int((now + timedelta(hours=1)).timestamp()),
            "app_metadata": {"provider": "email"},
            "user_metadata": {"display_name": "Test User"},
            # Custom claims
            "family_unit_id": "660e8400-e29b-41d4-a716-446655440001",
            "user_role": "adult",
        }

        token = jwt.encode(payload, config.secret_key, algorithm=config.algorithm)

        # Verify token
        decoded = verifier.verify_token(token)

        assert decoded["sub"] == "550e8400-e29b-41d4-a716-446655440000"
        assert decoded["email"] == "test@example.com"
        assert decoded["aud"] == "authenticated"
        assert decoded["family_unit_id"] == "660e8400-e29b-41d4-a716-446655440001"
        assert decoded["user_role"] == "adult"

    def test_verify_expired_token(self):
        """Test that expired tokens are rejected."""
        config = get_jwt_config()
        verifier = SupabaseJWTVerifier()

        # Create an expired token
        now = datetime.utcnow()
        payload = {
            "sub": "550e8400-e29b-41d4-a716-446655440000",
            "email": "test@example.com",
            "aud": "authenticated",
            "iat": int((now - timedelta(hours=2)).timestamp()),
            "exp": int((now - timedelta(hours=1)).timestamp()),  # Expired 1 hour ago
        }

        token = jwt.encode(payload, config.secret_key, algorithm=config.algorithm)

        # Should raise JWTError
        with pytest.raises(Exception):
            verifier.verify_token(token)

    def test_verify_invalid_signature(self):
        """Test that tokens with invalid signatures are rejected."""
        config = get_jwt_config()
        verifier = SupabaseJWTVerifier()

        # Create token with wrong secret
        now = datetime.utcnow()
        payload = {
            "sub": "550e8400-e29b-41d4-a716-446655440000",
            "aud": "authenticated",
            "exp": int((now + timedelta(hours=1)).timestamp()),
        }

        wrong_secret = "wrong_secret_key_for_testing_purposes_only"
        token = jwt.encode(payload, wrong_secret, algorithm="HS256")

        # Should raise JWTError
        with pytest.raises(Exception):
            verifier.verify_token(token)

    def test_verify_wrong_audience(self):
        """Test that tokens with wrong audience are rejected."""
        config = get_jwt_config()
        verifier = SupabaseJWTVerifier()

        # Create token with wrong audience
        now = datetime.utcnow()
        payload = {
            "sub": "550e8400-e29b-41d4-a716-446655440000",
            "aud": "wrong_audience",  # Should be "authenticated"
            "exp": int((now + timedelta(hours=1)).timestamp()),
        }

        token = jwt.encode(payload, config.secret_key, algorithm=config.algorithm)

        # Should raise JWTError due to audience mismatch
        with pytest.raises(Exception):
            verifier.verify_token(token)


class TestSupabaseUserModel:
    """Test SupabaseUser model creation."""

    def test_create_supabase_user_with_all_fields(self):
        """Test creating SupabaseUser with all fields."""
        user = SupabaseUser(
            id="550e8400-e29b-41d4-a716-446655440000",
            email="test@example.com",
            role="authenticated",
            app_metadata={"provider": "email"},
            user_metadata={"display_name": "Test User"},
            aud="authenticated",
            family_unit_id="660e8400-e29b-41d4-a716-446655440001",
            user_role="adult",
        )

        assert user.id == "550e8400-e29b-41d4-a716-446655440000"
        assert user.email == "test@example.com"
        assert user.family_unit_id == "660e8400-e29b-41d4-a716-446655440001"
        assert user.user_role == "adult"

    def test_create_supabase_user_minimal(self):
        """Test creating SupabaseUser with minimal fields."""
        user = SupabaseUser(id="550e8400-e29b-41d4-a716-446655440000")

        assert user.id == "550e8400-e29b-41d4-a716-446655440000"
        assert user.email is None
        assert user.family_unit_id is None
        assert user.aud == "authenticated"  # Default value


@pytest.mark.asyncio
class TestVerifySupabaseTokenDependency:
    """Test the FastAPI dependency for Supabase token verification."""

    async def test_verify_valid_token_dependency(self, mock_settings):
        """Test successful token verification via dependency."""
        from fastapi.security import HTTPAuthorizationCredentials

        config = get_jwt_config()

        # Create valid token
        now = datetime.utcnow()
        payload = {
            "sub": "550e8400-e29b-41d4-a716-446655440000",
            "email": "adult@example.com",
            "aud": "authenticated",
            "iat": int(now.timestamp()),
            "exp": int((now + timedelta(hours=1)).timestamp()),
            "family_unit_id": "660e8400-e29b-41d4-a716-446655440001",
            "user_role": "adult",
        }

        token = jwt.encode(payload, config.secret_key, algorithm=config.algorithm)

        # Create mock credentials
        credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials=token)

        # Call dependency
        user = await verify_supabase_token(credentials)

        assert isinstance(user, SupabaseUser)
        assert user.id == "550e8400-e29b-41d4-a716-446655440000"
        assert user.email == "adult@example.com"
        assert user.family_unit_id == "660e8400-e29b-41d4-a716-446655440001"
        assert user.user_role == "adult"

    async def test_verify_invalid_token_dependency(self):
        """Test that invalid tokens raise HTTPException."""
        from fastapi.security import HTTPAuthorizationCredentials

        # Create invalid token
        credentials = HTTPAuthorizationCredentials(
            scheme="Bearer", credentials="invalid.token.here"
        )

        # Should raise HTTPException with 401
        with pytest.raises(HTTPException) as exc_info:
            await verify_supabase_token(credentials)

        assert exc_info.value.status_code == 401
        assert "Token verification failed" in exc_info.value.detail

    async def test_verify_token_missing_user_id(self, mock_settings):
        """Test that tokens without sub claim are rejected."""
        from fastapi.security import HTTPAuthorizationCredentials

        config = get_jwt_config()

        # Create token without 'sub' claim
        now = datetime.utcnow()
        payload = {
            "email": "test@example.com",
            "aud": "authenticated",
            "exp": int((now + timedelta(hours=1)).timestamp()),
        }

        token = jwt.encode(payload, config.secret_key, algorithm=config.algorithm)
        credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials=token)

        # Should raise HTTPException
        with pytest.raises(HTTPException) as exc_info:
            await verify_supabase_token(credentials)

        assert exc_info.value.status_code == 401
        assert "missing user ID" in exc_info.value.detail


@pytest.mark.asyncio
class TestOptionalSupabaseToken:
    """Test optional authentication dependency."""

    async def test_optional_token_with_valid_token(self, mock_settings):
        """Test optional auth with valid token returns user."""
        from fastapi import Request

        config = get_jwt_config()

        # Create valid token
        now = datetime.utcnow()
        payload = {
            "sub": "550e8400-e29b-41d4-a716-446655440000",
            "email": "test@example.com",
            "aud": "authenticated",
            "exp": int((now + timedelta(hours=1)).timestamp()),
        }

        token = jwt.encode(payload, config.secret_key, algorithm=config.algorithm)

        # Create mock request with Authorization header
        class MockRequest:
            def __init__(self, token):
                self.headers = {"Authorization": f"Bearer {token}"}

        request = MockRequest(token)

        # Call optional dependency
        user = await optional_supabase_token(request)

        assert user is not None
        assert user.id == "550e8400-e29b-41d4-a716-446655440000"
        assert user.email == "test@example.com"

    async def test_optional_token_without_header(self):
        """Test optional auth without Authorization header returns None."""

        class MockRequest:
            def __init__(self):
                self.headers = {}

        request = MockRequest()

        # Should return None, not raise exception
        user = await optional_supabase_token(request)
        assert user is None

    async def test_optional_token_with_invalid_token(self):
        """Test optional auth with invalid token returns None."""

        class MockRequest:
            def __init__(self, token):
                self.headers = {"Authorization": f"Bearer {token}"}

        request = MockRequest("invalid.token.here")

        # Should return None, not raise exception
        user = await optional_supabase_token(request)
        assert user is None


@pytest.mark.asyncio
class TestSupabaseAuthIntegration:
    """Integration tests using FastAPI TestClient."""

    async def test_protected_endpoint_with_valid_token(self, client, mock_settings):
        """Test accessing protected endpoint with valid Supabase token."""
        from fastapi import APIRouter, Depends
        from app.dependencies.supabase_auth import verify_supabase_token, SupabaseUser

        # Create test router
        test_router = APIRouter()

        @test_router.get("/test/protected")
        async def protected_route(user: SupabaseUser = Depends(verify_supabase_token)):
            return {"user_id": user.id, "email": user.email}

        # Add router to app
        from app.main import app

        app.include_router(test_router)

        # Create valid token
        config = get_jwt_config()
        now = datetime.utcnow()
        payload = {
            "sub": "550e8400-e29b-41d4-a716-446655440000",
            "email": "test@example.com",
            "aud": "authenticated",
            "exp": int((now + timedelta(hours=1)).timestamp()),
        }

        token = jwt.encode(payload, config.secret_key, algorithm=config.algorithm)

        # Make request with token
        response = client.get(
            "/test/protected", headers={"Authorization": f"Bearer {token}"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["user_id"] == "550e8400-e29b-41d4-a716-446655440000"
        assert data["email"] == "test@example.com"

    async def test_protected_endpoint_without_token(self, client):
        """Test accessing protected endpoint without token returns 403."""
        from fastapi import APIRouter, Depends
        from app.dependencies.supabase_auth import verify_supabase_token, SupabaseUser

        # Create test router
        test_router = APIRouter()

        @test_router.get("/test/protected-no-auth")
        async def protected_route(user: SupabaseUser = Depends(verify_supabase_token)):
            return {"user_id": user.id}

        # Add router to app
        from app.main import app

        app.include_router(test_router)

        # Make request without token
        response = client.get("/test/protected-no-auth")

        # Should return 403 Forbidden (no credentials provided)
        assert response.status_code == 403


@pytest.mark.asyncio
class TestSupabaseAuthRoleValidation:
    """Test role-based access control with Supabase tokens."""

    async def test_adult_role_extraction(self, mock_settings):
        """Test that adult role is correctly extracted from token."""
        from fastapi.security import HTTPAuthorizationCredentials

        config = get_jwt_config()

        # Create token with adult role
        now = datetime.utcnow()
        payload = {
            "sub": "550e8400-e29b-41d4-a716-446655440000",
            "email": "adult@example.com",
            "aud": "authenticated",
            "exp": int((now + timedelta(hours=1)).timestamp()),
            "user_role": "adult",
            "family_unit_id": "660e8400-e29b-41d4-a716-446655440001",
        }

        token = jwt.encode(payload, config.secret_key, algorithm=config.algorithm)
        credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials=token)

        user = await verify_supabase_token(credentials)

        assert user.user_role == "adult"
        assert user.family_unit_id == "660e8400-e29b-41d4-a716-446655440001"

    async def test_multiple_roles(self, mock_settings):
        """Test token verification for different user roles."""
        from fastapi.security import HTTPAuthorizationCredentials

        config = get_jwt_config()
        roles = ["adult", "teen", "child", "grandparent", "pet"]

        for role in roles:
            now = datetime.utcnow()
            payload = {
                "sub": f"user-{role}-id",
                "email": f"{role}@example.com",
                "aud": "authenticated",
                "exp": int((now + timedelta(hours=1)).timestamp()),
                "user_role": role,
                "family_unit_id": "660e8400-e29b-41d4-a716-446655440001",
            }

            token = jwt.encode(payload, config.secret_key, algorithm=config.algorithm)
            credentials = HTTPAuthorizationCredentials(
                scheme="Bearer", credentials=token
            )

            user = await verify_supabase_token(credentials)

            assert user.user_role == role
            assert user.email == f"{role}@example.com"
