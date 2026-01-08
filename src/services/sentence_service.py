"""Sentence service for business logic."""

import asyncio
import json
import logging
from datetime import UTC, datetime
from uuid import UUID, uuid4

from src.clients.abstract_llm_client import AbstractLLMClient
from src.core.config import settings
from src.core.exceptions import NotFoundError
from src.prompts.response_schemas import (
    get_correct_sentence_response_schema,
    get_incorrect_sentence_response_schema,
)
from src.prompts.sentences import ErrorType, SentencePromptBuilder
from src.repositories.sentence_repository import SentenceRepository
from src.schemas.llm_response import LLMResponse
from src.schemas.problems import GrammarFocus
from src.schemas.sentences import (
    DirectObject,
    IndirectObject,
    Negation,
    Pronoun,
    Sentence,
    SentenceCreate,
    SentenceUpdate,
    Tense,
)
from src.schemas.verbs import Verb
from src.services.verb_service import VerbService

logger = logging.getLogger(__name__)


class SentenceService:
    def __init__(
        self,
        llm_client: AbstractLLMClient,
        sentence_repository: SentenceRepository | None = None,
        verb_service: VerbService | None = None,
        sentence_builder: SentencePromptBuilder | None = None,
        use_compositional: bool = True,
    ):
        """Initialize the sentence service with injectable dependencies.

        Args:
            llm_client: Required LLM client for AI operations.
            sentence_repository: Optional repository (can be set later for lazy init).
            verb_service: Optional verb service (can be set later for lazy init).
            sentence_builder: Optional prompt builder (defaults to SentencePromptBuilder).
            use_compositional: Whether to use compositional prompts.
        """
        self.llm_client = llm_client
        self.sentence_repository = sentence_repository
        self.verb_service = verb_service
        self.sentence_builder = sentence_builder or SentencePromptBuilder()
        self.use_compositional = use_compositional

    def set_repository(self, sentence_repository: SentenceRepository) -> None:
        """Set the sentence repository (for cases requiring lazy initialization)."""
        self.sentence_repository = sentence_repository

    def set_verb_service(self, verb_service: VerbService) -> None:
        """Set the verb service (for cases requiring lazy initialization)."""
        self.verb_service = verb_service

    def _get_sentence_repository(self) -> SentenceRepository:
        """Get the sentence repository, raising if not set."""
        if self.sentence_repository is None:
            raise RuntimeError(
                "SentenceRepository not set. Either pass it to __init__ or call set_repository()."
            )
        return self.sentence_repository

    def _get_verb_service(self) -> VerbService:
        """Get the verb service, raising if not set."""
        if self.verb_service is None:
            raise RuntimeError(
                "VerbService not set. Either pass it to __init__ or call set_verb_service()."
            )
        return self.verb_service

    async def count_sentences(
        self,
        verb_id: UUID | None = None,
        is_correct: bool | None = None,
    ) -> int:
        """Count sentences with optional filters."""
        repo = self._get_sentence_repository()
        return await repo.count_sentences(verb_id=verb_id, is_correct=is_correct)

    async def create_sentence(self, sentence_data: SentenceCreate) -> Sentence:
        """Create a new sentence."""
        repo = self._get_sentence_repository()
        return await repo.create_sentence(sentence_data)

    async def delete_sentence(self, sentence_id: UUID) -> bool:
        """Delete a sentence."""
        repo = self._get_sentence_repository()
        # First, check if the sentence exists
        sentence = await repo.get_sentence(sentence_id)
        if not sentence:
            raise NotFoundError(f"Sentence with ID {sentence_id} not found")
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
        error_type: ErrorType | None = None,
        verb: Verb | None = None,
        conjugations: list | None = None,
        focus: GrammarFocus = GrammarFocus.CONJUGATION,
    ) -> tuple[Sentence, LLMResponse]:
        """Generate a sentence using AI integration.

        Args:
            verb: Optional pre-fetched verb to avoid duplicate DB calls
            conjugations: Optional pre-fetched conjugations to avoid duplicate DB calls
            focus: Grammar focus area (conjugation or pronouns)

        Returns:
            Tuple of (Sentence, LLMResponse) for trace capture
        """
        logger.debug(f"Generating sentence for verb_id {verb_id}")

        # Get the verb details (use provided or fetch)
        verb_service = self._get_verb_service()
        if verb is None:
            verb = await verb_service.get_verb(verb_id)
            if not verb:
                raise NotFoundError(f"Verb with ID {verb_id} not found")

        # Fetch conjugations to get the correct form for this pronoun+tense
        correct_conjugation_form = None
        try:
            if conjugations is None:
                conjugations = await verb_service.get_conjugations(
                    infinitive=verb.infinitive,
                    auxiliary=verb.auxiliary.value,
                    reflexive=verb.reflexive,
                )
            # Find the conjugation for this tense
            tense_conjugation = next(
                (c for c in conjugations if c.tense == tense), None
            )
            if tense_conjugation:
                # Extract the form for this pronoun
                pronoun_to_field = {
                    Pronoun.FIRST_PERSON: tense_conjugation.first_person_singular,
                    Pronoun.SECOND_PERSON: tense_conjugation.second_person_singular,
                    Pronoun.THIRD_PERSON: tense_conjugation.third_person_singular,
                    Pronoun.FIRST_PERSON_PLURAL: tense_conjugation.first_person_plural,
                    Pronoun.SECOND_PERSON_PLURAL: tense_conjugation.second_person_plural,
                    Pronoun.THIRD_PERSON_PLURAL: tense_conjugation.third_person_plural,
                }
                correct_conjugation_form = pronoun_to_field.get(pronoun)
                if correct_conjugation_form:
                    logger.debug(
                        f"✓ Found correct conjugation: '{correct_conjugation_form}' "
                        f"for {pronoun.value} + {verb.infinitive} + {tense.value}"
                    )
        except Exception as e:
            logger.warning(f"Could not fetch conjugation: {e}")

        logger.debug(
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
        if self.use_compositional:
            # Use new compositional prompt builder
            if not is_correct and error_type is None:
                raise ValueError(
                    "error_type must be provided for incorrect sentences when using compositional prompts"
                )
            prompt = self.sentence_builder.build_prompt(
                sentence_request,
                verb,
                conjugations,  # Pass conjugations to the builder
                error_type=error_type,
                focus=focus,
            )

            # Get appropriate response schema based on correctness
            response_schema = (
                get_correct_sentence_response_schema()
                if is_correct
                else get_incorrect_sentence_response_schema()
            )

            logger.debug(
                "🎨 Using compositional prompt builder"
                + (f" with error type: {error_type.value}" if error_type else "")
            )
        else:
            # Use legacy prompt generator
            prompt = self.prompt_generator.generate_sentence_prompt(
                sentence_request, verb
            )
            response_schema = None  # Legacy prompts don't use structured output
            logger.debug("📝 Using legacy prompt generator")

        response = await self.llm_client.handle_request(
            prompt,
            model=settings.reasoning_model,
            operation="sentence_generation",
            response_format=response_schema,
        )
        # Attach the prompt to the response for trace capture
        response.prompt_text = prompt
        response_json = json.loads(response.content)

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

        try:
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
        except ValueError as e:
            logger.error(
                f"❌ Error extracting grammatical elements from response '{response_json.get('sentence', '(no sentence was generated)')}'"
            )
            raise e

        logger.debug(
            f"⬅️ Generated: COD: {sentence_request.direct_object.value}, "
            f"COI: {sentence_request.indirect_object.value}, NEG: {sentence_request.negation.value}"
        )

        # Generate UUID and timestamp for both response and database
        sentence_id = uuid4()
        now = datetime.now(UTC)

        # Persist to repository in background (fire and forget)
        asyncio.create_task(
            self._create_sentence_background(sentence_request, sentence_id, now)
        )

        # Return sentence immediately without waiting for DB write
        # Construct a Sentence object from the SentenceCreate data
        sentence = Sentence(
            id=sentence_id,
            created_at=now,
            updated_at=now,
            **sentence_request.model_dump(),
        )
        return sentence, response

    async def _create_sentence_background(
        self, sentence_data: SentenceCreate, sentence_id: UUID, timestamp: datetime
    ) -> None:
        """Create sentence in database in background (fire and forget)."""
        try:
            # Add the ID to the sentence data before persisting
            sentence_dict = sentence_data.model_dump(mode="json")
            sentence_dict["id"] = str(sentence_id)
            sentence_dict["created_at"] = timestamp.isoformat()
            sentence_dict["updated_at"] = timestamp.isoformat()

            repo = self._get_sentence_repository()
            # Insert directly with our generated ID
            await repo.client.table("sentences").insert(sentence_dict).execute()
        except Exception as e:
            logger.error(f"Failed to persist sentence {sentence_id} to database: {e}")

    async def get_all_sentences(self, limit: int = 100) -> list[Sentence]:
        """Get all sentences."""
        repo = self._get_sentence_repository()
        return await repo.get_all_sentences(limit)

    async def get_random_sentence(
        self,
        is_correct: bool | None = None,
        verb_id: UUID | None = None,
    ) -> Sentence | None:
        """Get a random sentence."""
        repo = self._get_sentence_repository()
        return await repo.get_random_sentence(is_correct=is_correct, verb_id=verb_id)

    async def get_sentence(self, sentence_id: UUID) -> Sentence | None:
        """Get a sentence by ID."""
        repo = self._get_sentence_repository()
        return await repo.get_sentence(sentence_id)

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
        repo = self._get_sentence_repository()
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
    ) -> list[Sentence]:
        """Get all sentences for a specific verb."""
        repo = self._get_sentence_repository()
        return await repo.get_sentences_by_verb(verb_id, limit)

    async def update_sentence(
        self, sentence_id: UUID, sentence_data: SentenceUpdate
    ) -> Sentence | None:
        """Update a sentence."""
        repo = self._get_sentence_repository()
        return await repo.update_sentence(sentence_id, sentence_data)
