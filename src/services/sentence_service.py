"""Sentence service for business logic."""

import json
import logging
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
    IndirectObject,
    Negation,
    CorrectnessValidationResponse,
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

    async def _validate_sentence(
        self, sentence: SentenceCreate, verb
    ) -> CorrectnessValidationResponse:
        """Validate sentence correctness using AI."""
        try:
            # Generate validation prompt directly with SentenceCreate
            prompt = self.prompt_generator.generate_correctness_prompt(sentence, verb)

            # Get AI response
            response = await self.openai_client.handle_request(prompt)

            # Parse validation response
            response_json = json.loads(response)
            return CorrectnessValidationResponse.model_validate(response_json)

        except (json.JSONDecodeError, Exception) as e:
            logger.warning(f"Validation failed due to error: {e}")
            # Return a default "valid" response if validation fails
            return CorrectnessValidationResponse(
                is_valid=True,
                explanation="Validation service error - proceeding without validation",
                actual_direct_object=sentence.direct_object,
                actual_indirect_object=sentence.indirect_object,
                actual_negation=sentence.negation,
            )

    async def count_sentences(
        self,
        verb_id: Optional[UUID] = None,
        is_correct: Optional[bool] = None,
    ) -> int:
        """Count sentences with optional filters."""
        repo = await self._get_sentence_repository()
        return await repo.count_sentences(verb_id=verb_id, is_correct=is_correct)

    async def create_sentence(self, sentence_data: SentenceCreate) -> Sentence:
        """Create a new sentence."""
        repo = await self._get_sentence_repository()
        return await repo.create_sentence(sentence_data)

    async def delete_sentence(self, sentence_id: UUID) -> bool:
        """Delete a sentence."""
        repo = await self._get_sentence_repository()
        return await repo.delete_sentence(sentence_id)

    async def generate_sentence(
        self,
        verb_id: UUID,
        pronoun: Pronoun = Pronoun.FIRST_PERSON,
        tense: Tense = Tense.PRESENT,
        direct_object: DirectObject = DirectObject.NONE,
        indirect_object: IndirectObject = IndirectObject.NONE,
        negation: Negation = Negation.NONE,
        is_correct: bool = True,
        target_language_code: str = "eng",
        validate: bool = False,
    ) -> Sentence:
        """Generate a sentence using AI integration with validation."""
        logger.info(f"Generating sentence for verb_id {verb_id}")

        # Get the verb details first
        verb = await self.verb_service.get_verb(verb_id)
        if not verb:
            raise ValueError(f"Verb with ID {verb_id} not found")

        logger.info(
            f"➡️ Generating: {verb.infinitive}, {pronoun.value}, {tense.value}, "
            f"COD: {direct_object.value}, COI: {indirect_object.value}, NEG: {negation.value}"
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
            indirect_object=indirect_object,
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
        is_correct_response = response_json.get("is_correct")
        if isinstance(is_correct_response, bool):
            sentence_request.is_correct = is_correct_response

        # Set explanation if sentence is incorrect
        if not sentence_request.is_correct:
            sentence_request.explanation = response_json.get("explanation", "")

        # Update grammatical elements if AI modified them
        sentence_request.direct_object = (
            DirectObject(response_json["direct_object"])
            if response_json.get("has_compliment_object_direct")
            else DirectObject.NONE
        )

        sentence_request.indirect_object = (
            IndirectObject(response_json["indirect_object"])
            if response_json.get("has_compliment_object_indirect")
            else IndirectObject.NONE
        )

        sentence_request.negation = Negation(
            response_json.get("negation", Negation.NONE.value)
        )

        logger.info(
            f"⬅️ Generated: COD: {sentence_request.direct_object.value}, "
            f"COI: {sentence_request.indirect_object.value}, NEG: {sentence_request.negation.value}"
        )

        # Conditional validation based on validate parameter
        if validate:
            logger.info("🔍 Validation enabled - performing additional LLM validation")
            validation = await self._validate_sentence(sentence_request, verb)

            if validation.is_valid:
                # Update sentence with detected values from validation
                sentence_request.direct_object = validation.actual_direct_object
                sentence_request.indirect_object = validation.actual_indirect_object
                sentence_request.negation = validation.actual_negation

                logger.info("✅ Validation passed")
            else:
                logger.error(f"❌ Validation failed: {validation.explanation}")
                raise ValueError(f"Sentence validation failed: {validation.explanation}")
        else:
            logger.info("⚡ Validation disabled - skipping additional LLM validation")

        # Persist to repository
        repo = await self._get_sentence_repository()
        return await repo.create_sentence(sentence_request)

    async def get_all_sentences(self, limit: int = 100) -> List[Sentence]:
        """Get all sentences."""
        repo = await self._get_sentence_repository()
        return await repo.get_all_sentences(limit)

    async def get_random_sentence(
        self,
        is_correct: Optional[bool] = None,
        verb_id: Optional[UUID] = None,
    ) -> Optional[Sentence]:
        """Get a random sentence."""
        repo = await self._get_sentence_repository()
        return await repo.get_random_sentence(is_correct=is_correct, verb_id=verb_id)

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

    async def update_sentence(
        self, sentence_id: UUID, sentence_data: SentenceUpdate
    ) -> Optional[Sentence]:
        """Update a sentence."""
        repo = await self._get_sentence_repository()
        return await repo.update_sentence(sentence_id, sentence_data)
