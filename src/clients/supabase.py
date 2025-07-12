"""Supabase client configuration."""

from supabase import acreate_client, Client

from src.core.config import settings


async def get_supabase_client() -> Client:
    """Get Supabase client with service role key for backend operations."""
    return await acreate_client(settings.supabase_url, settings.supabase_service_key)
