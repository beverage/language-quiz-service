"""CLI decorators for common functionality."""

import functools
from collections.abc import Callable

import asyncclick


def output_format_options(func: Callable) -> Callable:
    """
    Decorator that adds common output formatting options to CLI commands.

    Adds the following options:
    - --json: Output raw JSON
    - --format: Choose between pretty, compact, or table formats
    """

    @asyncclick.option("--json", "output_json", is_flag=True, help="Output raw JSON")
    @asyncclick.option(
        "--format",
        "output_format",
        type=asyncclick.Choice(["pretty", "compact", "table"], case_sensitive=False),
        default="pretty",
        help="Output format style (default: pretty)",
    )
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        return func(*args, **kwargs)

    return wrapper


def list_format_options(func: Callable) -> Callable:
    """
    Decorator for commands that output lists of items.

    Adds additional options for list formatting:
    - --limit: Limit number of items displayed
    - --sort: Sort by field
    """

    @asyncclick.option("--json", "output_json", is_flag=True, help="Output raw JSON")
    @asyncclick.option(
        "--format",
        "output_format",
        type=asyncclick.Choice(["pretty", "compact", "table"], case_sensitive=False),
        default="table",
        help="Output format style (default: table for lists)",
    )
    @asyncclick.option("--limit", type=int, help="Limit number of items to display")
    @asyncclick.option("--sort", "sort_by", help="Sort by field name")
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        return func(*args, **kwargs)

    return wrapper
