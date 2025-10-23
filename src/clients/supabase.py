"""Supabase client configuration."""

import logging

from supabase import AsyncClient, acreate_client

logger = logging.getLogger(__name__)


async def get_supabase_client() -> AsyncClient:
    """Get Supabase client with service role key for backend operations."""
    # Import settings here to allow for runtime environment overrides (e.g., --local flag)
    from src.core.config import settings

    return await acreate_client(settings.supabase_url, settings.supabase_key)
