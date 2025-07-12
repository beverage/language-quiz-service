"""
CLI sentence database operations - MIGRATED.

Migrated to use Supabase services instead of SQLAlchemy.
Maintained for backward compatibility.
"""

from src.schemas.sentences import Pronoun, DirectObject, IndirectPronoun, Negation
from src.schemas.verbs import Tense
from src.services.sentence_service import SentenceService


async def get_random_sentence(
    quantity: int,
    verb_infinitive: str,
    pronoun: Pronoun = Pronoun.FIRST_PERSON,
    tense: Tense = Tense.PRESENT,
    direct_object: DirectObject = DirectObject.NONE,
    indirect_pronoun: IndirectPronoun = IndirectPronoun.NONE,
    negation: Negation = Negation.NONE,
    is_correct: bool = True,
):
    """Get random sentences - migrated to use SentenceService."""
    sentence_service = SentenceService()

    # Get sentences with filters
    sentences = await sentence_service.get_sentences(
        infinitive=verb_infinitive if verb_infinitive else None,
        is_correct=is_correct,
        limit=quantity,
    )

    return sentences


async def save_sentence(sentence):
    """Save a sentence - migrated to use SentenceService."""
    sentence_service = SentenceService()

    # Convert old sentence object to SentenceCreate if needed
    from schemas.sentences import SentenceCreate

    if hasattr(sentence, "__dict__"):
        # Convert from old model format
        sentence_data = {
            key: value
            for key, value in sentence.__dict__.items()
            if not key.startswith("_")
        }
        sentence_create = SentenceCreate(**sentence_data)
    else:
        sentence_create = sentence

    return await sentence_service.create_sentence(sentence_create)
