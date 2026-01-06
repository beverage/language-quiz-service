"""Supabase client configuration."""

import logging

from supabase import AsyncClient, acreate_client

logger = logging.getLogger(__name__)


async def get_supabase_client() -> AsyncClient:
    """Get Supabase client with service role key for backend operations."""
    # Import settings here to allow for runtime environment overrides (e.g., --local flag)
    from src.core.config import settings

    try:
        return await acreate_client(settings.supabase_url, settings.supabase_key)
    except Exception as e:
        logger.error(
            f"Failed to create Supabase client: {e}",
            exc_info=True,
            extra={
                "supabase_url": settings.supabase_url,
                "has_key": bool(settings.supabase_key),
                "key_length": len(settings.supabase_key)
                if settings.supabase_key
                else 0,
            },
        )
        raise
