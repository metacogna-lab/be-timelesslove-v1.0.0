"""
Unit tests for adapter layer.
"""

import pytest
from datetime import date, datetime
from adapters.transformers.request import RequestTransformer
from adapters.transformers.response import ResponseTransformer
from adapters.transformers.errors import ErrorTransformer
from adapters.validators.schemas import (
    FrontendMemoryRequest,
    FrontendFeedFilters,
    FrontendAuthRequest,
    FrontendInviteRequest,
)
from adapters.middleware.sanitization import Sanitizer
from httpx import HTTPStatusError, Response, Request


class TestRequestTransformer:
    """Test request transformation."""
    
    def test_normalize_date_string(self):
        """Test date normalization from string."""
        transformer = RequestTransformer()
        
        # ISO date string
        assert transformer._normalize_date("2024-07-15") == "2024-07-15"
        
        # Datetime string
        assert transformer._normalize_date("2024-07-15T10:30:00Z") == "2024-07-15"
        
        # Date object
        assert transformer._normalize_date(date(2024, 7, 15)) == "2024-07-15"
        
        # Datetime object
        assert transformer._normalize_date(datetime(2024, 7, 15, 10, 30)) == "2024-07-15"
        
        # None
        assert transformer._normalize_date(None) is None
    
    def test_transform_memory_request(self):
        """Test memory request transformation."""
        transformer = RequestTransformer()
        
        data = {
            "title": "Vacation",
            "memory_date": "2024-07-15",
            "tags": ["beach", "summer"],
            "status": "published",
        }
        
        result = transformer.transform_memory_request(data)
        
        assert result["title"] == "Vacation"
        assert result["memory_date"] == "2024-07-15"
        assert result["tags"] == ["beach", "summer"]
        assert result["status"] == "published"
    
    def test_transform_memory_request_tags_string(self):
        """Test memory request with tags as string."""
        transformer = RequestTransformer()
        
        data = {
            "tags": "beach,summer,vacation",
        }
        
        result = transformer.transform_memory_request(data)
        assert result["tags"] == ["beach", "summer", "vacation"]
    
    def test_transform_feed_filters(self):
        """Test feed filter transformation."""
        transformer = RequestTransformer()
        
        params = {
            "page": 1,
            "page_size": 20,
            "tags": "beach,summer",
            "order_by": "feed_score",
            "order_direction": "desc",
        }
        
        result = transformer.transform_feed_filters(params)
        
        assert result["page"] == 1
        assert result["page_size"] == 20
        assert result["tags"] == "beach,summer"  # Backend expects string
        assert result["order_by"] == "feed_score"
        assert result["order_direction"] == "desc"


class TestResponseTransformer:
    """Test response transformation."""
    
    def test_transform_memory_response(self):
        """Test memory response transformation."""
        transformer = ResponseTransformer()
        
        data = {
            "id": "550e8400-e29b-41d4-a716-446655440000",
            "user_id": "660e8400-e29b-41d4-a716-446655440001",
            "title": "Vacation",
            "tags": ["beach", "summer"],
            "media": [],
        }
        
        result = transformer.transform_memory_response(data)
        
        assert result["id"] == "550e8400-e29b-41d4-a716-446655440000"
        assert result["user_id"] == "660e8400-e29b-41d4-a716-446655440001"
        assert result["title"] == "Vacation"
        assert isinstance(result["tags"], list)
    
    def test_transform_feed_response(self):
        """Test feed response transformation."""
        transformer = ResponseTransformer()
        
        data = {
            "items": [
                {
                    "id": "memory-id",
                    "reaction_count": 5,
                    "comment_count": 3,
                }
            ],
            "pagination": {
                "page": 1,
                "page_size": 20,
            },
            "total_count": 100,
        }
        
        result = transformer.transform_feed_response(data)
        
        assert len(result["items"]) == 1
        assert result["pagination"]["page"] == 1
        assert result["pagination"]["total_pages"] == 5  # Calculated
        assert result["has_more"] is True


class TestErrorTransformer:
    """Test error transformation."""
    
    def test_transform_http_error(self):
        """Test HTTP error transformation."""
        transformer = ErrorTransformer()
        
        # Create mock HTTP error
        request = Request("POST", "http://example.com/test")
        response = Response(400, json={"detail": "Validation failed"})
        error = HTTPStatusError("Bad Request", request=request, response=response)
        
        result = transformer.transform_error(error, "/test", "POST")
        
        assert "error" in result
        assert result["error"]["code"] == "VALIDATION_ERROR"
        assert result["error"]["status_code"] == 400


class TestValidators:
    """Test validation schemas."""
    
    def test_frontend_memory_request_valid(self):
        """Test valid memory request."""
        request = FrontendMemoryRequest(
            title="Vacation",
            memory_date="2024-07-15",
            tags=["beach"],
            status="published",
        )
        
        assert request.title == "Vacation"
        assert request.memory_date == "2024-07-15"
        assert request.tags == ["beach"]
        assert request.status == "published"
    
    def test_frontend_memory_request_invalid_date(self):
        """Test invalid date format."""
        with pytest.raises(Exception):  # Pydantic validation error
            FrontendMemoryRequest(
                title="Vacation",
                memory_date="2024/07/15",  # Invalid format
                status="published",
            )
    
    def test_frontend_feed_filters_valid(self):
        """Test valid feed filters."""
        filters = FrontendFeedFilters(
            page=1,
            page_size=20,
            order_by="feed_score",
            order_direction="desc",
        )
        
        assert filters.page == 1
        assert filters.page_size == 20
        assert filters.order_by == "feed_score"
        assert filters.order_direction == "desc"
    
    def test_frontend_auth_request_valid(self):
        """Test valid auth request."""
        request = FrontendAuthRequest(
            email="user@example.com",
            password="SecurePass123!",
            display_name="John Doe",
        )
        
        assert request.email == "user@example.com"
        assert request.password == "SecurePass123!"
        assert request.display_name == "John Doe"


class TestSanitizer:
    """Test sanitization utilities."""
    
    def test_sanitize_string(self):
        """Test string sanitization."""
        sanitizer = Sanitizer()
        
        # Control characters removed
        result = sanitizer.sanitize_string("test\x00\x1fstring")
        assert result == "teststring"
        
        # Truncation
        result = sanitizer.sanitize_string("very long string", max_length=10)
        assert result == "very long "
    
    def test_sanitize_dict(self):
        """Test dictionary sanitization."""
        sanitizer = Sanitizer()
        
        data = {
            "title": "Test\x00Title",
            "description": "Description",
            "nested": {
                "value": "Nested\x1fValue",
            },
        }
        
        result = sanitizer.sanitize_dict(data)
        
        assert "\x00" not in result["title"]
        assert "\x1f" not in result["nested"]["value"]
    
    def test_remove_sensitive_data(self):
        """Test sensitive data removal."""
        sanitizer = Sanitizer()
        
        data = {
            "email": "user@example.com",
            "password": "secret123",
            "token": "abc123",
            "display_name": "John Doe",
        }
        
        result = sanitizer.remove_sensitive_data(data)
        
        assert result["email"] == "user@example.com"
        assert result["password"] == "[REDACTED]"
        assert result["token"] == "[REDACTED]"
        assert result["display_name"] == "John Doe"

