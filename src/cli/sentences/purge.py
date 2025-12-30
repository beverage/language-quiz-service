"""
CLI command to purge orphaned sentences from the database.
"""

import logging
from uuid import UUID

import asyncclick as click

from src.cli.utils.safety import forbid_remote, get_remote_flag, require_confirmation
from src.clients.supabase import get_supabase_client

logger = logging.getLogger(__name__)


@click.command("purge")
@click.option(
    "--orphaned",
    is_flag=True,
    help="Delete sentences that are not referenced by any problem",
)
@click.option("--force", "-f", is_flag=True, help="Skip confirmation prompt")
@click.pass_context
async def purge_orphaned_sentences(ctx, orphaned: bool, force: bool):
    """
    Delete orphaned sentences from the database.

    Orphaned sentences are those that are not referenced in any problem's
    source_statement_ids array. This can happen if the service restarts during
    problem generation, leaving sentences without their corresponding problems.

    Examples:
        lqs sentence purge --orphaned              # Delete orphaned sentences
        lqs sentence purge --orphaned -f            # Skip confirmation

    WARNING: Remote purge is FORBIDDEN for safety.
    """
    is_remote = get_remote_flag(ctx)

    # Forbid remote purge operations
    if forbid_remote("lqs sentence purge", is_remote):
        return

    if not orphaned:
        click.echo("❌ Error: --orphaned flag is required")
        click.echo("   Use: lqs sentence purge --orphaned")
        return

    try:
        client = await get_supabase_client()

        # Get all sentences
        click.echo("🔍 Scanning for orphaned sentences...")
        all_sentences_result = await client.table("sentences").select("id").execute()
        all_sentences = all_sentences_result.data if all_sentences_result.data else []

        if not all_sentences:
            click.echo("✅ No sentences found in database.")
            return

        # Get all problems with their source_statement_ids
        all_problems_result = (
            await client.table("problems").select("source_statement_ids").execute()
        )
        all_problems = all_problems_result.data if all_problems_result.data else []

        # Flatten all referenced sentence IDs
        referenced_ids = set()
        for problem in all_problems:
            source_ids = problem.get("source_statement_ids")
            if source_ids:
                # Convert string UUIDs to UUID objects for comparison
                for sid in source_ids:
                    if isinstance(sid, str):
                        try:
                            referenced_ids.add(UUID(sid))
                        except ValueError:
                            logger.warning(
                                f"Invalid UUID in source_statement_ids: {sid}"
                            )
                    elif isinstance(sid, UUID):
                        referenced_ids.add(sid)
                    else:
                        # Try to convert to UUID if it's not already
                        try:
                            referenced_ids.add(UUID(str(sid)))
                        except (ValueError, TypeError):
                            logger.warning(
                                f"Invalid UUID format in source_statement_ids: {sid}"
                            )

        # Find orphaned sentences
        orphaned_sentences = []
        for sentence in all_sentences:
            sentence_id = sentence["id"]
            # Convert to UUID if it's a string
            if isinstance(sentence_id, str):
                try:
                    sentence_id = UUID(sentence_id)
                except ValueError:
                    logger.warning(f"Invalid sentence UUID: {sentence_id}")
                    continue
            elif not isinstance(sentence_id, UUID):
                # Try to convert to UUID if it's not already
                try:
                    sentence_id = UUID(str(sentence_id))
                except (ValueError, TypeError):
                    logger.warning(f"Invalid sentence UUID format: {sentence_id}")
                    continue

            if sentence_id not in referenced_ids:
                orphaned_sentences.append(sentence_id)

        orphaned_count = len(orphaned_sentences)

        if orphaned_count == 0:
            click.echo("✅ No orphaned sentences found.")
            return

        click.echo(f"🎯 Found {orphaned_count} orphaned sentences")

        # Confirm deletion
        if not require_confirmation(
            operation_name=f"delete {orphaned_count} orphaned sentences",
            is_remote=is_remote,
            force=force,
            item_count=orphaned_count,
        ):
            click.echo("❌ Aborted.")
            return

        # Perform deletion
        click.echo(f"🗑️  Deleting {orphaned_count} orphaned sentences...")

        # Delete orphaned sentences in batches (Supabase has limits)
        deleted_count = 0
        batch_size = 100
        for i in range(0, len(orphaned_sentences), batch_size):
            batch = orphaned_sentences[i : i + batch_size]
            delete_result = (
                await client.table("sentences")
                .delete()
                .in_("id", [str(sid) for sid in batch])
                .execute()
            )
            deleted_count += len(delete_result.data) if delete_result.data else 0

        click.echo(f"✅ Deleted {deleted_count} orphaned sentences")

        if deleted_count < orphaned_count:
            click.echo(
                f"⚠️  Note: {orphaned_count - deleted_count} sentences may have been "
                "deleted by another process or had foreign key constraints"
            )

    except Exception as e:
        logger.error(f"Error purging orphaned sentences: {e}", exc_info=True)
        click.echo(f"❌ Error: {e}")
