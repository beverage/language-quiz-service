import asyncclick

from src.cli.utils.decorators import output_format_options
from src.cli.utils.formatters import format_output
from src.cli.verbs.get import download_verb, get_random_verb, get_verb


@asyncclick.command()
@output_format_options
@asyncclick.argument("verbs", nargs=-1, required=True)
async def download(verbs, output_json: bool, output_format: str):
    """Download one or more verbs. Use quotes for multi-word verbs like 'se sentir'."""
    if not verbs:
        asyncclick.echo("❌ Please provide at least one verb to download.")
        return

    asyncclick.echo(f"Downloading {len(verbs)} verb(s): {', '.join(verbs)}")

    # Import here to avoid circular imports
    from src.cli.utils.queues import parallel_execute

    # Create tasks for parallel execution
    tasks = [download_verb(verb) for verb in verbs]

    # Define error handler
    def handle_error(error: Exception, task_index: int):
        verb_name = verbs[task_index]
        asyncclick.echo(f"❌ Failed to download '{verb_name}': {error}")

    # Execute in parallel with error handling
    results = await parallel_execute(
        tasks=tasks,
        max_concurrent=5,  # Limit concurrent downloads to avoid overwhelming the API
        batch_delay=0.5,
        error_handler=handle_error,
    )

    # Print results for successful downloads
    for result in results:
        formatted_output = format_output(result, output_json, output_format)
        asyncclick.echo(formatted_output)


@asyncclick.command("get")
@output_format_options
@asyncclick.argument("verb")
async def get(verb: str, output_json: bool, output_format: str):
    """Get a specific verb by infinitive."""
    asyncclick.echo(f"Fetching verb {verb}.")
    result = await get_verb(verb)

    formatted_output = format_output(result, output_json, output_format)
    asyncclick.echo(formatted_output)


@asyncclick.command("random")
@output_format_options
async def random(output_json: bool, output_format: str):
    """Get a random verb."""
    result = await get_random_verb()

    if not output_json:
        asyncclick.echo(f"Selected verb: {result.infinitive}")

    formatted_output = format_output(result, output_json, output_format)
    asyncclick.echo(formatted_output)
