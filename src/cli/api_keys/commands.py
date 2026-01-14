"""
API Keys CLI commands for managing API keys via the API.
"""

import json
from uuid import UUID

import asyncclick as click
from rich.console import Console
from rich.table import Table

from src.cli.utils.http_client import get_api_key, make_api_request


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
@click.pass_context
async def create(
    ctx,
    name: str,
    description: str | None,
    client_name: str | None,
    permissions: str,
    rate_limit: int,
    allowed_ips: str | None,
):
    """Create a new API key."""
    # Get service URL from root context
    root_ctx = ctx.find_root()
    service_url = root_ctx.obj.get("service_url") if root_ctx.obj else None

    if not service_url:
        raise click.ClickException(
            "Service URL not configured. This should not happen - please report a bug."
        )

    # Get API key for authentication
    api_key = get_api_key()

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
        method="POST",
        endpoint="/api/v1/api-keys/",
        base_url=service_url,
        api_key=api_key,
        json_data=request_data,
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
@click.pass_context
async def list_keys(ctx, output_json: bool):
    """List all API keys."""
    # Get service URL from root context
    root_ctx = ctx.find_root()
    service_url = root_ctx.obj.get("service_url") if root_ctx.obj else None

    if not service_url:
        raise click.ClickException(
            "Service URL not configured. This should not happen - please report a bug."
        )

    # Get API key for authentication
    api_key = get_api_key()

    # Make API request
    response = await make_api_request(
        method="GET",
        endpoint="/api/v1/api-keys/",
        base_url=service_url,
        api_key=api_key,
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
    table.add_column("ID", style="dim", no_wrap=True)
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
            key.get("id", "N/A"),
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
@click.option("--name", help="Update the key's name")
@click.option("--description", help="Update the description")
@click.option("--client-name", help="Update the client application name")
@click.option(
    "--permissions",
    help="Update permissions (comma-separated: read,write,admin)",
)
@click.option(
    "--rate-limit", type=int, help="Update requests per minute limit (1-10000)"
)
@click.option(
    "--allowed-ips", help="Update IP allowlist (comma-separated, or 'none' to clear)"
)
@click.option(
    "--activate/--deactivate",
    "is_active",
    default=None,
    help="Activate or deactivate the key",
)
@click.option("--json", "output_json", is_flag=True, help="Output in JSON format")
@click.pass_context
async def update(
    ctx,
    key_id: str,
    name: str | None,
    description: str | None,
    client_name: str | None,
    permissions: str | None,
    rate_limit: int | None,
    allowed_ips: str | None,
    is_active: bool | None,
    output_json: bool,
):
    """Update an API key's properties.

    KEY_ID is the UUID of the API key to update.

    Note: API keys cannot modify themselves (use a different admin key).

    Examples:
        lqs api-keys update <key-id> --name "New Name"
        lqs api-keys update <key-id> --permissions read,write
        lqs api-keys update <key-id> --deactivate
        lqs api-keys update <key-id> --rate-limit 500 --allowed-ips 192.168.1.0/24
    """
    # Get service URL from root context
    root_ctx = ctx.find_root()
    service_url = root_ctx.obj.get("service_url") if root_ctx.obj else None

    if not service_url:
        raise click.ClickException(
            "Service URL not configured. This should not happen - please report a bug."
        )

    # Get API key for authentication
    api_key = get_api_key()

    # Validate UUID format
    try:
        UUID(key_id)
    except ValueError:
        raise click.ClickException(f"Invalid UUID format: {key_id}")

    # Build request data from provided options
    request_data = {}

    if name is not None:
        request_data["name"] = name
    if description is not None:
        request_data["description"] = description
    if client_name is not None:
        request_data["client_name"] = client_name
    if permissions is not None:
        request_data["permissions_scope"] = [
            p.strip() for p in permissions.split(",") if p.strip()
        ]
    if rate_limit is not None:
        request_data["rate_limit_rpm"] = rate_limit
    if allowed_ips is not None:
        if allowed_ips.lower() == "none":
            request_data["allowed_ips"] = []
        else:
            request_data["allowed_ips"] = [
                ip.strip() for ip in allowed_ips.split(",") if ip.strip()
            ]
    if is_active is not None:
        request_data["is_active"] = is_active

    if not request_data:
        raise click.ClickException(
            "No update options provided. Use --help to see available options."
        )

    # Make API request
    response = await make_api_request(
        method="PUT",
        endpoint=f"/api/v1/api-keys/{key_id}",
        base_url=service_url,
        api_key=api_key,
        json_data=request_data,
    )

    result = response.json()

    if output_json:
        click.echo(json.dumps(result, indent=2, default=str))
        return

    # Display result
    click.echo("✅ API key updated successfully!")
    click.echo(f"   Name: {result.get('name')}")
    click.echo(f"   Prefix: {result.get('key_prefix')}")
    click.echo(f"   Active: {'Yes' if result.get('is_active') else 'No'}")
    click.echo(f"   Permissions: {', '.join(result.get('permissions_scope', []))}")
    click.echo(f"   Rate Limit: {result.get('rate_limit_rpm')} RPM")
    if result.get("allowed_ips"):
        click.echo(f"   Allowed IPs: {', '.join(result.get('allowed_ips'))}")
    else:
        click.echo("   Allowed IPs: All (no restrictions)")


@click.command()
@click.argument("key_id", type=str)
@click.pass_context
async def revoke(ctx, key_id: str):
    """Revoke an API key by UUID.

    Note: API keys cannot revoke themselves (use a different admin key).
    """
    # Get service URL from root context
    root_ctx = ctx.find_root()
    service_url = root_ctx.obj.get("service_url") if root_ctx.obj else None

    if not service_url:
        raise click.ClickException(
            "Service URL not configured. This should not happen - please report a bug."
        )

    # Get API key for authentication
    api_key = get_api_key()

    # Validate UUID format
    try:
        UUID(key_id)
    except ValueError:
        raise click.ClickException(f"Invalid UUID format: {key_id}")

    # Make API request
    await make_api_request(
        method="DELETE",
        endpoint=f"/api/v1/api-keys/{key_id}",
        base_url=service_url,
        api_key=api_key,
    )

    # Display result
    click.echo(f"✅ API key {key_id} revoked successfully!")
