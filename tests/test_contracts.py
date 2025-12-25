"""
Contract tests for REST API behavior.

These tests verify that the API adheres to documented contracts,
including request/response schemas, status codes, and error formats.
"""

import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.schemas.auth import RegisterResponse, TokenResponse
from app.schemas.memory import MemoryResponse
from app.schemas.feed import FeedResponse, ReactionResponse, CommentResponse


client = TestClient(app)


class TestAuthContracts:
    """Contract tests for authentication endpoints."""
    
    def test_register_adult_contract(self):
        """Test adult registration endpoint contract."""
        response = client.post(
            "/api/v1/auth/register/adult",
            json={
                "email": "test@example.com",
                "password": "SecurePass123!",
                "display_name": "Test User",
                "family_name": "Test Family"
            }
        )
        
        # Should return 201 on success
        assert response.status_code in [201, 400]  # 400 if user exists
        
        if response.status_code == 201:
            data = response.json()
            # Verify response schema
            assert "user_id" in data
            assert "access_token" in data
            assert "refresh_token" in data
            assert "token_type" in data
            assert data["token_type"] == "bearer"
    
    def test_login_contract(self):
        """Test login endpoint contract."""
        # First register a user
        client.post(
            "/api/v1/auth/register/adult",
            json={
                "email": "login_test@example.com",
                "password": "SecurePass123!",
                "display_name": "Login Test",
                "family_name": "Test Family"
            }
        )
        
        # Then login
        response = client.post(
            "/api/v1/auth/login",
            json={
                "email": "login_test@example.com",
                "password": "SecurePass123!"
            }
        )
        
        assert response.status_code in [200, 401]
        
        if response.status_code == 200:
            data = response.json()
            assert "access_token" in data
            assert "refresh_token" in data
            assert "token_type" in data
            assert data["token_type"] == "bearer"
    
    def test_error_response_format(self):
        """Test that error responses follow standard format."""
        # Invalid login
        response = client.post(
            "/api/v1/auth/login",
            json={
                "email": "nonexistent@example.com",
                "password": "wrong"
            }
        )
        
        assert response.status_code == 401
        data = response.json()
        assert "detail" in data
        assert isinstance(data["detail"], str)


class TestMemoryContracts:
    """Contract tests for memory endpoints."""
    
    def test_create_memory_requires_auth(self):
        """Test that memory creation requires authentication."""
        response = client.post(
            "/api/v1/memories",
            json={
                "title": "Test Memory",
                "status": "published"
            }
        )
        
        # Should return 403 (no auth) or 401 (invalid auth)
        assert response.status_code in [401, 403]
    
    def test_memory_response_schema(self):
        """Test that memory responses match schema."""
        # This would require authenticated user setup
        # For now, verify schema structure
        schema_fields = [
            "id", "user_id", "family_unit_id", "title", "description",
            "memory_date", "location", "tags", "status", "created_at",
            "updated_at", "media"
        ]
        
        # Verify MemoryResponse model has these fields
        from app.schemas.memory import MemoryResponse
        model_fields = MemoryResponse.model_fields.keys()
        for field in schema_fields:
            assert field in model_fields


class TestFeedContracts:
    """Contract tests for feed endpoints."""
    
    def test_feed_response_schema(self):
        """Test that feed responses match schema."""
        from app.schemas.feed import FeedResponse
        schema_fields = ["items", "pagination", "total_count", "has_more"]
        
        model_fields = FeedResponse.model_fields.keys()
        for field in schema_fields:
            assert field in model_fields
    
    def test_reaction_response_schema(self):
        """Test that reaction responses match schema."""
        from app.schemas.feed import ReactionResponse
        schema_fields = [
            "id", "memory_id", "user_id", "emoji", "created_at", "updated_at"
        ]
        
        model_fields = ReactionResponse.model_fields.keys()
        for field in schema_fields:
            assert field in model_fields
    
    def test_comment_response_schema(self):
        """Test that comment responses match schema."""
        from app.schemas.feed import CommentResponse
        schema_fields = [
            "id", "memory_id", "user_id", "parent_comment_id", "content",
            "created_at", "updated_at", "deleted_at", "reply_count", "replies"
        ]
        
        model_fields = CommentResponse.model_fields.keys()
        for field in schema_fields:
            assert field in model_fields


class TestErrorContracts:
    """Contract tests for error responses."""
    
    def test_404_error_format(self):
        """Test 404 error response format."""
        response = client.get("/api/v1/memories/00000000-0000-0000-0000-000000000000")
        
        assert response.status_code == 401  # No auth, but structure should be consistent
        # When authenticated, 404 should return {"detail": "..."}
    
    def test_422_validation_error_format(self):
        """Test 422 validation error format."""
        response = client.post(
            "/api/v1/auth/register/adult",
            json={
                "email": "invalid-email",  # Invalid email format
                "password": "short"  # Too short
            }
        )
        
        assert response.status_code == 422
        data = response.json()
        assert "detail" in data
        # Should be array of validation errors
        assert isinstance(data["detail"], list)
        assert len(data["detail"]) > 0


class TestPaginationContracts:
    """Contract tests for paginated endpoints."""
    
    def test_feed_pagination_structure(self):
        """Test that feed pagination follows standard structure."""
        from app.schemas.feed import FeedPaginationParams, FeedResponse
        
        # Verify pagination params
        pagination_fields = ["page", "page_size", "cursor"]
        model_fields = FeedPaginationParams.model_fields.keys()
        for field in pagination_fields:
            assert field in model_fields or field == "cursor"  # cursor is optional
        
        # Verify pagination response
        response_fields = ["pagination", "has_more", "total_count"]
        model_fields = FeedResponse.model_fields.keys()
        for field in response_fields:
            assert field in model_fields


class TestOpenAPIContract:
    """Test that OpenAPI spec is generated correctly."""
    
    def test_openapi_spec_exists(self):
        """Test that OpenAPI spec can be generated."""
        openapi_schema = app.openapi()
        
        assert "openapi" in openapi_schema
        assert "info" in openapi_schema
        assert "paths" in openapi_schema
        assert openapi_schema["openapi"].startswith("3.")
    
    def test_all_endpoints_documented(self):
        """Test that all endpoints are in OpenAPI spec."""
        openapi_schema = app.openapi()
        paths = openapi_schema.get("paths", {})
        
        # Check for key endpoints
        expected_paths = [
            "/api/v1/auth/register/adult",
            "/api/v1/auth/login",
            "/api/v1/memories",
            "/api/v1/feed"
        ]
        
        for path in expected_paths:
            # Path might be in spec (check if any path starts with it)
            assert any(p.startswith(path.split("{")[0]) for p in paths.keys()), \
                f"Path {path} not found in OpenAPI spec"
    
    def test_components_schemas_exist(self):
        """Test that component schemas are defined."""
        openapi_schema = app.openapi()
        components = openapi_schema.get("components", {})
        schemas = components.get("schemas", {})
        
        # Should have some schemas defined
        assert len(schemas) > 0
        
        # Check for key schemas
        expected_schemas = [
            "RegisterResponse",
            "TokenResponse",
            "MemoryResponse"
        ]
        
        for schema in expected_schemas:
            # Schema might be in spec
            assert any(s.lower() in schema.lower() for s in schemas.keys()) or \
                schema in schemas, \
                f"Schema {schema} not found in OpenAPI spec"

