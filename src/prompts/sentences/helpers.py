"""Helper functions for sentence prompt generation."""

import random

from src.prompts.sentences.templates import COMPOUND_TENSES
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
        pronoun: The pronoun to use
        tense: The tense to use
        verb: The verb being conjugated
        conjugations: List of conjugation objects for the verb
        correct: If True, return correct form. If False, return a different form.

    Returns:
        (pronoun_display, conjugation_form, auxiliary) where:
        - If correct=True: conjugation matches the pronoun
        - If correct=False: conjugation is a DIFFERENT form (guaranteed wrong)

    Raises:
        ValueError: If conjugation for tense not found or no wrong form available
    """
    if not conjugations:
        raise ValueError(f"No conjugations provided for verb {verb.infinitive}")

    # Find the conjugation for this tense
    tense_conjugation = next((c for c in conjugations if c.tense == tense), None)
    if not tense_conjugation:
        raise ValueError(
            f"No conjugation found for verb '{verb.infinitive}' in tense '{tense.value}'"
        )

    # Get all forms for this tense
    all_forms = {
        "first_person_singular": tense_conjugation.first_person_singular,
        "second_person_singular": tense_conjugation.second_person_singular,
        "third_person_singular": tense_conjugation.third_person_singular,
        "first_person_plural": tense_conjugation.first_person_plural,
        "second_person_plural": tense_conjugation.second_person_plural,
        "third_person_plural": tense_conjugation.third_person_plural,
    }

    # Map pronoun enum to field name
    pronoun_to_field = {
        Pronoun.FIRST_PERSON: "first_person_singular",
        Pronoun.SECOND_PERSON: "second_person_singular",
        Pronoun.THIRD_PERSON: "third_person_singular",
        Pronoun.FIRST_PERSON_PLURAL: "first_person_plural",
        Pronoun.SECOND_PERSON_PLURAL: "second_person_plural",
        Pronoun.THIRD_PERSON_PLURAL: "third_person_plural",
    }

    # Get the correct form for this pronoun
    correct_field = pronoun_to_field[pronoun]
    correct_form = all_forms[correct_field]

    if correct:
        conjugation_form = correct_form
    else:
        # Get all forms that are DIFFERENT from the correct one
        wrong_forms = [
            form
            for field, form in all_forms.items()
            if form != correct_form and form is not None
        ]

        if not wrong_forms:
            raise ValueError(
                f"Cannot create wrong conjugation for '{verb.infinitive}' in {tense.value}: "
                f"all forms are identical to '{correct_form}'"
            )

        # Pick a random wrong form
        conjugation_form = random.choice(wrong_forms)

    # Get pronoun display (always use the requested pronoun)
    pronoun_display_raw = get_pronoun_display(pronoun.value)
    if "/" in pronoun_display_raw:
        pronoun_forms = pronoun_display_raw.split("/")
        pronoun_display = random.choice(pronoun_forms)
    else:
        pronoun_display = pronoun_display_raw

    if not conjugation_form:
        raise ValueError(
            f"Missing conjugation form for verb '{verb.infinitive}', "
            f"tense '{tense.value}', pronoun '{pronoun.value}'"
        )

    # For compound tenses, extract just the auxiliary verb from the compound form.
    # E.g., "sommes descendus" -> "sommes"
    # This prevents conflating auxiliary errors with participle agreement errors.
    if tense in COMPOUND_TENSES and " " in conjugation_form:
        conjugation_form = conjugation_form.split()[0]

    auxiliary = verb.auxiliary.value

    return pronoun_display, conjugation_form, auxiliary
