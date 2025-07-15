"""Verb repository for data access with updated Supabase schema."""

from typing import List, Optional
from uuid import UUID

from supabase import Client

from src.schemas.verbs import (
    Verb,
    VerbCreate,
    VerbUpdate,
    VerbWithConjugations,
    Conjugation,
    ConjugationCreate,
    ConjugationUpdate,
    Tense,
)


class VerbRepository:
    def __init__(self, client: Client):
        self.client = client

    async def create_verb(self, verb: VerbCreate) -> Verb:
        """Create a new verb."""
        verb_dict = verb.model_dump(
            mode="json"
        )  # Use mode="json" to serialize enums correctly
        result = await self.client.table("verbs").insert(verb_dict).execute()

        if result.data:
            return Verb.model_validate(result.data[0])
        raise Exception("Failed to create verb")

    async def delete_verb(self, verb_id: UUID) -> bool:
        """Delete a verb."""
        result = (
            await self.client.table("verbs").delete().eq("id", str(verb_id)).execute()
        )
        return len(result.data) > 0

    async def get_all_verbs(
        self, limit: int = 100, target_language_code: Optional[str] = None
    ) -> List[Verb]:
        """Get all verbs, optionally filtered by language."""
        query = self.client.table("verbs").select("*").limit(limit)

        if target_language_code:
            query = query.eq("target_language_code", target_language_code)

        result = await query.execute()
        return [Verb.model_validate(verb) for verb in result.data]

    async def get_random_verb(
        self, target_language_code: str = "eng"
    ) -> Optional[Verb]:
        """
        Get a random verb using the database function.

        Uses the get_random_verb_simple() function defined in the schema.
        """
        result = await self.client.rpc(
            "get_random_verb_simple", {"p_target_language": target_language_code}
        ).execute()

        if result.data:
            return Verb.model_validate(result.data[0])
        return None

    async def get_verb(self, verb_id: UUID) -> Optional[Verb]:
        """Get a verb by ID."""
        result = (
            await self.client.table("verbs")
            .select("*")
            .eq("id", str(verb_id))
            .execute()
        )

        if result.data:
            return Verb.model_validate(result.data[0])
        return None

    async def get_verb_by_infinitive(
        self,
        infinitive: str,
        auxiliary: Optional[str] = None,
        reflexive: Optional[bool] = None,
        target_language_code: Optional[str] = None,
    ) -> Optional[Verb]:
        """
        Get a verb by infinitive and optional parameters.

        Since infinitive is no longer unique, we may need additional
        parameters to identify the specific verb variant.
        """
        query = self.client.table("verbs").select("*").eq("infinitive", infinitive)

        if auxiliary:
            query = query.eq("auxiliary", auxiliary)
        if reflexive is not None:
            query = query.eq("reflexive", reflexive)
        if target_language_code:
            query = query.eq("target_language_code", target_language_code)

        result = await query.execute()

        if result.data:
            return Verb.model_validate(result.data[0])
        return None

    async def get_verbs_by_infinitive(self, infinitive: str) -> List[Verb]:
        """Get all verbs with the same infinitive (different auxiliary/reflexive combinations)."""
        result = (
            await self.client.table("verbs")
            .select("*")
            .eq("infinitive", infinitive)
            .execute()
        )
        return [Verb.model_validate(verb) for verb in result.data]

    async def get_verb_with_conjugations(
        self,
        infinitive: str,
        auxiliary: str,
        reflexive: bool = False,
        target_language_code: str = "eng",
    ) -> Optional[VerbWithConjugations]:
        """Get a verb with all its conjugations."""
        verb = await self.get_verb_by_infinitive(
            infinitive=infinitive,
            auxiliary=auxiliary,
            reflexive=reflexive,
            target_language_code=target_language_code,
        )
        if not verb:
            return None

        conjugations = await self.get_conjugations(
            infinitive=verb.infinitive,
            auxiliary=verb.auxiliary.value,
            reflexive=verb.reflexive,
        )

        return VerbWithConjugations(**verb.model_dump(), conjugations=conjugations)

    async def search_verbs(
        self,
        query: str,
        search_translation: bool = True,
        target_language_code: Optional[str] = None,
        limit: int = 20,
    ) -> List[Verb]:
        """
        Search verbs by infinitive or translation.

        Args:
            query: Search term
            search_translation: Whether to search in translation field
            target_language_code: Filter by language
            limit: Maximum number of results
        """
        # Build search query
        supabase_query = self.client.table("verbs").select("*")

        if search_translation:
            # Search in both infinitive and translation
            supabase_query = supabase_query.or_(
                f"infinitive.ilike.%{query}%,translation.ilike.%{query}%"
            )
        else:
            # Search only in infinitive
            supabase_query = supabase_query.ilike("infinitive", f"%{query}%")

        if target_language_code:
            supabase_query = supabase_query.eq(
                "target_language_code", target_language_code
            )

        supabase_query = supabase_query.limit(limit)

        result = await supabase_query.execute()
        return [Verb.model_validate(v) for v in result.data]

    async def update_last_used(self, verb_id: UUID) -> bool:
        """Update the last_used_at timestamp for a verb."""
        result = (
            await self.client.table("verbs")
            .update({"last_used_at": "now()"})
            .eq("id", str(verb_id))
            .execute()
        )
        return len(result.data) > 0

    async def update_verb(self, verb_id: UUID, verb: VerbUpdate) -> Optional[Verb]:
        """Update a verb."""
        verb_dict = verb.model_dump(
            exclude_unset=True, mode="json"
        )  # Add mode="json" for enum serialization
        result = (
            await self.client.table("verbs")
            .update(verb_dict)
            .eq("id", str(verb_id))
            .execute()
        )

        if result.data:
            return Verb.model_validate(result.data[0])
        return None

    async def upsert_verb(self, verb_data: VerbCreate) -> Verb:
        """
        Creates a new verb or updates an existing one based on the infinitive.
        """
        existing_verb = await self.get_verb_by_infinitive(
            infinitive=verb_data.infinitive,
            auxiliary=verb_data.auxiliary.value if verb_data.auxiliary else None,
            reflexive=verb_data.reflexive,
            target_language_code=verb_data.target_language_code,
        )

        if existing_verb:
            update_data = VerbUpdate.model_validate(verb_data.model_dump())
            updated_verb = await self.update_verb(existing_verb.id, update_data)
            if updated_verb:
                return updated_verb
            return existing_verb  # Should not happen in normal flow

        return await self.create_verb(verb_data)

    async def create_conjugation(self, conjugation: ConjugationCreate) -> Conjugation:
        """Create a new conjugation."""
        conj_dict = conjugation.model_dump(
            mode="json"
        )  # Use mode="json" to serialize enums correctly

        result = await self.client.table("conjugations").insert(conj_dict).execute()

        if result.data:
            return Conjugation.model_validate(result.data[0])
        raise Exception("Failed to create conjugation")

    async def delete_conjugations_by_verb(
        self, infinitive: str, auxiliary: str, reflexive: bool
    ) -> bool:
        """Delete all conjugations for a given verb."""
        result = (
            await self.client.table("conjugations")
            .delete()
            .eq("infinitive", infinitive)
            .eq("auxiliary", auxiliary)
            .eq("reflexive", reflexive)
            .execute()
        )
        return len(result.data) > 0

    async def get_conjugation(
        self, infinitive: str, auxiliary: str, reflexive: bool, tense: Tense
    ) -> Optional[Conjugation]:
        """Get a specific conjugation by verb parameters and tense."""
        result = (
            await self.client.table("conjugations")
            .select("*")
            .eq("infinitive", infinitive)
            .eq("auxiliary", auxiliary)
            .eq("reflexive", reflexive)
            .eq("tense", tense.value)
            .execute()
        )

        if result.data:
            return Conjugation.model_validate(result.data[0])
        return None

    async def get_conjugation_by_verb_and_tense(
        self, infinitive: str, auxiliary: str, reflexive: bool, tense: Tense
    ) -> Optional[Conjugation]:
        """Get a specific conjugation by verb parameters and tense."""
        result = (
            await self.client.table("conjugations")
            .select("*")
            .eq("infinitive", infinitive)
            .eq("auxiliary", auxiliary)
            .eq("reflexive", reflexive)
            .eq("tense", tense.value)
            .execute()
        )

        if result.data:
            return Conjugation.model_validate(result.data[0])
        return None

    async def get_conjugations(
        self, infinitive: str, auxiliary: str, reflexive: bool = False
    ) -> List[Conjugation]:
        """
        Get all conjugations for a verb identified by infinitive, auxiliary, and reflexive.

        Updated to use the new schema's compound key approach.
        """
        result = (
            await self.client.table("conjugations")
            .select("*")
            .eq("infinitive", infinitive)
            .eq("auxiliary", auxiliary)
            .eq("reflexive", reflexive)
            .execute()
        )
        return [Conjugation.model_validate(conj) for conj in result.data]

    async def update_conjugation_by_verb_and_tense(
        self,
        infinitive: str,
        auxiliary: str,
        reflexive: bool,
        tense: Tense,
        conjugation: ConjugationUpdate,
    ) -> Optional[Conjugation]:
        """Update a conjugation by verb parameters and tense."""
        conj_dict = conjugation.model_dump(
            exclude_unset=True, mode="json"
        )  # Use mode="json" for enum serialization

        result = (
            await self.client.table("conjugations")
            .update(conj_dict)
            .eq("infinitive", infinitive)
            .eq("auxiliary", auxiliary)
            .eq("reflexive", reflexive)
            .eq("tense", tense.value)
            .execute()
        )
        if result.data:
            return Conjugation.model_validate(result.data[0])
        return None

    async def upsert_conjugation(self, conjugation_data: ConjugationCreate) -> None:
        """Upsert a conjugation."""
        existing = await self.get_conjugation(
            conjugation_data.infinitive,
            conjugation_data.auxiliary.value,
            conjugation_data.reflexive,
            conjugation_data.tense,
        )
        if existing:
            update_payload = ConjugationUpdate.model_validate(
                conjugation_data.model_dump(
                    mode="json"
                )  # Use mode="json" for enum serialization
            )
            await self.update_conjugation_by_verb_and_tense(
                conjugation_data.infinitive,
                conjugation_data.auxiliary.value,
                conjugation_data.reflexive,
                conjugation_data.tense,
                update_payload,
            )
        else:
            await self.create_conjugation(conjugation_data)
