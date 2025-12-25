"""
Tests for LangGraph PostgreSQL connection pool and checkpointer.

Tests verify that:
1. Connection pool is correctly initialized
2. Database URL construction works with various env configurations
3. Checkpointer setup handles missing dependencies gracefully
4. Pool lifecycle (open/close) works correctly
5. FastAPI dependency injection works
"""

import pytest
import os
from unittest.mock import Mock, patch, AsyncMock, MagicMock
from app.db.graph_db import (
    get_db_url,
    get_connection_pool,
    init_checkpointer,
    get_checkpointer,
    close_pool,
    get_graph_checkpointer,
)


class TestDatabaseURLConstruction:
    """Test database URL construction from environment variables."""

    def test_get_db_url_from_env(self, monkeypatch):
        """Test getting DB URL directly from SUPABASE_DB_URL env var."""
        test_url = "postgresql://postgres.test:password@aws-0-us-east-1.pooler.supabase.com:6543/postgres"
        monkeypatch.setenv("SUPABASE_DB_URL", test_url)

        url = get_db_url()
        assert url == test_url

    def test_get_db_url_constructed(self, monkeypatch, mock_settings):
        """Test constructing DB URL from individual components."""
        # Clear SUPABASE_DB_URL to force construction
        monkeypatch.delenv("SUPABASE_DB_URL", raising=False)
        monkeypatch.setenv("SUPABASE_DB_PASSWORD", "test_password_123")
        monkeypatch.setenv("SUPABASE_DB_REGION", "us-west-1")

        # Mock settings to return test Supabase URL
        with patch("app.db.graph_db.get_settings") as mock_get_settings:
            mock_get_settings.return_value = Mock(
                supabase_url="https://fjevxcnpgydosicdyugt.supabase.co"
            )

            url = get_db_url()

            # Should construct URL with project ref extracted from supabase_url
            assert "postgresql://postgres.fjevxcnpgydosicdyugt:" in url
            assert "test_password_123" in url
            assert "aws-0-us-west-1.pooler.supabase.com:6543" in url

    def test_get_db_url_missing_credentials(self, monkeypatch):
        """Test that missing credentials raise ValueError."""
        # Clear all database-related env vars
        monkeypatch.delenv("SUPABASE_DB_URL", raising=False)
        monkeypatch.delenv("SUPABASE_DB_PASSWORD", raising=False)

        with pytest.raises(ValueError) as exc_info:
            get_db_url()

        assert "Missing database configuration" in str(exc_info.value)
        assert "SUPABASE_DB_URL" in str(exc_info.value)

    def test_get_db_url_default_region(self, monkeypatch):
        """Test that default region (us-east-1) is used when not specified."""
        monkeypatch.delenv("SUPABASE_DB_URL", raising=False)
        monkeypatch.setenv("SUPABASE_DB_PASSWORD", "test_password")
        monkeypatch.delenv("SUPABASE_DB_REGION", raising=False)

        with patch("app.db.graph_db.get_settings") as mock_get_settings:
            mock_get_settings.return_value = Mock(
                supabase_url="https://testproject.supabase.co"
            )

            url = get_db_url()

            # Should use default region us-east-1
            assert "aws-0-us-east-1.pooler.supabase.com" in url


@pytest.mark.asyncio
class TestConnectionPool:
    """Test connection pool creation and management."""

    async def test_get_connection_pool_creates_singleton(self, monkeypatch):
        """Test that connection pool is a singleton."""
        test_url = "postgresql://postgres:password@localhost:6543/postgres"
        monkeypatch.setenv("SUPABASE_DB_URL", test_url)

        with patch("app.db.graph_db.AsyncConnectionPool") as MockPool:
            mock_pool_instance = Mock()
            MockPool.return_value = mock_pool_instance

            # First call should create pool
            pool1 = get_connection_pool()
            assert pool1 == mock_pool_instance
            assert MockPool.call_count == 1

            # Second call should return same instance
            pool2 = get_connection_pool()
            assert pool2 == mock_pool_instance
            assert MockPool.call_count == 1  # Not called again

    async def test_connection_pool_configuration(self, monkeypatch):
        """Test that connection pool is configured correctly."""
        test_url = "postgresql://postgres:password@localhost:6543/postgres"
        monkeypatch.setenv("SUPABASE_DB_URL", test_url)

        # Clear global pool
        import app.db.graph_db as graph_db

        graph_db._pool = None

        with patch("app.db.graph_db.AsyncConnectionPool") as MockPool:
            get_connection_pool()

            # Verify pool was created with correct parameters
            MockPool.assert_called_once()
            call_kwargs = MockPool.call_args[1]

            assert call_kwargs["conninfo"] == test_url
            assert call_kwargs["min_size"] == 2
            assert call_kwargs["max_size"] == 10
            assert call_kwargs["timeout"] == 30
            assert call_kwargs["kwargs"]["autocommit"] is True
            assert call_kwargs["kwargs"]["prepare_threshold"] == 0

    async def test_close_pool(self, monkeypatch):
        """Test that pool closure works correctly."""
        test_url = "postgresql://postgres:password@localhost:6543/postgres"
        monkeypatch.setenv("SUPABASE_DB_URL", test_url)

        # Create mock pool
        import app.db.graph_db as graph_db

        mock_pool = AsyncMock()
        graph_db._pool = mock_pool

        # Close pool
        await close_pool()

        # Verify close was called
        mock_pool.close.assert_called_once()

        # Verify globals are reset
        assert graph_db._pool is None
        assert graph_db._checkpointer is None

    async def test_close_pool_when_not_initialized(self):
        """Test closing pool when it was never created."""
        import app.db.graph_db as graph_db

        graph_db._pool = None

        # Should not raise error
        await close_pool()

        # Should still be None
        assert graph_db._pool is None


@pytest.mark.asyncio
class TestCheckpointerInitialization:
    """Test LangGraph checkpointer initialization."""

    async def test_init_checkpointer_creates_singleton(self, monkeypatch):
        """Test that checkpointer is a singleton."""
        test_url = "postgresql://postgres:password@localhost:6543/postgres"
        monkeypatch.setenv("SUPABASE_DB_URL", test_url)

        # Reset globals
        import app.db.graph_db as graph_db

        graph_db._checkpointer = None
        graph_db._pool = None

        with patch("app.db.graph_db.AsyncConnectionPool") as MockPool, patch(
            "app.db.graph_db.PostgresSaver"
        ) as MockSaver:

            # Setup mocks
            mock_pool = AsyncMock()
            mock_conn = AsyncMock()

            # Create a properly async context manager for pool.connection()
            mock_context_manager = AsyncMock()
            mock_context_manager.__aenter__ = AsyncMock(return_value=mock_conn)
            mock_context_manager.__aexit__ = AsyncMock(return_value=None)
            mock_pool.connection = Mock(return_value=mock_context_manager)

            MockPool.return_value = mock_pool

            mock_saver = AsyncMock()
            mock_saver.setup = AsyncMock()
            MockSaver.return_value = mock_saver

            # First call should create checkpointer
            checkpointer1 = await init_checkpointer()
            assert checkpointer1 == mock_saver
            assert MockSaver.call_count == 1

            # Setup should be called
            mock_saver.setup.assert_called_once_with(mock_conn)

            # Second call should return same instance
            checkpointer2 = await init_checkpointer()
            assert checkpointer2 == mock_saver
            assert MockSaver.call_count == 1  # Not called again

    async def test_init_checkpointer_calls_setup(self, monkeypatch):
        """Test that checkpointer setup is called during initialization."""
        test_url = "postgresql://postgres:password@localhost:6543/postgres"
        monkeypatch.setenv("SUPABASE_DB_URL", test_url)

        # Reset globals
        import app.db.graph_db as graph_db

        graph_db._checkpointer = None
        graph_db._pool = None

        with patch("app.db.graph_db.AsyncConnectionPool") as MockPool, patch(
            "app.db.graph_db.PostgresSaver"
        ) as MockSaver:

            # Setup mocks
            mock_pool = AsyncMock()
            mock_conn = AsyncMock()

            # Create a mock context manager for pool.connection()
            mock_context_manager = AsyncMock()
            mock_context_manager.__aenter__ = AsyncMock(return_value=mock_conn)
            mock_context_manager.__aexit__ = AsyncMock(return_value=None)
            mock_pool.connection = Mock(return_value=mock_context_manager)

            MockPool.return_value = mock_pool

            mock_saver = AsyncMock()
            mock_saver.setup = AsyncMock()
            MockSaver.return_value = mock_saver

            # Initialize checkpointer
            await init_checkpointer()

            # Verify setup was called with connection
            mock_saver.setup.assert_called_once_with(mock_conn)

    async def test_get_checkpointer_before_init(self):
        """Test getting checkpointer before initialization returns None."""
        import app.db.graph_db as graph_db

        graph_db._checkpointer = None

        checkpointer = get_checkpointer()
        assert checkpointer is None

    async def test_get_checkpointer_after_init(self, monkeypatch):
        """Test getting checkpointer after initialization."""
        test_url = "postgresql://postgres:password@localhost:6543/postgres"
        monkeypatch.setenv("SUPABASE_DB_URL", test_url)

        # Reset globals
        import app.db.graph_db as graph_db

        graph_db._checkpointer = None
        graph_db._pool = None

        with patch("app.db.graph_db.AsyncConnectionPool") as MockPool, patch(
            "app.db.graph_db.PostgresSaver"
        ) as MockSaver:

            mock_pool = AsyncMock()
            mock_conn = AsyncMock()

            # Create a properly async context manager for pool.connection()
            mock_context_manager = AsyncMock()
            mock_context_manager.__aenter__ = AsyncMock(return_value=mock_conn)
            mock_context_manager.__aexit__ = AsyncMock(return_value=None)
            mock_pool.connection = Mock(return_value=mock_context_manager)

            MockPool.return_value = mock_pool

            mock_saver = AsyncMock()
            mock_saver.setup = AsyncMock()
            MockSaver.return_value = mock_saver

            # Initialize
            await init_checkpointer()

            # Get checkpointer
            checkpointer = get_checkpointer()
            assert checkpointer == mock_saver


@pytest.mark.asyncio
class TestFastAPIDependency:
    """Test FastAPI dependency injection for checkpointer."""

    async def test_get_graph_checkpointer_when_initialized(self, monkeypatch):
        """Test dependency returns checkpointer when initialized."""
        import app.db.graph_db as graph_db

        mock_checkpointer = Mock()
        graph_db._checkpointer = mock_checkpointer

        result = await get_graph_checkpointer()
        assert result == mock_checkpointer

    async def test_get_graph_checkpointer_not_initialized(self):
        """Test dependency raises error when checkpointer not initialized."""
        import app.db.graph_db as graph_db

        graph_db._checkpointer = None

        with pytest.raises(RuntimeError) as exc_info:
            await get_graph_checkpointer()

        assert "not initialized" in str(exc_info.value)
        assert "init_checkpointer()" in str(exc_info.value)


@pytest.mark.asyncio
class TestDatabaseConnection:
    """Test direct database connection context manager."""

    async def test_get_db_connection_context_manager(self, monkeypatch):
        """Test that get_db_connection provides a connection."""
        test_url = "postgresql://postgres:password@localhost:6543/postgres"
        monkeypatch.setenv("SUPABASE_DB_URL", test_url)

        # Reset globals
        import app.db.graph_db as graph_db

        graph_db._pool = None

        with patch("app.db.graph_db.AsyncConnectionPool") as MockPool:
            mock_pool = AsyncMock()
            mock_conn = AsyncMock()

            # Create a properly async context manager for pool.connection()
            mock_context_manager = AsyncMock()
            mock_context_manager.__aenter__ = AsyncMock(return_value=mock_conn)
            mock_context_manager.__aexit__ = AsyncMock(return_value=None)
            mock_pool.connection = Mock(return_value=mock_context_manager)

            MockPool.return_value = mock_pool

            # Use context manager
            from app.db.graph_db import get_db_connection

            async with get_db_connection() as conn:
                assert conn == mock_conn

            # Verify connection context was entered
            mock_pool.connection.assert_called_once()


@pytest.mark.asyncio
class TestIntegration:
    """Integration tests for full workflow."""

    async def test_full_initialization_workflow(self, monkeypatch):
        """Test complete initialization workflow."""
        test_url = "postgresql://postgres:password@localhost:6543/postgres"
        monkeypatch.setenv("SUPABASE_DB_URL", test_url)

        # Reset globals
        import app.db.graph_db as graph_db

        graph_db._pool = None
        graph_db._checkpointer = None

        with patch("app.db.graph_db.AsyncConnectionPool") as MockPool, patch(
            "app.db.graph_db.PostgresSaver"
        ) as MockSaver:

            # Setup mocks
            mock_pool = AsyncMock()
            mock_conn = AsyncMock()

            # Create a properly async context manager for pool.connection()
            mock_context_manager = AsyncMock()
            mock_context_manager.__aenter__ = AsyncMock(return_value=mock_conn)
            mock_context_manager.__aexit__ = AsyncMock(return_value=None)
            mock_pool.connection = Mock(return_value=mock_context_manager)
            mock_pool.close = AsyncMock()

            MockPool.return_value = mock_pool

            mock_saver = AsyncMock()
            mock_saver.setup = AsyncMock()
            MockSaver.return_value = mock_saver

            # 1. Initialize checkpointer
            checkpointer = await init_checkpointer()
            assert checkpointer is not None

            # 2. Get checkpointer (should return same instance)
            same_checkpointer = get_checkpointer()
            assert same_checkpointer == checkpointer

            # 3. Use as FastAPI dependency
            dep_checkpointer = await get_graph_checkpointer()
            assert dep_checkpointer == checkpointer

            # 4. Close pool
            await close_pool()
            mock_pool.close.assert_called_once()

            # 5. Verify cleanup
            assert graph_db._pool is None
            assert graph_db._checkpointer is None
