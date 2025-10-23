"""
CLI database initialization - Download conjugations for all verbs.

This command queries all non-test verbs from the database and downloads
their conjugations via the verb download API, ensuring all verbs have
complete conjugation data.
"""

import asyncio
import logging
from dataclasses import dataclass

import asyncclick as click

from src.cli.utils.http_client import get_api_key, make_api_request
from src.cli.utils.verb_diff import format_verb_diff, get_verb_diff
from src.clients.supabase import get_supabase_client
from src.schemas.verbs import Tense

logger = logging.getLogger(__name__)


@dataclass
class VerbTask:
    """Represents a verb to be downloaded."""

    infinitive: str
    target_language_code: str
    attempts: int = 0
    max_attempts: int = 3


async def _download_verb_conjugations_http(
    service_url: str, api_key: str, infinitive: str, target_language_code: str = "eng"
) -> dict:
    """Download conjugations for a verb via HTTP API."""
    request_data = {
        "infinitive": infinitive,
        "target_language_code": target_language_code,
    }

    response = await make_api_request(
        method="POST",
        endpoint="/api/v1/verbs/download",
        base_url=service_url,
        api_key=api_key,
        json_data=request_data,
        timeout=120.0,  # Longer timeout for LLM generation (2 minutes per verb)
    )

    return response.json()


async def _worker(
    worker_id: int,
    queue: asyncio.Queue,
    service_url: str,
    api_key: str,
    success_count: dict,
    failure_count: dict,
    changes_report: dict,
    db_client=None,
):
    """Worker that processes verbs from the queue with retry logic."""
    while True:
        try:
            # Get task from queue
            task: VerbTask = await queue.get()

            should_mark_done = True  # Track if we should call task_done

            try:
                # GET verb before download to compare
                before_verb = None
                if db_client:
                    try:
                        result = (
                            await db_client.table("verbs")
                            .select(
                                "infinitive,auxiliary,reflexive,classification,can_have_cod,can_have_coi"
                            )
                            .eq("infinitive", task.infinitive)
                            .eq("target_language_code", task.target_language_code)
                            .execute()
                        )

                        if result.data:
                            # If multiple variants exist, just take the first for comparison
                            before_verb = result.data[0]
                    except Exception as e:
                        logger.debug(f"Could not GET verb before download: {e}")

                # Attempt to download
                await _download_verb_conjugations_http(
                    service_url, api_key, task.infinitive, task.target_language_code
                )

                # GET verb after download to compare
                after_verb = None
                if db_client:
                    try:
                        result = (
                            await db_client.table("verbs")
                            .select(
                                "infinitive,auxiliary,reflexive,classification,can_have_cod,can_have_coi"
                            )
                            .eq("infinitive", task.infinitive)
                            .eq("target_language_code", task.target_language_code)
                            .execute()
                        )

                        if result.data:
                            # Same logic - take first if multiple
                            after_verb = result.data[0]
                    except Exception as e:
                        logger.debug(f"Could not GET verb after download: {e}")

                # Calculate and display diff
                if after_verb:
                    changes = get_verb_diff(before_verb, after_verb)
                    if changes:
                        # Save changes to report
                        changes_report[task.infinitive] = changes

                        diff_output = format_verb_diff(task.infinitive, changes)
                        if diff_output:
                            click.echo(diff_output)
                    else:
                        # No changes - just show checkmark
                        click.echo(f"   ✅ {task.infinitive}")
                else:
                    # Couldn't get after verb - just show success
                    click.echo(f"   ✅ {task.infinitive}")

                # Success
                success_count["value"] += 1
                logger.info(f"Successfully processed '{task.infinitive}'")

            except Exception as e:
                # Failure - check if we should retry
                task.attempts += 1

                if task.attempts < task.max_attempts:
                    # Retry - mark current task done, then add back to queue
                    logger.warning(
                        f"Failed '{task.infinitive}' (attempt {task.attempts}/{task.max_attempts}): {str(e)[:80]}"
                    )
                    # IMPORTANT: Mark done first, then re-add to queue
                    # This keeps the queue's unfinished task count correct
                    queue.task_done()
                    await queue.put(task)
                    should_mark_done = False  # Already called task_done
                else:
                    # Max attempts reached - give up
                    failure_count["value"] += 1
                    logger.error(
                        f"Failed '{task.infinitive}' after {task.max_attempts} attempts: {e}"
                    )
                    click.echo(f"   ❌ {task.infinitive}: {str(e)[:60]}")

            finally:
                # Mark task as done (unless we already did it for retry)
                if should_mark_done:
                    queue.task_done()

        except asyncio.CancelledError:
            # Worker is being cancelled - exit gracefully
            break


@click.command()
@click.option(
    "--verbs-only",
    is_flag=True,
    help="DISABLED: Verb properties must be added via database migrations",
)
@click.pass_context
async def init_verbs(ctx, verbs_only: bool):
    """
    Download conjugations for all non-test verbs in the database.

    This command:
    1. Queries all verbs from the database that don't have '_' in their infinitive (non-test verbs)
    2. Calls the verb download API for each verb to download conjugations
    3. Uses a worker pool of 50 concurrent workers processing from a queue
    4. Retries failures up to 3 times
    5. Respects --local/--remote flags (default: local at http://localhost:8000)

    Use --local to target local service (default)
    Use --remote to target remote service from SERVICE_URL env var

    Note: Verbs must already exist in the database (added via migrations).
    """
    # Check for disabled --verbs-only flag
    if verbs_only:
        click.echo(
            "❌ Error: --verbs-only is disabled. Verb properties must be added via database migrations.\n"
            "   This command only downloads conjugations for existing verbs."
        )
        return

    # Get service URL from context (set by root CLI)
    service_url = ctx.obj.get("service_url") if ctx.obj else None

    if not service_url:
        # Default to local if no flags provided
        service_url = "http://localhost:8000"

    logger.info(f"Initializing verb conjugations using API at {service_url}")

    try:
        # Get API key
        api_key = get_api_key()

        # Get all verbs from database
        client = await get_supabase_client()
        result = (
            await client.table("verbs")
            .select("infinitive,target_language_code")
            .execute()
        )

        # Filter out test verbs (those with underscore in infinitive)
        all_verbs = result.data
        non_test_verbs = [
            (v["infinitive"], v["target_language_code"])
            for v in all_verbs
            if "_" not in v["infinitive"]
        ]

        if not non_test_verbs:
            click.echo("✅ No verbs found in database to initialize.")
            return

        click.echo(f"📚 Found {len(non_test_verbs)} non-test verbs to initialize")
        click.echo(f"🎯 Downloading conjugations for all {len(Tense)} tenses...")
        click.echo(
            "⚙️  Using 50 concurrent workers with retry logic (max 3 attempts)..."
        )

        # Create queue and populate with tasks
        queue = asyncio.Queue()
        for infinitive, target_lang in non_test_verbs:
            await queue.put(VerbTask(infinitive, target_lang))

        # Shared counters and report data (using dict for mutability across workers)
        success_count = {"value": 0}
        failure_count = {"value": 0}
        changes_report = {}  # Dict[infinitive, Dict[field, (old_val, new_val)]]

        # Create 50 workers - pass db client for diff functionality
        workers = []
        for i in range(50):
            worker = asyncio.create_task(
                _worker(
                    i,
                    queue,
                    service_url,
                    api_key,
                    success_count,
                    failure_count,
                    changes_report,
                    client,
                )
            )
            workers.append(worker)

        # Wait for all tasks to be processed
        await queue.join()

        # Cancel workers
        for worker in workers:
            worker.cancel()

        # Wait for workers to finish cancelling
        await asyncio.gather(*workers, return_exceptions=True)

        # Generate and display report
        _display_report(
            success_count["value"],
            failure_count["value"],
            len(non_test_verbs),
            changes_report,
        )

    except Exception as e:
        logger.error(f"Failed to initialize verbs: {e}")
        click.echo(f"❌ Error: {e}")
        raise


def _display_report(
    success_count: int, failure_count: int, total_verbs: int, changes_report: dict
):
    """Display a comprehensive report of verb initialization results."""
    click.echo(f"\n{'='*70}")
    click.echo("📊 Verb Initialization Report")
    click.echo(f"{'='*70}")
    click.echo(f"✅ Successfully processed: {success_count}/{total_verbs} verbs")

    if changes_report:
        click.echo(f"📝 Verbs with changes: {len(changes_report)}")
        click.echo()

        # Calculate field change statistics
        field_stats = {}
        for verb_changes in changes_report.values():
            for field in verb_changes.keys():
                field_stats[field] = field_stats.get(field, 0) + 1

        if field_stats:
            click.echo("Changes by Field:")
            for field in sorted(field_stats.keys()):
                count = field_stats[field]
                click.echo(
                    f"  • {field}: {count} verb{'s' if count != 1 else ''} changed"
                )
            click.echo()

        # Display detailed changes (alphabetically by verb)
        click.echo("Detailed Changes:")
        for infinitive in sorted(changes_report.keys()):
            changes = changes_report[infinitive]
            diff_output = format_verb_diff(infinitive, changes)
            if diff_output:
                click.echo(diff_output)
    else:
        click.echo("📝 Verbs with changes: 0")
        click.echo()
        click.echo("✨ No verbs were modified - all data was already up to date!")

    click.echo(f"\n{'='*70}")

    if failure_count > 0:
        click.echo(
            f"⚠️  {failure_count} verb{'s' if failure_count != 1 else ''} failed after 3 attempts. Check logs for details."
        )
    else:
        click.echo("🎉 All verbs successfully initialized!")

    click.echo(f"{'='*70}")
