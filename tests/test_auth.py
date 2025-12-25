"""
Unit and integration tests for authentication endpoints.
"""

import pytest
from unittest.mock import Mock, patch, AsyncMock
from fastapi import status
from app.utils.jwt import create_access_token, create_refresh_token, decode_token


class TestJWTUtilities:
    """Test JWT encoding and decoding utilities."""
    
    def test_create_access_token(self, sample_user_id, sample_family_unit_id):
        """Test access token creation."""
        token = create_access_token(
            sample_user_id,
            "adult",
            sample_family_unit_id
        )
        
        assert token is not None
        assert isinstance(token, str)
        assert len(token) > 0
    
    def test_create_refresh_token(self, sample_user_id, sample_family_unit_id):
        """Test refresh token creation."""
        token = create_refresh_token(
            sample_user_id,
            "adult",
            sample_family_unit_id
        )
        
        assert token is not None
        assert isinstance(token, str)
        assert len(token) > 0
    
    def test_decode_token(self, sample_user_id, sample_family_unit_id):
        """Test token decoding."""
        from app.utils.jwt import JWTConfig

        # Use test config with long expiration
        test_config = JWTConfig()
        test_config.access_token_expire_minutes = 525600  # 1 year
        test_config.secret_key = "test_jwt_secret_key_minimum_32_bytes_long"

        token = create_access_token(
            sample_user_id,
            "adult",
            sample_family_unit_id,
            config=test_config
        )

        claims = decode_token(token, config=test_config, expected_type="access")

        assert claims["sub"] == sample_user_id
        assert claims["role"] == "adult"
        assert claims["family_unit_id"] == sample_family_unit_id
        assert claims["type"] == "access"
        assert "iat" in claims
        assert "exp" in claims
        assert "jti" in claims
    
    def test_decode_token_wrong_type(self, sample_user_id, sample_family_unit_id):
        """Test token decoding with wrong type."""
        from app.utils.jwt import JWTConfig

        # Use test config with long expiration
        test_config = JWTConfig()
        test_config.access_token_expire_minutes = 525600  # 1 year
        test_config.secret_key = "test_jwt_secret_key_minimum_32_bytes_long"

        token = create_access_token(
            sample_user_id,
            "adult",
            sample_family_unit_id,
            config=test_config
        )

        with pytest.raises(ValueError, match="Token type mismatch"):
            decode_token(token, config=test_config, expected_type="refresh")
    
    def test_decode_invalid_token(self):
        """Test decoding invalid token."""
        with pytest.raises(Exception):
            decode_token("invalid.token.here")


class TestRegistrationEndpoints:
    """Test user registration endpoints."""
    
    @pytest.mark.asyncio
    @patch('app.api.v1.auth.get_supabase_service_client')
    @patch('app.api.v1.auth.create_family_unit')
    @patch('app.api.v1.auth.create_user_profile')
    @patch('app.api.v1.auth.generate_tokens')
    @patch('app.api.v1.auth.check_user_exists')
    async def test_register_adult_success(
        self,
        mock_check_exists,
        mock_generate_tokens,
        mock_create_profile,
        mock_create_family,
        mock_supabase_client,
        client
    ):
        """Test successful adult registration."""
        # Setup mocks
        mock_check_exists.return_value = False
        mock_supabase = Mock()
        mock_supabase.auth.sign_up.return_value = Mock(
            user=Mock(id="550e8400-e29b-41d4-a716-446655440000")
        )
        mock_supabase_client.return_value = mock_supabase
        
        mock_create_family.return_value = Mock(
            id="660e8400-e29b-41d4-a716-446655440001"
        )
        mock_create_profile.return_value = Mock(
            id="550e8400-e29b-41d4-a716-446655440000",
            role="adult",
            family_unit_id="660e8400-e29b-41d4-a716-446655440001"
        )
        mock_generate_tokens.return_value = (
            "access_token",
            "refresh_token"
        )
        
        # Make request
        response = client.post(
            "/api/v1/auth/register/adult",
            json={
                "email": "adult@example.com",
                "password": "SecurePass123!",
                "display_name": "Adult User",
                "family_name": "Test Family"
            }
        )
        
        # Assertions
        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert "user_id" in data
        assert "tokens" in data
        assert data["role"] == "adult"
    
    @pytest.mark.asyncio
    @patch('app.api.v1.auth.check_user_exists')
    async def test_register_adult_duplicate_email(
        self,
        mock_check_exists,
        client
    ):
        """Test registration with duplicate email."""
        mock_check_exists.return_value = True
        
        response = client.post(
            "/api/v1/auth/register/adult",
            json={
                "email": "existing@example.com",
                "password": "SecurePass123!",
                "display_name": "User"
            }
        )
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "already exists" in response.json()["detail"].lower()
    
    def test_register_adult_invalid_password(self, client):
        """Test registration with invalid password."""
        response = client.post(
            "/api/v1/auth/register/adult",
            json={
                "email": "user@example.com",
                "password": "weak",
                "display_name": "User"
            }
        )
        
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


class TestLoginEndpoint:
    """Test login endpoint."""
    
    @pytest.mark.asyncio
    @patch('app.api.v1.auth.get_supabase_service_client')
    @patch('app.api.v1.auth.get_user_profile')
    @patch('app.api.v1.auth.generate_tokens')
    async def test_login_success(
        self,
        mock_generate_tokens,
        mock_get_profile,
        mock_supabase_client,
        client,
        sample_user_id,
        sample_family_unit_id
    ):
        """Test successful login."""
        # Setup mocks
        mock_supabase = Mock()
        mock_supabase.auth.sign_in_with_password.return_value = Mock(
            user=Mock(id=sample_user_id)
        )
        mock_supabase_client.return_value = mock_supabase
        
        mock_get_profile.return_value = Mock(
            id=sample_user_id,
            role="adult",
            family_unit_id=sample_family_unit_id
        )
        mock_generate_tokens.return_value = (
            "access_token",
            "refresh_token"
        )
        
        # Make request
        response = client.post(
            "/api/v1/auth/login",
            json={
                "email": "user@example.com",
                "password": "SecurePass123!"
            }
        )
        
        # Assertions
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"
    
    @pytest.mark.asyncio
    @patch('app.api.v1.auth.get_supabase_service_client')
    async def test_login_invalid_credentials(
        self,
        mock_supabase_client,
        client
    ):
        """Test login with invalid credentials."""
        mock_supabase = Mock()
        mock_supabase.auth.sign_in_with_password.side_effect = Exception("Invalid credentials")
        mock_supabase_client.return_value = mock_supabase
        
        response = client.post(
            "/api/v1/auth/login",
            json={
                "email": "user@example.com",
                "password": "WrongPassword"
            }
        )
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED


class TestRefreshToken:
    """Test refresh token endpoint."""
    
    @pytest.mark.asyncio
    @patch('app.api.v1.auth.validate_refresh_token')
    @patch('app.api.v1.auth.revoke_refresh_token')
    @patch('app.api.v1.auth.generate_tokens')
    async def test_refresh_token_success(
        self,
        mock_generate_tokens,
        mock_revoke,
        mock_validate,
        client,
        sample_user_id,
        sample_family_unit_id
    ):
        """Test successful token refresh."""
        from app.utils.jwt import TokenClaims
        
        # Setup mocks
        mock_validate.return_value = TokenClaims(
            sub=sample_user_id,
            role="adult",
            family_unit_id=sample_family_unit_id,
            iat=1000,
            exp=2000,
            jti="token-id",
            type="refresh"
        )
        mock_revoke.return_value = True
        mock_generate_tokens.return_value = (
            "new_access_token",
            "new_refresh_token"
        )
        
        # Make request
        refresh_token = create_refresh_token(
            sample_user_id,
            "adult",
            sample_family_unit_id
        )
        
        response = client.post(
            "/api/v1/auth/refresh",
            json={
                "refresh_token": refresh_token
            }
        )
        
        # Assertions
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["access_token"] == "new_access_token"
        assert data["refresh_token"] == "new_refresh_token"
    
    def test_refresh_token_invalid(self, client):
        """Test refresh with invalid token."""
        response = client.post(
            "/api/v1/auth/refresh",
            json={
                "refresh_token": "invalid.token.here"
            }
        )
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED


class TestChildProvisioning:
    """Test child account provisioning."""
    
    @pytest.mark.asyncio
    @patch('app.api.v1.auth.get_supabase_service_client')
    @patch('app.api.v1.auth.create_user_profile')
    async def test_provision_child_success(
        self,
        mock_create_profile,
        mock_supabase_client,
        client,
        sample_user_id,
        sample_access_token,
        sample_family_unit_id
    ):
        """Test successful child provisioning."""
        # Setup mocks
        from app.utils.jwt import TokenClaims
        from app.dependencies import get_current_user
        from app.main import app

        # Override the get_current_user dependency to return a valid adult user
        async def override_get_current_user():
            return TokenClaims(
                sub=sample_user_id,
                role="adult",
                family_unit_id=str(sample_family_unit_id),
                iat=1234567890,
                exp=1234567890 + 3600,
                jti="test-jti",
                type="access"
            )

        app.dependency_overrides[get_current_user] = override_get_current_user

        try:
            mock_supabase = Mock()
            mock_supabase.auth.sign_up.return_value = Mock(
                user=Mock(id="770e8400-e29b-41d4-a716-446655440000")
            )
            mock_supabase_client.return_value = mock_supabase

            mock_create_profile.return_value = Mock(
                id="770e8400-e29b-41d4-a716-446655440000",
                role="child",
                family_unit_id=sample_family_unit_id
            )

            # Make request
            response = client.post(
                "/api/v1/auth/provision/child",
                headers={"Authorization": f"Bearer {sample_access_token}"},
                json={
                    "display_name": "Child User",
                    "email": "child@example.com"
                }
            )

            # Assertions
            assert response.status_code == status.HTTP_201_CREATED
            data = response.json()
            assert "user_id" in data
            assert "username" in data
            assert "password" in data
            assert data["family_unit_id"] == sample_family_unit_id
        finally:
            # Clean up dependency override
            app.dependency_overrides.clear()
    
    def test_provision_child_unauthorized(self, client):
        """Test child provisioning without authentication."""
        response = client.post(
            "/api/v1/auth/provision/child",
            json={
                "display_name": "Child User"
            }
        )

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

