"""
LangGraph checkpoint persistence layer using Supabase PostgreSQL.

This module provides connection pooling and checkpoint management for
LangGraph agents using the Supabase Transaction Pooler (Port 6543).

CRITICAL: Use the Transaction Pooler connection string to avoid exhausting
standard connections due to frequent checkpoint writes.

Environment Variables Required:
    SUPABASE_DB_URL: PostgreSQL connection string for transaction pooler
        Format: postgresql://postgres.{ref}:{password}@aws-0-{region}.pooler.supabase.com:6543/postgres
"""

import os
from typing import Optional
from contextlib import asynccontextmanager
from psycopg_pool import AsyncConnectionPool
from langgraph.checkpoint.postgres import PostgresSaver
from app.config import get_settings


# Global connection pool instance
_pool: Optional[AsyncConnectionPool] = None
_checkpointer: Optional[PostgresSaver] = None


def get_db_url() -> str:
    """
    Get Supabase PostgreSQL connection URL for LangGraph.

    Returns the transaction pooler URL (port 6543) for optimal performance.

    Returns:
        PostgreSQL connection string

    Raises:
        ValueError: If SUPABASE_DB_URL is not configured
    """
    db_url = os.getenv("SUPABASE_DB_URL")

    if not db_url:
        # Try to construct from existing env vars if SUPABASE_DB_URL not set
        settings = get_settings()
        db_password = os.getenv("SUPABASE_DB_PASSWORD")

        if not db_password:
            raise ValueError(
                "Missing database configuration. Set SUPABASE_DB_URL or SUPABASE_DB_PASSWORD.\n"
                "Get your connection string from Supabase Dashboard > Project Settings > Database.\n"
                "Use the Transaction Pooler connection (Port 6543) for LangGraph."
            )

        # Extract project ref from Supabase URL
        # https://fjevxcnpgydosicdyugt.supabase.co -> fjevxcnpgydosicdyugt
        project_ref = settings.supabase_url.split("//")[1].split(".")[0]

        # Construct transaction pooler URL
        # Note: Region detection would require additional logic; defaulting to us-east-1
        region = os.getenv("SUPABASE_DB_REGION", "us-east-1")
        db_url = f"postgresql://postgres.{project_ref}:{db_password}@aws-0-{region}.pooler.supabase.com:6543/postgres"

        print(
            f"⚠️  SUPABASE_DB_URL not found. Using constructed URL.\n"
            f"   For production, set SUPABASE_DB_URL explicitly in .env"
        )

    return db_url


def get_connection_pool() -> AsyncConnectionPool:
    """
    Get or create PostgreSQL connection pool for LangGraph.

    Connection pool configuration:
    - min_size=2: Minimum connections to keep alive
    - max_size=10: Maximum concurrent connections
    - timeout=30: Connection acquisition timeout (seconds)

    Returns:
        AsyncConnectionPool instance

    Raises:
        ValueError: If database URL is not configured
    """
    global _pool

    if _pool is None:
        db_url = get_db_url()

        _pool = AsyncConnectionPool(
            conninfo=db_url,
            min_size=2,
            max_size=10,
            timeout=30,
            kwargs={
                "autocommit": True,  # Required for LangGraph checkpointing
                "prepare_threshold": 0,  # Disable prepared statements for pooler compatibility
            },
        )

        print("✅ LangGraph connection pool initialized")

    return _pool


async def init_checkpointer() -> PostgresSaver:
    """
    Initialize LangGraph PostgreSQL checkpointer.

    Creates necessary tables for checkpoint storage if they don't exist.
    Should be called during application startup.

    Returns:
        PostgresSaver instance for LangGraph graph compilation

    Usage:
        checkpointer = await init_checkpointer()
        graph = graph_builder.compile(checkpointer=checkpointer)
    """
    global _checkpointer

    if _checkpointer is None:
        pool = get_connection_pool()

        # Create PostgresSaver with connection pool
        _checkpointer = PostgresSaver(pool)

        # Setup checkpoint tables
        async with pool.connection() as conn:
            await _checkpointer.setup(conn)

        print("✅ LangGraph checkpointer initialized")

    return _checkpointer


def get_checkpointer() -> Optional[PostgresSaver]:
    """
    Get initialized checkpointer instance.

    Returns None if checkpointer hasn't been initialized yet.
    Call init_checkpointer() during app startup first.

    Returns:
        PostgresSaver instance or None
    """
    return _checkpointer


@asynccontextmanager
async def get_db_connection():
    """
    Context manager for direct database connections.

    Useful for custom queries outside of LangGraph checkpointing.

    Usage:
        async with get_db_connection() as conn:
            result = await conn.execute("SELECT * FROM checkpoints")
    """
    pool = get_connection_pool()
    async with pool.connection() as conn:
        yield conn


async def close_pool():
    """
    Close the connection pool.

    Should be called during application shutdown to clean up resources.

    Usage:
        @app.on_event("shutdown")
        async def shutdown():
            await close_pool()
    """
    global _pool, _checkpointer

    if _pool is not None:
        await _pool.close()
        _pool = None
        _checkpointer = None
        print("✅ LangGraph connection pool closed")


# Convenience function for FastAPI dependency injection
async def get_graph_checkpointer() -> PostgresSaver:
    """
    FastAPI dependency to inject checkpointer into route handlers.

    Usage:
        @router.post("/agent/run")
        async def run_agent(
            checkpointer: PostgresSaver = Depends(get_graph_checkpointer)
        ):
            graph = build_graph().compile(checkpointer=checkpointer)
            return await graph.invoke(...)
    """
    checkpointer = get_checkpointer()

    if checkpointer is None:
        raise RuntimeError(
            "LangGraph checkpointer not initialized. "
            "Call init_checkpointer() during app startup."
        )

    return checkpointer
