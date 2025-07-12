"""
CLI sentence operations - MIGRATED.

Migrated to use Supabase services instead of SQLAlchemy.
Maintained for backward compatibility.
"""

import logging

from src.services.sentence_service import SentenceService
from src.schemas.sentences import (
    Pronoun,
    Tense,
    DirectObject,
    IndirectPronoun,
    Negation,
)
from src.services.verb_service import VerbService

logger = logging.getLogger(__name__)


async def create_sentence(
    verb_infinitive: str,
    pronoun: Pronoun = Pronoun.FIRST_PERSON,
    tense: Tense = Tense.PRESENT,
    direct_object: DirectObject = DirectObject.NONE,
    indirect_pronoun: IndirectPronoun = IndirectPronoun.NONE,
    negation: Negation = Negation.NONE,
    is_correct: bool = True,
):
    """Create a sentence using AI - migrated to use Supabase services."""

    sentence_service = SentenceService()
    verb_service = VerbService()

    if not verb_infinitive:
        verb = await verb_service.get_random_verb()
        if not verb:
            raise ValueError("No verbs available to generate a sentence.")
    else:
        verb = await verb_service.get_verb_by_infinitive(verb_infinitive)
        if not verb:
            raise ValueError(f"Verb '{verb_infinitive}' not found")

    # The CLI passes strings; the service expects enums. We convert them here.
    return await sentence_service.generate_sentence(
        verb_id=verb.id,
        pronoun=Pronoun(pronoun),
        tense=Tense(tense),
        direct_object=DirectObject(direct_object),
        indirect_pronoun=IndirectPronoun(indirect_pronoun),
        negation=Negation(negation),
        is_correct=is_correct,
    )


async def create_random_sentence(is_correct: bool = True):
    """Create a random sentence by calling the SentenceService."""
    sentence_service = SentenceService()
    return await sentence_service.generate_random_sentence(is_correct=is_correct)
