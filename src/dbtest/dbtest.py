#!/usr/bin/env python3
from os import environ

import logging
import asyncclick as click

from .database.clear import clear_database
from .database.engine import reflect_tables
from .database.init import init_auxiliaries

from .verbs.get import fetch_verb

API_KEY = environ["OPENAI_API_KEY"]

@click.group()
@click.option('--debug/--no-debug', default=False)
async def cli(debug=False):
    click.echo(f"Debug mode is {'on' if debug else 'off'}")
    if debug:
        logging.basicConfig(level = logging.DEBUG)
    else:
        logging.basicConfig(level = logging.INFO)

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
    await init_auxiliaries(with_common_irregulars=True)

@database.command()
async def reset():
    click.echo("Resetting the database container.")

@cli.group()
async def sentence():
    pass

@cli.group()
async def verb():
    pass

@verb.command()
@click.argument('verb')
async def get(requested_verb: str):
    click.echo(f"Fetching verb {requested_verb}.")
    await fetch_verb(requested_verb)

@verb.command()
async def decorate():
    click.echo("Decorating verb.")

def main():
    cli(_anyio_backend="asyncio")
