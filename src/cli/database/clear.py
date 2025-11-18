"""
CLI database cleanup - Remove test data from the database.

This command removes all verbs, sentences, conjugations, and problems created during testing.
Test verbs/conjugations are identified by having an underscore '_' in their infinitive name.
"""

import asyncclick as click

from src.clients.supabase import get_supabase_client


@click.command()
@click.pass_context
async def clear_database(ctx):
    """
    Clean up test data from the database.

    This command removes:
    - All test verbs (those with '_' in infinitive)
    - Their associated sentences (cascade-deleted via foreign keys)
    - All orphaned test conjugations (those with '_' in infinitive)
    - All problems tagged with 'test_data' in topic_tags
    - All generation requests with 'test_data' in metadata topic_tags

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
            click.echo("✅ No test verbs found to clean.")
        else:
            click.echo(f"🎯 Found {test_verb_count} test verbs to remove...")

            # Delete all test verbs (sentences cascade via FK)
            # Pattern: any infinitive containing underscore
            delete_result = (
                await client.table("verbs")
                .delete()
                .like("infinitive", "%\\_%")
                .execute()
            )

            deleted_count = len(delete_result.data) if delete_result.data else 0
            click.echo(f"✅ Cleaned up {deleted_count} test verbs")
            click.echo("✅ Associated sentences automatically removed (CASCADE)")

        # Clean up orphaned test conjugations (those without matching verbs)
        # This catches conjugations created directly in tests without verbs
        click.echo("🔍 Checking for orphaned test conjugations...")

        orphaned_count_result = (
            await client.table("conjugations")
            .select("id", count="exact")
            .like("infinitive", "%\\_%")
            .execute()
        )
        orphaned_conjugation_count = (
            orphaned_count_result.count
            if hasattr(orphaned_count_result, "count")
            else len(orphaned_count_result.data)
        )

        if orphaned_conjugation_count == 0:
            click.echo("✅ No orphaned test conjugations found.")
        else:
            click.echo(
                f"🎯 Found {orphaned_conjugation_count} orphaned test conjugations to remove..."
            )

            # Delete all test conjugations by infinitive pattern
            conjugation_delete_result = (
                await client.table("conjugations")
                .delete()
                .like("infinitive", "%\\_%")
                .execute()
            )

            conjugation_deleted_count = (
                len(conjugation_delete_result.data)
                if conjugation_delete_result.data
                else 0
            )
            click.echo(
                f"✅ Cleaned up {conjugation_deleted_count} orphaned test conjugations"
            )

        # Now delete test problems (identified by "test_data" in topic_tags)
        click.echo("🔍 Checking for test problems...")

        # Query for problems with "test_data" tag
        # Supabase array containment query - looks for "test_data" in topic_tags array
        test_problems_result = (
            await client.table("problems")
            .select("id, title")
            .contains("topic_tags", ["test_data"])
            .execute()
        )

        test_problem_count = (
            len(test_problems_result.data) if test_problems_result.data else 0
        )

        if test_problem_count == 0:
            click.echo("✅ No test problems found to clean.")
        else:
            click.echo(f"🎯 Found {test_problem_count} test problems to remove...")

            # Delete in batches of 100 to avoid query size limits
            test_problem_ids = [p["id"] for p in test_problems_result.data]
            batch_size = 100
            total_deleted = 0

            for i in range(0, len(test_problem_ids), batch_size):
                batch = test_problem_ids[i : i + batch_size]
                delete_result = (
                    await client.table("problems").delete().in_("id", batch).execute()
                )
                batch_deleted = len(delete_result.data) if delete_result.data else 0
                total_deleted += batch_deleted

            click.echo(f"✅ Cleaned up {total_deleted} test problems")

        # Finally, clean up test generation_requests (identified by "test_data" in metadata->'topic_tags')
        # NOTE: Must be done AFTER problems cleanup since problems.generation_request_id references generation_requests(id)
        click.echo("🔍 Checking for test generation requests...")

        # Get all generation_requests and filter in Python
        # PostgREST doesn't have a simple way to query nested JSONB arrays
        all_gen_requests_result = (
            await client.table("generation_requests").select("id, metadata").execute()
        )

        # Filter for requests with "test_data" in metadata topic_tags
        test_gen_request_ids = []
        if all_gen_requests_result.data:
            for req in all_gen_requests_result.data:
                metadata = req.get("metadata", {}) or {}
                topic_tags = metadata.get("topic_tags", []) or []
                if "test_data" in topic_tags:
                    test_gen_request_ids.append(req["id"])

        test_gen_request_count = len(test_gen_request_ids)

        if test_gen_request_count == 0:
            click.echo("✅ No test generation requests found to clean.")
        else:
            click.echo(
                f"🎯 Found {test_gen_request_count} test generation requests to remove..."
            )

            # Delete test generation requests
            delete_result = (
                await client.table("generation_requests")
                .delete()
                .in_("id", test_gen_request_ids)
                .execute()
            )

            deleted_count = len(delete_result.data) if delete_result.data else 0
            click.echo(f"✅ Cleaned up {deleted_count} test generation requests")

        if (
            test_verb_count == 0
            and orphaned_conjugation_count == 0
            and test_problem_count == 0
            and test_gen_request_count == 0
        ):
            click.echo("✨ Database is already clean!")

    except Exception as e:
        click.echo(f"❌ Error cleaning database: {e}")
        raise
