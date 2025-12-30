"""
CLI commands for managing generation requests.
"""

import logging
from uuid import UUID

import asyncclick as click

from src.cli.utils.safety import get_remote_flag, require_confirmation
from src.core.factories import create_generation_request_repository
from src.schemas.generation_requests import GenerationStatus

logger = logging.getLogger(__name__)


@click.command("list")
@click.option(
    "--status",
    type=click.Choice(
        ["pending", "processing", "completed", "failed", "partial", "expired"]
    ),
    help="Filter by status",
)
@click.option("--limit", default=20, help="Number of requests to show")
@click.pass_context
async def list_requests(ctx, status: str | None, limit: int):
    """
    List generation requests.

    Shows recent generation requests with their status and counts.
    """
    try:
        repo = await create_generation_request_repository()

        # Convert status string to enum if provided
        status_filter = GenerationStatus(status) if status else None

        requests, total = await repo.get_all_requests(
            status=status_filter,
            limit=limit,
        )

        if not requests:
            if status:
                click.echo(f"📭 No generation requests found with status '{status}'")
            else:
                click.echo("📭 No generation requests found")
            return

        click.echo(f"📋 Generation Requests (showing {len(requests)} of {total}):\n")

        for req in requests:
            # Status indicator
            status_emoji = {
                GenerationStatus.PENDING: "⏳",
                GenerationStatus.PROCESSING: "🔄",
                GenerationStatus.COMPLETED: "✅",
                GenerationStatus.FAILED: "❌",
                GenerationStatus.PARTIAL: "⚠️",
                GenerationStatus.EXPIRED: "⌛",
            }.get(req.status, "❓")

            # Format time
            time_str = req.requested_at.strftime("%Y-%m-%d %H:%M")

            # Progress
            progress = f"{req.generated_count}/{req.requested_count}"
            if req.failed_count > 0:
                progress += f" ({req.failed_count} failed)"

            click.echo(
                f"  {status_emoji} {req.id}  "
                f"[{req.status.value:10}]  "
                f"{progress:15}  "
                f"{time_str}"
            )

            # Show error if failed or expired
            if req.error_message and req.status in (
                GenerationStatus.FAILED,
                GenerationStatus.EXPIRED,
            ):
                click.echo(f"      └─ {req.error_message[:60]}...")

        click.echo()

    except Exception as e:
        logger.error(f"Error listing generation requests: {e}", exc_info=True)
        click.echo(f"❌ Error: {e}")


@click.command("status")
@click.argument("request_id", type=click.UUID)
@click.pass_context
async def get_status(ctx, request_id: UUID):
    """
    Get detailed status of a generation request.

    REQUEST_ID is the UUID of the generation request.
    """
    try:
        repo = await create_generation_request_repository()
        request = await repo.get_generation_request(request_id)

        if not request:
            click.echo(f"❌ Generation request {request_id} not found")
            return

        # Status indicator
        status_emoji = {
            GenerationStatus.PENDING: "⏳",
            GenerationStatus.PROCESSING: "🔄",
            GenerationStatus.COMPLETED: "✅",
            GenerationStatus.FAILED: "❌",
            GenerationStatus.PARTIAL: "⚠️",
            GenerationStatus.EXPIRED: "⌛",
        }.get(request.status, "❓")

        click.echo(f"\n{status_emoji} Generation Request: {request.id}\n")
        click.echo(f"  Status:      {request.status.value}")
        click.echo(f"  Entity Type: {request.entity_type}")
        click.echo(
            f"  Progress:    {request.generated_count}/{request.requested_count}"
        )

        if request.failed_count > 0:
            click.echo(f"  Failed:      {request.failed_count}")

        click.echo(
            f"\n  Requested:   {request.requested_at.strftime('%Y-%m-%d %H:%M:%S')}"
        )

        if request.started_at:
            click.echo(
                f"  Started:     {request.started_at.strftime('%Y-%m-%d %H:%M:%S')}"
            )

        if request.completed_at:
            click.echo(
                f"  Completed:   {request.completed_at.strftime('%Y-%m-%d %H:%M:%S')}"
            )
            # Calculate duration
            duration = request.completed_at - request.requested_at
            click.echo(f"  Duration:    {duration.total_seconds():.1f}s")

        if request.constraints:
            click.echo(f"\n  Constraints: {request.constraints}")

        if request.error_message:
            click.echo(f"\n  ❌ Error: {request.error_message}")

        # Get associated problems
        problems = await repo.get_problems_by_request_id(request_id)
        if problems:
            click.echo(f"\n  📋 Problems Generated: {len(problems)}")
            for p in problems[:5]:  # Show first 5
                click.echo(f"     - {p['id']} ({p.get('title', 'Untitled')})")
            if len(problems) > 5:
                click.echo(f"     ... and {len(problems) - 5} more")

        click.echo()

    except Exception as e:
        logger.error(f"Error getting generation request status: {e}", exc_info=True)
        click.echo(f"❌ Error: {e}")


@click.command("clean")
@click.option(
    "--older-than",
    default=7,
    help="Delete completed/failed requests older than N days (default: 7)",
)
@click.option("--force", "-f", is_flag=True, help="Skip confirmation prompt")
@click.pass_context
async def clean_requests(ctx, older_than: int, force: bool):
    """
    Delete old completed/failed/expired generation requests.

    By default, deletes completed, failed, and expired requests older than 7 days.
    Does NOT delete pending or processing requests.
    """
    is_remote = get_remote_flag(ctx)

    try:
        repo = await create_generation_request_repository()

        # Get count of requests that will be deleted
        from datetime import UTC, datetime, timedelta

        cutoff = datetime.now(UTC) - timedelta(days=older_than)

        # Count requests to be deleted (include EXPIRED in cleanup)
        statuses = [
            GenerationStatus.COMPLETED,
            GenerationStatus.FAILED,
            GenerationStatus.EXPIRED,
        ]
        all_requests, _ = await repo.get_all_requests(limit=10000)

        # Filter locally to get count
        requests_to_delete = [
            r for r in all_requests if r.status in statuses and r.requested_at < cutoff
        ]
        count = len(requests_to_delete)

        if count == 0:
            click.echo(
                f"✅ No completed/failed/expired requests older than {older_than} days to delete."
            )
            return

        click.echo(
            f"🎯 Found {count} completed/failed/expired requests older than {older_than} days"
        )

        # Confirm deletion
        if not require_confirmation(
            operation_name=f"delete {count} old generation requests",
            is_remote=is_remote,
            force=force,
            item_count=count,
        ):
            click.echo("❌ Aborted.")
            return

        # Perform deletion
        click.echo(f"🗑️  Deleting {count} old generation requests...")

        deleted = await repo.delete_old_requests(
            older_than_days=older_than,
            statuses=statuses,
        )

        click.echo(f"✅ Deleted {deleted} generation requests")

    except Exception as e:
        logger.error(f"Error cleaning generation requests: {e}", exc_info=True)
        click.echo(f"❌ Error: {e}")
