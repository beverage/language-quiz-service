#!/usr/bin/env python3
from pprint import pprint

import logging
import traceback
import asyncclick as click

from .cli.options import random_options, sentence_options

from .database.clear import clear_database
from .database.engine import reflect_tables
from .database.init import init_auxiliaries
from .database.utils import object_as_dict

from .problems.create import create_random_problem_with_delay, create_random_problem

from .sentences.create import create_random_sentence, create_sentence
from .sentences.database import get_random_sentence
from .sentences.utils import problem_formatter

from .verbs.get import download_verb, get_verb, get_random_verb

from .utils.console import Style
from .utils.queues import batch_operation

from .webserver.app import app

import os
import uvicorn

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
    try:
        results = await batch_operation(workers=workers, quantity=quantity, method=create_random_problem_with_delay, display=True)
        print(f"{Style.BOLD}Generated {len(results)}{Style.RESET}")
    except Exception as ex:
        print(f"str({ex}): {traceback.format_exc()}")

@cli.group()
async def sentence():
    pass

@sentence.command('get')
@click.option('-q', '--quantity', required=False, default=1)
@sentence_options
async def get(quantity: int, **kwargs):
    result = await get_random_sentence(quantity, **kwargs)
    print(problem_formatter(result))

@sentence.command('new')
@click.option('-q', '--quantity', required=False, default=1)
@sentence_options
async def generate(quantity: int, **kwargs):
    try:
        results = []
        for i in range(quantity):
            results.append(await create_sentence(**kwargs))
        print(problem_formatter(results))
    except Exception as ex:
        print(f"str({ex}): {traceback.format_exc()}")

@sentence.command('random')
@click.option('-q', '--quantity', required=False, default=1)
@random_options
async def random(quantity: int, **kwargs):
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

@cli.group()
async def webserver():
    pass

@webserver.command()
async def start():

    host = os.getenv("WEB_HOST", "127.0.0.1")
    port = int(os.getenv("WEB_PORT", 5000))

    config = uvicorn.Config(app, host=host, port=port, log_level="info", access_log=True)
    server = uvicorn.Server(config)

    await server.serve()

def main():
    cli(_anyio_backend="asyncio")
