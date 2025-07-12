#!/usr/bin/env python3
import asyncclick as click
import logging
import traceback
import uvicorn
from pprint import pprint

from .cli.options import random_options, sentence_options

from .cloud.database import (
    down as database_down,
    up as database_up,
    status as database_status,
)
from .cloud.service import down as service_down, up as service_up

from .database.clear import clear_database

# Removed: from .database.engine import reflect_tables  # SQLAlchemy dependency removed
from .database.init import init_auxiliaries
from .database.utils import object_as_dict

from .problems.create import create_random_problem_with_delay, create_random_problem

from .sentences.create import create_random_sentence
from services.sentence_service import SentenceService
from .sentences.database import get_random_sentence
from .sentences.utils import problem_formatter

from .verbs.get import download_verb, get_verb, get_random_verb

from .utils.console import Style
from .utils.queues import batch_operation

from .webserver.app import app


@click.group()
@click.option("--debug", default=False, is_flag=True)
@click.option("--debug-openai", default=False, is_flag=True)
@click.option("--debug-recovery", default=False, is_flag=True)
async def cli(debug=False, debug_openai=False, debug_recovery=True):
    logging.basicConfig(level=logging.DEBUG if debug else logging.INFO)

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


# Migrated
@database.command()
async def init():
    click.echo("Initializing the database to default settings and content.")
    click.echo("Fetching auxiliaries.")
    await init_auxiliaries(with_common_verbs=True)


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
        svc = SentenceService()
        results = []
        for _ in range(quantity):
            results.append(await svc.create_sentence(**kwargs))
        print(problem_formatter(results))
    except Exception as ex:
        print(f"{ex}: {traceback.format_exc()}")


# Migrated
@sentence.command("random")
@click.option("-q", "--quantity", required=False, default=1)
@random_options
async def sentence_random(quantity: int, **kwargs):
    try:
        results = []
        for i in range(quantity):
            results.append(await create_random_sentence(**kwargs))
        print(problem_formatter(results))
    except Exception as ex:
        print(f"str({ex}): {traceback.format_exc()}")


@cli.group()
async def verb():
    pass


# Migrated
@verb.command()
@click.argument("verb")
async def download(verb: str):
    click.echo(f"Downloading verb {verb}.")
    result = await download_verb(verb)
    print(object_as_dict(result))


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
