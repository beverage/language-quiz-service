"""Helper functions for sentence prompt generation."""

import random

from src.schemas.sentences import Pronoun
from src.schemas.verbs import Tense, Verb


def get_pronoun_display(pronoun: str) -> str:
    """Convert pronoun enum to French display format.

    Args:
        pronoun: Pronoun enum value as string

    Returns:
        French pronoun display string
    """
    pronoun_map = {
        "first_person": "je",
        "second_person": "tu",
        "third_person": "il/elle/on",
        "first_person_plural": "nous",
        "second_person_plural": "vous",
        "third_person_plural": "ils/elles",
    }
    return pronoun_map.get(pronoun, pronoun)


def get_conjugation_pair(
    pronoun: Pronoun,
    tense: Tense,
    verb: Verb,
    conjugations: list,
    correct: bool = True,
) -> tuple[str, str, str]:
    """Get a pronoun/conjugation/auxiliary triplet.

    Args:
        pronoun: The pronoun to use (already selected externally)
        tense: The tense to use (already selected externally)
        verb: The verb being conjugated
        conjugations: List of conjugation objects for the verb
        correct: If True, return matching pair. If False, return mismatched pair.

    Returns:
        (pronoun_display, conjugation_form, auxiliary) where:
        - If correct=True: conjugation matches the pronoun
        - If correct=False: conjugation is for a DIFFERENT pronoun

    Raises:
        ValueError: If conjugation for tense not found or conjugation form is missing
    """
    # Validate inputs
    if not conjugations:
        raise ValueError(f"No conjugations provided for verb {verb.infinitive}")

    # Find the conjugation for this tense
    tense_conjugation = next((c for c in conjugations if c.tense == tense), None)
    if not tense_conjugation:
        raise ValueError(
            f"No conjugation found for verb '{verb.infinitive}' in tense '{tense.value}'"
        )

    # Get pronoun display and handle multiple forms (e.g., "il/elle/on")
    pronoun_display_raw = get_pronoun_display(pronoun.value)
    if "/" in pronoun_display_raw:
        # Randomly select one form
        pronoun_forms = pronoun_display_raw.split("/")
        pronoun_display = random.choice(pronoun_forms)
    else:
        pronoun_display = pronoun_display_raw

    # Map pronouns to conjugation fields
    pronoun_to_field = {
        Pronoun.FIRST_PERSON: tense_conjugation.first_person_singular,
        Pronoun.SECOND_PERSON: tense_conjugation.second_person_singular,
        Pronoun.THIRD_PERSON: tense_conjugation.third_person_singular,
        Pronoun.FIRST_PERSON_PLURAL: tense_conjugation.first_person_plural,
        Pronoun.SECOND_PERSON_PLURAL: tense_conjugation.second_person_plural,
        Pronoun.THIRD_PERSON_PLURAL: tense_conjugation.third_person_plural,
    }

    if correct:
        # Return matching pronoun/conjugation
        conjugation_form = pronoun_to_field.get(pronoun)
    else:
        # Return mismatched pair - pick a different pronoun's conjugation
        available_pronouns = [p for p in Pronoun if p != pronoun]
        if not available_pronouns:
            raise ValueError(
                "Cannot create incorrect pair: no alternative pronouns available"
            )
        wrong_pronoun = random.choice(available_pronouns)
        conjugation_form = pronoun_to_field.get(wrong_pronoun)

    # Validate we got a conjugation
    if not conjugation_form:
        raise ValueError(
            f"Missing conjugation form for verb '{verb.infinitive}', "
            f"tense '{tense.value}', pronoun '{pronoun.value}'"
        )

    # Get auxiliary
    auxiliary = verb.auxiliary.value

    return pronoun_display, conjugation_form, auxiliary
