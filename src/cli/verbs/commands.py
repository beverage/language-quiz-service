import asyncclick

from src.cli.utils.decorators import output_format_options
from src.cli.utils.formatters import format_output
from src.cli.utils.http_client import get_api_key, make_api_request
from src.cli.verbs.get import get_random_verb
from src.schemas.verbs import Verb, VerbWithConjugations


async def _download_verb_http(
    verb: str, service_url: str, api_key: str
) -> VerbWithConjugations:
    """Download conjugations for a verb via HTTP API."""
    response = await make_api_request(
        method="POST",
        endpoint="/api/v1/verbs/download",
        base_url=service_url,
        api_key=api_key,
        json_data={"infinitive": verb, "target_language_code": "eng"},
    )
    return VerbWithConjugations(**response.json())


async def _get_verb_with_conjugations_http(
    verb: str, service_url: str, api_key: str
) -> VerbWithConjugations:
    """Get a verb with conjugations via HTTP API."""
    response = await make_api_request(
        method="GET",
        endpoint=f"/api/v1/verbs/{verb}/conjugations",
        base_url=service_url,
        api_key=api_key,
    )
    return VerbWithConjugations(**response.json())


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
    """Download conjugations for existing verbs. Verbs must already exist in the database."""
    if not verbs:
        asyncclick.echo("❌ Please provide at least one verb to download.")
        return

    if not output_json:
        asyncclick.echo(
            f"Downloading conjugations for {len(verbs)} verb(s): {', '.join(verbs)}"
        )

    # Check if using HTTP mode
    service_url = ctx.obj.get("service_url") if ctx.obj else None

    # Process each verb
    results = []
    for verb in verbs:
        try:
            # Download conjugations (verb must already exist)
            if service_url:
                api_key = get_api_key()
                result = await _download_verb_http(verb, service_url, api_key)
            else:
                # Direct mode - call service directly
                from src.core.factories import create_verb_service

                service = await create_verb_service()
                result = await service.download_conjugations(
                    infinitive=verb, target_language_code="eng"
                )

            # Display progress (only in non-JSON mode)
            if not output_json:
                conj_count = len(result.conjugations) if result.conjugations else 0
                asyncclick.echo(f"✅ {verb}: Downloaded {conj_count} conjugations")

            results.append(result)

        except Exception as error:
            error_msg = str(error)
            if "not found" in error_msg.lower():
                asyncclick.echo(
                    f"❌ Verb '{verb}' not found in database. Verbs must be added via database migrations before downloading conjugations."
                )
            else:
                asyncclick.echo(
                    f"❌ Failed to download conjugations for '{verb}': {error}"
                )

    # Output results
    if output_json:
        # Clean JSON output (no preamble text)
        import json

        for result in results:
            print(json.dumps(result.model_dump(mode="json"), indent=2, default=str))
    elif results:
        # Pretty print with conjugations (same format as 'get' command)
        for result in results:
            _print_verb_with_conjugations(result)


def _print_verb_with_conjugations(verb_with_conj: VerbWithConjugations):
    """Pretty print a verb with its conjugations."""
    asyncclick.echo(f"\n📚 {verb_with_conj.infinitive}")
    asyncclick.echo(f"   Translation: {verb_with_conj.translation}")
    asyncclick.echo(f"   Auxiliary: {verb_with_conj.auxiliary.value}")
    asyncclick.echo(f"   Classification: {verb_with_conj.classification.value}")

    if verb_with_conj.conjugations:
        asyncclick.echo(
            f"\n   Conjugations ({len(verb_with_conj.conjugations)} tenses):"
        )
        for conj in verb_with_conj.conjugations:
            asyncclick.echo(f"\n   {conj.tense.value.upper()}:")
            asyncclick.echo(f"      je:       {conj.first_person_singular}")
            asyncclick.echo(f"      tu:       {conj.second_person_singular}")
            asyncclick.echo(f"      il/elle:  {conj.third_person_singular}")
            asyncclick.echo(f"      nous:     {conj.first_person_plural}")
            asyncclick.echo(f"      vous:     {conj.second_person_plural}")
            asyncclick.echo(f"      ils/elles: {conj.third_person_plural}")
    else:
        asyncclick.echo("\n   No conjugations downloaded.")
    asyncclick.echo()


@asyncclick.command("get")
@output_format_options
@asyncclick.argument("verb")
@asyncclick.pass_context
async def get(ctx, verb: str, output_json: bool, output_format: str):
    """Get a specific verb by infinitive with all conjugations."""
    # Check if using HTTP mode
    service_url = ctx.obj.get("service_url") if ctx.obj else None

    if not output_json:
        asyncclick.echo(f"Fetching verb {verb}...")

    if service_url:
        # HTTP mode - make API call
        api_key = get_api_key()
        result = await _get_verb_with_conjugations_http(verb, service_url, api_key)
    else:
        # Direct mode - use service layer to get verb with conjugations
        from src.core.factories import create_verb_service

        service = await create_verb_service()
        result = await service.get_verb_with_conjugations(infinitive=verb)

        if not result:
            asyncclick.echo(f"Verb '{verb}' not found.")
            return

    if output_json:
        # Clean JSON output (no preamble text)
        import json

        print(json.dumps(result.model_dump(mode="json"), indent=2, default=str))
    else:
        # Pretty print with conjugations
        _print_verb_with_conjugations(result)


@asyncclick.command("random")
@output_format_options
@asyncclick.pass_context
async def random(ctx, output_json: bool, output_format: str):
    """Get a random verb."""
    # Check if using HTTP mode
    service_url = ctx.obj.get("service_url") if ctx.obj else None

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
