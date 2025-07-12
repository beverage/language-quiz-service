"""Verb service for business logic with updated schema support."""

import json
import logging
from typing import List, Optional
from uuid import UUID

from src.clients.openai_client import OpenAIClient
from src.repositories.verb_repository import VerbRepository
from src.prompts.verb_prompts import VerbPromptGenerator
from src.schemas.verbs import (
    VerbCreate,
    VerbUpdate,
    Verb,
    VerbWithConjugations,
    Conjugation,
    ConjugationCreate,
    ConjugationUpdate,
    Tense,
    AuxiliaryType,
    VerbClassification,
)

logger = logging.getLogger(__name__)


class VerbService:
    def __init__(
        self,
        openai_client: Optional[OpenAIClient] = None,
        verb_repository: Optional[VerbRepository] = None,
        prompt_generator: Optional[VerbPromptGenerator] = None,
    ):
        """Initialize the verb service with injectable dependencies."""
        self.openai_client = openai_client or OpenAIClient()
        self.verb_prompt_generator = prompt_generator or VerbPromptGenerator()
        self.verb_repository = verb_repository or VerbRepository()

    # ===== VERB CRUD OPERATIONS =====

    async def create_verb(self, verb_data: VerbCreate) -> Verb:
        """Create a new verb."""
        return await self.verb_repository.create_verb(verb_data)

    async def get_verb(self, verb_id: UUID) -> Optional[Verb]:
        """Get a verb by ID."""
        return await self.verb_repository.get_verb(verb_id)

    async def get_verb_by_infinitive(
        self,
        infinitive: str,
        auxiliary: Optional[str] = None,
        reflexive: Optional[bool] = None,
        target_language_code: str = "eng",
    ) -> Optional[Verb]:
        """
        Get a verb by infinitive and optional parameters.

        Since infinitive is no longer unique, additional parameters may be needed.
        If not specified, returns the first match found.
        """
        return await self.verb_repository.get_verb_by_infinitive(
            infinitive=infinitive,
            auxiliary=auxiliary,
            reflexive=reflexive,
            target_language_code=target_language_code,
        )

    async def get_verbs_by_infinitive(self, infinitive: str) -> List[Verb]:
        """Get all verb variants with the same infinitive."""
        return await self.verb_repository.get_verbs_by_infinitive(infinitive)

    async def get_all_verbs(
        self, limit: int = 100, target_language_code: Optional[str] = None
    ) -> List[Verb]:
        """Get all verbs, optionally filtered by language."""
        return await self.verb_repository.get_all_verbs(
            limit=limit, target_language_code=target_language_code
        )

    async def get_random_verb(
        self, target_language_code: str = "eng"
    ) -> Optional[Verb]:
        """Get a random verb."""
        verb = await self.verb_repository.get_random_verb(target_language_code)
        if verb:
            # Update last used timestamp
            await self.verb_repository.update_last_used(verb.id)
        return verb

    async def update_verb(self, verb_id: UUID, verb_data: VerbUpdate) -> Optional[Verb]:
        """Update a verb."""
        return await self.verb_repository.update_verb(verb_id, verb_data)

    async def delete_verb(self, verb_id: UUID) -> bool:
        """Delete a verb and all its conjugations."""
        # First get the verb to know its parameters
        verb = await self.get_verb(verb_id)
        if not verb:
            return False

        # Delete all conjugations for this verb first
        await self.verb_repository.delete_conjugations_by_verb(
            infinitive=verb.infinitive,
            auxiliary=verb.auxiliary.value,
            reflexive=verb.reflexive,
        )

        # Then delete the verb
        return await self.verb_repository.delete_verb(verb_id)

    # ===== CONJUGATION OPERATIONS =====

    async def get_conjugations(
        self, infinitive: str, auxiliary: str, reflexive: bool = False
    ) -> List[Conjugation]:
        """Get all conjugations for a verb."""
        return await self.verb_repository.get_conjugations(
            infinitive=infinitive, auxiliary=auxiliary, reflexive=reflexive
        )

    async def get_conjugations_by_verb_id(self, verb_id: UUID) -> List[Conjugation]:
        """Get conjugations by verb ID (backwards compatibility)."""
        verb = await self.get_verb(verb_id)
        if not verb:
            return []

        return await self.get_conjugations(
            infinitive=verb.infinitive,
            auxiliary=verb.auxiliary.value,
            reflexive=verb.reflexive,
        )

    async def create_conjugation(self, conjugation: ConjugationCreate) -> Conjugation:
        """Create a new conjugation."""
        return await self.verb_repository.create_conjugation(conjugation)

    async def update_conjugation(
        self,
        infinitive: str,
        auxiliary: str,
        reflexive: bool,
        tense: Tense,
        conjugation_data: ConjugationUpdate,
    ) -> Optional[Conjugation]:
        """Update a conjugation by verb parameters and tense."""
        return await self.verb_repository.update_conjugation_by_verb_and_tense(
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
        auxiliary: Optional[str] = None,
        reflexive: bool = False,
        target_language_code: str = "eng",
    ) -> Optional[VerbWithConjugations]:
        """Get a verb with all its conjugations."""
        # If auxiliary not specified, try to find any variant
        if auxiliary is None:
            verbs = await self.get_verbs_by_infinitive(infinitive)
            if not verbs:
                return None
            # Use the first variant found
            verb = verbs[0]
            auxiliary = verb.auxiliary.value

        return await self.verb_repository.get_verb_with_conjugations(
            infinitive=infinitive,
            auxiliary=auxiliary,
            reflexive=reflexive,
            target_language_code=target_language_code,
        )

    async def search_verbs(
        self,
        query: str,
        search_translation: bool = True,
        target_language_code: Optional[str] = None,
        limit: int = 20,
    ) -> List[Verb]:
        """Search verbs by infinitive or translation."""
        return await self.verb_repository.search_verbs(
            query=query,
            search_translation=search_translation,
            target_language_code=target_language_code,
            limit=limit,
        )

    # ===== AI INTEGRATION =====

    async def download_verb(
        self, requested_verb: str, target_language_code: str = "eng"
    ) -> Verb:
        """
        Download a verb using AI integration.

        This method fetches verb data from AI and creates/updates the verb and conjugations.
        """
        logger.info("Fetching verb %s", requested_verb)

        # Generate AI prompt
        verb_prompt = self.verb_prompt_generator.generate_verb_prompt(
            verb_infinitive=requested_verb
        )

        # Get AI response
        response = await self.openai_client.handle_request(verb_prompt)
        logger.debug("✅ AI Response: %s", response)

        try:
            response_json = json.loads(response)
        except json.JSONDecodeError as e:
            logger.error("Failed to parse AI response as JSON: %s", e)
            raise ValueError(f"Invalid AI response format: {e}")

        infinitive = response_json["infinitive"]
        auxiliary = response_json["auxiliary"]
        reflexive = response_json.get("reflexive", False)
        translation = response_json.get("translation", "")
        past_participle = response_json.get("past_participle", "")
        present_participle = response_json.get("present_participle", "")
        is_irregular = response_json.get("is_irregular", False)

        # Validate required fields
        if not past_participle:
            raise ValueError(
                f"AI response missing past_participle for verb: {infinitive}"
            )
        if not present_participle:
            raise ValueError(
                f"AI response missing present_participle for verb: {infinitive}"
            )

        # Determine classification from AI response or auxiliary
        classification = response_json.get("classification")
        if not classification:
            # Default classification based on infinitive ending
            if infinitive.endswith("er"):
                classification = "first_group"
            elif infinitive.endswith("ir"):
                classification = "second_group"
            else:
                classification = "third_group"

        # Check if verb exists
        existing_verb = await self.get_verb_by_infinitive(
            infinitive=infinitive,
            auxiliary=auxiliary,
            reflexive=reflexive,
            target_language_code=target_language_code,
        )

        if existing_verb:
            logger.info("Verb %s already exists, updating if needed", infinitive)
            verb = existing_verb

            # Update verb if needed
            update_data = VerbUpdate(
                translation=translation,
                past_participle=past_participle,
                present_participle=present_participle,
                classification=VerbClassification(classification),
                is_irregular=is_irregular,
            )
            updated_verb = await self.update_verb(verb.id, update_data)
            if updated_verb:
                verb = updated_verb
        else:
            logger.info("Creating new verb %s", infinitive)
            # Create new verb
            verb_data = VerbCreate(
                infinitive=infinitive,
                auxiliary=AuxiliaryType(auxiliary),
                reflexive=reflexive,
                target_language_code=target_language_code,
                translation=translation,
                past_participle=past_participle,
                present_participle=present_participle,
                classification=VerbClassification(classification),
                is_irregular=is_irregular,
            )
            verb = await self.create_verb(verb_data)

        # Process conjugations from AI response
        if "tenses" in response_json:
            await self._process_ai_conjugations(
                response_json["tenses"],
                infinitive=infinitive,
                auxiliary=auxiliary,
                reflexive=reflexive,
            )

        # Update last used timestamp
        await self.verb_repository.update_last_used(verb.id)

        return verb

    async def _process_ai_conjugations(
        self, ai_tenses: list, infinitive: str, auxiliary: str, reflexive: bool
    ) -> None:
        """Process conjugations from AI response."""
        for tense_data in ai_tenses:
            tense_name = tense_data["tense"]

            # Validate tense name
            try:
                tense = Tense(tense_name)
            except ValueError:
                logger.error("Unknown tense: %s", tense_name)
                continue

            conjugations_data = tense_data.get("conjugations", {})

            # Create conjugation data
            conjugation_data = ConjugationCreate(
                infinitive=infinitive,
                auxiliary=AuxiliaryType(auxiliary),
                reflexive=reflexive,
                tense=tense,
                first_person_singular=conjugations_data.get("first_person_singular"),
                second_person_singular=conjugations_data.get("second_person_singular"),
                third_person_singular=conjugations_data.get("third_person_singular"),
                first_person_plural=conjugations_data.get("first_person_plural"),
                second_person_formal=conjugations_data.get("second_person_formal"),
                third_person_plural=conjugations_data.get("third_person_plural"),
            )

            # Check if conjugation already exists
            existing_conjugation = await self.verb_repository.get_conjugation(
                infinitive=infinitive,
                auxiliary=auxiliary,
                reflexive=reflexive,
                tense=tense,
            )

            if existing_conjugation:
                # Update existing conjugation
                update_data = ConjugationUpdate(
                    **conjugation_data.model_dump(
                        exclude={"infinitive", "auxiliary", "reflexive", "tense"}
                    )
                )
                await self.verb_repository.update_conjugation_by_verb_and_tense(
                    infinitive=infinitive,
                    auxiliary=auxiliary,
                    reflexive=reflexive,
                    tense=tense,
                    conjugation=update_data,
                )
                logger.info("Updated conjugation: %s - %s", infinitive, tense_name)
            else:
                # Create new conjugation
                await self.verb_repository.create_conjugation(conjugation_data)
                logger.info("Created conjugation: %s - %s", infinitive, tense_name)
