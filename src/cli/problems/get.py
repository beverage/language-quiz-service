"""CLI command for getting problems by ID or generation request ID."""

import json
import sys
from uuid import UUID

import asyncclick as click

from src.cli.problems.display import display_problem
from src.cli.utils.http_client import get_api_key, make_api_request
from src.schemas.problems import Problem


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
                "  Example: lqs problem list --json | jq -r '.problems[].id' | lqs problem get"
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


async def _get_problem_by_id_http(
    service_url: str, api_key: str, problem_id: str, include_metadata: bool = False
) -> Problem:
    """Get a problem by ID via HTTP API."""
    endpoint = f"/api/v1/problems/{problem_id}"
    if include_metadata:
        endpoint += "?include_metadata=true"
    response = await make_api_request(
        method="GET",
        endpoint=endpoint,
        base_url=service_url,
        api_key=api_key,
    )
    return Problem(**response.json())


@click.command("get")
@click.argument("problem_id", type=click.UUID, required=False)
@click.option("--verbose", "-v", is_flag=True, help="Show detailed problem information")
@click.option(
    "--json",
    "output_json",
    is_flag=True,
    help="Output raw JSON (one per line for streaming)",
)
@click.option(
    "--llm-trace", "llm_trace", is_flag=True, help="Include LLM generation trace"
)
@click.pass_context
async def get_problem(
    ctx,
    problem_id: UUID | None,
    verbose: bool,
    output_json: bool,
    llm_trace: bool,
):
    """
    Get problem(s) by ID.

    PROBLEM_ID can be provided as an argument or piped from stdin.

    Supports piping multiple IDs from stdin for streaming:
        lqs problem list --json | jq -r '.problems[].id' | lqs problem get

    When multiple IDs are piped, each problem is fetched and output.
    With --json, outputs one JSON object per line (JSONL format) for streaming.

    Examples:
        lqs problem get 123e4567-e89b-12d3-a456-426614174000
        lqs problem get 123e4567-e89b-12d3-a456-426614174000 --verbose
        echo "uuid1\\nuuid2" | lqs problem get --json
    """
    # Get all problem IDs from argument or stdin
    problem_ids = _get_ids_from_stdin_or_option(problem_id)

    if not problem_ids:
        raise click.UsageError(
            "Must specify a problem ID as argument or pipe IDs from stdin"
        )

    # Get service URL and flags from root context
    root_ctx = ctx.find_root()
    service_url = root_ctx.obj.get("service_url") if root_ctx.obj else None
    detailed = root_ctx.params.get("detailed", False) or verbose

    # Include metadata when detailed/verbose or when llm_trace is requested
    include_metadata = detailed or llm_trace

    if not service_url:
        raise click.ClickException(
            "Service URL not configured. This should not happen - please report a bug."
        )

    api_key = get_api_key()

    try:
        # Get problems by ID(s) - supports streaming multiple IDs
        for idx, pid in enumerate(problem_ids):
            try:
                problem = await _get_problem_by_id_http(
                    service_url, api_key, str(pid), include_metadata=include_metadata
                )

                if output_json:
                    # Output one JSON object per line (JSONL) for streaming
                    print(json.dumps(problem.model_dump(mode="json"), default=str))
                else:
                    if len(problem_ids) > 1 and idx > 0:
                        click.echo("\n" + "─" * 80 + "\n")
                    display_problem(problem, detailed=detailed, show_trace=llm_trace)

            except Exception as ex:
                # Log error but continue processing remaining IDs
                click.echo(f"❌ Failed to get problem {pid}: {ex}", err=True)

    except Exception as ex:
        raise click.ClickException(f"Failed to get problem(s): {ex}")
