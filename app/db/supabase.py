"""
Supabase client initialization and connection management.
"""

from supabase import create_client, Client
from app.config import get_settings


_supabase_client: Client | None = None
_supabase_service_client: Client | None = None


def get_supabase_client() -> Client:
    """
    Get Supabase client with anon key (for user operations).
    
    Returns:
        Supabase client instance
    """
    global _supabase_client
    if _supabase_client is None:
        settings = get_settings()
        _supabase_client = create_client(
            settings.supabase_url,
            settings.supabase_anon_key
        )
    return _supabase_client


def get_supabase_service_client() -> Client:
    """
    Get Supabase client with service role key (for admin operations).

    WARNING: This client bypasses RLS. Use only for trusted operations.

    Returns:
        Supabase service client instance
    """
    global _supabase_service_client
    if _supabase_service_client is None:
        settings = get_settings()
        _supabase_service_client = create_client(
            settings.supabase_url,
            settings.supabase_service_role_key
        )
    return _supabase_service_client


def get_supabase_admin() -> Client:
    """
    Get Supabase client with service role key (for admin operations).

    This is an alias for get_supabase_service_client() for backwards compatibility.

    WARNING: This client bypasses RLS. Use only for trusted operations.

    Returns:
        Supabase service client instance
    """
    return get_supabase_service_client()

