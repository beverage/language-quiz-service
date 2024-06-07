#!/usr/bin/env python3
from os import environ

import asyncclick as click
import logging

from .database.engine import reflect_tables
from .database.init import init_auxiliaries
from .verbs.get import fetch_verb

API_KEY = environ["OPENAI_API_KEY"]

@click.group()
@click.option('--debug/--no-debug', default=False)
async def cli(debug):
    click.echo(f"Debug mode is {'on' if debug else 'off'}")
    if debug == True:
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

@database.command()
async def init():
    click.echo("Initializing the database to default settings and content.")
    click.echo("Fetching auxiliaries.")
    await init_auxiliaries()

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
@click.option('-s', '--save', is_flag=True, default=False)
async def get(verb, save):
    click.echo(f"Fetching verb {verb}.")
    await fetch_verb(verb, save)
    
@verb.command()
async def decorate():
    click.echo("Decorating verb.")

def main():
    cli(_anyio_backend="asyncio")
