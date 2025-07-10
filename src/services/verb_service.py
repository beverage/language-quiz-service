"""Verb service for business logic."""

import json
import logging
from typing import List, Optional

from clients.openai_client import OpenAIClient
from repositories.verb_repository import VerbRepository
from prompts.verb_prompts import VerbPromptGenerator
from schemas.verb import VerbCreate, Verb, Conjugation, ConjugationCreate, Tense

logger = logging.getLogger(__name__)


class VerbService:
    def __init__(
        self,
        openai_client: OpenAIClient = None,
        verb_repository: VerbRepository = None,
        prompt_generator: VerbPromptGenerator = None,
    ):
        """Initialize the verb service with injectable dependencies."""
        self.openai_client = openai_client or OpenAIClient()
        self.verb_prompt_generator = prompt_generator or VerbPromptGenerator()
        self.verb_repository = verb_repository or VerbRepository()

    async def create_verb(self, verb_data: VerbCreate) -> Verb:
        """Create a new verb."""
        return await self.verb_repository.create_verb(verb_data)

    async def get_verb(self, verb_id: int) -> Optional[Verb]:
        """Get a verb by ID."""
        return await self.verb_repository.get_verb(verb_id)

    async def get_verb_by_infinitive(self, infinitive: str) -> Optional[Verb]:
        """Get a verb by infinitive."""
        return await self.verb_repository.get_verb_by_infinitive(infinitive)

    async def get_all_verbs(self, limit: int = 100) -> List[Verb]:
        """Get all verbs."""
        return await self.verb_repository.get_all_verbs(limit=limit)

    async def get_random_verb(self) -> Optional[Verb]:
        """Get a random verb."""
        return await self.verb_repository.get_random_verb()

    async def update_verb(self, verb_id: int, verb_data: VerbCreate) -> Optional[Verb]:
        """Update a verb."""
        return await self.verb_repository.update_verb(verb_id, verb_data)

    async def delete_verb(self, verb_id: int) -> bool:
        """Delete a verb."""
        return await self.verb_repository.delete_verb(verb_id)

    async def get_conjugations(self, verb_id: int) -> List[Conjugation]:
        """Get conjugations for a verb."""
        return await self.verb_repository.get_conjugations(verb_id)

    async def download_verb(self, requested_verb: str) -> Verb:
        """Download a verb using AI integration."""
        logger.info("Fetching verb %s.", requested_verb)

        client = OpenAIClient()
        verb_prompt = self.verb_prompt_generator.generate_verb_prompt(
            verb_infinitive=requested_verb
        )

        # Get AI response
        response = await client.handle_request(verb_prompt)
        logger.debug(f"✅ Response: {response}")
        response_json = json.loads(response)

        infinitive = response_json["infinitive"]

        # Check if verb exists
        existing_verb = await self.get_verb_by_infinitive(requested_verb)

        if existing_verb:
            logger.info(
                "The verb %s already exists and will be updated if needed.", infinitive
            )
            verb = existing_verb
        else:
            logger.info("The verb %s does not yet exist in the database.", infinitive)
            # Create new verb
            verb_data = VerbCreate(
                infinitive=infinitive,
                auxiliary=response_json["auxiliary"],
                reflexive=response_json["reflexive"],
            )
            verb = await self.create_verb(verb_data)

        existing_conjugations = await self.get_conjugations(verb.id)

        # Process tenses/conjugations
        for response_tense in response_json["tenses"]:
            tense_name = response_tense["tense"]

            if tense_name not in (t.value for t in Tense):
                logger.error(f"❌ Unknown tense: {tense_name}")
                continue

            tense = Tense(tense_name)
            logger.debug(f"✅ Tense: {tense}")

            response_conjugations = response_tense["conjugations"]

            conjugation_data = {
                "verb_id": verb.id,
                "tense": tense_name,
                "infinitive": infinitive,
                "first_person_singular": response_conjugations.get(
                    "first_person_singular", ""
                ),
                "second_person_singular": response_conjugations.get(
                    "second_person_singular", ""
                ),
                "third_person_singular": response_conjugations.get(
                    "third_person_singular", ""
                ),
                "first_person_plural": response_conjugations.get(
                    "first_person_plural", ""
                ),
                "second_person_formal": response_conjugations.get(
                    "second_person_formal", ""
                ),
                "third_person_plural": response_conjugations.get(
                    "third_person_plural", ""
                ),
            }

            conjugation_create = ConjugationCreate(**conjugation_data)

            existing_conjugation = next(
                (c for c in existing_conjugations if c.tense == tense), None
            )

            if existing_conjugation:
                await self.verb_repository.update_conjugation(
                    existing_conjugation.id, conjugation_create
                )
                logger.info(f"Updated conjugation: {conjugation_create}")
            else:
                await self.verb_repository.create_conjugation(conjugation_create)
                logger.info(f"Created conjugation: {conjugation_create}")

        return verb
