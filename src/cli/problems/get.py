"""CLI command for getting problems by ID or generation request ID."""

import asyncclick as click

from src.cli.problems.display import display_problem
from src.cli.utils.http_client import get_api_key, make_api_request
from src.schemas.problems import Problem


async def _get_problem_by_id_http(
    service_url: str, api_key: str, problem_id: str
) -> Problem:
    """Get a problem by ID via HTTP API."""
    response = await make_api_request(
        method="GET",
        endpoint=f"/api/v1/problems/{problem_id}",
        base_url=service_url,
        api_key=api_key,
    )
    return Problem(**response.json())


async def _get_problems_by_generation_id_http(
    service_url: str, api_key: str, generation_id: str
) -> dict:
    """Get generation request with problems via HTTP API."""
    response = await make_api_request(
        method="GET",
        endpoint=f"/api/v1/generation-requests/{generation_id}",
        base_url=service_url,
        api_key=api_key,
    )
    return response.json()


@click.command("get")
@click.option("--id", "problem_id", help="Get problem by problem ID")
@click.option(
    "--generation-id", "generation_id", help="Get all problems by generation request ID"
)
@click.option("--verbose", "-v", is_flag=True, help="Show detailed problem information")
@click.option("--json", "output_json", is_flag=True, help="Output raw JSON")
@click.pass_context
async def get_problem(
    ctx,
    problem_id: str | None,
    generation_id: str | None,
    verbose: bool,
    output_json: bool,
):
    """
    Get problem(s) by ID or generation request ID.

    Examples:
        lqs problem get --id 123e4567-e89b-12d3-a456-426614174000
        lqs problem get --generation-id 550e8400-e29b-41d4-a716-446655440000
        lqs problem get --generation-id 550e8400-e29b-41d4-a716-446655440000 --verbose
    """
    # Validate that exactly one option is provided
    if not problem_id and not generation_id:
        raise click.UsageError("Must specify either --id or --generation-id")
    if problem_id and generation_id:
        raise click.UsageError("Cannot specify both --id and --generation-id")

    # Get service URL from root context
    root_ctx = ctx.find_root()
    service_url = root_ctx.obj.get("service_url") if root_ctx.obj else None
    detailed = root_ctx.params.get("detailed", False) or verbose

    if not service_url:
        raise click.ClickException(
            "Service URL not configured. This should not happen - please report a bug."
        )

    api_key = get_api_key()

    try:
        if problem_id:
            # Get single problem by ID
            problem = await _get_problem_by_id_http(service_url, api_key, problem_id)

            if output_json:
                import json

                print(
                    json.dumps(problem.model_dump(mode="json"), indent=2, default=str)
                )
            else:
                display_problem(problem, detailed=detailed)

        elif generation_id:
            # Get generation request with all problems
            data = await _get_problems_by_generation_id_http(
                service_url, api_key, generation_id
            )

            if output_json:
                import json

                print(json.dumps(data, indent=2, default=str))
            else:
                # Display generation request metadata
                click.echo("\n📋 Generation Request Details:")
                click.echo(f"   Request ID: {data['request_id']}")
                click.echo(f"   Status: {data['status']}")
                click.echo(f"   Entity Type: {data['entity_type']}")
                click.echo(
                    f"   Progress: {data['generated_count']}/{data['requested_count']}"
                )
                if data.get("failed_count", 0) > 0:
                    click.echo(f"   Failed: {data['failed_count']}")
                click.echo(f"   Requested At: {data['requested_at']}")
                if data.get("completed_at"):
                    click.echo(f"   Completed At: {data['completed_at']}")
                if data.get("error_message"):
                    click.echo(f"   Error: {data['error_message']}")

                # Display problems
                problems = data.get("entities", [])
                if problems:
                    click.echo(f"\n✅ Generated {len(problems)} problem(s):\n")
                    for idx, problem_data in enumerate(problems, 1):
                        problem = Problem(**problem_data)
                        if detailed:
                            click.echo(f"Problem {idx}:")
                            display_problem(problem, detailed=True)
                            if idx < len(problems):
                                click.echo("\n" + "─" * 80 + "\n")
                        else:
                            click.echo(
                                f"{idx}. {problem.id} - {problem.title or 'Untitled'}"
                            )
                else:
                    click.echo("\n⏳ No problems generated yet.")

    except Exception as ex:
        raise click.ClickException(f"Failed to get problem(s): {ex}")
