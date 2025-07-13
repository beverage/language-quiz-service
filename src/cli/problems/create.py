"""
CLI problem creation using ProblemsService.

Updated to use new atomic problems system.
"""

import logging
import random
import traceback
from asyncio import sleep
from typing import List, Optional, Tuple

from src.services.problem_service import ProblemService
from src.schemas.problems import (
    Problem,
    ProblemType,
    ProblemFilters,
    GrammarProblemConstraints,
)

logger = logging.getLogger(__name__)


async def create_random_problem_with_delay(
    statement_count: int = 4,
    constraints: Optional[GrammarProblemConstraints] = None,
    display: bool = True,
) -> Problem:
    """Create a random problem with a delay (for batch operations)."""
    problem = await create_random_problem(
        statement_count=statement_count, constraints=constraints, display=display
    )
    await sleep(random.uniform(1.5, 2.0))
    return problem


async def create_random_problem(
    statement_count: int = 4,
    constraints: Optional[GrammarProblemConstraints] = None,
    display: bool = False,
) -> Problem:
    """Create a random grammar problem using the ProblemsService."""
    problems_service = ProblemService()

    try:
        logger.info(f"🎯 Creating random problem with {statement_count} statements")

        problem = await problems_service.create_random_grammar_problem(
            constraints=constraints,
            statement_count=statement_count,
        )

        if display:
            display_problem(problem)

        logger.info(f"✅ Created problem {problem.id}")
        return problem

    except Exception as ex:
        logger.error(f"Failed to create problem: {ex}")
        logger.error(traceback.format_exc())
        raise


async def create_random_problems_batch(
    quantity: int,
    statement_count: int = 4,
    constraints: Optional[GrammarProblemConstraints] = None,
    workers: int = 10,
    display: bool = True,
) -> List[Problem]:
    """Create multiple random problems in parallel."""
    from src.cli.utils.queues import parallel_execute

    logger.info(f"🎯 Creating {quantity} problems with {workers} workers")

    # Create tasks for parallel execution
    tasks = [
        create_random_problem_with_delay(
            statement_count=statement_count,
            constraints=constraints,
            display=False,  # Don't display individual problems in batch
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

    if display and results:
        print(f"\n🎯 Generated {len(results)} problems:")
        for i, problem in enumerate(results, 1):
            print(f"\n--- Problem {i} ---")
            display_problem_summary(problem)

    return results


# Problem listing and search functions
async def list_problems(
    problem_type: Optional[str] = None,
    topic_tags: Optional[List[str]] = None,
    limit: int = 10,
    verbose: bool = False,
) -> Tuple[List[Problem], int]:
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
            display_problem(problem)
    else:
        summaries, total = await problems_service.get_problem_summaries(filters)

        print(f"📋 Found {total} problems:")
        for summary in summaries:
            display_problem_summary_from_summary(summary)

    return problems if verbose else summaries, total


async def search_problems_by_focus(
    grammatical_focus: str,
    limit: int = 10,
) -> List[Problem]:
    """Search problems by grammatical focus."""
    problems_service = ProblemService()

    problems = await problems_service.get_problems_by_grammatical_focus(
        grammatical_focus, limit
    )

    print(f"🔍 Found {len(problems)} problems focusing on '{grammatical_focus}':")
    for problem in problems:
        display_problem_summary(problem)

    return problems


async def search_problems_by_topic(
    topic_tags: List[str],
    limit: int = 10,
) -> List[Problem]:
    """Search problems by topic tags."""
    problems_service = ProblemService()

    problems = await problems_service.get_problems_by_topic(topic_tags, limit)

    print(f"🔍 Found {len(problems)} problems with topics {topic_tags}:")
    for problem in problems:
        display_problem_summary(problem)

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


# Display functions
def display_problem(problem: Problem):
    """Display a complete problem in formatted output."""
    from src.cli.utils.console import Style, Color

    print(f"\n{'='*60}")
    print(f"🎯 {problem.title or 'Untitled Problem'}")
    print(f"📋 {problem.instructions}")
    print(f"🏷️  Tags: {', '.join(problem.topic_tags) if problem.topic_tags else 'None'}")

    if hasattr(problem, "metadata") and problem.metadata:
        focus = problem.metadata.get("grammatical_focus", [])
        if focus:
            print(f"🎯 Focus: {', '.join(focus)}")

    print("\n📝 Statements:")
    for i, statement in enumerate(problem.statements):
        is_correct = statement.get("is_correct", False)
        marker = (
            f"{Style.BOLD}{Color.STRONG_GREEN}✓{Style.RESET}"
            if is_correct
            else f"{Color.STRONG_RED}✗{Style.RESET}"
        )

        if i == problem.correct_answer_index:
            marker += f" {Style.BOLD}(ANSWER){Style.RESET}"

        print(f"   {i+1}. {marker} {statement.get('content', '')}")

        if is_correct and "translation" in statement:
            print(f"      {Color.BRIGHT_BLUE}→ {statement['translation']}{Style.RESET}")
        elif not is_correct and "explanation" in statement:
            print(
                f"      {Color.BRIGHT_YELLOW}→ {statement['explanation']}{Style.RESET}"
            )

    print(f"\n🆔 ID: {problem.id}")
    print(f"📅 Created: {problem.created_at.strftime('%Y-%m-%d %H:%M')}")


def display_problem_summary(problem: Problem):
    """Display a problem summary in compact format."""
    statement_count = len(problem.statements) if problem.statements else 0
    focus = ""
    if hasattr(problem, "metadata") and problem.metadata:
        focus_list = problem.metadata.get("grammatical_focus", [])
        if focus_list:
            focus = f" - {', '.join(focus_list)}"

    print(
        f"🎯 {problem.title or 'Untitled'} "
        f"({problem.problem_type.value}, {statement_count} statements{focus}) "
        f"- {problem.id}"
    )


def display_problem_summary_from_summary(summary):
    """Display a problem summary from a ProblemSummary object."""
    print(
        f"🎯 {summary.title or 'Untitled'} "
        f"({summary.problem_type.value}, {summary.statement_count} statements) "
        f"- {summary.id}"
    )
