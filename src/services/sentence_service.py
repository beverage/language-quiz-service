"""Sentence service for business logic."""

from typing import List, Optional
from repositories.sentence_repository import SentenceRepository
from repositories.verb_repository import VerbRepository
from schemas.sentence import SentenceCreate, Sentence


class SentenceService:
    def __init__(self):
        self.sentence_repository = SentenceRepository()
        self.verb_repository = VerbRepository()

    async def create_sentence(self, sentence_data: SentenceCreate) -> Sentence:
        """Create a new sentence."""
        return await self.sentence_repository.create_sentence(sentence_data)

    async def get_sentence(self, sentence_id: int) -> Optional[Sentence]:
        """Get a sentence by ID."""
        return await self.sentence_repository.get_sentence(sentence_id)

    async def get_sentences(
        self,
        infinitive: Optional[str] = None,
        is_correct: Optional[bool] = None,
        limit: int = 50,
    ) -> List[Sentence]:
        """Get sentences with optional filters."""
        return await self.sentence_repository.get_sentences(
            infinitive=infinitive, is_correct=is_correct, limit=limit
        )

    async def get_random_sentence(self) -> Optional[Sentence]:
        """Get a random sentence."""
        return await self.sentence_repository.get_random_sentence()

    async def update_sentence(
        self, sentence_id: int, sentence_data: SentenceCreate
    ) -> Optional[Sentence]:
        """Update a sentence."""
        return await self.sentence_repository.update_sentence(
            sentence_id, sentence_data
        )

    async def delete_sentence(self, sentence_id: int) -> bool:
        """Delete a sentence."""
        return await self.sentence_repository.delete_sentence(sentence_id)
