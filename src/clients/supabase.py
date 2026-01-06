"""Supabase client configuration."""

import logging
import socket

from supabase import AsyncClient, acreate_client

logger = logging.getLogger(__name__)


async def get_supabase_client() -> AsyncClient:
    """Get Supabase client with service role key for backend operations."""
    # Import settings here to allow for runtime environment overrides (e.g., --local flag)
    from src.core.config import settings

    # Validate URL format before attempting connection
    supabase_url = settings.supabase_url
    if not supabase_url:
        error_msg = "SUPABASE_URL is not set or is empty"
        logger.error(error_msg)
        raise ValueError(error_msg)

    # Check if URL looks valid
    if not (supabase_url.startswith("http://") or supabase_url.startswith("https://")):
        error_msg = f"Invalid SUPABASE_URL format (must start with http:// or https://): {supabase_url}"
        logger.error(error_msg)
        raise ValueError(error_msg)

    try:
        return await acreate_client(supabase_url, settings.supabase_key)
    except socket.gaierror as e:
        # DNS resolution failure
        error_msg = (
            f"DNS resolution failed for Supabase URL: {supabase_url}. "
            f"Error: {e}. "
            f"Please verify SUPABASE_URL is correct and the hostname is resolvable."
        )
        logger.error(error_msg, exc_info=True, extra={"supabase_url": supabase_url})
        raise ConnectionError(error_msg) from e
    except OSError as e:
        # Network errors (connection refused, timeout, etc.)
        if e.errno == -2:  # Name or service not known
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
