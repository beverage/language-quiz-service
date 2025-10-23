"""
Database wipe command - clears all tables.

This command truncates all tables in the database. It is ONLY allowed
when using --local flag to prevent accidental data loss on remote/production.
"""

import logging

import asyncclick as click

from src.clients.supabase import get_supabase_client

logger = logging.getLogger(__name__)


@click.command()
@click.pass_context
async def wipe_database(ctx):
    """
    Wipe all tables in the database.

    This command truncates all tables, removing all data but keeping the schema.

    SAFETY: This command ONLY works with --local flag. It is forbidden on remote
    databases to prevent accidental data loss.

    Tables wiped (in order to respect foreign keys):
    1. sentences
    2. problems
    3. conjugations
    4. verbs
    5. api_keys
    """
    # Get flags from root context
    root_ctx = ctx.find_root()
    is_local = root_ctx.obj.get("local", False) if root_ctx.obj else False
    is_remote = root_ctx.obj.get("remote", False) if root_ctx.obj else False

    # Safety check: MUST be --local
    if not is_local:
        click.echo("❌ ERROR: 'lqs database wipe' can ONLY be used with --local flag")
        click.echo("   This is a safety measure to prevent accidental data loss.")
        click.echo("   Usage: lqs --local database wipe")
        return

    if is_remote:
        click.echo("❌ ERROR: 'lqs database wipe' is FORBIDDEN with --remote flag")
        click.echo("   This command can only target local databases.")
        return

    # Confirm with user
    click.echo("⚠️  WARNING: This will DELETE ALL DATA from your LOCAL database!")
    click.echo("   Tables affected: sentences, problems, conjugations, verbs, api_keys")
    confirm = click.confirm("   Are you sure you want to continue?", default=False)

    if not confirm:
        click.echo("❌ Aborted.")
        return

    try:
        client = await get_supabase_client()

        # Delete in order to respect foreign key constraints
        tables_to_wipe = [
            "sentences",  # References problems
            "problems",  # References verbs (via problem_verbs join table if exists)
            "conjugations",  # References verbs
            "verbs",  # Base table
            "api_keys",  # Independent table
        ]

        click.echo("\n🗑️  Wiping database tables...")

        total_deleted = 0
        for table in tables_to_wipe:
            try:
                result = (
                    await client.table(table)
                    .delete()
                    .neq("id", "00000000-0000-0000-0000-000000000000")
                    .execute()
                )
                deleted = len(result.data) if result.data else 0
                total_deleted += deleted

                if deleted > 0:
                    click.echo(f"   ✅ {table}: deleted {deleted} rows")
                else:
                    click.echo(f"   ⚪ {table}: already empty")

            except Exception as e:
                # Some tables might not exist or have different constraints
                logger.debug(f"Could not wipe {table}: {e}")
                click.echo(f"   ⚠️  {table}: skipped ({str(e)[:50]})")

        click.echo("\n🎉 Database wipe complete!")
        click.echo(f"   Total rows deleted: {total_deleted}")
        click.echo("\n💡 To restore seed data, run: supabase db reset")

    except Exception as e:
        logger.error(f"Failed to wipe database: {e}")
        click.echo(f"❌ Error: {e}")
        raise
