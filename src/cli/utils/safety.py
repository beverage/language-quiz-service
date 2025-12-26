"""
Safety utilities for CLI commands.

Provides confirmation helpers for dangerous operations, especially
when targeting remote databases.
"""

import asyncclick as click


def require_confirmation(
    operation_name: str,
    is_remote: bool = False,
    force: bool = False,
    item_count: int | None = None,
) -> bool:
    """
    Require user confirmation for dangerous operations.

    Args:
        operation_name: Human-readable description of the operation
        is_remote: True if targeting remote database (extra warning)
        force: True to skip confirmation (for scripting)
        item_count: Optional count of items to be affected

    Returns:
        True if operation should proceed, False to abort
    """
    if force:
        return True

    # Build confirmation message
    if is_remote:
        target = "REMOTE"
        prefix = "⚠️  WARNING: "
    else:
        target = "LOCAL"
        prefix = ""

    if item_count is not None:
        msg = f"{prefix}You are about to {operation_name} ({item_count} items) on {target} database."
    else:
        msg = f"{prefix}You are about to {operation_name} on {target} database."

    # Remote operations require extra caution
    if is_remote:
        click.echo(f"\n{msg}")
        click.echo("   This is a DESTRUCTIVE operation on PRODUCTION data!")
        return click.confirm("   Are you absolutely sure?", default=False)
    else:
        return click.confirm(f"{msg} Continue?", default=True)


def forbid_remote(operation_name: str, is_remote: bool) -> bool:
    """
    Check if an operation should be forbidden for remote targets.

    Args:
        operation_name: Human-readable description of the operation
        is_remote: True if targeting remote database

    Returns:
        True if operation is forbidden (caller should abort)
    """
    if is_remote:
        click.echo(f"❌ ERROR: '{operation_name}' is FORBIDDEN with --remote flag")
        click.echo("   This command can only target local databases.")
        click.echo("   This is a safety measure to prevent accidental data loss.")
        return True
    return False


def get_remote_flag(ctx: click.Context) -> bool:
    """
    Get the --remote flag from the root context.

    Args:
        ctx: Click context

    Returns:
        True if --remote flag was set
    """
    root_ctx = ctx.find_root()
    return root_ctx.obj.get("remote", False) if root_ctx.obj else False
