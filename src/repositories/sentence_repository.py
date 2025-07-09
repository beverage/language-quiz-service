"""Sentence data access layer."""
from supabase import Client
from typing import List, Optional
from ..schemas.sentence import Sentence, SentenceCreate, SentenceUpdate, Pronoun, Tense, DirectObject, IndirectPronoun, Negation


class SentenceRepository:
    """Repository for sentence-related database operations."""
    
    def __init__(self, client: Client):
        self.client = client

    async def get_by_id(self, sentence_id: int) -> Optional[Sentence]:
        """Get sentence by ID."""
        response = self.client.table('sentences').select('*').eq('id', sentence_id).execute()
        return Sentence(**response.data[0]) if response.data else None

    async def get_all(self, limit: int = 100, offset: int = 0) -> List[Sentence]:
        """Get all sentences with pagination."""
        response = self.client.table('sentences').select('*').range(offset, offset + limit - 1).execute()
        return [Sentence(**row) for row in response.data]

    async def get_by_verb_infinitive(self, infinitive: str, limit: int = 10) -> List[Sentence]:
        """Get sentences by verb infinitive."""
        response = self.client.table('sentences').select('*').eq('infinitive', infinitive).limit(limit).execute()
        return [Sentence(**row) for row in response.data]

    async def get_random_sentences(
        self,
        quantity: int,
        verb_infinitive: Optional[str] = None,
        pronoun: Optional[Pronoun] = None,
        tense: Optional[Tense] = None,
        direct_object: Optional[DirectObject] = None,
        indirect_pronoun: Optional[IndirectPronoun] = None,
        negation: Optional[Negation] = None,
        is_correct: bool = True
    ) -> List[Sentence]:
        """Get random sentences with optional filters."""
        query = self.client.table('sentences').select('*')
        
        # Apply filters
        if verb_infinitive:
            query = query.eq('infinitive', verb_infinitive)
        if pronoun:
            query = query.eq('pronoun', pronoun.value)
        if tense:
            query = query.eq('tense', tense.value)
        if direct_object:
            query = query.eq('direct_object', direct_object.value)
        if indirect_pronoun:
            query = query.eq('indirect_pronoun', indirect_pronoun.value)
        if negation:
            query = query.eq('negation', negation.value)
        
        query = query.eq('is_correct', is_correct)
        
        # Note: Supabase doesn't have a built-in random function
        # In production, you might want to implement this differently
        response = query.limit(quantity * 3).execute()  # Get more than needed
        
        if response.data:
            import random
            selected = random.sample(response.data, min(quantity, len(response.data)))
            return [Sentence(**row) for row in selected]
        
        return []

    async def create(self, sentence: SentenceCreate) -> Sentence:
        """Create new sentence."""
        response = self.client.table('sentences').insert(sentence.dict()).execute()
        return Sentence(**response.data[0])

    async def update(self, sentence_id: int, sentence: SentenceUpdate) -> Optional[Sentence]:
        """Update existing sentence."""
        update_data = {k: v for k, v in sentence.dict().items() if v is not None}
        if not update_data:
            return await self.get_by_id(sentence_id)
        
        response = self.client.table('sentences').update(update_data).eq('id', sentence_id).execute()
        return Sentence(**response.data[0]) if response.data else None

    async def delete(self, sentence_id: int) -> bool:
        """Delete sentence."""
        response = self.client.table('sentences').delete().eq('id', sentence_id).execute()
        return len(response.data) > 0

    async def delete_all_by_verb(self, infinitive: str) -> int:
        """Delete all sentences for a specific verb. Returns count of deleted sentences."""
        response = self.client.table('sentences').delete().eq('infinitive', infinitive).execute()
        return len(response.data) 