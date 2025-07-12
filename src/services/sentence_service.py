import logging

from typing import List, Optional
from repositories.sentence_repository import SentenceRepository
from schemas.sentences import (
    SentenceCreate,
    Sentence,
    DirectObject,
    IndirectPronoun,
    Negation,
)
import json
from clients.openai_client import OpenAIClient
from prompts.sentence_prompts import SentencePromptGenerator
from services.verb_service import VerbService

logger = logging.getLogger(__name__)


class SentenceService:
    def __init__(
        self,
        openai_client: OpenAIClient = None,
        sentence_repository: SentenceRepository = None,
        verb_service: VerbService = None,
        prompt_generator: SentencePromptGenerator = None,
    ):
        """Initialize the sentence service with injectable dependencies."""
        self.openai_client = openai_client or OpenAIClient()
        self.sentence_repository = sentence_repository or SentenceRepository()
        self.verb_service = verb_service or VerbService()
        self.prompt_generator = prompt_generator or SentencePromptGenerator()

    async def create_sentence(self, sentence: SentenceCreate) -> Sentence:
        """Generate and persist a sentence via AI, then save to Supabase using the provided SentenceCreate model."""

        logger.info(
            f"➡️ COD: {sentence.direct_object}, COI: {sentence.indirect_pronoun}, NEG: {sentence.negation}"
        )

        # Generate AI prompt and request
        prompt = self.prompt_generator.generate_sentence_prompt(sentence)
        response = await self.openai_client.handle_request(prompt)
        response_json = json.loads(response)

        # Update the input model with AI response
        sentence.content = response_json.get("sentence")
        sentence.translation = response_json.get("translation")
        # Convert string booleans if necessary
        is_correct = response_json.get("is_correct")
        sentence.is_correct = (
            is_correct if isinstance(is_correct, bool) else is_correct.lower() == "true"
        )
        sentence.direct_object = DirectObject(response_json.get("direct_object"))
        sentence.indirect_pronoun = IndirectPronoun(
            response_json.get("indirect_pronoun")
        )
        sentence.negation = Negation(response_json.get("negation"))

        logger.info(
            f"⬅️ COD: {sentence.direct_object}, COI: {sentence.indirect_pronoun}, NEG: {sentence.negation}"
        )

        # Persist to repository
        return await self.sentence_repository.create_sentence(sentence)

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
