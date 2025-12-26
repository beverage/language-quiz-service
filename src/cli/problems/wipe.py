"""
CLI command to wipe (delete all) problems from the database.
"""

import logging

import asyncclick as click

from src.cli.utils.safety import forbid_remote, get_remote_flag, require_confirmation
from src.clients.supabase import get_supabase_client

logger = logging.getLogger(__name__)


@click.command("wipe")
@click.option(
    "--topic",
    multiple=True,
    help="Only delete problems with these topic tags (can specify multiple)",
)
@click.option("--force", "-f", is_flag=True, help="Skip confirmation prompt")
@click.pass_context
async def wipe_problems(ctx, topic: tuple, force: bool):
    """
    Delete all problems (or a filtered subset) from the database.

    By default, deletes ALL problems. Use --topic to filter.

    Examples:
        lqs problem wipe                    # Delete all problems
        lqs problem wipe --topic test_data  # Delete only test problems
        lqs problem wipe -f                 # Skip confirmation

    WARNING: Remote wipe is FORBIDDEN for safety.
    """
    is_remote = get_remote_flag(ctx)

    # Forbid remote wipe operations
    if forbid_remote("lqs problem wipe", is_remote):
        return

    try:
        client = await get_supabase_client()

        # Build query to count affected problems
        if topic:
            # Filter by topic tags
            topic_list = list(topic)
            count_result = (
                await client.table("problems")
                .select("id", count="exact")
                .contains("topic_tags", topic_list)
                .execute()
            )
            filter_desc = f"with topics {topic_list}"
        else:
            # All problems
            count_result = (
                await client.table("problems").select("id", count="exact").execute()
            )
            filter_desc = "(ALL)"

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

        # Perform deletion
        click.echo(f"🗑️  Deleting {problem_count} problems...")

        if topic:
            # Delete filtered problems
            topic_list = list(topic)
            delete_result = (
                await client.table("problems")
                .delete()
                .contains("topic_tags", topic_list)
                .execute()
            )
        else:
            # Delete all problems (use a condition that matches everything)
            delete_result = (
                await client.table("problems")
                .delete()
                .neq("id", "00000000-0000-0000-0000-000000000000")
                .execute()
            )

        deleted_count = len(delete_result.data) if delete_result.data else 0

        click.echo(f"✅ Deleted {deleted_count} problems")

        if deleted_count < problem_count:
            click.echo(
                f"⚠️  Note: {problem_count - deleted_count} problems may have been "
                "deleted by another process or had foreign key constraints"
            )

    except Exception as e:
        logger.error(f"Error wiping problems: {e}", exc_info=True)
        click.echo(f"❌ Error: {e}")
