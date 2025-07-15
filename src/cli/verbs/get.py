"""
CLI verb operations - MIGRATED.

Migrated to use Supabase VerbService instead of SQLAlchemy.
Maintained for backward compatibility.
"""

from rich.console import Console

from src.services.verb_service import VerbService

console = Console()


async def get_verb(requested_verb: str, database_session=None):
    """Get a verb by infinitive - migrated to use VerbService."""
    verb = await VerbService().get_verb_by_infinitive(requested_verb)
    return verb


async def get_random_verb(database_session=None):
    """Get a random verb - migrated to use VerbService."""
    verb = await VerbService().get_random_verb()
    return verb


async def download_verb(requested_verb: str, target_language_code: str = "eng"):
    """
    Download a verb and its conjugations from the AI service and store it.
    Returns the downloaded verb object.
    """
    service = VerbService()
    verb = await service.download_verb(
        requested_verb=requested_verb, target_language_code=target_language_code
    )
    console.print(f"✅ Verb '{verb.infinitive}' downloaded successfully.")
    return verb
