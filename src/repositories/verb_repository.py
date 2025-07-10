"""Verb repository for data access."""

from typing import List, Optional
from supabase import Client
from schemas.verb import Verb, VerbCreate, Conjugation, ConjugationCreate
from clients.supabase import get_supabase_client


class VerbRepository:
    def __init__(self, client: Optional[Client] = None):
        self.client = client or get_supabase_client()

    async def create_verb(self, verb: VerbCreate) -> Verb:
        """Create a new verb."""
        verb_dict = verb.model_dump()
        result = self.client.table("verbs").insert(verb_dict).execute()

        if result.data:
            return Verb(**result.data[0])
        raise Exception("Failed to create verb")

    async def get_verb(self, verb_id: int) -> Optional[Verb]:
        """Get a verb by ID."""
        result = self.client.table("verbs").select("*").eq("id", verb_id).execute()

        if result.data:
            return Verb(**result.data[0])
        return None

    async def get_verb_by_infinitive(self, infinitive: str) -> Optional[Verb]:
        """Get a verb by infinitive."""
        result = (
            self.client.table("verbs")
            .select("*")
            .eq("infinitive", infinitive)
            .execute()
        )

        if result.data:
            return Verb(**result.data[0])
        return None

    async def get_all_verbs(self, limit: int = 100) -> List[Verb]:
        """Get all verbs."""
        result = self.client.table("verbs").select("*").limit(limit).execute()
        return [Verb(**verb) for verb in result.data]

    async def get_random_verb(self) -> Optional[Verb]:
        """Get a random verb."""
        # Note: This could be improved with better random selection
        result = self.client.table("verbs").select("*").limit(50).execute()

        if result.data:
            import random

            return Verb(**random.choice(result.data))
        return None

    async def update_verb(self, verb_id: int, verb: VerbCreate) -> Optional[Verb]:
        """Update a verb."""
        verb_dict = verb.model_dump(exclude_unset=True)
        result = (
            self.client.table("verbs").update(verb_dict).eq("id", verb_id).execute()
        )

        if result.data:
            return Verb(**result.data[0])
        return None

    async def delete_verb(self, verb_id: int) -> bool:
        """Delete a verb."""
        result = self.client.table("verbs").delete().eq("id", verb_id).execute()
        return len(result.data) > 0

    async def get_conjugations(self, verb_id: int) -> List[Conjugation]:
        """Get all conjugations for a verb."""
        result = (
            self.client.table("conjugations")
            .select("*")
            .eq("verb_id", verb_id)
            .execute()
        )
        return [Conjugation(**conj) for conj in result.data]

    async def create_conjugation(self, conjugation: ConjugationCreate) -> Conjugation:
        """Create a new conjugation."""
        conj_dict = conjugation.model_dump()

        # Convert enum to string value for storage
        if hasattr(conj_dict["tense"], "value"):
            conj_dict["tense"] = conj_dict["tense"].value

        result = self.client.table("conjugations").insert(conj_dict).execute()

        if result.data:
            return Conjugation(**result.data[0])
        raise Exception("Failed to create conjugation")

    async def update_conjugation(
        self, conjugation_id: int, conjugation: ConjugationCreate
    ) -> Optional[Conjugation]:
        """Update a conjugation."""
        conj_dict = conjugation.model_dump(exclude_unset=True)

        # Convert enum to string value for storage
        if "tense" in conj_dict and hasattr(conj_dict["tense"], "value"):
            conj_dict["tense"] = conj_dict["tense"].value

        result = (
            self.client.table("conjugations")
            .update(conj_dict)
            .eq("id", conjugation_id)
            .execute()
        )

        if result.data:
            return Conjugation(**result.data[0])
        return None

    async def delete_conjugation(self, conjugation_id: int) -> bool:
        """Delete a conjugation."""
        result = (
            self.client.table("conjugations")
            .delete()
            .eq("id", conjugation_id)
            .execute()
        )
        return len(result.data) > 0
