"""Verb service for business logic."""

import json
import logging
from typing import List, Optional

from repositories.verb_repository import VerbRepository
from schemas.verb import VerbCreate, Verb, ConjugationCreate, Tense


class VerbService:
    def __init__(self):
        self.verb_repository = VerbRepository()

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

    async def get_conjugations(self, verb_id: int):
        """Get conjugations for a verb."""
        return await self.verb_repository.get_conjugations(verb_id)

    async def download_verb_with_ai(self, requested_verb: str, openai_client):
        """Download a verb using AI integration."""

        # Import here to avoid path issues
        import sys
        from pathlib import Path

        # Add CLI path
        cli_path = Path(__file__).parent.parent / "cli"
        sys.path.insert(0, str(cli_path))

        from verbs.prompts import generate_verb_prompt

        logging.info("Fetching verb %s.", requested_verb)

        # Get AI response
        response = await openai_client.handle_request(
            prompt=generate_verb_prompt(verb_infinitive=requested_verb)
        )
        response_json = json.loads(response)
        infinitive = response_json["infinitive"]

        # Check if verb exists
        existing_verb = await self.get_verb_by_infinitive(requested_verb)

        if existing_verb:
            logging.info(
                "The verb %s already exists and will be updated if needed.", infinitive
            )
            verb = existing_verb
        else:
            logging.info("The verb %s does not yet exist in the database.", infinitive)
            # Create new verb
            verb_data = VerbCreate(
                infinitive=infinitive, auxiliary=response_json["auxiliary"]
            )
            verb = await self.create_verb(verb_data)

        # Process tenses/conjugations
        for response_tense in response_json["tenses"]:
            tense_name = response_tense["tense"]

            # Map tense names to enum values (using correct enum format)
            tense_mapping = {
                "present": Tense.PRESENT,
                "imparfait": Tense.IMPARFAIT,
                "future_simple": Tense.FUTURE_SIMPLE,
                "passe_compose": Tense.PASSE_COMPOSE,
                "participle": Tense.PARTICIPLE,
                # Handle AI variations
                "passecompose": Tense.PASSE_COMPOSE,
                "futuresimple": Tense.FUTURE_SIMPLE,
            }

            if tense_name not in tense_mapping:
                logging.warning(f"Unknown tense: {tense_name}")
                continue

            tense = tense_mapping[tense_name]

            # Check if conjugation exists
            existing_conjugations = await self.get_conjugations(verb.id)
            existing_conjugation = next(
                (c for c in existing_conjugations if c.tense == tense), None
            )

            if existing_conjugation:
                logging.info(
                    "A verb conjugation for %s, %s already exists and will be updated.",
                    infinitive,
                    tense.value,
                )
            else:
                logging.info(
                    "Verb conjugations are missing for %s, %s and will be added.",
                    infinitive,
                    tense.value,
                )

            # Build conjugation data
            conjugation_data = {
                "verb_id": verb.id,
                "tense": tense,
                "infinitive": infinitive,  # Add infinitive field
                "first_person_singular": "",
                "second_person_singular": "",
                "third_person_singular": "",
                "first_person_plural": "",
                "second_person_formal": "",
                "third_person_plural": "",
            }

            # Process each conjugation response
            for response_conjugation in response_tense["conjugations"]:
                pronoun = response_conjugation["pronoun"]
                verb_form = response_conjugation["verb"]

                # Map pronouns to conjugation fields
                match pronoun:
                    case "je" | "j'" | "j":
                        conjugation_data["first_person_singular"] = verb_form
                    case "tu":
                        conjugation_data["second_person_singular"] = verb_form
                    case "il/elle/on" | "il" | "elle" | "on":
                        conjugation_data["third_person_singular"] = verb_form
                    case "nous":
                        conjugation_data["first_person_plural"] = verb_form
                    case "vous":
                        conjugation_data["second_person_formal"] = verb_form
                    case "ils/elles" | "ils" | "elles":
                        conjugation_data["third_person_plural"] = verb_form
                    case "-":  # Participle case - set all forms to same value
                        conjugation_data.update(
                            {
                                "first_person_singular": verb_form,
                                "second_person_singular": verb_form,
                                "third_person_singular": verb_form,
                                "first_person_plural": verb_form,
                                "second_person_formal": verb_form,
                                "third_person_plural": verb_form,
                            }
                        )

            # Create or update conjugation
            conjugation_create = ConjugationCreate(**conjugation_data)

            if existing_conjugation:
                await self.verb_repository.update_conjugation(
                    existing_conjugation.id, conjugation_create
                )
            else:
                await self.verb_repository.create_conjugation(conjugation_create)
                logging.info(
                    "Added conjugation for %s with tense %s.", infinitive, tense.value
                )

        return verb
