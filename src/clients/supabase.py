"""Supabase client configuration."""

import logging
import socket

from supabase import AsyncClient, acreate_client

logger = logging.getLogger(__name__)

# Module-level singleton for the Supabase client
_supabase_client: AsyncClient | None = None


async def create_supabase_client() -> AsyncClient:
    """Create a new Supabase client. Called once at startup."""
    from src.core.config import settings

    supabase_url = settings.supabase_url
    if not supabase_url:
        error_msg = "SUPABASE_URL is not set or is empty"
        logger.error(error_msg)
        raise ValueError(error_msg)

    if not (supabase_url.startswith("http://") or supabase_url.startswith("https://")):
        error_msg = f"Invalid SUPABASE_URL format (must start with http:// or https://): {supabase_url}"
        logger.error(error_msg)
        raise ValueError(error_msg)

    try:
        return await acreate_client(supabase_url, settings.supabase_key)
    except socket.gaierror as e:
        error_msg = (
            f"DNS resolution failed for Supabase URL: {supabase_url}. "
            f"Error: {e}. "
            f"Please verify SUPABASE_URL is correct and the hostname is resolvable."
        )
        logger.error(error_msg, exc_info=True, extra={"supabase_url": supabase_url})
        raise ConnectionError(error_msg) from e
    except OSError as e:
        if e.errno == -2:
            error_msg = (
                f"Hostname resolution failed for Supabase URL: {supabase_url}. "
                f"Error: {e}. "
                f"Please verify SUPABASE_URL is correct and the hostname is resolvable."
            )
            logger.error(error_msg, exc_info=True, extra={"supabase_url": supabase_url})
            raise ConnectionError(error_msg) from e
        else:
            error_msg = (
                f"Network error connecting to Supabase: {supabase_url}. "
                f"Error: {e} (errno: {e.errno})"
            )
            logger.error(error_msg, exc_info=True, extra={"supabase_url": supabase_url})
            raise ConnectionError(error_msg) from e
    except Exception as e:
        error_msg = f"Failed to create Supabase client: {e}"
        logger.error(
            error_msg,
            exc_info=True,
            extra={
                "supabase_url": supabase_url,
                "has_key": bool(settings.supabase_key),
                "key_length": len(settings.supabase_key)
                if settings.supabase_key
                else 0,
                "error_type": type(e).__name__,
            },
        )
        raise


async def get_supabase_client() -> AsyncClient:
    """Get the singleton Supabase client, creating it if needed.

    For production use, the client should be created at startup via
    create_supabase_client() and stored in app.state. This function
    provides a fallback for CLI/test contexts where app.state isn't available.
    """
    global _supabase_client
    if _supabase_client is None:
        _supabase_client = await create_supabase_client()
    return _supabase_client


def set_supabase_client(client: AsyncClient) -> None:
    """Set the singleton Supabase client. Called during app startup."""
    global _supabase_client
    _supabase_client = client


async def close_supabase_client() -> None:
    """Close the singleton Supabase client. Called during app shutdown."""
    global _supabase_client
    if _supabase_client is not None:
        # Supabase AsyncClient doesn't expose a close method.
        # The underlying httpx client is managed internally.
        # Just clear our reference to allow garbage collection.
        _supabase_client = None
