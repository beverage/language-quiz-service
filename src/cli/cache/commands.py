"""
CLI commands for managing caches via API.

These commands call the API endpoints to interact with caches,
requiring the server to be running.
"""

import logging

import asyncclick as click
import httpx

logger = logging.getLogger(__name__)


def get_api_url() -> str:
    """Get the API base URL from environment or default."""
    import os

    return os.environ.get("LQS_API_URL", "http://localhost:8000")


def get_api_key() -> str | None:
    """Get API key from environment."""
    import os

    return os.environ.get("LQS_API_KEY")


@click.command("stats")
@click.pass_context
async def cache_stats(ctx):
    """
    Show cache statistics.

    Displays hit rates, sizes, and load status for all caches.
    Requires the server to be running.
    """
    api_url = get_api_url()
    api_key = get_api_key()

    headers = {}
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"

    click.echo(f"\n📊 Cache Statistics (from {api_url})\n")

    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{api_url}/api/v1/cache/stats",
                headers=headers,
                timeout=10.0,
            )

            if response.status_code == 401:
                click.echo(
                    "❌ Authentication required. Set LQS_API_KEY environment variable."
                )
                return

            if response.status_code != 200:
                click.echo(f"❌ API error: {response.status_code} - {response.text}")
                return

            stats = response.json()

            # Verb cache
            verb_stats = stats.get("verb_cache", {})
            click.echo("🔤 Verb Cache:")
            click.echo(f"   Loaded:      {verb_stats.get('loaded', 'N/A')}")
            click.echo(f"   Total Verbs: {verb_stats.get('total_verbs', 'N/A')}")
            click.echo(f"   Languages:   {verb_stats.get('languages', 'N/A')}")
            click.echo(f"   Hits:        {verb_stats.get('hits', 'N/A')}")
            click.echo(f"   Misses:      {verb_stats.get('misses', 'N/A')}")
            click.echo(f"   Hit Rate:    {verb_stats.get('hit_rate', 'N/A')}")
            click.echo()

            # Conjugation cache
            conj_stats = stats.get("conjugation_cache", {})
            click.echo("📝 Conjugation Cache:")
            click.echo(f"   Loaded:             {conj_stats.get('loaded', 'N/A')}")
            click.echo(
                f"   Total Conjugations: {conj_stats.get('total_conjugations', 'N/A')}"
            )
            click.echo(
                f"   Unique Verbs:       {conj_stats.get('unique_verbs', 'N/A')}"
            )
            click.echo(f"   Hits:               {conj_stats.get('hits', 'N/A')}")
            click.echo(f"   Misses:             {conj_stats.get('misses', 'N/A')}")
            click.echo(f"   Hit Rate:           {conj_stats.get('hit_rate', 'N/A')}")
            click.echo()

            # API key cache
            key_stats = stats.get("api_key_cache", {})
            click.echo("🔑 API Key Cache:")
            click.echo(f"   Loaded:      {key_stats.get('loaded', 'N/A')}")
            click.echo(f"   Total Keys:  {key_stats.get('total_keys', 'N/A')}")
            click.echo(f"   Active Keys: {key_stats.get('active_keys', 'N/A')}")
            click.echo(f"   Hits:        {key_stats.get('hits', 'N/A')}")
            click.echo(f"   Misses:      {key_stats.get('misses', 'N/A')}")
            click.echo(f"   Hit Rate:    {key_stats.get('hit_rate', 'N/A')}")
            click.echo()

    except httpx.ConnectError:
        click.echo(f"❌ Could not connect to {api_url}")
        click.echo("   Is the server running?")
    except Exception as e:
        click.echo(f"❌ Error: {e}")


@click.command("reload")
@click.pass_context
async def reload_cache(ctx):
    """
    Force reload all caches from database.

    Use this after making direct database changes outside the API.
    Requires admin API key and the server to be running.
    """
    api_url = get_api_url()
    api_key = get_api_key()

    if not api_key:
        click.echo("❌ Admin API key required. Set LQS_API_KEY environment variable.")
        return

    headers = {"Authorization": f"Bearer {api_key}"}

    click.echo(f"\n🔄 Reloading caches via {api_url}...\n")

    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{api_url}/api/v1/cache/reload",
                headers=headers,
                timeout=30.0,
            )

            if response.status_code == 401:
                click.echo("❌ Authentication failed. Check your API key.")
                return

            if response.status_code == 403:
                click.echo("❌ Admin permission required.")
                return

            if response.status_code != 200:
                click.echo(f"❌ API error: {response.status_code} - {response.text}")
                return

            result = response.json()

            click.echo(f"✅ {result.get('message', 'Caches reloaded')}")
            click.echo()

            # Show updated stats
            verb_stats = result.get("verb_cache", {})
            click.echo(f"   Verb cache: {verb_stats.get('total_verbs', 'N/A')} verbs")

            conj_stats = result.get("conjugation_cache", {})
            click.echo(
                f"   Conjugation cache: {conj_stats.get('total_conjugations', 'N/A')} conjugations"
            )

            key_stats = result.get("api_key_cache", {})
            click.echo(f"   API key cache: {key_stats.get('total_keys', 'N/A')} keys")
            click.echo()

    except httpx.ConnectError:
        click.echo(f"❌ Could not connect to {api_url}")
        click.echo("   Is the server running?")
    except Exception as e:
        click.echo(f"❌ Error: {e}")
