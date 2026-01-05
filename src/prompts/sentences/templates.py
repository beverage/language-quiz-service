"""Reusable template sections for sentence prompts."""

from src.schemas.sentences import DirectObject, IndirectObject, Negation
from src.schemas.verbs import Tense, Verb

# Compound tenses that require auxiliary verb (avoir/être)
# Extend this set when adding tenses like plus-que-parfait, futur antérieur, etc.
COMPOUND_TENSES = frozenset([Tense.PASSE_COMPOSE])


def requires_auxiliary(tense: Tense) -> bool:
    """Check if a tense requires the auxiliary verb in the sentence.

    Compound tenses (passé composé, plus-que-parfait, etc.) use the auxiliary.
    Simple tenses (present, future, conditional, etc.) do not.

    Args:
        tense: The tense being used

    Returns:
        True if the tense requires auxiliary, False otherwise
    """
    return tense in COMPOUND_TENSES


def format_optional_dimension(value: DirectObject | IndirectObject | Negation) -> str:
    """Format a dimension value for prompt display.

    If the value is ANY, returns instruction for LLM to choose naturally.
    Otherwise returns the specific value.

    Args:
        value: The dimension enum value

    Returns:
        Formatted string for use in prompts
    """
    if value.value == "any":
        return "choose what's natural for the sentence"
    return value.value


def build_base_template(verb: Verb, tense: Tense) -> str:
    """Build the base template shared by all prompts.

    Only includes auxiliary info for compound tenses where it's relevant.

    Args:
        verb: The verb being used
        tense: The tense being used (determines if auxiliary info is included)

    Returns:
        Base template string with verb details
    """
    base = f"""Generate a simple, natural French sentence using the verb "{verb.infinitive}".

VERB INFO:
- Infinitive: {verb.infinitive}"""

    if requires_auxiliary(tense):
        base += f"""
- Past Participle: {verb.past_participle}
- Auxiliary: {verb.auxiliary.value}"""

    base += "\n"
    return base
