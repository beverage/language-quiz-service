"""
API Keys CLI commands for managing API keys via the API.
"""

import json
import os
from uuid import UUID

import asyncclick as click
import httpx
from rich.console import Console
from rich.table import Table


def get_api_key_from_env_or_flag(api_key_flag: str | None) -> str:
    """
    Get API key from environment variable or CLI flag.

    Args:
        api_key_flag: API key from --api-key flag

    Returns:
        API key string

    Raises:
        click.ClickException: If no API key is found
    """
    # Check environment variable first
    env_key = os.getenv("LQS_API_KEY")
    if env_key:
        return env_key

    # Fall back to CLI flag
    if api_key_flag:
        return api_key_flag

    # Fail with helpful error
    raise click.ClickException(
        "No API key provided. Set LQS_API_KEY environment variable or use --api-key flag."
    )


def get_api_base_url() -> str:
    """Get the API base URL from environment variable LQS_SERVICE_URL or default to localhost."""
    base_url = os.getenv("LQS_SERVICE_URL", "http://localhost:8000")
    return base_url


async def make_api_request(
    method: str,
    endpoint: str,
    api_key: str,
    json_data: dict | None = None,
    params: dict | None = None,
) -> httpx.Response:
    """
    Make an authenticated API request.

    Args:
        method: HTTP method (GET, POST, etc.)
        endpoint: API endpoint path
        api_key: API key for authentication
        json_data: JSON data for POST requests
        params: Query parameters

    Returns:
        Response object

    Raises:
        click.ClickException: If request fails
    """
    base_url = get_api_base_url()
    url = f"{base_url}{endpoint}"

    headers = {
        "X-API-Key": api_key,
        "Content-Type": "application/json",
    }

    async with httpx.AsyncClient() as client:
        try:
            response = await client.request(
                method=method,
                url=url,
                headers=headers,
                json=json_data,
                params=params,
                timeout=30.0,
            )

            # Check for HTTP errors
            if response.status_code >= 400:
                try:
                    error_data = response.json()
                    error_msg = error_data.get("detail", f"HTTP {response.status_code}")
                except (ValueError, Exception):
                    error_msg = f"HTTP {response.status_code}: {response.text}"
                raise click.ClickException(f"API request failed: {error_msg}")

            return response

        except httpx.RequestError as e:
            raise click.ClickException(f"Network error connecting to {url}: {e}")
        except httpx.TimeoutException:
            raise click.ClickException(
                f"Request timeout connecting to {url} - is the API server running?"
            )


@click.command()
@click.option("--name", required=True, help="Human-readable name for the API key")
@click.option("--description", help="Optional description")
@click.option("--client-name", help="Client application name")
@click.option(
    "--permissions",
    default="read",
    help="Comma-separated permissions (read,write,admin)",
)
@click.option("--rate-limit", type=int, default=100, help="Requests per minute limit")
@click.option("--allowed-ips", help="Comma-separated IP addresses or CIDR blocks")
@click.option("--api-key", help="API key for authentication (or set LQS_API_KEY)")
async def create(
    name: str,
    description: str | None,
    client_name: str | None,
    permissions: str,
    rate_limit: int,
    allowed_ips: str | None,
    api_key: str | None,
):
    """Create a new API key."""

    # Get API key for authentication
    auth_key = get_api_key_from_env_or_flag(api_key)

    # Parse permissions
    permissions_list = [p.strip() for p in permissions.split(",") if p.strip()]

    # Parse allowed IPs
    allowed_ips_list = None
    if allowed_ips:
        allowed_ips_list = [ip.strip() for ip in allowed_ips.split(",") if ip.strip()]

    # Build request data
    request_data = {
        "name": name,
        "permissions_scope": permissions_list,
        "rate_limit_rpm": rate_limit,
    }

    if description:
        request_data["description"] = description
    if client_name:
        request_data["client_name"] = client_name
    if allowed_ips_list:
        request_data["allowed_ips"] = allowed_ips_list

    # Make API request
    response = await make_api_request(
        method="POST", endpoint="/api-keys/", api_key=auth_key, json_data=request_data
    )

    # Display result
    result = response.json()

    click.echo("✅ API key created successfully!")
    click.echo(f"   Name: {result['key_info']['name']}")
    click.echo(f"   Prefix: {result['key_info']['key_prefix']}")
    click.echo(f"   Permissions: {', '.join(result['key_info']['permissions_scope'])}")
    click.echo()
    click.echo("🔑 API Key (save this securely - it won't be shown again):")
    click.echo(f"   {result['api_key']}")


@click.command()
@click.option("--json", "output_json", is_flag=True, help="Output in JSON format")
@click.option("--api-key", help="API key for authentication (or set LQS_API_KEY)")
async def list_keys(output_json: bool, api_key: str | None):
    """List all API keys."""

    # Get API key for authentication
    auth_key = get_api_key_from_env_or_flag(api_key)

    # Make API request
    response = await make_api_request(
        method="GET", endpoint="/api-keys/", api_key=auth_key
    )

    keys = response.json()

    if output_json:
        click.echo(json.dumps(keys, indent=2, default=str))
        return

    # Display as table
    if not keys:
        click.echo("No API keys found.")
        return

    # Create rich table
    table = Table(title="API Keys", show_header=True)
    table.add_column("Key Prefix", style="cyan")
    table.add_column("Name", style="bold")
    table.add_column("Active", justify="center")
    table.add_column("Permissions", style="yellow")
    table.add_column("Rate Limit", justify="right")
    table.add_column("Created", style="green")
    table.add_column("Last Used", style="green")
    table.add_column("Usage Count", justify="right")

    for key in keys:
        # Format dates
        created_at = (
            key.get("created_at", "").split("T")[0] if key.get("created_at") else "N/A"
        )
        last_used = (
            key.get("last_used_at", "").split("T")[0]
            if key.get("last_used_at")
            else "Never"
        )

        # Format permissions
        permissions = ", ".join(key.get("permissions_scope", []))

        table.add_row(
            key.get("key_prefix", ""),
            key.get("name", ""),
            "✅" if key.get("is_active", False) else "❌",
            permissions,
            str(key.get("rate_limit_rpm", 0)),
            created_at,
            last_used,
            str(key.get("usage_count", 0)),
        )

    # Display table
    console = Console()
    console.print(table)


@click.command()
@click.argument("key_id", type=str)
@click.option("--api-key", help="API key for authentication (or set LQS_API_KEY)")
async def revoke(key_id: str, api_key: str | None):
    """Revoke an API key by UUID."""

    # Get API key for authentication
    auth_key = get_api_key_from_env_or_flag(api_key)

    # Validate UUID format
    try:
        UUID(key_id)
    except ValueError:
        raise click.ClickException(f"Invalid UUID format: {key_id}")

    # Make API request
    await make_api_request(
        method="POST", endpoint=f"/api-keys/{key_id}/revoke", api_key=auth_key
    )

    # Display result
    click.echo(f"✅ API key {key_id} revoked successfully!")
