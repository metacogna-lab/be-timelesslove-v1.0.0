"""
Pytest configuration and fixtures for testing.
"""

import os

# Set test JWT secret BEFORE importing app modules
os.environ["JWT_SECRET_KEY"] = "test_jwt_secret_key_minimum_32_bytes_long"
os.environ["JWT_ALGORITHM"] = "HS256"
os.environ["JWT_ACCESS_TOKEN_EXPIRE_MINUTES"] = "15"
os.environ["JWT_REFRESH_TOKEN_EXPIRE_DAYS"] = "7"

import pytest
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch
from app.main import app
from app.config import Settings


@pytest.fixture
def client():
    """Create a test client."""
    return TestClient(app)


@pytest.fixture
def mock_settings():
    """Mock application settings."""
    return Settings(
        supabase_url="https://test.supabase.co",
        supabase_anon_key="test_anon_key",
        supabase_service_role_key="test_service_key",
        jwt_secret_key="test_jwt_secret_key_minimum_32_bytes_long",
        jwt_algorithm="HS256",
        jwt_access_token_expire_minutes=15,
        jwt_refresh_token_expire_days=7,
        environment="test",
        debug="true",
        api_version="v1",
        cors_origins="http://localhost:5173"
    )


@pytest.fixture
def mock_supabase_client():
    """Mock Supabase client."""
    mock_client = Mock()
    mock_client.auth = Mock()
    mock_client.table = Mock(return_value=Mock())
    return mock_client


@pytest.fixture
def sample_user_id():
    """Sample user UUID for testing."""
    return "550e8400-e29b-41d4-a716-446655440000"


@pytest.fixture
def sample_family_unit_id():
    """Sample family unit UUID for testing."""
    return "660e8400-e29b-41d4-a716-446655440001"


@pytest.fixture
def sample_access_token(sample_user_id, sample_family_unit_id):
    """Sample JWT access token for testing."""
    from app.utils.jwt import create_access_token, JWTConfig

    # Create test config with long expiration for testing
    test_config = JWTConfig()
    test_config.access_token_expire_minutes = 525600  # 1 year for testing
    test_config.secret_key = "test_jwt_secret_key_minimum_32_bytes_long"

    return create_access_token(
        sample_user_id,
        "adult",
        sample_family_unit_id,
        config=test_config
    )


@pytest.fixture
def sample_refresh_token(sample_user_id, sample_family_unit_id):
    """Sample JWT refresh token for testing."""
    from app.utils.jwt import create_refresh_token, JWTConfig

    # Create test config with long expiration for testing
    test_config = JWTConfig()
    test_config.refresh_token_expire_days = 365  # 1 year for testing
    test_config.secret_key = "test_jwt_secret_key_minimum_32_bytes_long"

    return create_refresh_token(
        sample_user_id,
        "adult",
        sample_family_unit_id,
        config=test_config
    )


@pytest.fixture
def sample_teen_token(sample_user_id, sample_family_unit_id):
    """Sample JWT token for teen user."""
    from app.utils.jwt import create_access_token, JWTConfig

    test_config = JWTConfig()
    test_config.access_token_expire_minutes = 525600
    test_config.secret_key = "test_jwt_secret_key_minimum_32_bytes_long"

    return create_access_token(
        sample_user_id,
        "teen",
        sample_family_unit_id,
        config=test_config
    )


@pytest.fixture
def sample_child_token(sample_user_id, sample_family_unit_id):
    """Sample JWT token for child user."""
    from app.utils.jwt import create_access_token, JWTConfig

    test_config = JWTConfig()
    test_config.access_token_expire_minutes = 525600
    test_config.secret_key = "test_jwt_secret_key_minimum_32_bytes_long"

    return create_access_token(
        sample_user_id,
        "child",
        sample_family_unit_id,
        config=test_config
    )


@pytest.fixture
def sample_grandparent_token(sample_user_id, sample_family_unit_id):
    """Sample JWT token for grandparent user."""
    from app.utils.jwt import create_access_token, JWTConfig

    test_config = JWTConfig()
    test_config.access_token_expire_minutes = 525600
    test_config.secret_key = "test_jwt_secret_key_minimum_32_bytes_long"

    return create_access_token(
        sample_user_id,
        "grandparent",
        sample_family_unit_id,
        config=test_config
    )


@pytest.fixture
def sample_pet_token(sample_user_id, sample_family_unit_id):
    """Sample JWT token for pet user."""
    from app.utils.jwt import create_access_token, JWTConfig

    test_config = JWTConfig()
    test_config.access_token_expire_minutes = 525600
    test_config.secret_key = "test_jwt_secret_key_minimum_32_bytes_long"

    return create_access_token(
        sample_user_id,
        "pet",
        sample_family_unit_id,
        config=test_config
    )


@pytest.fixture
def different_family_token():
    """Sample JWT token for different family unit."""
    from app.utils.jwt import create_access_token, JWTConfig
    from uuid import uuid4

    test_config = JWTConfig()
    test_config.access_token_expire_minutes = 525600
    test_config.secret_key = "test_jwt_secret_key_minimum_32_bytes_long"

    return create_access_token(
        str(uuid4()),
        "adult",
        str(uuid4()),  # Different family unit
        config=test_config
    )



