"""
CLI command to purge (delete all) problems from the database.
"""

import logging
from datetime import datetime

import asyncclick as click

from src.cli.utils.safety import forbid_remote, get_remote_flag, require_confirmation
from src.cli.utils.types import DateOrDurationParam
from src.clients.supabase import get_supabase_client

logger = logging.getLogger(__name__)


def _apply_filters(
    query,
    topic_list: list | None,
    older_than: datetime | None,
    newer_than: datetime | None,
):
    """Apply all filters to a query."""
    if topic_list:
        query = query.contains("topic_tags", topic_list)
    if older_than:
        query = query.lte("created_at", older_than.isoformat())
    if newer_than:
        query = query.gte("created_at", newer_than.isoformat())
    return query


@click.command("purge")
@click.option(
    "--topic",
    multiple=True,
    help="Only delete problems with these topic tags (can specify multiple)",
)
@click.option(
    "--older-than",
    type=DateOrDurationParam(),
    help="Delete problems created before date/duration (e.g., '7d', '2w', '2025-01-01')",
)
@click.option(
    "--newer-than",
    type=DateOrDurationParam(),
    help="Delete problems created after date/duration (e.g., '1d', '2025-01-01')",
)
@click.option("--force", "-f", is_flag=True, help="Skip confirmation prompt")
@click.pass_context
async def purge_problems(
    ctx,
    topic: tuple,
    older_than: datetime | None,
    newer_than: datetime | None,
    force: bool,
):
    """
    Delete all problems (or a filtered subset) from the database.

    By default, deletes ALL problems. Use filters to narrow the scope.

    Examples:
        lqs problem purge                          # Delete all problems
        lqs problem purge --topic test_data        # Delete only test problems
        lqs problem purge --older-than 7d          # Delete problems older than 7 days
        lqs problem purge --older-than 2025-01-01  # Delete problems before a date
        lqs problem purge --newer-than 1d --older-than 1h  # Date range
        lqs problem purge --older-than 2d --topic test_data  # Combined filters
        lqs problem purge -f                       # Skip confirmation

    WARNING: Remote purge is FORBIDDEN for safety.
    """
    is_remote = get_remote_flag(ctx)

    # Forbid remote purge operations
    if forbid_remote("lqs problem purge", is_remote):
        return

    try:
        client = await get_supabase_client()

        # Build filter description parts
        filter_parts = []
        topic_list = list(topic) if topic else None

        if topic_list:
            filter_parts.append(f"topics {topic_list}")
        if older_than:
            filter_parts.append(
                f"created before {older_than.strftime('%Y-%m-%d %H:%M')}"
            )
        if newer_than:
            filter_parts.append(
                f"created after {newer_than.strftime('%Y-%m-%d %H:%M')}"
            )

        filter_desc = f"with {', '.join(filter_parts)}" if filter_parts else "(ALL)"

        # Build count query with all filters
        count_query = client.table("problems").select("id", count="exact")
        count_query = _apply_filters(count_query, topic_list, older_than, newer_than)
        count_result = await count_query.execute()

        problem_count = (
            count_result.count
            if hasattr(count_result, "count") and count_result.count is not None
            else len(count_result.data)
            if count_result.data
            else 0
        )

        if problem_count == 0:
            click.echo(f"✅ No problems found {filter_desc} to delete.")
            return

        click.echo(f"🎯 Found {problem_count} problems {filter_desc}")

        # Confirm deletion
        if not require_confirmation(
            operation_name=f"delete {problem_count} problems {filter_desc}",
            is_remote=is_remote,
            force=force,
            item_count=problem_count,
        ):
            click.echo("❌ Aborted.")
            return

        # Perform deletion with same filters
        click.echo(f"🗑️  Deleting {problem_count} problems...")

        delete_query = client.table("problems").delete()
        delete_query = _apply_filters(delete_query, topic_list, older_than, newer_than)

        # Supabase requires at least one filter for delete operations
        if not topic_list and not older_than and not newer_than:
            delete_query = delete_query.neq(
                "id", "00000000-0000-0000-0000-000000000000"
            )

        delete_result = await delete_query.execute()

        deleted_count = len(delete_result.data) if delete_result.data else 0

        click.echo(f"✅ Deleted {deleted_count} problems")

        if deleted_count < problem_count:
            click.echo(
                f"⚠️  Note: {problem_count - deleted_count} problems may have been "
                "deleted by another process or had foreign key constraints"
            )

    except Exception as e:
        logger.error(f"Error purging problems: {e}", exc_info=True)
        click.echo(f"❌ Error: {e}")
