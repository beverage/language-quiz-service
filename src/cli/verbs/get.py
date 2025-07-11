"""
CLI verb operations - MIGRATED.

Migrated to use Supabase VerbService instead of SQLAlchemy.
Maintained for backward compatibility.
"""

from services.verb_service import VerbService


async def get_verb(requested_verb: str, database_session=None):
    """Get a verb by infinitive - migrated to use VerbService."""
    verb = await VerbService().get_verb_by_infinitive(requested_verb)
    return verb


async def get_random_verb(database_session=None):
    """Get a random verb - migrated to use VerbService."""
    verb = await VerbService().get_random_verb()
    return verb


async def download_verb(requested_verb: str, openapi_client=None):
    """Download a verb using AI - migrated to use VerbService."""
    # Use the enhanced download method from VerbService
    verb = await VerbService().download_verb(requested_verb)
    return verb
