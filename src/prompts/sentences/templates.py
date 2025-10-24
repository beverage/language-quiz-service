"""Reusable template sections for sentence prompts."""

from src.schemas.verbs import Verb


def build_base_template(verb: Verb) -> str:
    """Build the base template shared by all prompts.

    Args:
        verb: The verb being used

    Returns:
        Base template string with verb details
    """
    base = f"""You are a French grammar expert. Generate a creative, natural-sounding French sentence.  The sentence must start with a capital letter and use correct punctuation.

The sentence must contain at least two phrases, and no more than two phrases.

VERB DETAILS:
- Infinitive: {verb.infinitive}
- Past Participle: {verb.past_participle}
- Auxiliary: {verb.auxiliary.value}
- Reflexive: {verb.reflexive}
- Can have COD: {verb.can_have_cod}
- Can have COI: {verb.can_have_coi}
"""
    return base
