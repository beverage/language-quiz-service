"""Prompt builder for wrong conjugation error generation."""

from src.prompts.sentences.helpers import get_conjugation_pair
from src.prompts.sentences.templates import (
    COMPOUND_TENSES,
    build_base_template,
    build_explanation_section,
    format_optional_dimension,
)
from src.schemas.sentences import SentenceBase
from src.schemas.verbs import Verb


def build_wrong_conjugation_prompt(
    sentence: SentenceBase, verb: Verb, conjugations: list
) -> str:
    """Build prompt for wrong verb conjugation error.

    Args:
        sentence: The sentence configuration
        verb: The verb being used
        conjugations: List of conjugation objects for the verb

    Returns:
        Complete prompt string for conjugation error generation
    """
    base = build_base_template(verb, sentence.tense)

    # Get INCORRECT conjugation pair (mismatched pronoun/conjugation)
    # For compound tenses, wrong_conjugation is just the auxiliary (e.g., "sommes")
    pronoun_display, wrong_conjugation, auxiliary = get_conjugation_pair(
        pronoun=sentence.pronoun,
        tense=sentence.tense,
        verb=verb,
        conjugations=conjugations,
        correct=False,
    )

    # For compound tenses, build the full wrong form: wrong auxiliary + correct participle
    # E.g., "sommes" + "descendu" = "sommes descendu"
    if sentence.tense in COMPOUND_TENSES:
        wrong_verb_display = f"{wrong_conjugation} {verb.past_participle}"
    else:
        wrong_verb_display = wrong_conjugation

    # Format optional dimensions (may be "any" or specific values)
    negation_display = format_optional_dimension(sentence.negation)
    direct_object_display = format_optional_dimension(sentence.direct_object)
    indirect_object_display = format_optional_dimension(sentence.indirect_object)

    required_params = f"""
REQUIRED (must use exactly):
- Pronoun: {pronoun_display}
- Wrong verb form: {wrong_verb_display} (DELIBERATELY INCORRECT - do not fix)
- Tense context: {sentence.tense.value}

OPTIONAL GUIDANCE (use if natural, ignore if problematic):
- Negation: {negation_display}
- Direct object: {direct_object_display}
- Indirect object: {indirect_object_display}
"""

    # Get the correct form for explanation
    _, correct_conjugation, _ = get_conjugation_pair(
        pronoun=sentence.pronoun,
        tense=sentence.tense,
        verb=verb,
        conjugations=conjugations,
        correct=True,
    )
    if sentence.tense in COMPOUND_TENSES:
        correct_verb_display = f"{correct_conjugation} {verb.past_participle}"
    else:
        correct_verb_display = correct_conjugation

    explanation = build_explanation_section(
        f"The verb should be '{correct_verb_display}' for '{pronoun_display}', not '{wrong_verb_display}'."
    )
    instructions = f"""
[TASK]
Generate a French sentence with the WRONG conjugation "{wrong_verb_display}" for "{pronoun_display}".

PRIMARY ERROR (required):
Use "{wrong_verb_display}" even though it's incorrect for "{pronoun_display}".

GUIDANCE:
- Make the sentence sound natural despite the conjugation error
- Other grammar can be correct OR have minor issues - focus on the conjugation error
- If the optional parameters create conflicts, ignore them and write a natural sentence
- Keep it simple - one clause is fine
{explanation}"""

    return base + required_params + instructions
