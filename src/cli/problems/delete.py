"""
CLI command to delete problems by ID or generation request ID.
"""

import logging
import sys
from uuid import UUID

import asyncclick as click

from src.cli.utils.safety import get_remote_flag, require_confirmation
from src.core.factories import create_problem_service
from src.services.problem_service import ProblemService

logger = logging.getLogger(__name__)


def _get_ids_from_stdin_or_option(option_value: UUID | None) -> list[UUID]:
    """Get IDs from option or stdin if piped. Returns a list of validated UUIDs."""
    if option_value:
        return [option_value]

    # Check if stdin has data (piped input)
    if not sys.stdin.isatty():
        stdin_data = sys.stdin.read().strip()
        if not stdin_data:
            return []

        # Detect JSON input and give helpful error
        if stdin_data.startswith("{") or stdin_data.startswith("["):
            raise click.UsageError(
                "Input looks like JSON. Pipe UUIDs (one per line), not raw JSON.\n"
                "  Example: lqs problem list --json | jq -r '.problems[].id' | lqs problem delete -f"
            )

        # Parse and validate each line as UUID
        ids = []
        for line_num, line in enumerate(stdin_data.split("\n"), 1):
            line = line.strip()
            if line:
                try:
                    ids.append(UUID(line))
                except ValueError:
                    raise click.UsageError(
                        f"Invalid UUID on line {line_num}: '{line}'\n"
                        "Expected valid UUIDs, one per line."
                    )
        return ids

    return []


@click.command("delete")
@click.argument("problem_id", type=click.UUID, required=False)
@click.option(
    "--force",
    "-f",
    is_flag=True,
    help="Skip confirmation prompt (required for piped input)",
)
@click.pass_context
async def delete_problem(
    ctx,
    problem_id: UUID | None,
    force: bool,
):
    """
    Delete problem(s) by ID.

    PROBLEM_ID can be provided as an argument or piped from stdin.

    Supports piping multiple IDs from stdin for streaming:
        lqs problem list --json | jq -r '.problems[].id' | lqs problem delete -f

    When piping multiple IDs, --force is required to skip per-item confirmation.

    Examples:
        lqs problem delete 123e4567-e89b-12d3-a456-426614174000
        lqs problem delete 123e4567-e89b-12d3-a456-426614174000 --force
        echo "uuid1\\nuuid2" | lqs problem delete -f

    By default, operates on local database. Use --remote to target remote database.
    Remote delete operations require confirmation.
    """
    # Get all problem IDs from argument or stdin
    problem_ids = _get_ids_from_stdin_or_option(problem_id)

    if not problem_ids:
        raise click.UsageError(
            "Must specify a problem ID as argument or pipe IDs from stdin"
        )

    is_remote = get_remote_flag(ctx)

    # Require --force when piping multiple IDs
    if len(problem_ids) > 1 and not force:
        raise click.UsageError(
            f"Multiple IDs detected ({len(problem_ids)}). Use --force to delete without per-item confirmation."
        )

    try:
        service = await create_problem_service()

        # Delete problem(s) by ID - supports streaming multiple IDs
        deleted_count = 0
        failed_count = 0

        for pid in problem_ids:
            try:
                success = await _delete_single_problem(
                    service, pid, is_remote, force, quiet=(len(problem_ids) > 1)
                )
                if success:
                    deleted_count += 1
                else:
                    failed_count += 1
            except Exception as e:
                click.echo(f"❌ Failed to delete {pid}: {e}", err=True)
                failed_count += 1

        # Summary for batch operations
        if len(problem_ids) > 1:
            click.echo(f"✅ Deleted {deleted_count} problem(s), {failed_count} failed")

    except click.UsageError:
        raise
    except Exception as e:
        if "not found" in str(e).lower():
            click.echo(f"❌ Not found: {e}")
        else:
            logger.error(f"Error deleting problem(s): {e}", exc_info=True)
            click.echo(f"❌ Error: {e}")


async def _delete_single_problem(
    service: ProblemService,
    problem_id: UUID,
    is_remote: bool,
    force: bool,
    quiet: bool = False,
) -> bool:
    """Delete a single problem by ID. Returns True if successful."""
    # First, verify the problem exists
    problem = await service.get_problem_by_id(problem_id)

    if not quiet:
        click.echo(f"📋 Found problem: {problem.title or problem.id}")
        click.echo(f"   Type: {problem.problem_type.value}")
        click.echo(f"   Created: {problem.created_at.strftime('%Y-%m-%d %H:%M')}")
        click.echo(f"   Statements: {len(problem.statements)}")

    # Confirm deletion (skipped in quiet mode since force is required)
    if not quiet and not require_confirmation(
        operation_name=f"delete problem {problem_id}",
        is_remote=is_remote,
        force=force,
    ):
        click.echo("❌ Aborted.")
        return False

    # Delete
    success = await service.delete_problem(problem_id)

    if success:
        if not quiet:
            click.echo(f"✅ Problem {problem_id} deleted successfully")
        return True
    else:
        if not quiet:
            click.echo(f"❌ Failed to delete problem {problem_id}")
        return False
