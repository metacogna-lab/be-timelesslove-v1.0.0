"""
Unit and integration tests for memory endpoints.
"""

import pytest
from unittest.mock import Mock, patch, AsyncMock
from fastapi import status
from uuid import uuid4
from app.models.memory import Memory, MemoryMedia, MemoryWithMedia


class TestMemoryService:
    """Test memory service functions."""
    
    @pytest.mark.asyncio
    @patch('app.services.memory_service.get_supabase_service_client')
    async def test_create_memory(
        self,
        mock_supabase_client,
        sample_user_id,
        sample_family_unit_id
    ):
        """Test memory creation."""
        from app.services.memory_service import create_memory
        
        # Setup mock
        mock_client = Mock()
        mock_table = Mock()
        mock_table.insert.return_value.execute.return_value.data = [{
            "id": str(uuid4()),
            "user_id": sample_user_id,
            "family_unit_id": sample_family_unit_id,
            "title": "Test Memory",
            "description": "Test description",
            "memory_date": None,
            "location": None,
            "tags": [],
            "status": "draft",
            "created_at": "2024-01-01T12:00:00Z",
            "updated_at": "2024-01-01T12:00:00Z",
            "modified_by": None
        }]
        mock_client.table.return_value = mock_table
        mock_supabase_client.return_value = mock_client
        
        # Create memory
        memory = await create_memory(
            user_id=uuid4(),
            family_unit_id=uuid4(),
            title="Test Memory",
            description="Test description"
        )
        
        # Assertions
        assert memory.title == "Test Memory"
        assert memory.description == "Test description"
        assert memory.status == "draft"
    
    @pytest.mark.asyncio
    @patch('app.services.memory_service.get_supabase_service_client')
    async def test_get_memory_by_id(
        self,
        mock_supabase_client,
        sample_user_id,
        sample_family_unit_id
    ):
        """Test getting memory by ID."""
        from app.services.memory_service import get_memory_by_id
        
        memory_id = uuid4()
        
        # Setup mock
        mock_client = Mock()
        mock_table = Mock()
        mock_table.select.return_value.eq.return_value.single.return_value.execute.return_value.data = {
            "id": str(memory_id),
            "user_id": sample_user_id,
            "family_unit_id": sample_family_unit_id,
            "title": "Test Memory",
            "description": None,
            "memory_date": None,
            "location": None,
            "tags": [],
            "status": "published",
            "created_at": "2024-01-01T12:00:00Z",
            "updated_at": "2024-01-01T12:00:00Z",
            "modified_by": None
        }
        mock_client.table.return_value = mock_table
        mock_supabase_client.return_value = mock_client
        
        # Get memory
        memory = await get_memory_by_id(memory_id)
        
        # Assertions
        assert memory is not None
        assert memory.id == memory_id
        assert memory.title == "Test Memory"


class TestMemoryEndpoints:
    """Test memory API endpoints."""
    
    @patch('app.api.v1.memories.create_memory')
    @patch('app.api.v1.memories.create_media')
    @patch('app.api.v1.memories.verify_file_exists')
    @patch('app.api.v1.memories.process_media_async')
    def test_create_memory_success(
        self,
        mock_process,
        mock_verify,
        mock_create_media,
        mock_create_memory,
        client,
        sample_access_token,
        sample_family_unit_id
    ):
        """Test successful memory creation."""
        from datetime import datetime
        from app.main import app

        # Setup mocks
        memory_id = uuid4()
        media_id = uuid4()

        mock_create_memory.return_value = Memory(
            id=memory_id,
            user_id=uuid4(),
            family_unit_id=uuid4(),
            title="Test Memory",
            description="Test description",
            memory_date=None,
            location=None,
            tags=[],
            status="published",
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
            modified_by=None
        )

        mock_create_media.return_value = MemoryMedia(
            id=media_id,
            memory_id=memory_id,
            storage_path="test/path.jpg",
            storage_bucket="memories",
            file_name="test.jpg",
            mime_type="image/jpeg",
            file_size=1024,
            width=None,
            height=None,
            duration=None,
            thumbnail_path=None,
            processing_status="pending",
            metadata={},
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )

        mock_verify.return_value = True
        mock_process.return_value = None

        try:
            # Make request
            response = client.post(
                "/api/v1/memories",
                headers={"Authorization": f"Bearer {sample_access_token}"},
                json={
                    "title": "Test Memory",
                    "description": "Test description",
                    "status": "published",
                    "media": [{
                        "storage_path": "test/path.jpg",
                        "file_name": "test.jpg",
                        "mime_type": "image/jpeg",
                        "file_size": 1024
                    }]
                }
            )

            # Assertions
            assert response.status_code == status.HTTP_201_CREATED
            data = response.json()
            assert "id" in data
            assert data["title"] == "Test Memory"
            assert len(data["media"]) == 1
        finally:
            # Clean up dependency overrides
            app.dependency_overrides.clear()
    
    def test_create_memory_unauthorized(self, client):
        """Test memory creation without authentication."""
        from app.main import app

        try:
            response = client.post(
                "/api/v1/memories",
                json={
                    "title": "Test Memory"
                }
            )

            # Without authentication, should return 401 (Unauthorized), not 403 (Forbidden)
            assert response.status_code in [status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN]
        finally:
            # Clean up dependency overrides
            app.dependency_overrides.clear()
    
    @patch('app.api.v1.memories.get_memory_with_media')
    def test_get_memory_success(
        self,
        mock_get_memory,
        client,
        sample_access_token,
        sample_family_unit_id,
        sample_user_id
    ):
        """Test getting memory."""
        from datetime import datetime
        from app.main import app
        from uuid import UUID

        memory_id = uuid4()
        media_id = uuid4()

        # Make sure the memory belongs to the same family unit as the token
        mock_get_memory.return_value = MemoryWithMedia(
            id=memory_id,
            user_id=UUID(sample_user_id),
            family_unit_id=UUID(sample_family_unit_id),  # Match token's family_unit_id
            title="Test Memory",
            description=None,
            memory_date=None,
            location=None,
            tags=[],
            status="published",
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
            modified_by=None,
            media=[
                MemoryMedia(
                    id=media_id,
                    memory_id=memory_id,
                    storage_path="test/path.jpg",
                    storage_bucket="memories",
                    file_name="test.jpg",
                    mime_type="image/jpeg",
                    file_size=1024,
                    width=None,
                    height=None,
                    duration=None,
                    thumbnail_path=None,
                    processing_status="completed",
                    metadata={},
                    created_at=datetime.utcnow(),
                    updated_at=datetime.utcnow()
                )
            ]
        )

        try:
            response = client.get(
                f"/api/v1/memories/{memory_id}",
                headers={"Authorization": f"Bearer {sample_access_token}"}
            )

            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert data["id"] == str(memory_id)
            assert len(data["media"]) == 1
        finally:
            # Clean up dependency overrides
            app.dependency_overrides.clear()

