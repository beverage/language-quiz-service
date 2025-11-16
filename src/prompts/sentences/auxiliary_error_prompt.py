"""Prompt builder for wrong auxiliary error generation."""

from src.prompts.sentences.helpers import get_conjugation_pair
from src.prompts.sentences.templates import build_base_template
from src.schemas.sentences import Negation, SentenceBase
from src.schemas.verbs import AuxiliaryType, Verb


def build_wrong_auxiliary_prompt(
    sentence: SentenceBase, verb: Verb, conjugations: list
) -> str:
    """Build prompt for wrong auxiliary verb error.

    Args:
        sentence: The sentence configuration
        verb: The verb being used
        conjugations: List of conjugation objects for the verb

    Returns:
        Complete prompt string for auxiliary error generation
    """
    base = build_base_template(verb)

    # Get CORRECT conjugation pair
    pronoun_display, conjugation_form, correct_auxiliary = get_conjugation_pair(
        pronoun=sentence.pronoun,
        tense=sentence.tense,
        verb=verb,
        conjugations=conjugations,
        correct=True,
    )

    # Determine wrong auxiliary
    wrong_auxiliary = "avoir" if verb.auxiliary == AuxiliaryType.ETRE else "être"

    # Build negation display
    negation_display = (
        sentence.negation.value if sentence.negation != Negation.NONE else "none"
    )

    required_params = f"""
REQUIRED PARAMETERS (you MUST use these exactly):
- Pronoun: {pronoun_display}
- Correct conjugation: {conjugation_form}
- Auxiliary you MUST use: {wrong_auxiliary} (this is deliberately WRONG)
- Correct auxiliary would be: {correct_auxiliary}
- Tense: {sentence.tense.value}
- Negation: {negation_display}
- Direct Object (COD): {sentence.direct_object.value}
- Indirect Object (COI): {sentence.indirect_object.value}
"""

    instructions = f"""
[SPECIFIC INSTRUCTIONS]
*** CRITICAL: You MUST use the wrong auxiliary "{wrong_auxiliary}" ***

DELIBERATE ERROR:
The verb "{verb.infinitive}" requires auxiliary "{correct_auxiliary}" in {sentence.tense.value},
but you MUST use "{wrong_auxiliary}" instead - this is a grammar exercise testing auxiliary errors.

Generate a natural French sentence using:
- Pronoun: {pronoun_display}
- Correct conjugation: {conjugation_form}
- WRONG auxiliary: {wrong_auxiliary} (required - do not fix this!)
- All other grammar MUST be correct (conjugation, agreement, negation, word order, objects)

Example:
- Correct: "Je suis allé" (aller uses être)
- Your task: "J'ai allé" (using avoir - WRONG but required)

EXPLANATION INSTRUCTION:
In your explanation, ONLY explain the auxiliary error. Concisely state which auxiliary
"{verb.infinitive}" requires and why "{wrong_auxiliary}" is incorrect.

Example explanation: "The verb 'aller' requires the auxiliary 'être' in compound tenses, not 'avoir'."
"""

    return base + required_params + instructions
