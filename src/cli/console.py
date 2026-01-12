#!/usr/bin/env python3
import logging
import os

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
    get_request as genreq_get,
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
    get_random_grammar_problem,
    list_problems,
)
from src.cli.problems.delete import delete_problem
from src.cli.problems.get import get_problem
from src.cli.problems.purge import purge_problems
from src.cli.sentences.create import create_random_sentence_batch, create_sentence
from src.cli.sentences.purge import purge_orphaned_sentences
from src.cli.utils.types import DateOrDurationParam
from src.cli.verbs.commands import download, get, random
from src.schemas.problems import GrammarFocus, GrammarProblemConstraints


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
    "-v",
    "--verbose",
    default=False,
    is_flag=True,
    help="Show startup messages and connection details",
)
@click.pass_context
async def cli(
    ctx,
    debug=False,
    debug_openai=False,
    debug_recovery=True,
    detailed=False,
    remote=False,
    verbose=False,
):
    # Load environment variables from .env file
    load_dotenv()

    # Default behavior: use local Supabase (unless --remote is set)
    if not remote:
        from src.cli.utils.local_supabase import get_local_supabase_config
        from src.core.config import reset_settings

        if verbose:
            click.echo("🔧 Using local Supabase connection (default)...")
        local_config = get_local_supabase_config()

        if verbose:
            click.echo(f"   Setting SUPABASE_URL to {local_config['SUPABASE_URL']}")
        for key, value in local_config.items():
            if value:  # Only set if value is non-empty
                os.environ[key] = value

        # Force settings reload with new environment variables
        reset_settings()

        # Verify the override worked
        from src.core.config import settings

        if verbose:
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
    ctx.obj["verbose"] = verbose


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


@problem.group("random")
async def problem_random_group():
    """Get random problems from the database."""
    pass


@problem_random_group.command("grammar")
@click.option(
    "--focus",
    multiple=True,
    type=click.Choice(["conjugation", "pronouns"]),
    help="Filter by grammatical focus area (can specify multiple: --focus conjugation --focus pronouns)",
)
@click.option(
    "--tenses",
    multiple=True,
    help="Filter by tenses used (e.g., futur_simple, imparfait). Can specify multiple.",
)
@click.option(
    "--json", "output_json", is_flag=True, help="Output raw JSON with metadata"
)
@click.option(
    "--llm-trace", "llm_trace", is_flag=True, help="Include LLM generation trace"
)
@click.pass_context
async def problem_random_grammar(
    ctx,
    focus: tuple,
    tenses: tuple,
    output_json: bool,
    llm_trace: bool,
):
    """Get a random grammar problem from the database."""
    try:
        # Get flags from root context
        root_ctx = ctx.find_root()
        detailed = root_ctx.params.get("detailed", False)
        service_url = root_ctx.obj.get("service_url") if root_ctx.obj else None

        # Convert tuples to lists
        focus_list = list(focus) if focus else None
        tenses_list = list(tenses) if tenses else None

        await get_random_grammar_problem(
            grammatical_focus=focus_list,
            tenses_used=tenses_list,
            display=not output_json,
            detailed=detailed,
            service_url=service_url,
            output_json=output_json,
            show_trace=llm_trace,
        )

    except Exception as ex:
        click.echo(f"❌ Error fetching random grammar problem: {ex}")


@problem.command("generate")
@click.option("--count", "-c", default=1, help="Number of problems to generate")
@click.option("--statements", "-s", default=4, help="Number of statements per problem")
@click.option(
    "--focus",
    type=click.Choice(["conjugation", "pronouns"]),
    default=None,
    help="Grammar focus area: conjugation or pronouns. If not specified, randomly selected.",
)
@click.option("--include-cod", is_flag=True, help="Force inclusion of direct objects")
@click.option("--include-coi", is_flag=True, help="Force inclusion of indirect objects")
@click.option("--include-negation", is_flag=True, help="Force inclusion of negation")
@click.option(
    "--tense", multiple=True, help="Limit to specific tenses (can specify multiple)"
)
@click.option(
    "--json", "output_json", is_flag=True, help="Output raw JSON with metadata"
)
@click.option(
    "--llm-trace", "llm_trace", is_flag=True, help="Include LLM generation trace"
)
@click.pass_context
async def problem_generate(
    ctx,
    count: int,
    statements: int,
    focus: str | None,
    include_cod: bool,
    include_coi: bool,
    include_negation: bool,
    tense: tuple,
    output_json: bool,
    llm_trace: bool,
):
    """Generate random grammar problems using AI."""
    try:
        # Get flags from root context
        root_ctx = ctx.find_root()
        detailed = root_ctx.params.get("detailed", False)
        service_url = root_ctx.obj.get("service_url") if root_ctx.obj else None

        # Convert focus string to enum (None means random selection)
        grammar_focus = GrammarFocus(focus) if focus else None

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
                focus=grammar_focus,
                display=not output_json,
                detailed=detailed,
                service_url=service_url,
                output_json=output_json,
                count=count,
                show_trace=llm_trace,
            )
        else:
            # Batch generation
            await generate_random_problems_batch(
                quantity=count,
                statement_count=statements,
                constraints=constraints,
                focus=grammar_focus,
                display=not output_json,
                detailed=detailed,
                service_url=service_url,
                output_json=output_json,
                show_trace=llm_trace,
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
@click.option(
    "--focus", help="Filter by grammatical focus (e.g., direct_objects, negation)"
)
@click.option("--verb", help="Filter by verb infinitive")
@click.option(
    "--older-than",
    type=DateOrDurationParam(),
    help="Filter problems created before date/duration (e.g., '7d', '2w', '2025-01-01')",
)
@click.option(
    "--newer-than",
    type=DateOrDurationParam(),
    help="Filter problems created after date/duration (e.g., '7d', '2w', '2025-01-01')",
)
@click.option("--limit", default=10, help="Number of problems to show (default: 10)")
@click.option("--offset", default=0, help="Skip N results for pagination")
@click.option("--all", "show_all", is_flag=True, help="Show all problems (up to 1000)")
@click.option(
    "--verbose",
    "-v",
    is_flag=True,
    help="Show full problem details (includes metadata in JSON)",
)
@click.option("--json", "output_json", is_flag=True, help="Output as JSON")
@click.pass_context
async def problem_list(
    ctx,
    problem_type: str,
    topic: tuple,
    focus: str,
    verb: str,
    older_than,
    newer_than,
    limit: int,
    offset: int,
    show_all: bool,
    verbose: bool,
    output_json: bool,
):
    """List existing problems with filtering."""
    try:
        # Get debug flag from parent context for detailed display mode
        detailed = ctx.find_root().params.get("detailed", False)

        # --all overrides --limit
        effective_limit = 1000 if show_all else limit

        await list_problems(
            problem_type=problem_type,
            topic_tags=list(topic) if topic else None,
            focus=focus,
            verb=verb,
            older_than=older_than,
            newer_than=newer_than,
            limit=effective_limit,
            offset=offset,
            verbose=verbose,
            detailed=detailed,
            output_json=output_json,
        )
    except Exception as ex:
        click.echo(f"❌ Error listing problems: {ex}")


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


@cli.group("generation")
async def generation():
    """Generation request management commands."""
    pass


# Add generation request commands to the group
generation.add_command(genreq_list, name="list")
generation.add_command(genreq_get, name="get")
generation.add_command(genreq_status, name="status")
generation.add_command(genreq_clean, name="clean")


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
