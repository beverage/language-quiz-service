"""Sentence repository for data access."""

import logging

from typing import List, Optional
from supabase import Client
from ..schemas.sentence import Sentence, SentenceCreate
from ..clients.supabase import get_supabase_client

logger = logging.getLogger(__name__)


class SentenceRepository:
    def __init__(self, client: Optional[Client] = None):
        self.client = client or get_supabase_client()

    async def create_sentence(self, sentence: SentenceCreate) -> Sentence:
        """Create a new sentence."""
        sentence_dict = sentence.model_dump()

        # Convert enums to string values for storage
        for key, value in sentence_dict.items():
            if hasattr(value, "value"):
                sentence_dict[key] = value.value

        result = self.client.table("sentences").insert(sentence_dict).execute()

        if result.data:
            return Sentence(**result.data[0])
        raise Exception("Failed to create sentence")

    async def get_sentence(self, sentence_id: int) -> Optional[Sentence]:
        """Get a sentence by ID."""
        result = (
            self.client.table("sentences").select("*").eq("id", sentence_id).execute()
        )

        if result.data:
            return Sentence(**result.data[0])
        return None

    async def get_sentences(
        self,
        infinitive: Optional[str] = None,
        is_correct: Optional[bool] = None,
        limit: int = 50,
    ) -> List[Sentence]:
        """Get sentences with optional filters."""
        query = self.client.table("sentences").select("*")

        if infinitive:
            query = query.eq("infinitive", infinitive)
        if is_correct is not None:
            query = query.eq("is_correct", is_correct)

        result = query.limit(limit).execute()

        return [Sentence(**sentence) for sentence in result.data]

    async def get_random_sentence(self) -> Optional[Sentence]:
        """Get a random sentence."""
        # Note: Supabase doesn't have native random, this is a simple implementation
        result = self.client.table("sentences").select("*").limit(50).execute()

        if result.data:
            import random

            return Sentence(**random.choice(result.data))
        return None

    async def update_sentence(
        self, sentence_id: int, sentence: SentenceCreate
    ) -> Optional[Sentence]:
        """Update a sentence."""
        sentence_dict = sentence.model_dump(exclude_unset=True)

        # Convert enums to string values for storage
        for key, value in sentence_dict.items():
            if hasattr(value, "value"):
                sentence_dict[key] = value.value

        result = (
            self.client.table("sentences")
            .update(sentence_dict)
            .eq("id", sentence_id)
            .execute()
        )

        if result.data:
            return Sentence(**result.data[0])
        return None

    async def delete_sentence(self, sentence_id: int) -> bool:
        """Delete a sentence."""
        result = self.client.table("sentences").delete().eq("id", sentence_id).execute()
        return len(result.data) > 0
