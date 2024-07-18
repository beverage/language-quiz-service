#!/usr/bin/env python3
from pprint import pprint

import logging
import asyncclick as click

from .database.clear import clear_database
from .database.engine import reflect_tables
from .database.init import init_auxiliaries
from .database.utils import object_as_dict

from .sentences.create import create_random_problem_with_delay, create_random_sentence, create_random_problem, problem_formatter
from .verbs.get import download_verb, get_verb, get_random_verb

from .utils.console import Style
from .utils.queues import batch_operation

@click.group()
@click.option('--debug', default=False, is_flag=True)
@click.option('--debug-openai', default=False, is_flag=True)
@click.option('--debug-recovery', default=False, is_flag=True)
async def cli(debug=False, debug_openai=False, debug_recovery=True):

    logging.basicConfig(level = logging.DEBUG if debug else logging.INFO)

    if debug_openai:
        logging.getLogger("openai").setLevel(logging.DEBUG)

    if debug_recovery:
        logging.getLogger("recovery").setLevel(logging.DEBUG)

    await reflect_tables()

@cli.group()
async def database():
    pass

@database.command()
async def clean():
    click.echo("Cleaning the database of any user data and history.")
    await clear_database()

@database.command()
async def init():
    click.echo("Initializing the database to default settings and content.")
    click.echo("Fetching auxiliaries.")
    await init_auxiliaries(with_common_verbs=True)

@database.command()
async def reset():
    click.echo("Resetting the database container.")

@cli.group()
async def problem():
    pass

@problem.command()
async def random():
    results = await create_random_problem()
    print(problem_formatter(results))

@problem.command()
@click.argument('quantity', default=10, type=click.INT)
@click.option('--workers', default=10, type=click.INT)
async def batch(quantity: int, workers: int):
    results = await batch_operation(workers=workers, quantity=quantity, method=create_random_problem_with_delay, display=True)
    print(f"{Style.BOLD}Generated {len(results)}{Style.RESET}")

@cli.group()
async def sentence():
    pass

@sentence.command()
async def random(correct: bool=True):
    result = await create_random_sentence(is_correct=correct)
    print(result)
    print(object_as_dict(result))

@cli.group()
async def verb():
    pass

@verb.command()
@click.argument('verb')
async def download(verb: str):
    click.echo(f"Downloading verb {verb}.")
    result = await download_verb(verb)
    print(object_as_dict(result))

@verb.command()
@click.argument('verb')
async def get(verb: str):
    click.echo(f"Fetching verb {verb}.")
    result = await get_verb(verb)
    pprint(object_as_dict(result))

@verb.command()
async def random():
    result = await get_random_verb()
    click.echo(f"Selected verb {result.infinitive}")
    pprint(object_as_dict(result))

def main():
    cli(_anyio_backend="asyncio")
