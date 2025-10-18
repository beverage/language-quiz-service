"""
CLI problem creation using ProblemsService.

Updated to use new atomic problems system.
"""

import logging
import traceback

from src.cli.problems.display import display_problem, display_problem_summary
from src.cli.utils.http_client import get_api_key, make_api_request
from src.schemas.problems import (
    GrammarProblemConstraints,
    Problem,
    ProblemFilters,
    ProblemType,
)
from src.services.problem_service import ProblemService

logger = logging.getLogger(__name__)


async def _create_problem_http(
    service_url: str,
    api_key: str,
    statement_count: int = 4,
    constraints: GrammarProblemConstraints | None = None,
    include_metadata: bool = False,
) -> Problem:
    """Create a problem via HTTP API."""
    request_data = {
        "statement_count": statement_count,
    }
    if constraints:
        request_data["constraints"] = constraints.model_dump(exclude_none=True)

    # Add include_metadata query parameter
    params = {}
    if include_metadata:
        params["include_metadata"] = "true"

    response = await make_api_request(
        method="POST",
        endpoint="/api/v1/problems/random",
        base_url=service_url,
        api_key=api_key,
        json_data=request_data,
        params=params,
    )
    return Problem(**response.json())


async def _get_problem_http(service_url: str, api_key: str, problem_id: str) -> Problem:
    """Get a problem by ID via HTTP API."""
    response = await make_api_request(
        method="GET",
        endpoint=f"/api/v1/problems/{problem_id}",
        base_url=service_url,
        api_key=api_key,
    )
    return Problem(**response.json())


async def create_random_problem_with_delay(
    statement_count: int = 4,
    constraints: GrammarProblemConstraints | None = None,
    display: bool = True,
    detailed: bool = False,
    service_url: str | None = None,
    output_json: bool = False,
) -> Problem:
    """Create a random problem (wrapper for batch operations)."""
    problem = await create_random_problem(
        statement_count=statement_count,
        constraints=constraints,
        display=display,
        detailed=detailed,
        service_url=service_url,
        output_json=output_json,
    )
    return problem


async def create_random_problem(
    statement_count: int = 4,
    constraints: GrammarProblemConstraints | None = None,
    display: bool = False,
    detailed: bool = False,
    service_url: str | None = None,
    output_json: bool = False,
) -> Problem:
    """Create a random grammar problem using the ProblemsService or HTTP API."""
    try:
        logger.debug(f"🎯 Creating random problem with {statement_count} statements")

        if service_url:
            # HTTP mode - make API call
            api_key = get_api_key()
            problem = await _create_problem_http(
                service_url=service_url,
                api_key=api_key,
                statement_count=statement_count,
                constraints=constraints,
                include_metadata=output_json,  # Request metadata when JSON output
            )
        else:
            # Direct mode - use service layer
            problems_service = ProblemService()
            problem = await problems_service.create_random_grammar_problem(
                constraints=constraints,
                statement_count=statement_count,
            )

        if output_json:
            # Output raw JSON with all fields
            import json

            print(json.dumps(problem.model_dump(mode="json"), indent=2, default=str))
        elif display:
            display_problem(problem, detailed=detailed)

        logger.debug(f"✅ Created problem {problem.id}")
        return problem

    except Exception as ex:
        logger.error(f"Failed to create problem: {ex}")
        logger.error(traceback.format_exc())
        raise


async def create_random_problems_batch(
    quantity: int,
    statement_count: int = 4,
    constraints: GrammarProblemConstraints | None = None,
    workers: int = 25,
    display: bool = True,
    detailed: bool = False,
    service_url: str | None = None,
    output_json: bool = False,
) -> list[Problem]:
    """Create multiple random problems in parallel."""
    from src.cli.utils.queues import parallel_execute

    logger.debug("🎯 Creating %s problems with %s workers", quantity, workers)

    # Create tasks for parallel execution
    tasks = [
        create_random_problem_with_delay(
            statement_count=statement_count,
            constraints=constraints,
            display=display and not output_json,  # Only display if not JSON mode
            detailed=detailed,
            service_url=service_url,
            output_json=False,  # Don't output JSON for individual items in batch
        )
        for _ in range(quantity)
    ]

    def handle_error(error: Exception, task_index: int):
        logger.debug(f"Failed to generate problem {task_index + 1}: {error}")

    # Execute in parallel
    results = await parallel_execute(
        tasks=tasks,
        max_concurrent=workers,
        batch_delay=0.5,
        error_handler=handle_error,
    )

    # Output results
    if output_json:
        # Output all results as JSON array
        import json

        print(
            json.dumps(
                [p.model_dump(mode="json") for p in results], indent=2, default=str
            )
        )
    elif display and results:
        logger.debug("🎯 Generated %s problems in total.", len(results))

    return results


# Problem listing and search functions
async def list_problems(
    problem_type: str | None = None,
    topic_tags: list[str] | None = None,
    limit: int = 10,
    verbose: bool = False,
    detailed: bool = False,
) -> tuple[list[Problem], int]:
    """List problems with optional filtering."""
    problems_service = ProblemService()

    # Build filters
    filters = ProblemFilters(limit=limit)

    if problem_type:
        filters.problem_type = ProblemType(problem_type)
    if topic_tags:
        filters.topic_tags = topic_tags

    if verbose:
        problems, total = await problems_service.get_problems(filters)

        print(f"📋 Found {total} problems:")
        for problem in problems:
            display_problem(problem, detailed=detailed)
    else:
        summaries, total = await problems_service.get_problem_summaries(filters)

        print(f"📋 Found {total} problems:")
        for summary in summaries:
            display_problem_summary(summary)

    return problems if verbose else summaries, total


async def search_problems_by_focus(
    grammatical_focus: str,
    limit: int = 10,
    detailed: bool = False,
) -> list[Problem]:
    """Search problems by grammatical focus."""
    problems_service = ProblemService()

    problems = await problems_service.get_problems_by_grammatical_focus(
        grammatical_focus, limit
    )

    print(f"🔍 Found {len(problems)} problems focusing on '{grammatical_focus}':")
    for problem in problems:
        display_problem(problem, detailed=detailed)

    return problems


async def search_problems_by_topic(
    topic_tags: list[str],
    limit: int = 10,
    detailed: bool = False,
) -> list[Problem]:
    """Search problems by topic tags."""
    problems_service = ProblemService()

    problems = await problems_service.get_problems_by_topic(topic_tags, limit)

    print(f"🔍 Found {len(problems)} problems with topics {topic_tags}:")
    for problem in problems:
        display_problem(problem, detailed=detailed)

    return problems


async def get_problem_statistics() -> dict:
    """Get and display problem statistics."""
    problems_service = ProblemService()

    stats = await problems_service.get_problem_statistics()

    print("📊 Problem Statistics:")
    print(f"   Total problems: {stats['total_problems']}")
    print("   By type:")

    for problem_type, count in stats["problems_by_type"].items():
        print(f"     {problem_type}: {count}")

    return stats
