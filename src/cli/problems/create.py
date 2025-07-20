"""
CLI problem creation using ProblemsService.

Updated to use new atomic problems system.
"""

import logging
import random
import traceback
from asyncio import sleep

from src.cli.problems.display import display_problem, display_problem_summary
from src.schemas.problems import (
    GrammarProblemConstraints,
    Problem,
    ProblemFilters,
    ProblemType,
)
from src.services.problem_service import ProblemService

logger = logging.getLogger(__name__)


async def create_random_problem_with_delay(
    statement_count: int = 4,
    constraints: GrammarProblemConstraints | None = None,
    display: bool = True,
    detailed: bool = False,
) -> Problem:
    """Create a random problem with a delay (for batch operations)."""
    problem = await create_random_problem(
        statement_count=statement_count,
        constraints=constraints,
        display=display,
        detailed=detailed,
    )
    await sleep(random.uniform(1.5, 2.0))
    return problem


async def create_random_problem(
    statement_count: int = 4,
    constraints: GrammarProblemConstraints | None = None,
    display: bool = False,
    detailed: bool = False,
) -> Problem:
    """Create a random grammar problem using the ProblemsService."""
    problems_service = ProblemService()

    try:
        logger.debug(f"🎯 Creating random problem with {statement_count} statements")

        problem = await problems_service.create_random_grammar_problem(
            constraints=constraints,
            statement_count=statement_count,
        )

        if display:
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
    workers: int = 10,
    display: bool = True,
    detailed: bool = False,
) -> list[Problem]:
    """Create multiple random problems in parallel."""
    from src.cli.utils.queues import parallel_execute

    logger.info(f"🎯 Creating {quantity} problems with {workers} workers")

    # Create tasks for parallel execution
    tasks = [
        create_random_problem_with_delay(
            statement_count=statement_count,
            constraints=constraints,
            display=display,  # Display individual problems in real-time
            detailed=detailed,
        )
        for _ in range(quantity)
    ]

    def handle_error(error: Exception, task_index: int):
        logger.warning(f"Failed to generate problem {task_index + 1}: {error}")

    # Execute in parallel
    results = await parallel_execute(
        tasks=tasks,
        max_concurrent=workers,
        batch_delay=0.5,
        error_handler=handle_error,
    )

    # Problems are already displayed in real-time during generation
    if display and results:
        print(f"\n🎯 Generated {len(results)} problems in total.")

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
