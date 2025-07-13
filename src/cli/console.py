#!/usr/bin/env python3
import asyncclick as click
import logging
import traceback
import uvicorn
from pprint import pprint

from src.cli.cli.options import random_options, sentence_options
from src.cli.cloud.database import (
    down as database_down,
    up as database_up,
    status as database_status,
)
from src.cli.cloud.service import down as service_down, up as service_up
from src.cli.database.clear import clear_database
from src.cli.database.init import init_verbs
from src.cli.database.utils import object_as_dict
from src.cli.problems.create import (
    create_random_problem_with_delay,
    create_random_problem,
)
from src.cli.sentences.create import create_random_sentence, create_sentence
from src.cli.sentences.database import get_random_sentence
from src.cli.sentences.utils import problem_formatter
from src.cli.verbs.get import download_verb, get_verb, get_random_verb
from src.cli.utils.console import Style
from src.cli.utils.queues import batch_operation
from src.cli.webserver.app import app


@click.group()
@click.option("--debug", default=False, is_flag=True)
@click.option("--debug-openai", default=False, is_flag=True)
@click.option("--debug-recovery", default=False, is_flag=True)
async def cli(debug=False, debug_openai=False, debug_recovery=True):
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


@cloud_database.command("down")
async def db_down():
    """
    Takes down the database by stopping the RDS instance.
    """
    await database_down()


@cloud_database.command("up")
async def db_up():
    """
    Brings up the database by starting the RDS instance.
    """
    await database_up()


@cloud_database.command("status")
async def db_status():
    """
    Checks the status of the database RDS instance.
    """
    await database_status()


@cloud.group()
async def service():
    pass


@service.command("down")
async def svc_down():
    """
    Takes down the service by setting the ECS tasks desired count to 0.
    """
    await service_down()


@service.command("up")
@click.option("--task-count", default=1, type=click.INT)
async def svc_up(task_count: int = 1):
    """
    Brings up the service by setting the ECS tasks desired count to --task-count.  (Default: 1)
    """
    await service_up(count=task_count)


@cli.group()
async def database():
    pass


@database.command()
async def clean():
    click.echo("Cleaning the database of any user data and history.")
    await clear_database()


@database.command("init")
async def db_init():
    """
    Seeds the database with an initial set of verbs.
    """
    click.echo("Seeding the database with initial verbs...")
    await init_verbs()


# Not needed
@database.command()
async def reset():
    click.echo("Resetting the database container.")


# Not migrated
@cli.group()
async def problem():
    pass


# Not migrated
@problem.command("random")
async def problem_random():
    results = await create_random_problem()
    print(problem_formatter(results))


# Not migrated
@problem.command()
@click.argument("quantity", default=10, type=click.INT)
@click.option("--workers", default=10, type=click.INT)
async def batch(quantity: int, workers: int):
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


# Migrated
@sentence.command("get")
@click.option("-q", "--quantity", required=False, default=1)
@sentence_options
async def sentence_get(quantity: int, **kwargs):
    result = await get_random_sentence(quantity, **kwargs)
    print(problem_formatter(result))


# Migrated
@sentence.command("new")
@click.option("-q", "--quantity", required=False, default=1)
@sentence_options
async def generate(quantity: int, **kwargs):
    try:
        if quantity == 1:
            # Single sentence - no need for parallel execution
            result = await create_sentence(**kwargs)
            print(problem_formatter([result]))
        else:
            # Multiple sentences - use parallel execution
            from src.cli.utils.queues import parallel_execute

            # Create coroutines for parallel execution
            tasks = [create_sentence(**kwargs) for _ in range(quantity)]

            # Define error handler
            def handle_error(error: Exception, task_index: int):
                print(f"Warning: Failed to generate sentence {task_index + 1}: {error}")

            # Execute in parallel with error handling
            results = await parallel_execute(
                tasks=tasks,
                max_concurrent=10,
                batch_delay=0.5,
                error_handler=handle_error,
            )

            if results:
                print(problem_formatter(results))
            else:
                print("No sentences were successfully generated.")
    except Exception as ex:
        print(f"{ex}: {traceback.format_exc()}")


# Migrated
@sentence.command("random")
@click.option("-q", "--quantity", required=False, default=1)
@random_options
async def sentence_random(quantity: int, **kwargs):
    try:
        if quantity == 1:
            # Single sentence - no need for parallel execution
            result = await create_random_sentence(**kwargs)
            print(problem_formatter([result]))
        else:
            # Multiple sentences - use parallel execution (max 10 concurrent)
            import asyncio

            max_concurrent = min(10, quantity)

            # Create coroutines for parallel execution
            tasks = [create_random_sentence(**kwargs) for _ in range(quantity)]

            # Execute in batches of max_concurrent with error handling
            results = []
            for i in range(0, len(tasks), max_concurrent):
                batch = tasks[i : i + max_concurrent]
                try:
                    batch_results = await asyncio.gather(*batch, return_exceptions=True)

                    # Filter out exceptions and collect successful results
                    for result in batch_results:
                        if isinstance(result, Exception):
                            print(f"Warning: Failed to generate sentence: {result}")
                        else:
                            results.append(result)

                    # Small delay between batches to avoid overwhelming the API
                    if i + max_concurrent < len(tasks):
                        await asyncio.sleep(0.5)

                except Exception as ex:
                    print(f"Batch failed: {ex}")

            if results:
                print(problem_formatter(results))
            else:
                print("No sentences were successfully generated.")
    except Exception as ex:
        print(f"str({ex}): {traceback.format_exc()}")


@cli.group()
async def verb():
    pass


# Migrated
@verb.command()
@click.argument("verbs", nargs=-1, required=True)
async def download(verbs):
    """Download one or more verbs. Use quotes for multi-word verbs like 'se sentir'."""
    if not verbs:
        click.echo("❌ Please provide at least one verb to download.")
        return

    click.echo(f"Downloading {len(verbs)} verb(s): {', '.join(verbs)}")

    # Import here to avoid circular imports
    from src.cli.utils.queues import parallel_execute

    # Create tasks for parallel execution
    tasks = [download_verb(verb) for verb in verbs]

    # Define error handler
    def handle_error(error: Exception, task_index: int):
        verb_name = verbs[task_index]
        click.echo(f"❌ Failed to download '{verb_name}': {error}")

    # Execute in parallel with error handling
    await parallel_execute(
        tasks=tasks,
        max_concurrent=5,  # Limit concurrent downloads to avoid overwhelming the API
        batch_delay=0.5,
        error_handler=handle_error,
    )

    # Print results for successful downloads
    # for result in results:
    #     print(object_as_dict(result))


# Migrated
@verb.command("get")
@click.argument("verb")
async def verb_get(verb: str):
    click.echo(f"Fetching verb {verb}.")
    result = await get_verb(verb)
    pprint(object_as_dict(result))


# Migrated
@verb.command("random")
async def verb_random():
    result = await get_random_verb()
    click.echo(f"Selected verb {result.infinitive}")
    pprint(object_as_dict(result))


@cli.group()
async def webserver():
    pass


@webserver.command()
async def start():
    config = uvicorn.Config(app, host="0.0.0.0", port=8000, log_level="info")
    server = uvicorn.Server(config)
    await server.serve()


def main():
    cli(_anyio_backend="asyncio")


if __name__ == "__main__":
    main()
