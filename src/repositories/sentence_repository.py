"""Sentence repository for data access."""

import logging
from uuid import UUID

from postgrest import APIError as PostgrestAPIError

from src.core.exceptions import RepositoryError
from src.schemas.sentences import Sentence, SentenceCreate, SentenceUpdate
from supabase import AsyncClient

logger = logging.getLogger(__name__)


class SentenceRepository:
    def __init__(self, client: AsyncClient):
        """Initialise the repository with a Supabase client."""
        self.client = client

    async def count_sentences(
        self,
        verb_id: UUID | None = None,
        is_correct: bool | None = None,
    ) -> int:
        """Count sentences with optional filters."""
        query = self.client.table("sentences").select("id", count="exact")

        if verb_id:
            query = query.eq("verb_id", str(verb_id))
        if is_correct is not None:
            query = query.eq("is_correct", is_correct)

        result = await query.execute()
        return result.count or 0

    async def create_sentence(self, sentence: SentenceCreate) -> Sentence:
        """Create a new sentence."""
        sentence_dict = sentence.model_dump()

        # Convert enums and UUIDs to string values for storage
        for key, value in sentence_dict.items():
            if hasattr(value, "value"):
                sentence_dict[key] = value.value
            elif isinstance(value, UUID):
                sentence_dict[key] = str(value)

        try:
            result = (
                await self.client.table("sentences").insert(sentence_dict).execute()
            )
        except PostgrestAPIError as e:
            logger.error(f"Database error creating sentence: {e.message}")
            raise RepositoryError(f"Failed to create sentence: {e.message}") from e

        if result.data:
            return Sentence.model_validate(result.data[0])
        raise RepositoryError("Failed to create sentence: No data returned.")

    async def delete_sentence(self, sentence_id: UUID) -> bool:
        """Delete a sentence."""
        result = (
            await self.client.table("sentences")
            .delete()
            .eq("id", str(sentence_id))
            .execute()
        )
        return len(result.data) > 0

    async def get_all_sentences(self, limit: int = 100) -> list[Sentence]:
        """Get all sentences."""
        result = await self.client.table("sentences").select("*").limit(limit).execute()
        return [Sentence.model_validate(sentence) for sentence in result.data]

    async def get_random_sentence(
        self,
        is_correct: bool | None = None,
        verb_id: UUID | None = None,
    ) -> Sentence | None:
        """Get a random sentence with optional filters."""
        # Note: Supabase doesn't have native random, this is a simple implementation
        query = self.client.table("sentences").select("*")

        if is_correct is not None:
            query = query.eq("is_correct", is_correct)
        if verb_id:
            query = query.eq("verb_id", str(verb_id))

        result = await query.limit(50).execute()

        if result.data:
            import random

            return Sentence.model_validate(random.choice(result.data))
        return None

    async def get_sentence(self, sentence_id: UUID) -> Sentence | None:
        """Get a sentence by ID."""
        result = (
            await self.client.table("sentences")
            .select("*")
            .eq("id", str(sentence_id))
            .execute()
        )

        if result.data:
            return Sentence.model_validate(result.data[0])
        return None

    async def get_sentences(
        self,
        verb_id: UUID | None = None,
        is_correct: bool | None = None,
        tense: str | None = None,
        pronoun: str | None = None,
        target_language_code: str | None = None,
        limit: int = 50,
    ) -> list[Sentence]:
        """Get sentences with optional filters."""
        query = self.client.table("sentences").select("*")

        if verb_id:
            query = query.eq("verb_id", str(verb_id))
        if is_correct is not None:
            query = query.eq("is_correct", is_correct)
        if tense:
            query = query.eq("tense", tense)
        if pronoun:
            query = query.eq("pronoun", pronoun)
        if target_language_code:
            query = query.eq("target_language_code", target_language_code)

        result = await query.limit(limit).execute()

        return [Sentence.model_validate(sentence) for sentence in result.data]

    async def get_sentences_by_verb(
        self, verb_id: UUID, limit: int = 50
    ) -> list[Sentence]:
        """Get all sentences for a specific verb."""
        return await self.get_sentences(verb_id=verb_id, limit=limit)

    async def update_sentence(
        self, sentence_id: UUID, sentence_data: SentenceUpdate
    ) -> Sentence | None:
        """Update a sentence."""
        sentence_dict = sentence_data.model_dump(exclude_unset=True)

        # Convert enums to string values for storage
        for key, value in sentence_dict.items():
            if hasattr(value, "value"):
                sentence_dict[key] = value.value

        result = (
            await self.client.table("sentences")
            .update(sentence_dict)
            .eq("id", str(sentence_id))
            .execute()
        )

        if result.data:
            return Sentence.model_validate(result.data[0])
        return None
