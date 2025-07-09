"""Sentence business logic service."""
from supabase import Client
from typing import Optional, List
from ..repositories.sentence_repository import SentenceRepository
from ..schemas.sentence import Sentence, SentenceCreate, Pronoun, Tense, DirectObject, IndirectPronoun, Negation
from ..clients.supabase import get_supabase_client


class SentenceService:
    """Service for sentence-related business logic."""
    
    def __init__(self, client: Optional[Client] = None):
        self.client = client or get_supabase_client()
        self.repository = SentenceRepository(self.client)

    async def get_sentence(self, sentence_id: int) -> Optional[Sentence]:
        """Get sentence by ID."""
        return await self.repository.get_by_id(sentence_id)

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
        """
        Get random sentences with optional filters.
        
        This replaces the current get_random_sentence function.
        """
        return await self.repository.get_random_sentences(
            quantity=quantity,
            verb_infinitive=verb_infinitive,
            pronoun=pronoun,
            tense=tense,
            direct_object=direct_object,
            indirect_pronoun=indirect_pronoun,
            negation=negation,
            is_correct=is_correct
        )

    async def create_sentence(
        self,
        infinitive: str,
        auxiliary: str,
        pronoun: Pronoun,
        tense: Tense,
        direct_object: DirectObject,
        indirect_pronoun: IndirectPronoun,
        negation: Negation,
        content: str,
        translation: str,
        is_correct: bool = True
    ) -> Sentence:
        """Create a new sentence."""
        sentence_create = SentenceCreate(
            infinitive=infinitive,
            auxiliary=auxiliary,
            pronoun=pronoun,
            tense=tense,
            direct_object=direct_object,
            indirect_pronoun=indirect_pronoun,
            negation=negation,
            content=content,
            translation=translation,
            is_correct=is_correct
        )
        return await self.repository.create(sentence_create)

    async def save_sentence(self, sentence: SentenceCreate) -> Sentence:
        """Save a sentence (wrapper for create)."""
        return await self.repository.create(sentence)

    async def get_sentences_by_verb(self, infinitive: str, limit: int = 10) -> List[Sentence]:
        """Get sentences for a specific verb."""
        return await self.repository.get_by_verb_infinitive(infinitive, limit)

    async def clear_sentences_for_verb(self, infinitive: str) -> int:
        """Clear all sentences for a specific verb. Returns count of deleted sentences."""
        return await self.repository.delete_all_by_verb(infinitive)

    async def get_all_sentences(self, limit: int = 100, offset: int = 0) -> List[Sentence]:
        """Get all sentences with pagination."""
        return await self.repository.get_all(limit=limit, offset=offset)


# Dependency injection helpers for FastAPI
def get_sentence_service(client: Optional[Client] = None) -> SentenceService:
    """Get sentence service instance."""
    return SentenceService(client) 