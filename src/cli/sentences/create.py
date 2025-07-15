"""
CLI sentence operations - MIGRATED.

Migrated to use Supabase services instead of SQLAlchemy.
Maintained for backward compatibility.
"""

import logging
import random

from src.schemas.sentences import (
    DirectObject,
    IndirectObject,
    Negation,
    Pronoun,
    Tense,
)
from src.services.sentence_service import SentenceService
from src.services.verb_service import VerbService

logger = logging.getLogger(__name__)


async def create_sentence(
    verb_infinitive: str,
    pronoun: Pronoun = Pronoun.FIRST_PERSON,
    tense: Tense = Tense.PRESENT,
    direct_object: DirectObject = DirectObject.NONE,
    indirect_object: IndirectObject = IndirectObject.NONE,
    negation: Negation = Negation.NONE,
    is_correct: bool = True,
    validate: bool = False,
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

    # Validate and adjust COD/COI parameters based on verb capabilities
    original_direct_object = direct_object
    original_indirect_object = indirect_object

    # Adjust COD if verb doesn't support it
    if direct_object != DirectObject.NONE and not verb.can_have_cod:
        logger.warning(f"⚠️ Verb '{verb.infinitive}' cannot have COD, setting to none")
        direct_object = DirectObject.NONE

    # Adjust COI if verb doesn't support it
    if indirect_object != IndirectObject.NONE and not verb.can_have_coi:
        logger.warning(f"⚠️ Verb '{verb.infinitive}' cannot have COI, setting to none")
        indirect_object = IndirectObject.NONE

    # If both were requested but only one is supported, choose the supported one
    if (
        original_direct_object != DirectObject.NONE
        and original_indirect_object != IndirectObject.NONE
    ):
        if verb.can_have_cod and not verb.can_have_coi:
            logger.warning(
                f"⚠️ Verb '{verb.infinitive}' supports COD but not COI, keeping COD only"
            )
            indirect_object = IndirectObject.NONE
        elif verb.can_have_coi and not verb.can_have_cod:
            logger.warning(
                f"⚠️ Verb '{verb.infinitive}' supports COI but not COD, keeping COI only"
            )
            direct_object = DirectObject.NONE

    # The CLI passes strings; the service expects enums. We convert them here.
    return await sentence_service.generate_sentence(
        verb_id=verb.id,
        pronoun=Pronoun(pronoun),
        tense=Tense(tense),
        direct_object=DirectObject(direct_object),
        indirect_object=IndirectObject(indirect_object),
        negation=Negation(negation),
        is_correct=is_correct,
        validate=validate,
    )


async def create_random_sentence(is_correct: bool = True):
    """Create a random sentence with client-side parameter selection and validation."""
    sentence_service = SentenceService()
    verb_service = VerbService()

    # Step 1: Generate random grammatical parameters first
    pronoun = random.choice(list(Pronoun))
    tense = random.choice(
        [t for t in Tense if t != Tense.IMPERATIF]
    )  # Avoid imperative for now
    direct_object = random.choice(list(DirectObject))
    indirect_object = random.choice(list(IndirectObject))

    # 70% chance of no negation, 30% chance of random negation
    if random.randint(1, 10) <= 7:
        negation = Negation.NONE
    else:
        negation = random.choice([n for n in Negation if n != Negation.NONE])

    # Step 2: Get a random verb
    verb = await verb_service.get_random_verb()
    if not verb:
        raise ValueError("No verbs available for sentence generation")

    # Step 3: Adjust parameters based on verb capabilities (verb takes precedence)
    original_direct_object = direct_object
    original_indirect_object = indirect_object

    # Disable unsupported features
    if direct_object != DirectObject.NONE and not verb.can_have_cod:
        logger.warning(f"⚠️ Random verb '{verb.infinitive}' cannot have COD, disabling")
        direct_object = DirectObject.NONE

    if indirect_object != IndirectObject.NONE and not verb.can_have_coi:
        logger.warning(f"⚠️ Random verb '{verb.infinitive}' cannot have COI, disabling")
        indirect_object = IndirectObject.NONE

    # If both were selected but only one is supported, choose the supported one
    if (
        original_direct_object != DirectObject.NONE
        and original_indirect_object != IndirectObject.NONE
    ):
        if verb.can_have_cod and not verb.can_have_coi:
            logger.warning(
                f"⚠️ Random verb '{verb.infinitive}' supports COD but not COI, using COD only"
            )
            indirect_object = IndirectObject.NONE
        elif verb.can_have_coi and not verb.can_have_cod:
            logger.warning(
                f"⚠️ Random verb '{verb.infinitive}' supports COI but not COD, using COI only"
            )
            direct_object = DirectObject.NONE

    # Step 4: Generate the sentence with validated parameters
    return await sentence_service.generate_sentence(
        verb_id=verb.id,
        pronoun=pronoun,
        tense=tense,
        direct_object=direct_object,
        indirect_object=indirect_object,
        negation=negation,
        is_correct=is_correct,
    )
