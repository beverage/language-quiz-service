"""Output formatters for CLI commands."""

import json
from datetime import datetime
from typing import Any
from uuid import UUID

from rich.console import Console
from rich.table import Table
from rich.tree import Tree

console = Console()


def format_output(
    data: Any, output_json: bool = False, output_format: str = "pretty"
) -> str:
    """Format data based on output preferences."""
    if output_json:
        if hasattr(data, "model_dump_json"):
            return data.model_dump_json(indent=2)
        return json.dumps(data, indent=2, default=str)

    if output_format == "pretty":
        return format_pretty(data)
    elif output_format == "compact":
        return format_compact(data)
    elif output_format == "table":
        return format_table(data)
    else:
        return format_pretty(data)  # Default fallback


def format_pretty(data: Any) -> str:
    """Pretty format with colors and structure using Rich."""
    if data is None:
        return "[dim]No data[/dim]"

    # Convert to dict if it's a Pydantic model
    if hasattr(data, "model_dump"):
        data_dict = data.model_dump()
    elif hasattr(data, "__dict__"):
        data_dict = data.__dict__
    else:
        data_dict = {"value": data}

    # Create a tree structure for nested display
    tree = Tree("📋 [bold blue]Data[/bold blue]")

    for key, value in data_dict.items():
        if value is None:
            tree.add(f"[dim]{key}:[/dim] [italic dim]None[/italic dim]")
        elif isinstance(value, str):
            if len(value) > 50:
                tree.add(f"[green]{key}:[/green] {value[:47]}...")
            else:
                tree.add(f"[green]{key}:[/green] {value}")
        elif isinstance(value, bool):
            color = "bright_green" if value else "bright_red"
            tree.add(f"[yellow]{key}:[/yellow] [{color}]{value}[/{color}]")
        elif isinstance(value, int | float):
            tree.add(f"[cyan]{key}:[/cyan] [bold]{value}[/bold]")
        elif isinstance(value, datetime):
            tree.add(f"[magenta]{key}:[/magenta] {value.strftime('%Y-%m-%d %H:%M:%S')}")
        elif isinstance(value, UUID):
            tree.add(f"[blue]{key}:[/blue] [dim]{str(value)[:8]}...[/dim]")
        elif isinstance(value, dict):
            branch = tree.add(f"[yellow]{key}:[/yellow]")
            for sub_key, sub_value in value.items():
                branch.add(f"[dim]{sub_key}:[/dim] {sub_value}")
        elif isinstance(value, list):
            if len(value) == 0:
                tree.add(f"[yellow]{key}:[/yellow] [dim][]</>")
            else:
                branch = tree.add(
                    f"[yellow]{key}:[/yellow] [dim]({len(value)} items)[/dim]"
                )
                for i, item in enumerate(value[:3]):  # Show first 3 items
                    branch.add(f"[dim]{i}:[/dim] {item}")
                if len(value) > 3:
                    branch.add(f"[dim]... and {len(value) - 3} more[/dim]")
        else:
            tree.add(f"[white]{key}:[/white] {str(value)}")

    # Capture the rich output as string
    console_capture = Console(file=None, width=80)
    with console_capture.capture() as capture:
        console_capture.print(tree)

    return capture.get()


def format_compact(data: Any) -> str:
    """Compact single-line format."""
    if data is None:
        return "None"

    # Convert to dict if it's a Pydantic model
    if hasattr(data, "model_dump"):
        data_dict = data.model_dump()
    elif hasattr(data, "__dict__"):
        data_dict = data.__dict__
    else:
        return str(data)

    # Create compact key=value pairs
    compact_pairs = []
    for key, value in data_dict.items():
        if value is None:
            continue  # Skip None values in compact mode
        elif isinstance(value, str):
            if len(value) > 20:
                compact_pairs.append(f"{key}={value[:17]}...")
            else:
                compact_pairs.append(f"{key}={value}")
        elif isinstance(value, datetime):
            compact_pairs.append(f"{key}={value.strftime('%Y-%m-%d')}")
        elif isinstance(value, UUID):
            compact_pairs.append(f"{key}={str(value)[:8]}")
        elif isinstance(value, dict | list):
            compact_pairs.append(f"{key}=[{type(value).__name__}]")
        else:
            compact_pairs.append(f"{key}={value}")

    return " | ".join(compact_pairs)


def format_table(data: Any) -> str:
    """Table format using Rich tables."""
    if data is None:
        return "No data"

    # Convert to dict if it's a Pydantic model
    if hasattr(data, "model_dump"):
        data_dict = data.model_dump()
    elif hasattr(data, "__dict__"):
        data_dict = data.__dict__
    else:
        data_dict = {"value": data}

    # Create a Rich table
    table = Table(title="📊 Data Table", show_header=True, header_style="bold magenta")
    table.add_column("Property", style="cyan", no_wrap=True, width=20)
    table.add_column("Value", style="white", overflow="fold")
    table.add_column("Type", style="dim", width=12)

    for key, value in data_dict.items():
        if value is None:
            table.add_row(key, "[dim italic]None[/dim italic]", "NoneType")
        elif isinstance(value, str):
            display_value = value if len(value) <= 50 else f"{value[:47]}..."
            table.add_row(key, display_value, "str")
        elif isinstance(value, bool):
            color = "[green]" if value else "[red]"
            table.add_row(key, f"{color}{value}[/{color.strip('[]')}]", "bool")
        elif isinstance(value, int | float):
            table.add_row(key, f"[bold]{value}[/bold]", type(value).__name__)
        elif isinstance(value, datetime):
            formatted_date = value.strftime("%Y-%m-%d %H:%M:%S UTC")
            table.add_row(key, formatted_date, "datetime")
        elif isinstance(value, UUID):
            table.add_row(key, f"[dim]{str(value)}[/dim]", "UUID")
        elif isinstance(value, dict):
            table.add_row(key, f"[yellow]{len(value)} keys[/yellow]", "dict")
        elif isinstance(value, list):
            table.add_row(key, f"[yellow]{len(value)} items[/yellow]", "list")
        else:
            table.add_row(key, str(value), type(value).__name__)

    # Capture the rich output as string
    console_capture = Console(file=None, width=100)
    with console_capture.capture() as capture:
        console_capture.print(table)

    return capture.get()


def format_list_table(data_list: list[dict[str, Any]], title: str = "Data") -> str:
    """Format a list of dictionaries as a table."""
    if not data_list:
        return "No data"

    # Get all unique keys from all dictionaries
    all_keys = set()
    for item in data_list:
        if hasattr(item, "model_dump"):
            all_keys.update(item.model_dump().keys())
        elif isinstance(item, dict):
            all_keys.update(item.keys())

    # Create table with dynamic columns
    table = Table(title=f"📊 {title}", show_header=True, header_style="bold magenta")

    for key in sorted(all_keys):
        table.add_column(key.replace("_", " ").title(), overflow="fold")

    # Add rows
    for item in data_list:
        if hasattr(item, "model_dump"):
            item_dict = item.model_dump()
        elif isinstance(item, dict):
            item_dict = item
        else:
            continue

        row = []
        for key in sorted(all_keys):
            value = item_dict.get(key)
            if value is None:
                row.append("[dim]None[/dim]")
            elif isinstance(value, str) and len(value) > 30:
                row.append(f"{value[:27]}...")
            elif isinstance(value, datetime):
                row.append(value.strftime("%Y-%m-%d"))
            elif isinstance(value, UUID):
                row.append(f"[dim]{str(value)[:8]}[/dim]")
            elif isinstance(value, bool):
                color = "green" if value else "red"
                row.append(f"[{color}]{value}[/{color}]")
            else:
                row.append(str(value))

        table.add_row(*row)

    # Capture the rich output as string
    console_capture = Console(file=None, width=120)
    with console_capture.capture() as capture:
        console_capture.print(table)

    return capture.get()
