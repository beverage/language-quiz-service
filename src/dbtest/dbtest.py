#!/usr/bin/env python3
from os import environ

import click
import logging

from pprint import pprint

from .verbs.get import fetch_verb

API_KEY = environ["OPENAI_API_KEY"]

@click.group()
@click.option('--debug/--no-debug', default=False)
def cli(debug):
    click.echo(f"Debug mode is {'on' if debug else 'off'}")
    if debug == True:
        logging.basicConfig(level = logging.DEBUG)
    else:
        logging.basicConfig(level = logging.INFO)

@cli.group()
def database():
    pass

@database.command()
def clean():
    click.echo("Cleaning the database of any user data and history.")

@database.command()
def init():
    click.echo("Initializing the database to default settings and content.")

@database.command()
def reset():
    click.echo("Resetting the database container.")

@cli.group()
def sentence():
    pass

@cli.group()
def verb():
    pass

@verb.command()
@click.argument('verb')
@click.option('-s', '--save', is_flag=True, default=False)
def get(verb, save):
    click.echo(f"Fetching verb {verb}.")
    result = fetch_verb(verb, save)
    pprint(result)
    
@verb.command()
def decorate():
    click.echo("Decorating verb.")

def main():
    click.echo(f"Loading application with API key {API_KEY}")
    cli(obj={})

if __name__ == "__main__":
    main()