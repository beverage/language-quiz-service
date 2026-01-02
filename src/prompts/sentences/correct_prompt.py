"""Prompt builder for correct sentence generation."""

from src.prompts.sentences.helpers import get_conjugation_pair
from src.prompts.sentences.templates import (
    build_base_template,
    format_optional_dimension,
    requires_auxiliary,
)
from src.schemas.sentences import SentenceBase
from src.schemas.verbs import Verb


def build_correct_sentence_prompt(
    sentence: SentenceBase, verb: Verb, conjugations: list
) -> str:
    """Build prompt for generating a grammatically correct sentence.

    Args:
        sentence: The sentence configuration
        verb: The verb being used
        conjugations: List of conjugation objects for the verb

    Returns:
        Complete prompt string for correct sentence generation
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

    # Format optional dimensions (may be "any" or specific values)
    negation_display = format_optional_dimension(sentence.negation)
    direct_object_display = format_optional_dimension(sentence.direct_object)
    indirect_object_display = format_optional_dimension(sentence.indirect_object)

    # Build required params - only include auxiliary for compound tenses
    required_params = f"""
REQUIRED (must use exactly):
- Pronoun: {pronoun_display}
- Correct conjugation: {conjugation_form}
- Tense: {sentence.tense.value}"""

    if requires_auxiliary(sentence.tense):
        required_params += f"\n- Auxiliary: {auxiliary}"

    required_params += f"""

OPTIONAL GUIDANCE (use if natural, ignore if problematic):
- Negation: {negation_display}
- Direct Object (COD): {direct_object_display}
- Indirect Object (COI): {indirect_object_display}
"""

    instructions = """
[TASK]
Generate a grammatically CORRECT French sentence.

GUIDANCE:
- Use the required pronoun, conjugation, and tense exactly
- For optional parameters, use them if they fit naturally; ignore if they create conflicts
- Follow all French grammar rules
- Keep it simple and idiomatic - one clause is fine
"""

    return base + required_params + instructions
