"""
CLI sentence operations - MIGRATED.

Migrated to use Supabase services instead of SQLAlchemy.
Maintained for backward compatibility.
"""

import logging
import random

from schemas.sentence import (
    SentenceCreate,
    Pronoun,
    DirectObject,
    IndirectPronoun,
    Negation,
)
from schemas.verbs import Tense
from services.sentence_service import SentenceService
from services.verb_service import VerbService

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

    if verb_infinitive == "":
        verb = await verb_service.get_random_verb()
    else:
        verb = await verb_service.get_verb_by_infinitive(verb_infinitive)

    if not verb:
        raise ValueError(f"Verb {verb_infinitive} not found")

    # Save sentence using the service
    sentence_create = SentenceCreate(
        infinitive=verb_infinitive,
        auxiliary=verb.auxiliary,
        pronoun=pronoun,
        tense=tense,
        direct_object=direct_object,
        indirect_pronoun=indirect_pronoun,
        negation=negation,
        content="",
        translation="",
        is_correct=is_correct,
    )

    saved_sentence = await sentence_service.create_sentence(sentence_create)

    return saved_sentence


async def create_random_sentence(is_correct: bool = True):
    """Create a random sentence - migrated to use Supabase services."""

    # Invalid pronoun + imperative combinations are possible here:
    verb_service = VerbService()
    verb = await verb_service.get_random_verb()

    return await create_sentence(
        verb.infinitive,
        random.choice([p for p in Pronoun]),
        random.choice(
            [t for t in Tense if t != Tense.IMPERATIVE]
        ),  # Verb, pronoun, and tense remain fully random for now.
        direct_object=random.choice(
            [d for d in DirectObject]
        ),  # Use correct enum values
        indirect_pronoun=random.choice([i for i in IndirectPronoun]),
        negation=Negation.NONE
        if random.randint(0, 2) == 0
        else random.choice([n for n in Negation if n != Negation.NONE]),
        is_correct=is_correct,
    )
