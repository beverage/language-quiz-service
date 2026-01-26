"""
CLI database seeding - Generate initial grammar problems for all focus/tense combinations.

This command seeds the database with grammar problems by calling the problem
generation API for each combination of grammar focus and tense.
"""

import json
import logging
from datetime import UTC, datetime

import asyncclick as click

from src.cli.utils.http_client import (
    get_api_key,
    get_service_url_from_flag,
    make_api_request,
)
from src.schemas.problems import GrammarFocus
from src.schemas.verbs import Tense

logger = logging.getLogger(__name__)

# Tenses supported for seeding (IMPERATIF excluded - not fully supported yet)
SUPPORTED_TENSES = [t for t in Tense if t != Tense.IMPERATIF]


async def _enqueue_problem_generation(
    service_url: str,
    api_key: str,
    focus: GrammarFocus,
    tense: Tense,
    count: int,
) -> dict:
    """
    Enqueue problem generation for a specific focus/tense combination.

    Returns the API response with request_id.
    """
    request_data = {
        "statement_count": 4,
        "count": count,
        "focus": focus.value,
        "constraints": {
            "tenses_used": [tense.value],
        },
    }

    response = await make_api_request(
        method="POST",
        endpoint="/api/v1/problems/generate",
        base_url=service_url,
        api_key=api_key,
        json_data=request_data,
    )

    return response.json()


@click.command("seed")
@click.option(
    "--count",
    "-c",
    default=10,
    help="Number of problems to generate per focus/tense combination (default: 10)",
)
@click.option(
    "--json",
    "output_json",
    is_flag=True,
    help="Output as JSON for piping to other commands",
)
@click.pass_context
async def seed_database(ctx, count: int, output_json: bool):
    """
    Seed the database with grammar problems for all focus/tense combinations.

    Generates problems for each combination of:
    - 2 grammar focuses: conjugation, pronouns
    - 7 tenses: present, passe_compose, plus_que_parfait, imparfait,
                future_simple, conditionnel, subjonctif
                (imperatif excluded - not fully supported yet)

    This results in 14 combinations. With the default count of 10, this
    generates 140 problems total.

    Examples:
        lqs database seed                    # 140 problems (10 per combo)
        lqs database seed --count 50         # 700 problems (50 per combo)
        lqs database seed --json | jq '.requests[].request_id'
        lqs --remote database seed           # Seed remote database
    """
    # Get service URL from context (set by root CLI based on --remote flag)
    root_ctx = ctx.find_root()
    remote = root_ctx.obj.get("remote", False) if root_ctx.obj else False
    service_url = get_service_url_from_flag(remote)

    focuses = list(GrammarFocus)
    tenses = SUPPORTED_TENSES
    total_combinations = len(focuses) * len(tenses)
    total_problems = total_combinations * count

    if not output_json:
        click.echo("🌱 Seeding database with grammar problems...")
        click.echo()
        click.echo(
            f"📋 Enqueuing {total_combinations} generation requests "
            f"({count} problems each = {total_problems} total)"
        )
        click.echo()

    try:
        api_key = get_api_key()
    except Exception as e:
        if output_json:
            click.echo(json.dumps({"error": str(e)}))
        else:
            click.echo(f"❌ {e}")
        raise SystemExit(1)

    # Track all requests for output
    requests = []
    errors = []

    for focus in focuses:
        for tense in tenses:
            timestamp = datetime.now(UTC).isoformat()

            try:
                response = await _enqueue_problem_generation(
                    service_url=service_url,
                    api_key=api_key,
                    focus=focus,
                    tense=tense,
                    count=count,
                )

                request_info = {
                    "request_id": response["request_id"],
                    "focus": focus.value,
                    "tense": tense.value,
                    "count": count,
                    "timestamp": timestamp,
                }
                requests.append(request_info)

                if not output_json:
                    # Format: focus + tense padded for alignment
                    combo = f"{focus.value} + {tense.value}"
                    request_id_short = response["request_id"][:8]
                    click.echo(f"   ✅ {combo:<35} → {request_id_short}...")

            except Exception as e:
                error_info = {
                    "focus": focus.value,
                    "tense": tense.value,
                    "error": str(e),
                    "timestamp": timestamp,
                }
                errors.append(error_info)

                if not output_json:
                    combo = f"{focus.value} + {tense.value}"
                    click.echo(f"   ❌ {combo:<35} → {str(e)[:40]}")

    # Build summary
    successful_count = len(requests)
    problems_requested = successful_count * count

    by_focus = {}
    by_tense = {}
    for req in requests:
        by_focus[req["focus"]] = by_focus.get(req["focus"], 0) + req["count"]
        by_tense[req["tense"]] = by_tense.get(req["tense"], 0) + req["count"]

    summary = {
        "total_requests": successful_count,
        "total_problems_requested": problems_requested,
        "failed_requests": len(errors),
        "by_focus": by_focus,
        "by_tense": by_tense,
    }

    if output_json:
        output = {
            "requests": requests,
            "errors": errors if errors else None,
            "summary": summary,
        }
        # Remove None values
        output = {k: v for k, v in output.items() if v is not None}
        click.echo(json.dumps(output, indent=2))
    else:
        click.echo()
        if errors:
            click.echo(
                f"📊 Summary: {successful_count} requests enqueued, "
                f"{problems_requested} problems requested, "
                f"{len(errors)} failed"
            )
        else:
            click.echo(
                f"📊 Summary: {successful_count} requests enqueued, "
                f"{problems_requested} problems requested"
            )

    if errors and not output_json:
        raise SystemExit(1)
