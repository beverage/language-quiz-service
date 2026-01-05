"""
CLI commands for managing in-memory caches.
"""

import logging

import asyncclick as click

from src.cache import api_key_cache, conjugation_cache, verb_cache
from src.clients.supabase import get_supabase_client
from src.repositories.api_keys_repository import ApiKeyRepository
from src.repositories.verb_repository import VerbRepository

logger = logging.getLogger(__name__)


@click.command("stats")
@click.pass_context
async def cache_stats(ctx):
    """
    Show cache statistics.

    Displays hit rates, sizes, and load status for all in-memory caches.
    """
    click.echo("\n📊 Cache Statistics\n")

    # Verb cache
    verb_stats = verb_cache.get_stats()
    click.echo("🔤 Verb Cache:")
    click.echo(f"   Loaded:      {verb_stats['loaded']}")
    click.echo(f"   Total Verbs: {verb_stats['total_verbs']}")
    click.echo(f"   Languages:   {verb_stats['languages']}")
    click.echo(f"   Hits:        {verb_stats['hits']}")
    click.echo(f"   Misses:      {verb_stats['misses']}")
    click.echo(f"   Hit Rate:    {verb_stats['hit_rate']}")
    click.echo()

    # Conjugation cache
    conj_stats = conjugation_cache.get_stats()
    click.echo("📝 Conjugation Cache:")
    click.echo(f"   Loaded:             {conj_stats['loaded']}")
    click.echo(f"   Total Conjugations: {conj_stats['total_conjugations']}")
    click.echo(f"   Unique Verbs:       {conj_stats['unique_verbs']}")
    click.echo(f"   Hits:               {conj_stats['hits']}")
    click.echo(f"   Misses:             {conj_stats['misses']}")
    click.echo(f"   Hit Rate:           {conj_stats['hit_rate']}")
    click.echo()

    # API key cache
    key_stats = api_key_cache.get_stats()
    click.echo("🔑 API Key Cache:")
    click.echo(f"   Loaded:      {key_stats['loaded']}")
    click.echo(f"   Total Keys:  {key_stats['total_keys']}")
    click.echo(f"   Active Keys: {key_stats['active_keys']}")
    click.echo(f"   Hits:        {key_stats['hits']}")
    click.echo(f"   Misses:      {key_stats['misses']}")
    click.echo(f"   Hit Rate:    {key_stats['hit_rate']}")
    click.echo()


@click.command("reload")
@click.argument(
    "cache_name",
    required=False,
    type=click.Choice(["verbs", "conjugations", "api-keys", "all"]),
    default="all",
)
@click.pass_context
async def reload_cache(ctx, cache_name: str):
    """
    Force reload cache(s) from database.

    CACHE_NAME can be: verbs, conjugations, api-keys, or all (default).

    Use this after making direct database changes outside the API
    (e.g., via Supabase dashboard or SQL).
    """
    try:
        client = await get_supabase_client()

        if cache_name in ("verbs", "all"):
            click.echo("🔄 Reloading verb cache...")
            verb_repo = VerbRepository(client)
            await verb_cache.reload(verb_repo)
            stats = verb_cache.get_stats()
            click.echo(f"   ✅ Loaded {stats['total_verbs']} verbs")

        if cache_name in ("conjugations", "all"):
            click.echo("🔄 Reloading conjugation cache...")
            verb_repo = VerbRepository(client)
            await conjugation_cache.reload(verb_repo)
            stats = conjugation_cache.get_stats()
            click.echo(f"   ✅ Loaded {stats['total_conjugations']} conjugations")

        if cache_name in ("api-keys", "all"):
            click.echo("🔄 Reloading API key cache...")
            api_key_repo = ApiKeyRepository(client)
            await api_key_cache.reload(api_key_repo)
            stats = api_key_cache.get_stats()
            click.echo(f"   ✅ Loaded {stats['total_keys']} API keys")

        click.echo("\n✅ Cache reload complete!")

    except Exception as e:
        logger.error(f"Error reloading cache: {e}", exc_info=True)
        click.echo(f"❌ Error: {e}")
