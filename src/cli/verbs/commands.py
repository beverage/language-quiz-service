import asyncclick

from src.cli.utils.decorators import output_format_options
from src.cli.utils.formatters import format_output
from src.cli.utils.http_client import get_api_key, make_api_request
from src.cli.verbs.get import download_verb, get_random_verb, get_verb
from src.schemas.verbs import Verb


async def _download_verb_http(verb: str, service_url: str, api_key: str) -> Verb:
    """Download a verb via HTTP API."""
    response = await make_api_request(
        method="POST",
        endpoint="/api/v1/verbs/download",
        base_url=service_url,
        api_key=api_key,
        json_data={"infinitive": verb, "target_language_code": "eng"},
    )
    return Verb(**response.json())


async def _get_verb_http(verb: str, service_url: str, api_key: str) -> Verb:
    """Get a verb via HTTP API."""
    response = await make_api_request(
        method="GET",
        endpoint=f"/api/v1/verbs/{verb}",
        base_url=service_url,
        api_key=api_key,
    )
    return Verb(**response.json())


async def _get_random_verb_http(service_url: str, api_key: str) -> Verb:
    """Get a random verb via HTTP API."""
    response = await make_api_request(
        method="GET",
        endpoint="/api/v1/verbs/random",
        base_url=service_url,
        api_key=api_key,
    )
    return Verb(**response.json())


@asyncclick.command()
@output_format_options
@asyncclick.argument("verbs", nargs=-1, required=True)
@asyncclick.pass_context
async def download(ctx, verbs, output_json: bool, output_format: str):
    """Download one or more verbs. Use quotes for multi-word verbs like 'se sentir'."""
    if not verbs:
        asyncclick.echo("❌ Please provide at least one verb to download.")
        return

    asyncclick.echo(f"Downloading {len(verbs)} verb(s): {', '.join(verbs)}")

    # Check if using HTTP mode
    service_url = ctx.obj.get('service_url') if ctx.obj else None

    # Import here to avoid circular imports
    from src.cli.utils.queues import parallel_execute

    # Create tasks for parallel execution
    if service_url:
        # HTTP mode - make API calls
        api_key = get_api_key()
        tasks = [
            _download_verb_http(verb, service_url, api_key) for verb in verbs
        ]
    else:
        # Direct mode - use service layer
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
@asyncclick.pass_context
async def get(ctx, verb: str, output_json: bool, output_format: str):
    """Get a specific verb by infinitive."""
    asyncclick.echo(f"Fetching verb {verb}.")

    # Check if using HTTP mode
    service_url = ctx.obj.get('service_url') if ctx.obj else None

    if service_url:
        # HTTP mode - make API call
        api_key = get_api_key()
        result = await _get_verb_http(verb, service_url, api_key)
    else:
        # Direct mode - use service layer
        result = await get_verb(verb)

    formatted_output = format_output(result, output_json, output_format)
    asyncclick.echo(formatted_output)


@asyncclick.command("random")
@output_format_options
@asyncclick.pass_context
async def random(ctx, output_json: bool, output_format: str):
    """Get a random verb."""
    # Check if using HTTP mode
    service_url = ctx.obj.get('service_url') if ctx.obj else None

    if service_url:
        # HTTP mode - make API call
        api_key = get_api_key()
        result = await _get_random_verb_http(service_url, api_key)
    else:
        # Direct mode - use service layer
        result = await get_random_verb()

    if not output_json:
        asyncclick.echo(f"Selected verb: {result.infinitive}")

    formatted_output = format_output(result, output_json, output_format)
    asyncclick.echo(formatted_output)
