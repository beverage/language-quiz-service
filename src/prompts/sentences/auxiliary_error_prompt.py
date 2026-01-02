"""Prompt builder for wrong auxiliary error generation."""

from src.prompts.sentences.helpers import get_pronoun_display
from src.prompts.sentences.templates import (
    build_base_template,
    format_optional_dimension,
)
from src.schemas.sentences import SentenceBase
from src.schemas.verbs import AuxiliaryType, Verb


def build_wrong_auxiliary_prompt(
    sentence: SentenceBase, verb: Verb, conjugations: list
) -> str:
    """Build prompt for wrong auxiliary verb error.

    Args:
        sentence: The sentence configuration
        verb: The verb being used
        conjugations: List of conjugation objects for the verb (unused, kept for API consistency)

    Returns:
        Complete prompt string for auxiliary error generation
    """
    base = build_base_template(verb, sentence.tense)

    # Get pronoun display
    pronoun_display = get_pronoun_display(sentence.pronoun.value)
    if "/" in pronoun_display:
        # Pick first form for consistency (e.g., "il" from "il/elle/on")
        pronoun_display = pronoun_display.split("/")[0]

    # Use the actual past participle from the verb, not the full compound conjugation
    past_participle = verb.past_participle

    # Determine correct and wrong auxiliary
    correct_auxiliary = verb.auxiliary.value
    wrong_auxiliary = "avoir" if verb.auxiliary == AuxiliaryType.ETRE else "être"

    # Format optional dimensions (may be "any" or specific values)
    negation_display = format_optional_dimension(sentence.negation)
    direct_object_display = format_optional_dimension(sentence.direct_object)
    indirect_object_display = format_optional_dimension(sentence.indirect_object)

    required_params = f"""
REQUIRED (must use exactly):
- Pronoun: {pronoun_display}
- Past participle: {past_participle}
- Wrong auxiliary: {wrong_auxiliary} (DELIBERATELY INCORRECT - do not fix)
- Tense: {sentence.tense.value}

OPTIONAL GUIDANCE (use if natural, ignore if problematic):
- Negation: {negation_display}
- Direct object: {direct_object_display}
- Indirect object: {indirect_object_display}
"""

    instructions = f"""
[TASK]
Generate a French sentence using the WRONG auxiliary "{wrong_auxiliary}" with "{verb.infinitive}".

PRIMARY ERROR (required):
Use "{wrong_auxiliary}" even though "{verb.infinitive}" requires "{correct_auxiliary}".

Example:
- Correct: "Je suis allé" (aller uses être)
- Your output: "J'ai allé" (wrong auxiliary)

GUIDANCE:
- Make the sentence sound natural despite the auxiliary error
- Other grammar can be correct OR have minor issues - focus on the auxiliary error
- If the optional parameters create conflicts, ignore them and write a natural sentence
- Keep it simple - one clause is fine

EXPLANATION:
Write a brief explanation stating ONLY the auxiliary error.
Format: "The verb '{verb.infinitive}' requires '{correct_auxiliary}', not '{wrong_auxiliary}'."
"""

    return base + required_params + instructions
