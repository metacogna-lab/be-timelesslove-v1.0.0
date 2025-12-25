"""
Tests for feed and interaction endpoints.
"""

import pytest
from uuid import uuid4
from unittest.mock import Mock, AsyncMock, patch
from fastapi.testclient import TestClient
from app.main import app
from app.models.user import CurrentUser
from app.services.reaction_service import ReactionService
from app.services.comment_service import CommentService
from app.services.feed_service import FeedService


client = TestClient(app)


@pytest.fixture
def mock_current_user():
    """Mock current user."""
    from app.models.user import CurrentUser
    return CurrentUser(
        user_id=uuid4(),
        role="adult",
        family_unit_id=uuid4(),
        email="test@example.com"
    )


@pytest.fixture
def mock_memory_id():
    """Mock memory ID."""
    return uuid4()


class TestReactions:
    """Tests for reaction endpoints."""

    @patch("app.api.v1.feed.ReactionService")
    def test_create_reaction(self, mock_service_class, mock_memory_id, sample_access_token):
        """Test creating a reaction."""
        mock_service = Mock()
        mock_service.create_reaction = AsyncMock()
        mock_reaction = Mock()
        mock_reaction.id = uuid4()
        mock_reaction.memory_id = mock_memory_id
        mock_reaction.user_id = uuid4()  # sample user id
        mock_reaction.emoji = "👍"
        mock_reaction.created_at = Mock()
        mock_reaction.created_at.isoformat = Mock(return_value="2024-01-01T00:00:00")
        mock_reaction.updated_at = Mock()
        mock_reaction.updated_at.isoformat = Mock(return_value="2024-01-01T00:00:00")
        mock_service.create_reaction.return_value = mock_reaction
        mock_service_class.return_value = mock_service

        response = client.post(
            f"/api/v1/feed/memories/{mock_memory_id}/reactions",
            json={"emoji": "👍"},
            headers={"Authorization": f"Bearer {sample_access_token}"}
        )

        assert response.status_code == 200
        assert response.json()["emoji"] == "👍"
        mock_service.create_reaction.assert_called_once()
    
    @patch("app.api.v1.feed.ReactionService")
    def test_create_reaction_invalid_emoji(self, mock_service_class, mock_memory_id, sample_access_token):
        """Test creating a reaction with invalid emoji."""
        response = client.post(
            f"/api/v1/feed/memories/{mock_memory_id}/reactions",
            json={"emoji": "invalid"},
            headers={"Authorization": f"Bearer {sample_access_token}"}
        )

        assert response.status_code == 422  # Validation error
    
    @patch("app.api.v1.feed.ReactionService")
    def test_delete_reaction(self, mock_service_class, mock_current_user, mock_memory_id, sample_access_token):
        """Test deleting a reaction."""
        # Override the dependency to return mock user
        from app.dependencies import get_current_user_model
        app.dependency_overrides[get_current_user_model] = lambda: mock_current_user

        mock_service = Mock()
        mock_service.delete_reaction = AsyncMock()
        mock_service_class.return_value = mock_service

        try:
            # Use a valid UUID for reaction_id
            reaction_id = uuid4()
            response = client.delete(
                f"/api/v1/feed/memories/{mock_memory_id}/reactions/{reaction_id}",
                headers={"Authorization": f"Bearer {sample_access_token}"}
            )

            assert response.status_code == 200
            mock_service.delete_reaction.assert_called_once()
        finally:
            # Clean up dependency override
            app.dependency_overrides.clear()


class TestComments:
    """Tests for comment endpoints."""
    
    @patch("app.api.v1.feed.CommentService")
    def test_create_comment(self, mock_service_class, mock_current_user, mock_memory_id, sample_access_token):
        """Test creating a comment."""
        # Override the dependency to return mock user
        from app.dependencies.rbac import exclude_pets_for_current_user
        app.dependency_overrides[exclude_pets_for_current_user] = lambda: mock_current_user

        mock_service = Mock()
        mock_service.create_comment = AsyncMock()
        mock_comment = Mock()
        mock_comment.id = uuid4()
        mock_comment.memory_id = mock_memory_id
        mock_comment.user_id = mock_current_user.user_id
        mock_comment.parent_comment_id = None
        mock_comment.content = "Test comment"
        mock_comment.created_at = Mock()
        mock_comment.created_at.isoformat = Mock(return_value="2024-01-01T00:00:00")
        mock_comment.updated_at = Mock()
        mock_comment.updated_at.isoformat = Mock(return_value="2024-01-01T00:00:00")
        mock_comment.deleted_at = None
        mock_service.create_comment.return_value = mock_comment
        mock_service_class.return_value = mock_service

        try:
            response = client.post(
                f"/api/v1/feed/memories/{mock_memory_id}/comments",
                json={"content": "Test comment"},
                headers={"Authorization": f"Bearer {sample_access_token}"}
            )

            assert response.status_code == 200
            assert response.json()["content"] == "Test comment"
            mock_service.create_comment.assert_called_once()
        finally:
            # Clean up dependency override
            app.dependency_overrides.clear()
    
    @patch("app.api.v1.feed.CommentService")
    def test_create_comment_empty_content(self, mock_service_class, mock_current_user, mock_memory_id, sample_access_token):
        """Test creating a comment with empty content."""
        # Override the dependency to return mock user
        from app.dependencies.rbac import exclude_pets_for_current_user
        app.dependency_overrides[exclude_pets_for_current_user] = lambda: mock_current_user

        try:
            response = client.post(
                f"/api/v1/feed/memories/{mock_memory_id}/comments",
                json={"content": "   "},
                headers={"Authorization": f"Bearer {sample_access_token}"}
            )

            assert response.status_code == 422  # Validation error
        finally:
            # Clean up dependency override
            app.dependency_overrides.clear()
    
    @patch("app.api.v1.feed.CommentService")
    def test_update_comment(self, mock_service_class, mock_current_user, mock_memory_id, sample_access_token):
        """Test updating a comment."""
        # Override the dependency to return mock user
        from app.dependencies.rbac import exclude_pets_for_current_user
        app.dependency_overrides[exclude_pets_for_current_user] = lambda: mock_current_user

        mock_service = Mock()
        mock_service.update_comment = AsyncMock()
        mock_comment = Mock()
        mock_comment.id = uuid4()
        mock_comment.memory_id = mock_memory_id
        mock_comment.user_id = mock_current_user.user_id
        mock_comment.parent_comment_id = None
        mock_comment.content = "Updated comment"
        mock_comment.created_at = Mock()
        mock_comment.created_at.isoformat = Mock(return_value="2024-01-01T00:00:00")
        mock_comment.updated_at = Mock()
        mock_comment.updated_at.isoformat = Mock(return_value="2024-01-01T00:00:00")
        mock_comment.deleted_at = None
        mock_service.update_comment.return_value = mock_comment
        mock_service_class.return_value = mock_service

        try:
            comment_id = uuid4()
            response = client.put(
                f"/api/v1/feed/memories/{mock_memory_id}/comments/{comment_id}",
                json={"content": "Updated comment"},
                headers={"Authorization": f"Bearer {sample_access_token}"}
            )

            assert response.status_code == 200
            assert response.json()["content"] == "Updated comment"
            mock_service.update_comment.assert_called_once()
        finally:
            # Clean up dependency override
            app.dependency_overrides.clear()


class TestFeed:
    """Tests for feed endpoint."""
    
    @patch("app.api.v1.feed.FeedService")
    def test_get_feed(self, mock_service_class, mock_current_user, sample_access_token):
        """Test getting the feed."""
        # Override the dependency to return mock user
        from app.dependencies import get_current_user_model
        app.dependency_overrides[get_current_user_model] = lambda: mock_current_user

        mock_service = Mock()
        mock_service.get_feed = AsyncMock()
        mock_service.get_feed.return_value = {
            "items": [],
            "pagination": {"page": 1, "page_size": 20, "total_pages": 0, "has_more": False},
            "total_count": 0,
            "has_more": False
        }
        mock_service_class.return_value = mock_service

        try:
            response = client.get(
                "/api/v1/feed",
                headers={"Authorization": f"Bearer {sample_access_token}"}
            )

            assert response.status_code == 200
            assert "items" in response.json()
            mock_service.get_feed.assert_called_once()
        finally:
            # Clean up dependency override
            app.dependency_overrides.clear()
    
    @patch("app.api.v1.feed.FeedService")
    def test_get_feed_with_filters(self, mock_service_class, mock_current_user, sample_access_token):
        """Test getting the feed with filters."""
        # Override the dependency to return mock user
        from app.dependencies import get_current_user_model
        app.dependency_overrides[get_current_user_model] = lambda: mock_current_user

        mock_service = Mock()
        mock_service.get_feed = AsyncMock()
        mock_service.get_feed.return_value = {
            "items": [],
            "pagination": {"page": 1, "page_size": 20, "total_pages": 0, "has_more": False},
            "total_count": 0,
            "has_more": False
        }
        mock_service_class.return_value = mock_service

        try:
            response = client.get(
                "/api/v1/feed?status=published&tags=family&page=1&page_size=10",
                headers={"Authorization": f"Bearer {sample_access_token}"}
            )

            assert response.status_code == 200
            mock_service.get_feed.assert_called_once()
        finally:
            # Clean up dependency override
            app.dependency_overrides.clear()


class TestFeedService:
    """Tests for FeedService."""
    
    @pytest.mark.asyncio
    async def test_calculate_feed_score(self):
        """Test feed score calculation."""
        from datetime import datetime, timedelta
        from app.models.feed import MemoryEngagement
        
        service = FeedService()
        
        # Test recent memory with high engagement
        recent_time = (datetime.utcnow() - timedelta(hours=1)).isoformat()
        high_engagement = MemoryEngagement(
            memory_id=uuid4(),
            reaction_count=10,
            comment_count=5,
            unique_reactors=8,
            reactions_by_emoji={"👍": 5, "❤️": 5},
            feed_score=0.0
        )
        
        score = await service._calculate_feed_score(recent_time, high_engagement)
        assert score > 0
        
        # Test old memory with low engagement
        old_time = (datetime.utcnow() - timedelta(days=60)).isoformat()
        low_engagement = MemoryEngagement(
            memory_id=uuid4(),
            reaction_count=1,
            comment_count=0,
            unique_reactors=1,
            reactions_by_emoji={"👍": 1},
            feed_score=0.0
        )
        
        score_old = await service._calculate_feed_score(old_time, low_engagement)
        assert score > score_old  # Recent with engagement should score higher

