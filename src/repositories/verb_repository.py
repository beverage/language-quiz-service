"""Verb data access layer."""
from supabase import Client
from typing import List, Optional

# Import path setup for direct execution
import sys
from pathlib import Path

# Get paths for imports
src_dir = Path(__file__).parent.parent
sys.path.insert(0, str(src_dir))

from schemas.verb import Verb, VerbCreate, VerbUpdate, Conjugation, ConjugationCreate, VerbGroup


class VerbRepository:
    """Repository for verb-related database operations."""
    
    def __init__(self, client: Client):
        self.client = client

    async def get_by_id(self, verb_id: int) -> Optional[Verb]:
        """Get verb by ID."""
        response = self.client.table('verbs').select('*').eq('id', verb_id).execute()
        return Verb(**response.data[0]) if response.data else None

    async def get_by_infinitive(self, infinitive: str) -> Optional[Verb]:
        """Get verb by infinitive."""
        response = self.client.table('verbs').select('*').eq('infinitive', infinitive).execute()
        return Verb(**response.data[0]) if response.data else None

    async def get_all(self, limit: int = 100, offset: int = 0) -> List[Verb]:
        """Get all verbs with pagination."""
        response = self.client.table('verbs').select('*').range(offset, offset + limit - 1).execute()
        return [Verb(**row) for row in response.data]

    async def create(self, verb: VerbCreate) -> Verb:
        """Create new verb."""
        response = self.client.table('verbs').insert(verb.dict()).execute()
        return Verb(**response.data[0])

    async def update(self, verb_id: int, verb: VerbUpdate) -> Optional[Verb]:
        """Update existing verb."""
        update_data = {k: v for k, v in verb.dict().items() if v is not None}
        if not update_data:
            return await self.get_by_id(verb_id)
        
        response = self.client.table('verbs').update(update_data).eq('id', verb_id).execute()
        return Verb(**response.data[0]) if response.data else None

    async def delete(self, verb_id: int) -> bool:
        """Delete verb."""
        response = self.client.table('verbs').delete().eq('id', verb_id).execute()
        return len(response.data) > 0

    async def get_conjugations(self, verb_id: int) -> List[Conjugation]:
        """Get all conjugations for a verb."""
        response = self.client.table('conjugations').select('*').eq('verb_id', verb_id).execute()
        return [Conjugation(**row) for row in response.data]

    async def create_conjugation(self, conjugation: ConjugationCreate) -> Conjugation:
        """Create new conjugation."""
        response = self.client.table('conjugations').insert(conjugation.dict()).execute()
        return Conjugation(**response.data[0])

    async def get_random_verb(self) -> Optional[Verb]:
        """Get a random verb."""
        # Supabase doesn't have a direct random function, so we'll get all and pick one
        # In production, you might want to implement this differently
        response = self.client.table('verbs').select('*').execute()
        if response.data:
            import random
            return Verb(**random.choice(response.data))
        return None

    async def get_verb_groups(self) -> List[VerbGroup]:
        """Get all verb groups."""
        response = self.client.table('verb_groups').select('*').execute()
        return [VerbGroup(**row) for row in response.data] 