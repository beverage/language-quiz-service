"""Verb service for business logic with updated schema support."""

import json
import logging
from uuid import UUID

from pydantic import ValidationError

from src.clients.openai_client import OpenAIClient
from src.clients.supabase import get_supabase_client
from src.core.exceptions import ContentGenerationError
from src.prompts.verb_prompts import VerbPromptGenerator
from src.repositories.verb_repository import VerbRepository
from src.schemas.verbs import (
    Conjugation,
    ConjugationCreate,
    ConjugationUpdate,
    LLMVerbPayload,
    Tense,
    Verb,
    VerbCreate,
    VerbUpdate,
    VerbWithConjugations,
)
from supabase import Client

logger = logging.getLogger(__name__)


class VerbService:
    def __init__(self):
        """Initialize the verb service with injectable dependencies."""
        self.openai_client: OpenAIClient = OpenAIClient()
        self.verb_prompt_generator: VerbPromptGenerator = VerbPromptGenerator()
        self.verb_repository: VerbRepository | None = None
        self.db_client: Client | None = None

    async def _get_db_client(self):
        if not self.db_client:
            self.db_client = await get_supabase_client()
        return self.db_client

    async def _get_verb_repository(self):
        if not self.verb_repository:
            client = await self._get_db_client()
            self.verb_repository = VerbRepository(client=client)
        return self.verb_repository

    # ===== VERB CRUD OPERATIONS =====

    async def create_verb(self, verb_data: VerbCreate) -> Verb:
        """Create a new verb."""
        repo = await self._get_verb_repository()
        return await repo.create_verb(verb_data)

    async def delete_verb(self, verb_id: UUID) -> bool:
        """Delete a verb and all its conjugations."""
        # First get the verb to know its parameters
        repo = await self._get_verb_repository()
        verb = await self.get_verb(verb_id)
        if not verb:
            return False

        # Delete all conjugations for this verb first
        await repo.delete_conjugations_by_verb(
            infinitive=verb.infinitive,
            auxiliary=verb.auxiliary.value,
            reflexive=verb.reflexive,
        )

        # Then delete the verb
        return await repo.delete_verb(verb_id)

    async def get_all_verbs(
        self, limit: int = 100, target_language_code: str | None = None
    ) -> list[Verb]:
        """Get all verbs, optionally filtered by language."""
        repo = await self._get_verb_repository()
        return await repo.get_all_verbs(
            limit=limit, target_language_code=target_language_code
        )

    async def get_random_verb(self, target_language_code: str = "eng") -> Verb | None:
        """Get a random verb."""
        repo = await self._get_verb_repository()
        verb = await repo.get_random_verb(target_language_code)
        if verb:
            # Update last used timestamp
            await repo.update_last_used(verb.id)
        return verb

    async def get_verb(self, verb_id: UUID) -> Verb | None:
        """Get a verb by ID."""
        repo = await self._get_verb_repository()
        return await repo.get_verb(verb_id)

    async def get_verb_by_infinitive(
        self,
        infinitive: str,
        auxiliary: str | None = None,
        reflexive: bool | None = None,
        target_language_code: str = "eng",
    ) -> Verb | None:
        """
        Get a verb by infinitive and optional parameters.

        Since infinitive is no longer unique, additional parameters may be needed.
        If not specified, returns the first match found.
        """
        repo = await self._get_verb_repository()
        return await repo.get_verb_by_infinitive(
            infinitive=infinitive,
            auxiliary=auxiliary,
            reflexive=reflexive,
            target_language_code=target_language_code,
        )

    async def get_verbs_by_infinitive(self, infinitive: str) -> list[Verb]:
        """Get all verb variants with the same infinitive."""
        repo = await self._get_verb_repository()
        return await repo.get_verbs_by_infinitive(infinitive)

    async def update_verb(self, verb_id: UUID, verb_data: VerbUpdate) -> Verb | None:
        """Update a verb."""
        repo = await self._get_verb_repository()
        return await repo.update_verb(verb_id, verb_data)

    # ===== CONJUGATION OPERATIONS =====

    async def create_conjugation(self, conjugation: ConjugationCreate) -> Conjugation:
        """Create a new conjugation."""
        repo = await self._get_verb_repository()
        return await repo.create_conjugation(conjugation)

    async def get_conjugations(
        self, infinitive: str, auxiliary: str, reflexive: bool = False
    ) -> list[Conjugation]:
        """Get all conjugations for a verb."""
        repo = await self._get_verb_repository()
        return await repo.get_conjugations(
            infinitive=infinitive, auxiliary=auxiliary, reflexive=reflexive
        )

    async def get_conjugations_by_verb_id(self, verb_id: UUID) -> list[Conjugation]:
        """Get conjugations by verb ID (backwards compatibility)."""
        await self._get_verb_repository()
        verb = await self.get_verb(verb_id)
        if not verb:
            return []

        return await self.get_conjugations(
            infinitive=verb.infinitive,
            auxiliary=verb.auxiliary.value,
            reflexive=verb.reflexive,
        )

    async def update_conjugation(
        self,
        infinitive: str,
        auxiliary: str,
        reflexive: bool,
        tense: Tense,
        conjugation_data: ConjugationUpdate,
    ) -> Conjugation | None:
        """Update a conjugation by verb parameters and tense."""
        repo = await self._get_verb_repository()
        return await repo.update_conjugation_by_verb_and_tense(
            infinitive=infinitive,
            auxiliary=auxiliary,
            reflexive=reflexive,
            tense=tense,
            conjugation=conjugation_data,
        )

    # ===== COMPOSITE OPERATIONS =====

    async def get_verb_with_conjugations(
        self,
        infinitive: str,
        auxiliary: str | None = None,
        reflexive: bool = False,
        target_language_code: str = "eng",
    ) -> VerbWithConjugations | None:
        """Get a verb with all its conjugations."""
        repo = await self._get_verb_repository()
        # If auxiliary not specified, try to find any variant
        if auxiliary is None:
            verbs = await self.get_verbs_by_infinitive(infinitive)
            if not verbs:
                return None
            # Use the first variant found
            verb = verbs[0]
            auxiliary = verb.auxiliary.value

        return await repo.get_verb_with_conjugations(
            infinitive=infinitive,
            auxiliary=auxiliary,
            reflexive=reflexive,
            target_language_code=target_language_code,
        )

    async def search_verbs(
        self,
        query: str,
        search_translation: bool = True,
        target_language_code: str | None = None,
        limit: int = 20,
    ) -> list[Verb]:
        """Search verbs by infinitive or translation."""
        repo = await self._get_verb_repository()
        return await repo.search_verbs(
            query=query,
            search_translation=search_translation,
            target_language_code=target_language_code,
            limit=limit,
        )

    # ===== LLM INTEGRATION =====

    async def download_verb(
        self, requested_verb: str, target_language_code: str = "eng"
    ) -> Verb:
        """
        Download a verb using AI integration with two-phase approach.

        Phase 1: Get verb data without COD/COI flags
        Phase 2: Use auxiliary to determine COD/COI flags
        """
        logger.info("Fetching verb %s", requested_verb)

        # Phase 1: Generate main verb prompt (without COD/COI)
        verb_prompt = self.verb_prompt_generator.generate_verb_prompt(
            verb_infinitive=requested_verb, target_language_code=target_language_code
        )

        # Get AI response for main verb data
        llm_response = await self.openai_client.handle_request(verb_prompt)
        logger.debug("✅ LLM Response: %s", llm_response)

        repo = await self._get_verb_repository()
        try:
            response_json = json.loads(llm_response)
            verb_payload = LLMVerbPayload.model_validate(response_json)
        except (json.JSONDecodeError, ValidationError) as e:
            logger.error(f"Failed to decode or validate LLM response: {e}")
            raise ContentGenerationError(
                content_type="verb",
                message=f"Failed to parse verb data from AI for '{requested_verb}'",
            ) from e

        # Check if this specific verb variant already exists using the correct unique tuple
        # NOTE: Verb uniqueness is determined by (infinitive, auxiliary, reflexive, target_language_code)
        existing_verb = await repo.get_verb_by_infinitive(
            infinitive=verb_payload.infinitive,
            auxiliary=verb_payload.auxiliary.value,
            reflexive=verb_payload.reflexive,
            target_language_code=target_language_code,  # Include in uniqueness check
        )
        if existing_verb:
            raise ContentGenerationError(
                content_type="verb",
                message=f"Verb '{verb_payload.infinitive}' with auxiliary '{verb_payload.auxiliary.value}', reflexive={verb_payload.reflexive}, and target_language='{target_language_code}' already exists.",
            )

        # Phase 2: Use the auxiliary from Phase 1 to determine COD/COI
        objects_prompt = self.verb_prompt_generator.generate_objects_prompt(
            verb_infinitive=verb_payload.infinitive,
            auxiliary=verb_payload.auxiliary.value,
        )
        objects_response = await self.openai_client.handle_request(objects_prompt)
        logger.debug(
            "✅ Objects Response (%s, %s): %s",
            verb_payload.infinitive,
            verb_payload.auxiliary,
            objects_response,
        )

        try:
            objects_json = json.loads(objects_response)
            can_have_cod = objects_json.get("can_have_cod", True)
            can_have_coi = objects_json.get("can_have_coi", True)
        except json.JSONDecodeError:
            logger.warning("Failed to decode COD/COI response, using defaults.")
            can_have_cod, can_have_coi = True, True

        # Create a new VerbCreate object with all the data
        verb_data = verb_payload.model_dump()
        verb_data.pop("can_have_cod", None)
        verb_data.pop("can_have_coi", None)

        verb_to_create = VerbCreate(
            **verb_data,
            can_have_cod=can_have_cod,
            can_have_coi=can_have_coi,
        )

        # Upsert the verb and its conjugations
        verb = await self._upsert_verb(verb_to_create, repo)
        await self._process_conjugations(verb, verb_payload.tenses, repo)

        return verb

    async def _upsert_verb(self, verb_data: VerbCreate, repo: VerbRepository) -> Verb:
        """Helper to upsert a verb."""
        return await repo.upsert_verb(verb_data)

    async def _process_conjugations(
        self, verb: Verb, conjugations: list, repo: VerbRepository
    ):
        """Helper to process and upsert conjugations."""
        for conj_data in conjugations:
            # The conj_data from the LLM might contain redundant fields
            # that are already defined in the parent verb object.
            dumped_data = conj_data.model_dump()
            dumped_data.pop("infinitive", None)
            dumped_data.pop("auxiliary", None)
            dumped_data.pop("reflexive", None)

            conj_create = ConjugationCreate(
                infinitive=verb.infinitive,
                auxiliary=verb.auxiliary,
                reflexive=verb.reflexive,
                **dumped_data,
            )
            await repo.upsert_conjugation(conj_create)
