"""Sentence service for business logic."""

import json
import logging
import random
from typing import List, Optional
from uuid import UUID

from src.clients.openai_client import OpenAIClient
from src.repositories.sentence_repository import SentenceRepository
from src.prompts.sentence_prompts import SentencePromptGenerator
from src.schemas.sentences import (
    SentenceCreate,
    Sentence,
    SentenceUpdate,
    Pronoun,
    Tense,
    DirectObject,
    IndirectPronoun,
    Negation,
)
from src.services.verb_service import VerbService

logger = logging.getLogger(__name__)


class SentenceService:
    def __init__(
        self,
        openai_client: OpenAIClient = None,
        sentence_repository: Optional[SentenceRepository] = None,
        verb_service: Optional[VerbService] = None,
        prompt_generator: Optional[SentencePromptGenerator] = None,
    ):
        """Initialize the sentence service with injectable dependencies."""
        self.openai_client = openai_client or OpenAIClient()
        self.sentence_repository = sentence_repository
        self.verb_service = verb_service or VerbService()
        self.prompt_generator = prompt_generator or SentencePromptGenerator()

    async def _get_sentence_repository(self) -> SentenceRepository:
        """Asynchronously get the sentence repository, creating it if it doesn't exist."""
        if self.sentence_repository is None:
            self.sentence_repository = await SentenceRepository.create()
        return self.sentence_repository

    async def create_sentence(self, sentence_data: SentenceCreate) -> Sentence:
        """Create a new sentence."""
        repo = await self._get_sentence_repository()
        return await repo.create_sentence(sentence_data)

    async def get_sentence(self, sentence_id: UUID) -> Optional[Sentence]:
        """Get a sentence by ID."""
        repo = await self._get_sentence_repository()
        return await repo.get_sentence(sentence_id)

    async def get_sentences(
        self,
        verb_id: Optional[UUID] = None,
        is_correct: Optional[bool] = None,
        tense: Optional[str] = None,
        pronoun: Optional[str] = None,
        target_language_code: Optional[str] = None,
        limit: int = 50,
    ) -> List[Sentence]:
        """Get sentences with optional filters."""
        repo = await self._get_sentence_repository()
        return await repo.get_sentences(
            verb_id=verb_id,
            is_correct=is_correct,
            tense=tense,
            pronoun=pronoun,
            target_language_code=target_language_code,
            limit=limit,
        )

    async def get_sentences_by_verb(
        self, verb_id: UUID, limit: int = 50
    ) -> List[Sentence]:
        """Get all sentences for a specific verb."""
        repo = await self._get_sentence_repository()
        return await repo.get_sentences_by_verb(verb_id, limit)

    async def get_random_sentence(
        self,
        is_correct: Optional[bool] = None,
        verb_id: Optional[UUID] = None,
    ) -> Optional[Sentence]:
        """Get a random sentence."""
        repo = await self._get_sentence_repository()
        return await repo.get_random_sentence(is_correct=is_correct, verb_id=verb_id)

    async def update_sentence(
        self, sentence_id: UUID, sentence_data: SentenceUpdate
    ) -> Optional[Sentence]:
        """Update a sentence."""
        repo = await self._get_sentence_repository()
        return await repo.update_sentence(sentence_id, sentence_data)

    async def delete_sentence(self, sentence_id: UUID) -> bool:
        """Delete a sentence."""
        repo = await self._get_sentence_repository()
        return await repo.delete_sentence(sentence_id)

    async def get_all_sentences(self, limit: int = 100) -> List[Sentence]:
        """Get all sentences."""
        repo = await self._get_sentence_repository()
        return await repo.get_all_sentences(limit)

    async def count_sentences(
        self,
        verb_id: Optional[UUID] = None,
        is_correct: Optional[bool] = None,
    ) -> int:
        """Count sentences with optional filters."""
        repo = await self._get_sentence_repository()
        return await repo.count_sentences(verb_id=verb_id, is_correct=is_correct)

    async def generate_sentence(
        self,
        verb_id: UUID,
        pronoun: Pronoun = Pronoun.FIRST_PERSON,
        tense: Tense = Tense.PRESENT,
        direct_object: DirectObject = DirectObject.NONE,
        indirect_pronoun: IndirectPronoun = IndirectPronoun.NONE,
        negation: Negation = Negation.NONE,
        is_correct: bool = True,
        target_language_code: str = "en",
    ) -> Sentence:
        """Generate a sentence using AI integration."""
        logger.info(f"Generating sentence for verb_id {verb_id}")

        # Get the verb details first
        verb = await self.verb_service.get_verb(verb_id)
        if not verb:
            raise ValueError(f"Verb with ID {verb_id} not found")

        logger.info(
            f"➡️ Generating: {verb.infinitive}, {pronoun.value}, {tense.value}, "
            f"COD: {direct_object.value}, COI: {indirect_pronoun.value}, NEG: {negation.value}"
        )

        # Create the sentence structure for AI prompt
        sentence_request = SentenceCreate(
            target_language_code=target_language_code,
            content="",  # Will be filled by AI
            translation="",  # Will be filled by AI
            verb_id=verb_id,
            pronoun=pronoun,
            tense=tense,
            direct_object=direct_object,
            indirect_pronoun=indirect_pronoun,
            negation=negation,
            is_correct=is_correct,
            explanation=None,  # Will be filled by AI if incorrect
            source="ai_generated",
        )

        # Generate AI prompt and request
        prompt = self.prompt_generator.generate_sentence_prompt(sentence_request, verb)
        response = await self.openai_client.handle_request(prompt)
        response_json = json.loads(response)

        # Update the sentence with AI response
        sentence_request.content = response_json.get("sentence", "")
        sentence_request.translation = response_json.get("translation", "")

        # Handle is_correct from AI response
        ai_is_correct = response_json.get("is_correct")
        if isinstance(ai_is_correct, bool):
            sentence_request.is_correct = ai_is_correct
        elif isinstance(ai_is_correct, str):
            sentence_request.is_correct = ai_is_correct.lower() == "true"

        # Set explanation if sentence is incorrect
        if not sentence_request.is_correct:
            sentence_request.explanation = response_json.get("explanation", "")

        # Update grammatical elements if AI modified them
        if "direct_object" in response_json:
            sentence_request.direct_object = DirectObject(
                response_json["direct_object"]
            )
        if "indirect_pronoun" in response_json:
            sentence_request.indirect_pronoun = IndirectPronoun(
                response_json["indirect_pronoun"]
            )
        if "negation" in response_json:
            sentence_request.negation = Negation(response_json["negation"])

        logger.info(
            f"⬅️ Generated: COD: {sentence_request.direct_object.value}, "
            f"COI: {sentence_request.indirect_pronoun.value}, NEG: {sentence_request.negation.value}"
        )

        # Persist to repository
        repo = await self._get_sentence_repository()
        return await repo.create_sentence(sentence_request)

    async def generate_random_sentence(
        self, is_correct: bool = True, target_language_code: str = "en"
    ) -> Sentence:
        """Generate a random sentence using a random verb."""
        # Get a random verb
        verb = await self.verb_service.get_random_verb()
        if not verb:
            raise ValueError("No verbs available for sentence generation")

        # Generate random grammatical elements

        pronoun = random.choice(list(Pronoun))
        tense = random.choice(
            [t for t in Tense if t != Tense.IMPERATIVE]
        )  # Avoid imperative for now
        direct_object = random.choice(list(DirectObject))
        indirect_pronoun = random.choice(list(IndirectPronoun))

        # 70% chance of no negation, 30% chance of random negation
        if random.randint(1, 10) <= 7:
            negation = Negation.NONE
        else:
            negation = random.choice([n for n in Negation if n != Negation.NONE])

        return await self.generate_sentence(
            verb_id=verb.id,
            pronoun=pronoun,
            tense=tense,
            direct_object=direct_object,
            indirect_pronoun=indirect_pronoun,
            negation=negation,
            is_correct=is_correct,
            target_language_code=target_language_code,
        )
