"""
CLI database cleanup - Remove test data from the database.

This command removes all verbs, sentences, and problems created during testing.
Test verbs are identified by having an underscore '_' in their infinitive name.
"""

import asyncclick as click

from src.clients.supabase import get_supabase_client


@click.command()
@click.pass_context
async def clear_database(ctx):
    """
    Clean up test data from the database.

    This command removes all test verbs (those with '_' in infinitive) and their
    associated data (sentences and problems are cascade-deleted via foreign keys).

    Respects --local/--remote flags:
    - Default: cleans local Supabase instance
    - Use --local to explicitly target local Supabase
    - Use --remote to target remote Supabase (disaster recovery)

    Warning: This is a destructive operation. Use --remote with caution.
    """
    # Get flag info from context
    is_remote = ctx.obj.get("remote", False) if ctx.obj else False
    is_local = ctx.obj.get("local", False) if ctx.obj else False

    # Default to local if no flags
    if not is_remote and not is_local:
        is_local = True

    target = "REMOTE" if is_remote else "LOCAL"

    click.echo(f"🧹 Cleaning test data from {target} database...")

    if is_remote:
        confirm = click.confirm(
            "⚠️  You are about to clean REMOTE database. This is destructive. Continue?",
            default=False,
        )
        if not confirm:
            click.echo("❌ Aborted.")
            return

    try:
        client = await get_supabase_client()

        # Get count of test verbs before deletion
        count_result = (
            await client.table("verbs")
            .select("id", count="exact")
            .like("infinitive", "%\\_%")
            .execute()
        )
        test_verb_count = (
            count_result.count
            if hasattr(count_result, "count")
            else len(count_result.data)
        )

        if test_verb_count == 0:
            click.echo("✅ No test data found to clean.")
            return

        click.echo(f"🎯 Found {test_verb_count} test verbs to remove...")

        # Delete all test verbs (sentences cascade via FK)
        # Pattern: any infinitive containing underscore
        delete_result = (
            await client.table("verbs").delete().like("infinitive", "%\\_%").execute()
        )

        deleted_count = len(delete_result.data) if delete_result.data else 0

        click.echo(f"✅ Cleaned up {deleted_count} test verbs")
        click.echo("✅ Associated sentences/problems automatically removed (CASCADE)")

    except Exception as e:
        click.echo(f"❌ Error cleaning database: {e}")
        raise
