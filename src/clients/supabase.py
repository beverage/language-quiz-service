"""Supabase client configuration."""

from src.core.config import settings
from supabase import Client, acreate_client


async def get_supabase_client() -> Client:
    """Get Supabase client with service role key for backend operations."""
    return await acreate_client(settings.supabase_url, settings.supabase_key)


async def create_test_supabase_client(
    database_url: str, service_key: str = "test_key"
) -> Client:
    """
    Create a Supabase client for testing that points directly to a PostgreSQL database.

    This allows repositories to use their existing Supabase client interface
    while connecting to a testcontainer PostgreSQL database.

    Args:
        database_url: PostgreSQL connection URL (e.g., from testcontainer)
        service_key: Service role key (can be dummy for testing)

    Returns:
        Supabase client configured for the test database
    """
    # For testcontainers, we use the PostgreSQL URL directly as the "Supabase URL"
    # The Supabase client will connect to our PostgreSQL container
    return await acreate_client(database_url, service_key)
