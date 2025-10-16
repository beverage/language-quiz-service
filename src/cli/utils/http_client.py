"""
Shared HTTP client utilities for CLI commands.

Provides a reusable interface for making authenticated requests to the
Language Quiz Service API when using --remote or --local flags.
"""

import logging
import os

import asyncclick as click
import httpx

logger = logging.getLogger(__name__)


def get_service_url_from_flag(local: bool, remote: bool) -> str | None:
    """
    Determine the service URL based on CLI flags.

    Args:
        local: True if --local flag was provided
        remote: True if --remote flag was provided

    Returns:
        Service URL string or None (for direct mode)

    Raises:
        click.ClickException: If both flags are provided
    """
    if local and remote:
        raise click.ClickException("Cannot use both --local and --remote flags")

    if local:
        return "http://localhost:8000"

    if remote:
        # Use LQS_SERVICE_URL from environment, default to localhost if not set
        return os.getenv("LQS_SERVICE_URL", "http://localhost:8000")

    # No flags = direct mode (use service layer directly)
    return None


def get_api_key() -> str:
    """
    Get API key from environment variable.

    Returns:
        API key string

    Raises:
        click.ClickException: If no API key is found
    """
    api_key = os.getenv("LQS_API_KEY")
    if not api_key:
        raise click.ClickException(
            "No API key found. Set LQS_API_KEY environment variable for remote/local mode."
        )

    logger.debug(f"Using API key: {api_key[:10]}... (length: {len(api_key)})")

    return api_key


async def make_api_request(
    method: str,
    endpoint: str,
    base_url: str,
    api_key: str,
    json_data: dict | None = None,
    params: dict | None = None,
    timeout: float = 30.0,
) -> httpx.Response:
    """
    Make an authenticated API request to the Language Quiz Service.

    Args:
        method: HTTP method (GET, POST, etc.)
        endpoint: API endpoint path (e.g., "/api/v1/verbs/random")
        base_url: Base URL of the service
        api_key: API key for authentication
        json_data: JSON data for request body (POST/PUT)
        params: Query parameters
        timeout: Request timeout in seconds

    Returns:
        Response object

    Raises:
        click.ClickException: If request fails
    """
    url = f"{base_url}{endpoint}"

    headers = {
        "X-API-Key": api_key,
        "Content-Type": "application/json",
    }

    logger.debug(f"Making {method} request to {url}")
    logger.debug(f"Headers: X-API-Key={api_key[:10]}..., Content-Type=application/json")

    async with httpx.AsyncClient() as client:
        try:
            response = await client.request(
                method=method,
                url=url,
                headers=headers,
                json=json_data,
                params=params,
                timeout=timeout,
            )

            logger.debug(f"Response status: {response.status_code}")

            # Check for HTTP errors
            if response.status_code >= 400:
                try:
                    error_data = response.json()
                    error_msg = error_data.get("detail", error_data.get("message", f"HTTP {response.status_code}"))
                    # Include full error details for debugging
                    logger.debug(f"Error response: {error_data}")
                except (ValueError, Exception):
                    error_msg = f"HTTP {response.status_code}: {response.text}"

                # Add helpful context for common errors
                if response.status_code == 401:
                    error_msg += "\n💡 Hint: Check that your LQS_API_KEY is valid and active"
                elif response.status_code == 403:
                    error_msg += "\n💡 Hint: Your API key may lack required permissions (read/write/admin)"

                raise click.ClickException(f"API request failed: {error_msg}")

            return response

        except httpx.RequestError as e:
            raise click.ClickException(f"Network error connecting to {url}: {e}")
        except httpx.TimeoutException:
            raise click.ClickException(
                f"Request timeout connecting to {url} - is the API server running?"
            )

