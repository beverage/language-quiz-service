"""Prompt builder for wrong conjugation error generation."""

from src.prompts.sentences.helpers import get_conjugation_pair
from src.prompts.sentences.templates import build_base_template
from src.schemas.sentences import Negation, SentenceBase
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
    base = build_base_template(verb)

    # Get INCORRECT conjugation pair (mismatched pronoun/conjugation)
    pronoun_display, wrong_conjugation, auxiliary = get_conjugation_pair(
        pronoun=sentence.pronoun,
        tense=sentence.tense,
        verb=verb,
        conjugations=conjugations,
        correct=False,
    )

    # Build negation display
    negation_display = (
        sentence.negation.value if sentence.negation != Negation.NONE else "none"
    )

    required_params = f"""
REQUIRED PARAMETERS (you MUST use these exactly):
- Pronoun: {pronoun_display}
- Conjugation you MUST use: {wrong_conjugation} (this is deliberately WRONG for this pronoun)
- Tense: {sentence.tense.value}
- Negation: {negation_display}
- Direct Object (COD): {sentence.direct_object.value}
- Indirect Object (COI): {sentence.indirect_object.value}
"""

    instructions = f"""
[SPECIFIC INSTRUCTIONS]
*** CRITICAL: You MUST use the wrong conjugation form "{wrong_conjugation}" ***

DELIBERATE ERROR:
The conjugation "{wrong_conjugation}" is INCORRECT for pronoun "{pronoun_display}".
You MUST use it anyway - this is a grammar exercise testing conjugation errors.

Generate a natural French sentence using:
- Pronoun: {pronoun_display}
- Wrong verb form: {wrong_conjugation} (required - do not fix this!)
- All other grammar MUST be correct (auxiliary, agreement, negation, word order, objects)

EXPLANATION INSTRUCTION:
In your explanation, ONLY explain the conjugation error. Concisely state what the correct conjugation
should be for "{pronoun_display}" and why "{wrong_conjugation}" is incorrect.

Example explanation: "The verb should be conjugated as 'parles' for 'tu', not 'parle', because 'parle' is the third person singular form."
"""

    return base + required_params + instructions
