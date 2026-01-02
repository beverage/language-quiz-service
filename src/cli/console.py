#!/usr/bin/env python3
import logging
import os
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
from src.cli.cache.commands import (
    cache_stats,
    reload_cache,
)
from src.cli.cloud.database import (
    status as database_status,
)
from src.cli.cloud.service import down as service_down
from src.cli.cloud.service import up as service_up
from src.cli.database.clear import clear_database
from src.cli.database.init import init_verbs
from src.cli.database.wipe import wipe_database
from src.cli.generation_requests.commands import (
    clean_requests as genreq_clean,
)
from src.cli.generation_requests.commands import (
    get_status as genreq_status,
)
from src.cli.generation_requests.commands import (
    list_requests as genreq_list,
)
from src.cli.problems.create import (
    generate_random_problem,
    generate_random_problems_batch,
    get_problem_statistics,
    get_random_problem,
    list_problems,
    search_problems_by_focus,
    search_problems_by_topic,
)
from src.cli.problems.delete import delete_problem
from src.cli.problems.get import get_problem
from src.cli.problems.purge import purge_problems
from src.cli.sentences.create import create_random_sentence_batch, create_sentence
from src.cli.sentences.purge import purge_orphaned_sentences
from src.cli.verbs.commands import download, get, random
from src.schemas.problems import GrammarProblemConstraints


@click.group()
@click.option("--debug", default=False, is_flag=True)
@click.option("--debug-openai", default=False, is_flag=True)
@click.option("--debug-recovery", default=False, is_flag=True)
@click.option(
    "--detailed", default=False, is_flag=True, help="Show detailed problem information"
)
@click.option(
    "--remote",
    default=False,
    is_flag=True,
    help="Target remote service from SERVICE_URL (requires confirmation for dangerous ops)",
)
@click.option(
    "-q",
    "--quiet",
    default=False,
    is_flag=True,
    help="Suppress startup messages (use with --json for clean output)",
)
@click.pass_context
async def cli(
    ctx,
    debug=False,
    debug_openai=False,
    debug_recovery=True,
    detailed=False,
    remote=False,
    quiet=False,
):
    # Load environment variables from .env file
    load_dotenv()

    # Auto-enable quiet mode if --json is anywhere in the command line
    # This allows `lqs problem random --json` to work without needing -q
    import sys

    if "--json" in sys.argv:
        quiet = True

    # Default behavior: use local Supabase (unless --remote is set)
    if not remote:
        from src.cli.utils.local_supabase import get_local_supabase_config
        from src.core.config import reset_settings

        if not quiet:
            click.echo("🔧 Using local Supabase connection (default)...")
        local_config = get_local_supabase_config()

        if not quiet:
            click.echo(f"   Setting SUPABASE_URL to {local_config['SUPABASE_URL']}")
        for key, value in local_config.items():
            if value:  # Only set if value is non-empty
                os.environ[key] = value

        # Force settings reload with new environment variables
        reset_settings()

        # Verify the override worked
        from src.core.config import settings

        if not quiet:
            click.echo(f"   ✅ Settings now use: {settings.supabase_url}")

    logging.basicConfig(level=logging.DEBUG if debug else logging.INFO)

    # Suppress httpx logging to reduce noise
    logging.getLogger("httpx").setLevel(logging.WARNING)

    if debug_openai:
        logging.getLogger("openai").setLevel(logging.DEBUG)

    if debug_recovery:
        logging.getLogger("recovery").setLevel(logging.DEBUG)

    # Store service URL in context for commands to access
    from src.cli.utils.http_client import get_service_url_from_flag

    ctx.ensure_object(dict)
    ctx.obj["service_url"] = get_service_url_from_flag(remote)
    ctx.obj["remote"] = remote
    ctx.obj["quiet"] = quiet

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
database.add_command(wipe_database, name="wipe")


@cli.group()
async def problem():
    """Problem generation and management commands."""
    pass


@problem.command("random")
@click.option(
    "--json", "output_json", is_flag=True, help="Output raw JSON with metadata"
)
@click.pass_context
async def problem_random(
    ctx,
    output_json: bool,
):
    """Get a random problem from the database."""
    try:
        # Get flags from root context
        root_ctx = ctx.find_root()
        detailed = root_ctx.params.get("detailed", False)
        service_url = root_ctx.obj.get("service_url") if root_ctx.obj else None

        await get_random_problem(
            display=not output_json,
            detailed=detailed,
            service_url=service_url,
            output_json=output_json,
        )

    except Exception as ex:
        click.echo(f"❌ Error fetching random problem: {ex}")


@problem.command("generate")
@click.option("--count", "-c", default=1, help="Number of problems to generate")
@click.option("--statements", "-s", default=4, help="Number of statements per problem")
@click.option("--include-cod", is_flag=True, help="Force inclusion of direct objects")
@click.option("--include-coi", is_flag=True, help="Force inclusion of indirect objects")
@click.option("--include-negation", is_flag=True, help="Force inclusion of negation")
@click.option(
    "--tense", multiple=True, help="Limit to specific tenses (can specify multiple)"
)
@click.option(
    "--json", "output_json", is_flag=True, help="Output raw JSON with metadata"
)
@click.pass_context
async def problem_generate(
    ctx,
    count: int,
    statements: int,
    include_cod: bool,
    include_coi: bool,
    include_negation: bool,
    tense: tuple,
    output_json: bool,
):
    """Generate random grammar problems using AI."""
    try:
        # Get flags from root context
        root_ctx = ctx.find_root()
        detailed = root_ctx.params.get("detailed", False)
        service_url = root_ctx.obj.get("service_url") if root_ctx.obj else None

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
            await generate_random_problem(
                statement_count=statements,
                constraints=constraints,
                display=not output_json,
                detailed=detailed,
                service_url=service_url,
                output_json=output_json,
                count=count,
            )
        else:
            # Batch generation
            await generate_random_problems_batch(
                quantity=count,
                statement_count=statements,
                constraints=constraints,
                display=not output_json,
                detailed=detailed,
                service_url=service_url,
                output_json=output_json,
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
@click.pass_context
async def problem_list(ctx, problem_type: str, topic: tuple, limit: int, verbose: bool):
    """List existing problems with filtering."""
    try:
        # Get debug flag from parent context for detailed display mode
        detailed = ctx.find_root().params.get("detailed", False)

        await list_problems(
            problem_type=problem_type,
            topic_tags=list(topic) if topic else None,
            limit=limit,
            verbose=verbose,
            detailed=detailed,
        )
    except Exception as ex:
        click.echo(f"❌ Error listing problems: {ex}")


@problem.command("search")
@click.option(
    "--focus", help="Search by grammatical focus (e.g., direct_objects, negation)"
)
@click.option("--topic", multiple=True, help="Search by topic tags")
@click.option("--limit", default=10, help="Number of results to show")
@click.pass_context
async def problem_search(ctx, focus: str, topic: tuple, limit: int):
    """Search problems by various criteria."""
    try:
        # Get debug flag from parent context for detailed display mode
        detailed = ctx.find_root().params.get("detailed", False)

        if focus:
            await search_problems_by_focus(focus, limit, detailed=detailed)
        elif topic:
            await search_problems_by_topic(list(topic), limit, detailed=detailed)
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


# Add get, delete, and purge commands to problem group
problem.add_command(get_problem)
problem.add_command(delete_problem)
problem.add_command(purge_problems)


# Keep the existing batch command but update it to use new system
@problem.command("batch")
@click.argument("quantity", default=10, type=click.INT)
@click.option("--workers", default=10, type=click.INT)
@click.option("--statements", "-s", default=4, help="Number of statements per problem")
@click.pass_context
async def batch(ctx, quantity: int, workers: int, statements: int):
    """Generate multiple problems in parallel."""

    try:
        # Get service_url and detailed from root context
        root_ctx = ctx.find_root()
        service_url = root_ctx.obj.get("service_url") if root_ctx.obj else None
        detailed = root_ctx.params.get("detailed", False)

        await generate_random_problems_batch(
            quantity=quantity,
            statement_count=statements,
            constraints=None,
            workers=workers,
            display=True,
            detailed=detailed,
            service_url=service_url,
            output_json=False,
        )
    except Exception as ex:
        print(f"str({ex}): {traceback.format_exc()}")


@cli.group()
async def sentence():
    pass


sentence.add_command(create_sentence, name="new")
sentence.add_command(create_random_sentence_batch, name="random")
sentence.add_command(purge_orphaned_sentences, name="purge")


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


@cli.group("generation-request")
async def generation_request():
    """Generation request management commands."""
    pass


# Add generation request commands to the group
generation_request.add_command(genreq_list, name="list")
generation_request.add_command(genreq_status, name="status")
generation_request.add_command(genreq_clean, name="clean")


@cli.group()
async def cache():
    """Cache management commands."""
    pass


# Add cache commands to the group
cache.add_command(cache_stats, name="stats")
cache.add_command(reload_cache, name="reload")


def main():
    cli(_anyio_backend="asyncio")


if __name__ == "__main__":
    main()
