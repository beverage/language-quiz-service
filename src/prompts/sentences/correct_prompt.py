"""Prompt builder for correct sentence generation."""

from src.prompts.sentences.helpers import get_conjugation_pair
from src.prompts.sentences.templates import build_base_template
from src.schemas.sentences import Negation, SentenceBase
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
    base = build_base_template(verb)

    # Get correct conjugation pair
    pronoun_display, conjugation_form, auxiliary = get_conjugation_pair(
        pronoun=sentence.pronoun,
        tense=sentence.tense,
        verb=verb,
        conjugations=conjugations,
        correct=True,
    )

    # Build negation display
    negation_display = (
        sentence.negation.value if sentence.negation != Negation.NONE else "none"
    )

    required_params = f"""
REQUIRED PARAMETERS (you MUST use these exactly):
- Pronoun: {pronoun_display}
- Correct conjugation: {conjugation_form}
- Auxiliary: {auxiliary}
- Tense: {sentence.tense.value}
- Negation: {negation_display}
- Direct Object (COD): {sentence.direct_object.value}
- Indirect Object (COI): {sentence.indirect_object.value}
"""

    instructions = """
[SPECIFIC INSTRUCTIONS]
Generate a grammatically CORRECT sentence that:
1. Uses all required parameters exactly as specified
2. Follows all French grammar rules:
   - Use the correct auxiliary verb specified
   - Proper past participle agreement with être
   - Correct reflexive pronoun placement if reflexive verb
   - Proper negation structure (ne...pas, ne...jamais, etc.)
   - Correct COD/COI pronoun placement and agreement
   - Proper prepositions for indirect objects
3. Is semantically meaningful and idiomatic
4. Sounds natural to native speakers
"""

    return base + required_params + instructions
