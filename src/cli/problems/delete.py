"""
CLI command to delete problems by ID or generation request ID.
"""

import logging
from uuid import UUID

import asyncclick as click

from src.cli.utils.safety import get_remote_flag, require_confirmation
from src.services.problem_service import ProblemService

logger = logging.getLogger(__name__)


@click.command("delete")
@click.option(
    "--id", "problem_id", type=click.UUID, help="Delete problem by problem ID"
)
@click.option(
    "--generation-id",
    "generation_id",
    type=click.UUID,
    help="Delete all problems by generation request ID",
)
@click.option("--force", "-f", is_flag=True, help="Skip confirmation prompt")
@click.pass_context
async def delete_problem(
    ctx,
    problem_id: UUID | None,
    generation_id: UUID | None,
    force: bool,
):
    """
    Delete problem(s) by ID or generation request ID.

    Examples:
        lqs problem delete --id 123e4567-e89b-12d3-a456-426614174000
        lqs problem delete --generation-id 550e8400-e29b-41d4-a716-446655440000
        lqs problem delete --generation-id 550e8400-e29b-41d4-a716-446655440000 --force

    By default, operates on local database. Use --remote to target remote database.
    Remote delete operations require confirmation.
    """
    # Validate that exactly one option is provided
    if not problem_id and not generation_id:
        raise click.UsageError("Must specify either --id or --generation-id")
    if problem_id and generation_id:
        raise click.UsageError("Cannot specify both --id and --generation-id")

    is_remote = get_remote_flag(ctx)

    try:
        service = ProblemService()

        if problem_id:
            # Delete single problem
            await _delete_single_problem(service, problem_id, is_remote, force)
        elif generation_id:
            # Delete all problems from generation request
            await _delete_by_generation_id(service, generation_id, is_remote, force)

    except Exception as e:
        if "not found" in str(e).lower():
            target = (
                f"Problem {problem_id}"
                if problem_id
                else f"Generation request {generation_id}"
            )
            click.echo(f"❌ {target} not found")
        else:
            logger.error(f"Error deleting problem(s): {e}", exc_info=True)
            click.echo(f"❌ Error: {e}")


async def _delete_single_problem(
    service: ProblemService,
    problem_id: UUID,
    is_remote: bool,
    force: bool,
) -> None:
    """Delete a single problem by ID."""
    # First, verify the problem exists
    problem = await service.get_problem_by_id(problem_id)

    click.echo(f"📋 Found problem: {problem.title or problem.id}")
    click.echo(f"   Type: {problem.problem_type.value}")
    click.echo(f"   Created: {problem.created_at.strftime('%Y-%m-%d %H:%M')}")
    click.echo(f"   Statements: {len(problem.statements)}")

    # Confirm deletion
    if not require_confirmation(
        operation_name=f"delete problem {problem_id}",
        is_remote=is_remote,
        force=force,
    ):
        click.echo("❌ Aborted.")
        return

    # Delete
    repo = await service._get_problem_repository()
    success = await repo.delete_problem(problem_id)

    if success:
        click.echo(f"✅ Problem {problem_id} deleted successfully")
    else:
        click.echo(f"❌ Failed to delete problem {problem_id}")


async def _delete_by_generation_id(
    service: ProblemService,
    generation_id: UUID,
    is_remote: bool,
    force: bool,
) -> None:
    """Delete all problems associated with a generation request."""
    # Get the generation request info first to show what we're deleting
    from src.services.generation_request_service import GenerationRequestService

    gen_service = GenerationRequestService()

    try:
        gen_request, problems = await gen_service.get_generation_request_with_entities(
            generation_id
        )
    except Exception:
        click.echo(f"❌ Generation request {generation_id} not found")
        return

    problem_count = len(problems) if problems else 0

    click.echo(f"📋 Found generation request: {generation_id}")
    click.echo(f"   Status: {gen_request.status.value}")
    click.echo(
        f"   Generated: {gen_request.generated_count}/{gen_request.requested_count}"
    )
    click.echo(f"   Problems to delete: {problem_count}")

    if problem_count == 0:
        click.echo("⚠️  No problems to delete for this generation request")
        return

    # Confirm deletion
    if not require_confirmation(
        operation_name=f"delete {problem_count} problem(s) from generation request {generation_id}",
        is_remote=is_remote,
        force=force,
    ):
        click.echo("❌ Aborted.")
        return

    # Delete
    deleted_count = await service.delete_problems_by_generation_id(generation_id)

    if deleted_count > 0:
        click.echo(
            f"✅ Deleted {deleted_count} problem(s) from generation request {generation_id}"
        )
    else:
        click.echo(
            f"❌ Failed to delete problems from generation request {generation_id}"
        )
