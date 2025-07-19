#!/usr/bin/env python3
import logging
import traceback

import asyncclick as click
from dotenv import load_dotenv

from src.cli.api_keys.commands import (
    create as api_keys_create,
)
from src.cli.api_keys.commands import (
    list_keys as api_keys_list,
)
from src.cli.api_keys.commands import (
    revoke as api_keys_revoke,
)
from src.cli.cloud.database import (
    status as database_status,
)
from src.cli.cloud.service import down as service_down
from src.cli.cloud.service import up as service_up
from src.cli.database.clear import clear_database
from src.cli.database.init import init_verbs
from src.cli.problems.create import (
    create_random_problem,
    create_random_problem_with_delay,
    create_random_problems_batch,
    get_problem_statistics,
    list_problems,
    search_problems_by_focus,
    search_problems_by_topic,
)
from src.cli.sentences.create import create_random_sentence_batch, create_sentence
from src.cli.utils.console import Style
from src.cli.utils.queues import batch_operation
from src.cli.verbs.commands import download, get, random
from src.schemas.problems import GrammarProblemConstraints


@click.group()
@click.option("--debug", default=False, is_flag=True)
@click.option("--debug-openai", default=False, is_flag=True)
@click.option("--debug-recovery", default=False, is_flag=True)
async def cli(debug=False, debug_openai=False, debug_recovery=True):
    # Load environment variables from .env file
    load_dotenv()

    logging.basicConfig(level=logging.DEBUG if debug else logging.INFO)

    # Suppress httpx logging to reduce noise
    logging.getLogger("httpx").setLevel(logging.WARNING)

    if debug_openai:
        logging.getLogger("openai").setLevel(logging.DEBUG)

    if debug_recovery:
        logging.getLogger("recovery").setLevel(logging.DEBUG)

    # Removed: await reflect_tables()  # SQLAlchemy dependency removed


@cli.group()
async def cloud():
    pass


@cloud.group("rds")
async def cloud_database():
    pass


cloud_database.add_command(service_down, name="down")
cloud_database.add_command(service_up, name="up")
cloud_database.add_command(database_status, name="status")


@cloud.group()
async def service():
    pass


service.add_command(service_down, name="down")
service.add_command(service_up, name="up")


@cli.group()
async def database():
    pass


database.add_command(clear_database, name="clean")
database.add_command(init_verbs, name="init")


@cli.group()
async def problem():
    """Problem generation and management commands."""
    pass


@problem.command("random")
@click.option("--count", "-c", default=1, help="Number of problems to generate")
@click.option("--statements", "-s", default=4, help="Number of statements per problem")
@click.option("--include-cod", is_flag=True, help="Force inclusion of direct objects")
@click.option("--include-coi", is_flag=True, help="Force inclusion of indirect objects")
@click.option("--include-negation", is_flag=True, help="Force inclusion of negation")
@click.option(
    "--tense", multiple=True, help="Limit to specific tenses (can specify multiple)"
)
async def problem_random(
    count: int,
    statements: int,
    include_cod: bool,
    include_coi: bool,
    include_negation: bool,
    tense: tuple,
):
    """Generate random grammar problems."""
    try:
        # Build constraints from CLI options
        constraints = None
        if any([include_cod, include_coi, include_negation, tense]):
            constraints = GrammarProblemConstraints()

            if include_cod:
                constraints.includes_cod = True
            if include_coi:
                constraints.includes_coi = True
            if include_negation:
                constraints.includes_negation = True
            if tense:
                constraints.tenses_used = list(tense)

        if count == 1:
            # Single problem generation
            await create_random_problem(
                statement_count=statements, constraints=constraints, display=True
            )
        else:
            # Batch generation
            await create_random_problems_batch(
                quantity=count,
                statement_count=statements,
                constraints=constraints,
                display=True,
            )

    except Exception as ex:
        click.echo(f"❌ Error generating problems: {ex}")


@problem.command("list")
@click.option(
    "--type",
    "problem_type",
    type=click.Choice(["grammar", "functional", "vocabulary"]),
    help="Filter by problem type",
)
@click.option("--topic", multiple=True, help="Filter by topic tags")
@click.option("--limit", default=10, help="Number of problems to show")
@click.option("--verbose", "-v", is_flag=True, help="Show full problem details")
async def problem_list(problem_type: str, topic: tuple, limit: int, verbose: bool):
    """List existing problems with filtering."""
    try:
        await list_problems(
            problem_type=problem_type,
            topic_tags=list(topic) if topic else None,
            limit=limit,
            verbose=verbose,
        )
    except Exception as ex:
        click.echo(f"❌ Error listing problems: {ex}")


@problem.command("search")
@click.option(
    "--focus", help="Search by grammatical focus (e.g., direct_objects, negation)"
)
@click.option("--topic", multiple=True, help="Search by topic tags")
@click.option("--limit", default=10, help="Number of results to show")
async def problem_search(focus: str, topic: tuple, limit: int):
    """Search problems by various criteria."""
    try:
        if focus:
            await search_problems_by_focus(focus, limit)
        elif topic:
            await search_problems_by_topic(list(topic), limit)
        else:
            click.echo(
                "❌ Please specify at least one search criteria (--focus or --topic)"
            )

    except Exception as ex:
        click.echo(f"❌ Error searching problems: {ex}")


@problem.command("stats")
async def problem_stats():
    """Show problem statistics."""
    try:
        await get_problem_statistics()
    except Exception as ex:
        click.echo(f"❌ Error getting statistics: {ex}")


# Keep the existing batch command but update it to use new system
@problem.command("batch")
@click.argument("quantity", default=10, type=click.INT)
@click.option("--workers", default=10, type=click.INT)
@click.option("--statements", "-s", default=4, help="Number of statements per problem")
async def batch(quantity: int, workers: int, statements: int):
    """Generate multiple problems in parallel."""
    try:
        results = await create_random_problems_batch(
            quantity=quantity, statement_count=statements, workers=workers, display=True
        )
        print(f"{Style.BOLD}Generated {len(results)} problems{Style.RESET}")
    except Exception as ex:
        print(f"❌ Error: {ex}")
        print(traceback.format_exc())
    try:
        results = await batch_operation(
            workers=workers,
            quantity=quantity,
            method=create_random_problem_with_delay,
            display=True,
        )
        print(f"{Style.BOLD}Generated {len(results)}{Style.RESET}")
    except Exception as ex:
        print(f"str({ex}): {traceback.format_exc()}")


@cli.group()
async def sentence():
    pass


sentence.add_command(create_sentence, name="new")
sentence.add_command(create_random_sentence_batch, name="random")


# Create the verb group
@cli.group()
async def verb():
    """Verb management commands."""
    pass


verb.add_command(download, name="download")
verb.add_command(get, name="get")
verb.add_command(random, name="random")


@cli.group("api-keys")
async def api_keys():
    """API key management commands."""
    pass


# Add API key commands to the group
api_keys.add_command(api_keys_create, name="create")
api_keys.add_command(api_keys_list, name="list")
api_keys.add_command(api_keys_revoke, name="revoke")


def main():
    cli(_anyio_backend="asyncio")


if __name__ == "__main__":
    main()
