[![linting: pylint](https://img.shields.io/badge/linting-pylint-yellowgreen)](https://github.com/pylint-dev/pylint) [![Buymeacoffee](https://badgen.net/badge/icon/buymeacoffee?icon=buymeacoffee&label)](https://www.buymeacoffee.com/mrbeverage)

> For the time being this will no longer work as a standalone console application while it is being transformed into a backend service to power other applications.  A console application will remain as a client of said service, runnable locally, when it is completed.
> 
# OpenAI Language Quiz Generator

A tool to provide quizzing material for a variety of French language features, and provide feedback for its learners.  What is seen here is it in its command-line application form, but what is within can be consumed by client applications later after further refinement.

![Example](docs/example.gif)
> This example is highly rate-limited and with randomised features.

While the overall correctness for right answers has been verified, some of the answers are not always ideomatic (around 10% of the time) given that they are generated with no surrounding context.  This is unavoidable for the time being.

## Getting started

Right now it is a simple Python app, installable from the command line via [Poetry](https://python-poetry.org/):
```
    pipx install poetry
    pipx inject poetry poetry-plugin-shell
    poetry install
```
This app will additiionally require a postgresql database, and an OpenAI API key in your environment.  (This will be configurable, and hidden later.)
```
    # It is probably better to put this into a dotfile:
    export $OPENAI_API_KEY=...
```
A postgresql database is then required, however this is already configured in a docker-compose.yml:
```
    # From the root directory of the repo:
    docker-compose up
```
Better secrets management for both the OpenAI keys and database passwords will be coming shortly when the effort to cloud host this as an an API will be undertaken.

Once running, you will need to pre-populate the database with a minimal verb set before any sentence or problem generation.  To do that, run the following command, which executes the CLI application as a module:
```bash
poetry run python -m src.cli database init
```

From there the application is ready to start generating problem data from the command line. See the documentation below.

### Development Setup

To ensure code quality and consistency, this project uses pre-commit Git hooks. These hooks automatically format and lint your code before each commit.

To install the hooks, run the following command from the root of the repository:
```bash
make install-githooks
```
This will set up the pre-commit hook, which runs `make lint-fix-unsafe` and `make format` on the files you are about to commit.

## Command Line Usage

To run the command-line interface, execute the `src.cli` module directly with Python. All commands and subcommands follow this pattern.

**Example: Get a random verb**
```bash
poetry run python -m src.cli verb random
```

**Example: Initialize the database**
```bash
poetry run python -m src.cli database init
```

## Webserver

This project intends to back services behind a mobile app that already exists, so coming soon.

## Examples

## Roadmap
