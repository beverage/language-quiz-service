"""Prompt builders for pronoun substitution sentence generation.

This module handles sentences with object pronoun substitution (le/la/les, lui/leur).
Pronouns replace explicit direct (COD) and indirect (COI) objects.
"""

from src.prompts.sentences.error_types import ErrorType
from src.prompts.sentences.helpers import get_conjugation_pair
from src.prompts.sentences.templates import (
    build_base_template,
    format_optional_dimension,
    requires_auxiliary,
)
from src.schemas.sentences import DirectObject, IndirectObject, SentenceBase
from src.schemas.verbs import Verb


def _get_cod_pronoun_display(direct_object: DirectObject) -> str:
    """Convert DirectObject enum to French COD pronoun.

    Args:
        direct_object: The DirectObject enum value

    Returns:
        French COD pronoun string
    """
    pronoun_map = {
        DirectObject.MASCULINE: "le",
        DirectObject.FEMININE: "la",
        DirectObject.PLURAL: "les",
    }
    return pronoun_map.get(direct_object, "le/la/les (choose one)")


def _get_coi_pronoun_display(indirect_object: IndirectObject) -> str:
    """Convert IndirectObject enum to French COI pronoun.

    Args:
        indirect_object: The IndirectObject enum value

    Returns:
        French COI pronoun string
    """
    pronoun_map = {
        IndirectObject.MASCULINE: "lui",
        IndirectObject.FEMININE: "lui",
        IndirectObject.PLURAL: "leur",
    }
    return pronoun_map.get(indirect_object, "lui/leur (choose one)")


def _build_pronoun_rules_section(sentence: SentenceBase) -> str:
    """Build the pronoun placement rules section.

    Args:
        sentence: The sentence configuration

    Returns:
        Rules section string
    """
    rules = """
FRENCH OBJECT PRONOUN RULES:
- Object pronouns go BEFORE the conjugated verb (or auxiliary in compound tenses)
- In negation: Subject + ne + PRONOUN(S) + verb + pas/jamais/etc.
- Double pronoun order: le/la/les BEFORE lui/leur
- Examples:
  - "Je le vois" (I see him/it)
  - "Je lui parle" (I speak to him/her)
  - "Je le lui donne" (I give it to him/her)
  - "Je ne le vois pas" (I don't see him/it)
"""
    return rules


def _build_pronoun_substitution_section(sentence: SentenceBase) -> str:
    """Build the pronoun substitution requirements section.

    Args:
        sentence: The sentence configuration

    Returns:
        Pronoun substitution section string
    """
    parts = ["PRONOUN SUBSTITUTION:"]

    if sentence.direct_object not in (DirectObject.NONE, DirectObject.ANY):
        cod_pronoun = _get_cod_pronoun_display(sentence.direct_object)
        parts.append(f"- COD (direct object pronoun): {cod_pronoun}")

    if sentence.indirect_object not in (IndirectObject.NONE, IndirectObject.ANY):
        coi_pronoun = _get_coi_pronoun_display(sentence.indirect_object)
        parts.append(f"- COI (indirect object pronoun): {coi_pronoun}")

    if sentence.has_double_pronouns:
        parts.append("- DOUBLE PRONOUNS: Use both COD and COI (COD before COI)")

    return "\n".join(parts)


def build_correct_pronoun_prompt(
    sentence: SentenceBase, verb: Verb, conjugations: list
) -> str:
    """Build prompt for generating a correct sentence with pronoun substitution.

    Args:
        sentence: The sentence configuration
        verb: The verb being used
        conjugations: List of conjugation objects for the verb

    Returns:
        Complete prompt string for correct pronoun sentence generation
    """
    base = build_base_template(verb, sentence.tense)

    # Get correct conjugation pair
    pronoun_display, conjugation_form, auxiliary = get_conjugation_pair(
        pronoun=sentence.pronoun,
        tense=sentence.tense,
        verb=verb,
        conjugations=conjugations,
        correct=True,
    )

    negation_display = format_optional_dimension(sentence.negation)

    # Build required params
    required_params = f"""
REQUIRED (must use exactly):
- Subject pronoun: {pronoun_display}
- Correct conjugation: {conjugation_form}
- Tense: {sentence.tense.value}"""

    if requires_auxiliary(sentence.tense):
        required_params += f"\n- Auxiliary: {auxiliary}"

    required_params += f"""

OPTIONAL GUIDANCE:
- Negation: {negation_display}
"""

    pronoun_section = _build_pronoun_substitution_section(sentence)
    rules_section = _build_pronoun_rules_section(sentence)

    instructions = """
[TASK]
Generate a grammatically CORRECT French sentence with object pronoun substitution.

GUIDANCE:
- Use the required subject pronoun, conjugation, and tense exactly
- Place object pronoun(s) correctly according to French grammar rules
- The sentence should sound natural and idiomatic
- Include context that makes the pronoun reference clear
"""

    return base + required_params + pronoun_section + rules_section + instructions


def build_wrong_placement_prompt(
    sentence: SentenceBase, verb: Verb, conjugations: list
) -> str:
    """Build prompt for wrong pronoun placement error.

    The pronoun is placed in the wrong position relative to the verb.

    Args:
        sentence: The sentence configuration
        verb: The verb being used
        conjugations: List of conjugation objects for the verb

    Returns:
        Complete prompt string for placement error generation
    """
    base = build_base_template(verb, sentence.tense)

    pronoun_display, conjugation_form, auxiliary = get_conjugation_pair(
        pronoun=sentence.pronoun,
        tense=sentence.tense,
        verb=verb,
        conjugations=conjugations,
        correct=True,
    )

    # Determine which pronoun to misplace
    if sentence.direct_object not in (DirectObject.NONE, DirectObject.ANY):
        object_pronoun = _get_cod_pronoun_display(sentence.direct_object)
        pronoun_type = "COD"
    else:
        object_pronoun = _get_coi_pronoun_display(sentence.indirect_object)
        pronoun_type = "COI"

    required_params = f"""
REQUIRED:
- Subject pronoun: {pronoun_display}
- Conjugation: {conjugation_form}
- Tense: {sentence.tense.value}
- Object pronoun to MISPLACE: {object_pronoun} ({pronoun_type})
"""

    # Determine if compound tense for better error examples
    is_compound = requires_auxiliary(sentence.tense)

    if is_compound:
        # For compound tenses: pronoun should go before auxiliary, not between auxiliary and participle
        instructions = f"""
[TASK]
Generate a French sentence with the object pronoun "{object_pronoun}" in the WRONG position.

IMPORTANT: This sentence is SUPPOSED to be grammatically incorrect.
It is perfectly fine - and expected - for the sentence to feel unnatural or awkward.
The error itself makes the sentence unnatural, and that's the point.

PRIMARY ERROR (required):
In compound tenses, pronouns go BEFORE the auxiliary. Place it BETWEEN auxiliary and participle instead.
- WRONG: "J'avais {object_pronoun} mangé" or "Il a {object_pronoun} vu"
- CORRECT would be: "Je {object_pronoun}'avais mangé" or "Il {object_pronoun}'a vu"

GUIDANCE:
- The auxiliary and participle should be correct
- Only the pronoun placement is wrong (between auxiliary and participle)
- Don't worry about making it sound natural - errors are unnatural by definition

EXPLANATION:
Write: "The pronoun '{object_pronoun}' should come BEFORE the auxiliary, not between auxiliary and participle."
"""
    else:
        # For simple tenses: pronoun after verb instead of before
        instructions = f"""
[TASK]
Generate a French sentence with the object pronoun "{object_pronoun}" in the WRONG position.

IMPORTANT: This sentence is SUPPOSED to be grammatically incorrect.
It is perfectly fine - and expected - for the sentence to feel unnatural or awkward.
The error itself makes the sentence unnatural, and that's the point.

PRIMARY ERROR (required):
Place the pronoun AFTER the verb instead of before it.
- WRONG: "Je regarde {object_pronoun} tous les jours" or "Elle attend {object_pronoun} depuis une heure"
- CORRECT would be: "Je {object_pronoun} regarde tous les jours" or "Elle {object_pronoun} attend depuis une heure"

GUIDANCE:
- The conjugation should be correct
- Only the pronoun placement is wrong
- Don't worry about making it sound natural - errors are unnatural by definition
- Create a COMPLETE sentence with context (time expressions, locations, complements, etc.)
- Avoid bare minimal sentences - include meaningful content beyond just subject + verb + pronoun

EXPLANATION:
Write: "The pronoun '{object_pronoun}' should come BEFORE the verb, not after."
"""

    return base + required_params + instructions


def build_wrong_order_prompt(
    sentence: SentenceBase, verb: Verb, conjugations: list
) -> str:
    """Build prompt for wrong double pronoun order error.

    When both COD and COI are present, they are in the wrong order.

    Args:
        sentence: The sentence configuration
        verb: The verb being used
        conjugations: List of conjugation objects for the verb

    Returns:
        Complete prompt string for order error generation
    """
    base = build_base_template(verb, sentence.tense)

    pronoun_display, conjugation_form, auxiliary = get_conjugation_pair(
        pronoun=sentence.pronoun,
        tense=sentence.tense,
        verb=verb,
        conjugations=conjugations,
        correct=True,
    )

    cod_pronoun = _get_cod_pronoun_display(sentence.direct_object)
    coi_pronoun = _get_coi_pronoun_display(sentence.indirect_object)

    required_params = f"""
REQUIRED:
- Subject pronoun: {pronoun_display}
- Conjugation: {conjugation_form}
- Tense: {sentence.tense.value}
- COD pronoun: {cod_pronoun}
- COI pronoun: {coi_pronoun}
"""

    instructions = f"""
[TASK]
Generate a French sentence with DOUBLE PRONOUNS in the WRONG order.

IMPORTANT: This sentence is SUPPOSED to be grammatically incorrect.
It is perfectly fine - and expected - for the sentence to feel unnatural or awkward.
The error itself makes the sentence unnatural, and that's the point.

Even if the verb doesn't naturally take both a direct and indirect object, USE BOTH PRONOUNS ANYWAY.
Using pronouns with a verb that doesn't accept them is ITSELF a grammatical error worth testing.
Do not worry about whether the verb semantically accepts these objects - just create the error.

PRIMARY ERROR (required):
Put the COI ({coi_pronoun}) BEFORE the COD ({cod_pronoun}).
- WRONG: "{coi_pronoun} {cod_pronoun}" (e.g., "Je lui le donne")
- CORRECT would be: "{cod_pronoun} {coi_pronoun}" (e.g., "Je le lui donne")

GUIDANCE:
- Both pronouns MUST be present, in the wrong order
- The conjugation should be correct
- Don't worry about making it sound natural - errors are unnatural by definition

EXPLANATION:
Write: "With double pronouns, COD (le/la/les) must come BEFORE COI (lui/leur). Should be '{cod_pronoun} {coi_pronoun}', not '{coi_pronoun} {cod_pronoun}'."
"""

    return base + required_params + instructions


def build_wrong_category_prompt(
    sentence: SentenceBase, verb: Verb, conjugations: list
) -> str:
    """Build prompt for wrong pronoun category error.

    COD pronoun used when COI was needed, or vice versa.

    Args:
        sentence: The sentence configuration
        verb: The verb being used
        conjugations: List of conjugation objects for the verb

    Returns:
        Complete prompt string for category error generation
    """
    base = build_base_template(verb, sentence.tense)

    pronoun_display, conjugation_form, auxiliary = get_conjugation_pair(
        pronoun=sentence.pronoun,
        tense=sentence.tense,
        verb=verb,
        conjugations=conjugations,
        correct=True,
    )

    # Determine correct and wrong pronouns based on what's specified
    if sentence.indirect_object not in (IndirectObject.NONE, IndirectObject.ANY):
        # Should use COI, but will wrongly use COD
        correct_pronoun = _get_coi_pronoun_display(sentence.indirect_object)
        wrong_pronoun = (
            "le" if sentence.indirect_object != IndirectObject.PLURAL else "les"
        )
        correct_type = "COI"
        wrong_type = "COD"
    else:
        # Should use COD, but will wrongly use COI
        correct_pronoun = _get_cod_pronoun_display(sentence.direct_object)
        wrong_pronoun = (
            "lui" if sentence.direct_object != DirectObject.PLURAL else "leur"
        )
        correct_type = "COD"
        wrong_type = "COI"

    required_params = f"""
REQUIRED:
- Subject pronoun: {pronoun_display}
- Conjugation: {conjugation_form}
- Tense: {sentence.tense.value}
- WRONG pronoun to use: {wrong_pronoun} ({wrong_type} - INCORRECT)
- Correct pronoun would be: {correct_pronoun} ({correct_type})
"""

    instructions = f"""
[TASK]
Generate a French sentence using the WRONG pronoun category.

IMPORTANT: This sentence is SUPPOSED to be grammatically incorrect.
It is perfectly fine - and expected - for the sentence to feel unnatural or awkward.
The error itself makes the sentence unnatural, and that's the point.

PRIMARY ERROR (required):
Use "{wrong_pronoun}" ({wrong_type}) when "{correct_pronoun}" ({correct_type}) is required.
- Example: "Je le parle" instead of "Je lui parle" (parler takes indirect object)

GUIDANCE:
- The conjugation should be correct
- Use the wrong pronoun category deliberately
- Don't worry about making it sound natural - errors are unnatural by definition

EXPLANATION:
Write: "This verb requires {correct_type} ({correct_pronoun}), not {wrong_type} ({wrong_pronoun})."
"""

    return base + required_params + instructions


def build_wrong_gender_prompt(
    sentence: SentenceBase, verb: Verb, conjugations: list
) -> str:
    """Build prompt for wrong gender pronoun error.

    Detectable via past participle agreement with être verbs.

    Args:
        sentence: The sentence configuration
        verb: The verb being used
        conjugations: List of conjugation objects for the verb

    Returns:
        Complete prompt string for gender error generation
    """
    base = build_base_template(verb, sentence.tense)

    pronoun_display, conjugation_form, auxiliary = get_conjugation_pair(
        pronoun=sentence.pronoun,
        tense=sentence.tense,
        verb=verb,
        conjugations=conjugations,
        correct=True,
    )

    # Determine correct and wrong gender
    if sentence.direct_object == DirectObject.MASCULINE:
        correct_pronoun = "le"
        wrong_pronoun = "la"
    elif sentence.direct_object == DirectObject.FEMININE:
        correct_pronoun = "la"
        wrong_pronoun = "le"
    else:
        # For plural or indirect objects, create a gender mismatch scenario
        correct_pronoun = "le"
        wrong_pronoun = "la"

    required_params = f"""
REQUIRED:
- Subject pronoun: {pronoun_display}
- Conjugation: {conjugation_form}
- Tense: {sentence.tense.value}
- WRONG pronoun: {wrong_pronoun} (wrong gender)
- Correct pronoun would be: {correct_pronoun}
"""

    # Determine the referent gender for context
    if correct_pronoun == "le":
        referent_example = "le livre"
        referent_gender = "masculine"
    else:
        referent_example = "la lettre"
        referent_gender = "feminine"

    instructions = f"""
[TASK]
Generate a French sentence with the WRONG GENDER pronoun.

IMPORTANT: This sentence is SUPPOSED to be grammatically incorrect.
It is perfectly fine - and expected - for the sentence to feel unnatural or awkward.
The error itself makes the sentence unnatural, and that's the point.

PRIMARY ERROR (required):
Use "{wrong_pronoun}" to refer to a {referent_gender} object.
Make the referent EXPLICIT in the sentence so the gender mismatch is clear.
- Example: "{referent_example.title()}, je {wrong_pronoun} tiens." (using wrong gender pronoun for {referent_gender} noun)

GUIDANCE:
- State the noun being referred to explicitly (e.g., "La promesse, je le tiens")
- Use the required tense ({sentence.tense.value}) - do NOT switch to a different tense
- The explicit noun makes the gender error detectable
- Don't worry about making it sound natural - errors are unnatural by definition

EXPLANATION:
Write: "The pronoun '{wrong_pronoun}' doesn't match the gender of the referent. Should be '{correct_pronoun}' ({referent_gender})."
"""

    return base + required_params + instructions


def build_wrong_number_prompt(
    sentence: SentenceBase, verb: Verb, conjugations: list
) -> str:
    """Build prompt for wrong number pronoun error.

    Singular pronoun used when plural was needed, or vice versa.

    Args:
        sentence: The sentence configuration
        verb: The verb being used
        conjugations: List of conjugation objects for the verb

    Returns:
        Complete prompt string for number error generation
    """
    base = build_base_template(verb, sentence.tense)

    pronoun_display, conjugation_form, auxiliary = get_conjugation_pair(
        pronoun=sentence.pronoun,
        tense=sentence.tense,
        verb=verb,
        conjugations=conjugations,
        correct=True,
    )

    # Determine correct and wrong number
    if sentence.direct_object == DirectObject.PLURAL:
        correct_pronoun = "les"
        wrong_pronoun = "le"
        correct_desc = "plural"
        wrong_desc = "singular"
    elif sentence.indirect_object == IndirectObject.PLURAL:
        correct_pronoun = "leur"
        wrong_pronoun = "lui"
        correct_desc = "plural"
        wrong_desc = "singular"
    elif sentence.direct_object in (DirectObject.MASCULINE, DirectObject.FEMININE):
        correct_pronoun = _get_cod_pronoun_display(sentence.direct_object)
        wrong_pronoun = "les"
        correct_desc = "singular"
        wrong_desc = "plural"
    else:
        correct_pronoun = "lui"
        wrong_pronoun = "leur"
        correct_desc = "singular"
        wrong_desc = "plural"

    required_params = f"""
REQUIRED:
- Subject pronoun: {pronoun_display}
- Conjugation: {conjugation_form}
- Tense: {sentence.tense.value}
- WRONG pronoun: {wrong_pronoun} ({wrong_desc} - INCORRECT)
- Correct pronoun would be: {correct_pronoun} ({correct_desc})
"""

    instructions = f"""
[TASK]
Generate a French sentence with a NUMBER MISMATCH in the object pronoun.

IMPORTANT: This sentence is SUPPOSED to be grammatically incorrect.
It is perfectly fine - and expected - for the sentence to feel unnatural or awkward.
The error itself makes the sentence unnatural, and that's the point.

PRIMARY ERROR (required):
Use "{wrong_pronoun}" ({wrong_desc}) when referring to something that is {correct_desc}.
- Create context that makes clear the referent is {correct_desc}
- But use the {wrong_desc} pronoun "{wrong_pronoun}"

GUIDANCE:
- Include context that reveals the number mismatch
- The conjugation should be correct
- Don't worry about making it sound natural - errors are unnatural by definition

EXPLANATION:
Write: "The pronoun '{wrong_pronoun}' is {wrong_desc}, but the referent is {correct_desc}. Should be '{correct_pronoun}'."
"""

    return base + required_params + instructions


# Mapping from error type to prompt builder function
PRONOUN_ERROR_BUILDERS = {
    ErrorType.WRONG_PLACEMENT: build_wrong_placement_prompt,
    ErrorType.WRONG_ORDER: build_wrong_order_prompt,
    ErrorType.WRONG_CATEGORY: build_wrong_category_prompt,
    ErrorType.WRONG_GENDER: build_wrong_gender_prompt,
    ErrorType.WRONG_NUMBER: build_wrong_number_prompt,
}


def build_pronoun_error_prompt(
    sentence: SentenceBase,
    verb: Verb,
    conjugations: list,
    error_type: ErrorType,
) -> str:
    """Build prompt for a specific pronoun error type.

    Args:
        sentence: The sentence configuration
        verb: The verb being used
        conjugations: List of conjugation objects for the verb
        error_type: The type of pronoun error to generate

    Returns:
        Complete prompt string for the specified error

    Raises:
        ValueError: If error_type is not a pronoun error
    """
    builder = PRONOUN_ERROR_BUILDERS.get(error_type)
    if builder is None:
        raise ValueError(f"Unknown pronoun error type: {error_type}")

    return builder(sentence, verb, conjugations)
