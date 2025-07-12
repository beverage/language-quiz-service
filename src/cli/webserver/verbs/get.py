"""
Webserver verb endpoints - MIGRATED.

Migrated to use Supabase VerbService instead of SQLAlchemy.
"""

from src.services.verb_service import VerbService


async def get_verb_and_conjugations(infinitive: str):
    """Get verb and its conjugations - migrated to use VerbService."""
    verb_service = VerbService()

    # Get verb with conjugations
    verb = await verb_service.get_verb_by_infinitive(infinitive)
    if not verb:
        return None

    # Get conjugations for this verb
    conjugations = await verb_service.get_conjugations_by_verb_id(verb.id)

    # Format conjugations for API response
    formatted_conjugations = []
    for conj in conjugations:
        conjugation = {
            "tense": conj.tense.value,  # Convert enum to string
            "infinitive": conj.infinitive,
        }

        # Add all conjugation fields, replacing underscores with spaces
        conjugation_fields = [
            "first_person_singular",
            "second_person_singular",
            "third_person_singular",
            "first_person_plural",
            "second_person_formal",
            "third_person_plural",
        ]

        for field in conjugation_fields:
            value = getattr(conj, field, None)
            if value is not None:
                conjugation[field] = value.replace("_", " ")

        formatted_conjugations.append(conjugation)

    return {
        "infinitive": verb.infinitive,
        "auxiliary": verb.auxiliary,
        "conjugations": formatted_conjugations,
    }
