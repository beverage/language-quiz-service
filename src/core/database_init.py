"""Database initialization using new Supabase service layer."""
import logging
from asyncio import gather, Semaphore

# Import path setup for direct execution
import sys
from pathlib import Path

# Get the absolute path to the src directory
src_dir = Path(__file__).parent.parent
sys.path.insert(0, str(src_dir))

from services.verb_service import VerbService
from clients.supabase import get_supabase_client
from cli.ai.client import AsyncChatGPTClient


# Hardcore some verbs for now. We will load verb lists later.
auxiliaries: list[str] = ["avoir", "être"]
irregulars: list[str] = ["aller", "devoir", "dire", "faire", "pouvoir", "prendre", "savoir", "venir", "voir", "vouloir"]
pronominals: list[str] = []  # ["se sentir", "se souvenir"]

# Artificial lower bound for testing. Will make this high enough for the hard coded verbs for now.
limit = Semaphore(17)


async def rate_limited_verb_fetch(verb: str, verb_service: VerbService, openai_client: AsyncChatGPTClient):
    """Fetch a verb with rate limiting using new service layer."""
    async with limit:
        try:
            await verb_service.download_verb_with_ai(infinitive=verb, openai_client=openai_client)
        except Exception as e:
            logging.error("Error downloading verb %s: %s", verb, e)


async def init_auxiliaries(with_common_verbs=False):
    """Initialize auxiliary verbs and optionally common verbs using new service layer."""
    # Setup clients and services
    supabase_client = get_supabase_client()
    verb_service = VerbService(supabase_client)
    openai_client = AsyncChatGPTClient()
    
    # Select verbs to download
    verbs = auxiliaries + irregulars + pronominals if with_common_verbs else auxiliaries
    
    logging.info("Starting initialization of %d verbs using Supabase service layer", len(verbs))
    
    # Create tasks for rate-limited verb fetching
    tasks = [
        rate_limited_verb_fetch(verb=verb, verb_service=verb_service, openai_client=openai_client) 
        for verb in verbs
    ]
    
    # Execute all tasks
    results = await gather(*tasks, return_exceptions=True)
    
    # Log results
    success_count = sum(1 for r in results if not isinstance(r, Exception))
    error_count = len(results) - success_count
    
    logging.info("Database initialization completed: %d successful, %d errors", success_count, error_count)
    
    if error_count > 0:
        logging.warning("Some verbs failed to download. Check logs for details.")
    
    return success_count, error_count 