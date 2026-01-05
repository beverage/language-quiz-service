"""Reusable template sections for sentence prompts."""

from src.schemas.sentences import DirectObject, IndirectObject, Negation
from src.schemas.verbs import Tense, Verb

# Compound tenses that require auxiliary verb (avoir/être)
# Extend this set when adding tenses like plus-que-parfait, futur antérieur, etc.
COMPOUND_TENSES = frozenset([Tense.PASSE_COMPOSE])

# Tense-specific hints to encourage idiomatic, varied sentence construction
# These guide the LLM toward natural French patterns for each tense
TENSE_HINTS: dict[Tense, str] = {
    Tense.PRESENT: (
        "Set the sentence in an everyday context: habits, current actions, or general truths. "
        "Examples: daily routines, opinions, descriptions of what someone does regularly."
    ),
    Tense.PASSE_COMPOSE: (
        "Set the sentence in a specific past context with time markers when natural: "
        "hier, la semaine dernière, ce matin, il y a deux jours, etc. "
        "Describe completed actions or events."
    ),
    Tense.IMPARFAIT: (
        "Use for past descriptions, habits, or ongoing states: "
        "quand j'étais jeune, chaque été, à cette époque, pendant que, etc. "
        "Describe what was happening or used to happen."
    ),
    Tense.FUTURE_SIMPLE: (
        "Set the sentence in a future context: demain, l'année prochaine, quand..., "
        "bientôt, un jour, etc. Express plans, predictions, or promises."
    ),
    Tense.CONDITIONNEL: (
        "Use conditional contexts: polite requests (je voudrais), hypotheticals (si j'avais...), "
        "uncertain future in the past, or softened statements. "
        "Avoid always using 'si' clauses - vary the construction."
    ),
    Tense.SUBJONCTIF: (
        "Use VARIED subjunctive triggers - do NOT always use 'il faut que'. "
        "Choose from: je veux que, je souhaite que, bien que, pour que, avant que, "
        "à moins que, je doute que, je suis content que, il est important que, "
        "je ne pense pas que, etc. Match the trigger to a natural context."
    ),
    Tense.IMPERATIF: (
        "Use imperative in natural command/instruction contexts: recipes, directions, "
        "advice, encouragement, or polite requests. "
        "Can be formal (vous) or informal (tu) based on context."
    ),
}


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


def get_tense_hint(tense: Tense) -> str | None:
    """Get the idiomatic hint for a specific tense.

    Args:
        tense: The tense to get hints for

    Returns:
        Hint string if available, None otherwise
    """
    return TENSE_HINTS.get(tense)


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
    Includes tense-specific hints for more idiomatic output.

    Args:
        verb: The verb being used
        tense: The tense being used (determines if auxiliary info is included)

    Returns:
        Base template string with verb details and contextual hints
    """
    base = f"""Generate a simple, natural French sentence using the verb "{verb.infinitive}".

VERB INFO:
- Infinitive: {verb.infinitive}"""

    if requires_auxiliary(tense):
        base += f"""
- Past Participle: {verb.past_participle}
- Auxiliary: {verb.auxiliary.value}"""

    # Add tense-specific hint for more idiomatic output
    hint = get_tense_hint(tense)
    if hint:
        base += f"""

STYLE HINT:
{hint}"""

    base += "\n"
    return base
