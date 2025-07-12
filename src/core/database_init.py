"""
Database initialization using Supabase services.

Migrated from the original database/init.py to use the new service layer.
"""

import asyncio
import logging
from pathlib import Path

from src.clients.supabase import get_supabase_client
from src.services.verb_service import VerbService


logger = logging.getLogger(__name__)


async def init_auxiliaries(with_common_verbs: bool = False):
    """
    Initialize the database with auxiliary verbs and optionally common verbs.

    This function replaces the original SQLAlchemy-based initialization
    with our new Supabase service layer approach.
    """

    # Get Supabase client (for potential direct operations if needed)
    get_supabase_client()

    # Use the verb service
    verb_service = VerbService()  # Don't pass client - it will create its own

    print("🔄 Starting database initialization...")

    if with_common_verbs:
        print("📚 Loading common verbs with AI assistance...")

        # Load essential verbs from data files
        auxiliary_verbs_file = (
            Path(__file__).parent.parent.parent / "data" / "auxilliary-verbs.txt"
        )
        essential_verbs_file = (
            Path(__file__).parent.parent.parent
            / "data"
            / "essential-irregular-verbs.txt"
        )

        # Read auxiliary verbs
        auxiliary_verbs = []
        if auxiliary_verbs_file.exists():
            with open(auxiliary_verbs_file, "r", encoding="utf-8") as f:
                auxiliary_verbs = [line.strip() for line in f if line.strip()]

        # Read essential irregular verbs
        essential_verbs = []
        if essential_verbs_file.exists():
            with open(essential_verbs_file, "r", encoding="utf-8") as f:
                essential_verbs = [line.strip() for line in f if line.strip()]

        # Combine all verbs and remove duplicates
        all_verbs = list(set(auxiliary_verbs + essential_verbs))

        print(f"📝 Processing {len(all_verbs)} verbs...")

        # Process verbs with AI assistance using semaphore for rate limiting
        semaphore = asyncio.Semaphore(17)  # Rate limit API calls

        successful_count = 0
        error_count = 0

        async def process_verb_with_limit(verb_infinitive):
            nonlocal successful_count, error_count
            async with semaphore:
                try:
                    # Import here to avoid circular dependency
                    from cli.ai.client import AsyncChatGPTClient

                    AsyncChatGPTClient()

                    # Download verb with AI assistance
                    print(f"🤖 Processing '{verb_infinitive}' with OpenAI...")
                    verb = await verb_service.download_verb(verb_infinitive)

                    print(f"✅ Successfully processed '{verb_infinitive}'")
                    successful_count += 1
                    return verb

                except Exception as e:
                    logger.error(f"❌ Error processing '{verb_infinitive}': {str(e)}")
                    logger.exception(e)
                    error_count += 1
                    return None

        # Process all verbs concurrently with rate limiting
        results = await asyncio.gather(
            *[process_verb_with_limit(verb) for verb in all_verbs]
        )

        print("\n📊 Initialization complete!")
        print(f"✅ {successful_count} successful, ❌ {error_count} errors")

        return results

    else:
        print("✅ Basic auxiliary initialization complete (no verbs loaded)")
        return []
