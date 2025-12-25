"""
Unit and integration tests for storage endpoints.
"""

import pytest
from unittest.mock import Mock, patch
from fastapi import status
from uuid import uuid4


class TestStorageService:
    """Test storage service functions."""
    
    @pytest.mark.asyncio
    @patch('app.services.storage_service.get_supabase_service_client')
    async def test_generate_upload_url(
        self,
        mock_supabase_client,
        sample_family_unit_id
    ):
        """Test upload URL generation."""
        from app.services.storage_service import generate_upload_url
        
        # Setup mock
        mock_client = Mock()
        mock_storage = Mock()
        mock_bucket = Mock()
        mock_bucket.create_signed_upload_url.return_value = {
            "signedUrl": "https://example.com/upload-url"
        }
        mock_storage.from_.return_value = mock_bucket
        mock_client.storage = mock_storage
        mock_supabase_client.return_value = mock_client
        
        # Generate URL
        url = generate_upload_url(
            family_unit_id=uuid4(),
            memory_id=uuid4(),
            file_name="test.jpg"
        )
        
        # Assertions
        assert url is not None
        assert isinstance(url, str)
    
    @pytest.mark.asyncio
    @patch('app.services.storage_service.get_supabase_service_client')
    async def test_generate_access_url(
        self,
        mock_supabase_client
    ):
        """Test access URL generation."""
        from app.services.storage_service import generate_access_url
        
        # Setup mock
        mock_client = Mock()
        mock_storage = Mock()
        mock_bucket = Mock()
        mock_bucket.create_signed_url.return_value = {
            "signedUrl": "https://example.com/access-url"
        }
        mock_storage.from_.return_value = mock_bucket
        mock_client.storage = mock_storage
        mock_supabase_client.return_value = mock_client
        
        # Generate URL
        url = generate_access_url("550e8400-e29b-41d4-a716-446655440000/660e8400-e29b-41d4-a716-446655440001/test.jpg")
        
        # Assertions
        assert url is not None
        assert isinstance(url, str)


class TestStorageEndpoints:
    """Test storage API endpoints."""
    
    @pytest.mark.asyncio
    @patch('app.api.v1.storage.generate_upload_url')
    async def test_create_upload_url_success(
        self,
        mock_generate_url,
        client,
        sample_access_token
    ):
        """Test successful upload URL generation."""
        memory_id = uuid4()
        
        mock_generate_url.return_value = "https://example.com/upload-url"
        
        response = client.post(
            "/api/v1/storage/upload-url",
            headers={"Authorization": f"Bearer {sample_access_token}"},
            json={
                "memory_id": str(memory_id),
                "file_name": "photo.jpg",
                "mime_type": "image/jpeg"
            }
        )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "upload_url" in data
        assert "storage_path" in data
        assert "expires_in" in data
    
    def test_create_upload_url_invalid_mime_type(
        self,
        client,
        sample_access_token
    ):
        """Test upload URL generation with invalid MIME type."""
        memory_id = uuid4()
        
        response = client.post(
            "/api/v1/storage/upload-url",
            headers={"Authorization": f"Bearer {sample_access_token}"},
            json={
                "memory_id": str(memory_id),
                "file_name": "file.exe",
                "mime_type": "application/x-msdownload"
            }
        )
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
    
    @pytest.mark.asyncio
    @patch('app.api.v1.storage.generate_access_url')
    async def test_create_access_url_success(
        self,
        mock_generate_url,
        client,
        sample_access_token,
        sample_family_unit_id
    ):
        """Test successful access URL generation."""
        storage_path = f"{sample_family_unit_id}/memory-id/file.jpg"
        
        mock_generate_url.return_value = "https://example.com/access-url"
        
        response = client.get(
            f"/api/v1/storage/access-url?storage_path={storage_path}",
            headers={"Authorization": f"Bearer {sample_access_token}"}
        )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "access_url" in data
        assert "expires_in" in data
    
    def test_create_access_url_wrong_family(
        self,
        client,
        sample_access_token
    ):
        """Test access URL generation for different family."""
        storage_path = "different-family-id/memory-id/file.jpg"
        
        response = client.get(
            f"/api/v1/storage/access-url?storage_path={storage_path}",
            headers={"Authorization": f"Bearer {sample_access_token}"}
        )
        
        assert response.status_code == status.HTTP_403_FORBIDDEN


class TestMediaProcessor:
    """Test media processing functions."""
    
    def test_generate_thumbnail(self):
        """Test thumbnail generation."""
        from PIL import Image
        from app.services.media_processor import generate_thumbnail
        
        # Create test image
        image = Image.new('RGB', (1000, 800), color='red')
        
        # Generate thumbnail
        thumbnail = generate_thumbnail(image, 400)
        
        # Assertions
        assert thumbnail is not None
        assert thumbnail.size[0] <= 400 or thumbnail.size[1] <= 400
        assert thumbnail.size[0] > 0 and thumbnail.size[1] > 0
    
    def test_validate_file_name(self):
        """Test file name validation."""
        from app.utils.media import validate_file_name
        
        assert validate_file_name("photo.jpg") is True
        assert validate_file_name("photo_123.jpg") is True
        assert validate_file_name("../photo.jpg") is False
        assert validate_file_name("photo/name.jpg") is False
        assert validate_file_name("photo\\name.jpg") is False
    
    def test_is_allowed_mime_type(self):
        """Test MIME type validation."""
        from app.utils.media import is_allowed_mime_type
        
        assert is_allowed_mime_type("image/jpeg") is True
        assert is_allowed_mime_type("image/png") is True
        assert is_allowed_mime_type("video/mp4") is True
        assert is_allowed_mime_type("application/pdf") is False
        assert is_allowed_mime_type("text/plain") is False

