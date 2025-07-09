"""Verb business logic service."""
import json
import logging
from supabase import Client
from typing import Optional, List

# Import path setup for direct execution
import sys
from pathlib import Path

# Get paths for imports
src_dir = Path(__file__).parent.parent
sys.path.insert(0, str(src_dir))

from repositories.verb_repository import VerbRepository
from schemas.verb import Verb, VerbCreate, Conjugation, ConjugationCreate, Tense
from clients.supabase import get_supabase_client


class VerbService:
    """Service for verb-related business logic."""
    
    def __init__(self, client: Optional[Client] = None):
        self.client = client or get_supabase_client()
        self.repository = VerbRepository(self.client)

    async def get_verb(self, infinitive: str) -> Optional[Verb]:
        """Get verb by infinitive."""
        return await self.repository.get_by_infinitive(infinitive)

    async def get_verb_by_id(self, verb_id: int) -> Optional[Verb]:
        """Get verb by ID."""
        return await self.repository.get_by_id(verb_id)

    async def get_random_verb(self) -> Optional[Verb]:
        """Get a random verb."""
        return await self.repository.get_random_verb()

    async def create_verb(self, infinitive: str, auxiliary: str) -> Verb:
        """Create a new verb."""
        verb_create = VerbCreate(infinitive=infinitive, auxiliary=auxiliary)
        return await self.repository.create(verb_create)

    async def get_conjugations(self, verb_id: int) -> List[Conjugation]:
        """Get all conjugations for a verb."""
        return await self.repository.get_conjugations(verb_id)

    async def download_verb_with_ai(self, infinitive: str, openai_client) -> Verb:
        """
        Download/create verb with AI assistance.
        
        This replaces the current download_verb function by integrating with OpenAI
        to generate verb information and conjugations, then storing via Supabase.
        """
        # Import the prompt generation function
        from cli.verbs.prompts import generate_verb_prompt
        
        logging.info("Fetching verb %s.", infinitive)
        
        # Get AI response
        response: str = await openai_client.handle_request(prompt=generate_verb_prompt(verb_infinitive=infinitive))
        response_json = json.loads(response)
        ai_infinitive: str = response_json["infinitive"]
        
        logging.info("Saving verb %s", ai_infinitive)
        
        # Check if verb already exists
        existing_verb = await self.get_verb(ai_infinitive)
        
        if existing_verb:
            logging.info("The verb %s already exists and will be updated if needed.", ai_infinitive)
            # Update existing verb
            verb = existing_verb
            # TODO: Update logic if needed
        else:
            logging.info("The verb %s does not yet exist in the database.", ai_infinitive)
            # Create new verb
            verb = await self.create_verb(
                infinitive=ai_infinitive,
                auxiliary=response_json["auxiliary"]
            )
        
        # Process each tense from the AI response
        for response_tense in response_json["tenses"]:
            tense_name = response_tense["tense"]
            
            # Map tense name to our enum
            tense_mapping = {
                "present": Tense.PRESENT,
                "passe_compose": Tense.PASSE_COMPOSE, 
                "imparfait": Tense.IMPARFAIT,
                "future_simple": Tense.FUTURE_SIMPLE,
                "participle": Tense.PARTICIPLE
            }
            
            tense = tense_mapping.get(tense_name)
            if not tense:
                logging.warning("Unknown tense: %s", tense_name)
                continue
            
            # Check if conjugation already exists
            existing_conjugations = await self.get_conjugations(verb.id)
            existing_conjugation = next(
                (c for c in existing_conjugations if c.tense == tense), 
                None
            )
            
            if existing_conjugation:
                logging.info("A verb conjugation for %s, %s already exists and will be updated.", ai_infinitive, tense_name)
                # TODO: Update logic if needed
                continue
            else:
                logging.info("Verb conjugations are missing for %s, %s and will be added.", ai_infinitive, tense_name)
            
            # Create conjugation data structure
            conjugation_data = {
                "verb_id": verb.id,
                "tense": tense,
                "infinitive": ai_infinitive,
                "first_person_singular": None,
                "second_person_singular": None,
                "third_person_singular": None,
                "first_person_plural": None,
                "second_person_formal": None,
                "third_person_plural": None,
            }
            
            # Map AI response to our conjugation fields
            for response_conjugation in response_tense["conjugations"]:
                pronoun = response_conjugation["pronoun"]
                conjugated_verb = response_conjugation["verb"]
                
                match pronoun:
                    case "je" | "j'" | "j":
                        conjugation_data["first_person_singular"] = conjugated_verb
                    case "tu":
                        conjugation_data["second_person_singular"] = conjugated_verb
                    case "il/elle/on" | "il" | "elle" | "on":
                        conjugation_data["third_person_singular"] = conjugated_verb
                    case "nous":
                        conjugation_data["first_person_plural"] = conjugated_verb
                    case "vous":
                        conjugation_data["second_person_formal"] = conjugated_verb
                    case "ils/elles" | "ils" | "elles":
                        conjugation_data["third_person_plural"] = conjugated_verb
                    case "-":
                        # For participles, set all forms to the same value
                        conjugation_data.update({
                            "first_person_singular": conjugated_verb,
                            "second_person_singular": conjugated_verb,
                            "third_person_singular": conjugated_verb,
                            "first_person_plural": conjugated_verb,
                            "second_person_formal": conjugated_verb,
                            "third_person_plural": conjugated_verb,
                        })
            
            # Create the conjugation
            conjugation_create = ConjugationCreate(**conjugation_data)
            await self.repository.create_conjugation(conjugation_create)
            logging.info("Added conjugation for %s with tense %s.", ai_infinitive, tense_name)
        
        return verb

    async def download_verb(self, infinitive: str) -> Verb:
        """
        Download/create verb with AI assistance.
        
        This will eventually replace the current download_verb function
        by integrating with OpenAI to generate verb information and conjugations.
        """
        # Check if verb already exists
        existing_verb = await self.get_verb(infinitive)
        if existing_verb:
            return existing_verb

        # TODO: Integrate with OpenAI client to generate verb info
        # For now, create with default auxiliary
        auxiliary = "avoir"  # Default auxiliary, could be improved with AI
        
        return await self.create_verb(infinitive, auxiliary)

    async def get_all_verbs(self, limit: int = 100, offset: int = 0) -> List[Verb]:
        """Get all verbs with pagination."""
        return await self.repository.get_all(limit=limit, offset=offset)


# Dependency injection helpers for FastAPI
def get_verb_service(client: Optional[Client] = None) -> VerbService:
    """Get verb service instance."""
    return VerbService(client) 