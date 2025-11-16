"""
CLI sentence operations - MIGRATED.

Migrated to use Supabase services instead of SQLAlchemy.
Maintained for backward compatibility.
"""

import asyncio
import logging
import random

import asyncclick

from src.cli.utils.decorators import output_format_options
from src.cli.utils.formatters import format_output
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


@asyncclick.command()
@output_format_options
@asyncclick.argument("verb_infinitive", type=str, required=True)
@asyncclick.option("--pronoun", type=Pronoun, default=Pronoun.FIRST_PERSON)
@asyncclick.option("--tense", type=Tense, default=Tense.PRESENT)
@asyncclick.option("--direct_object", type=DirectObject, default=DirectObject.NONE)
@asyncclick.option(
    "--indirect_object", type=IndirectObject, default=IndirectObject.NONE
)
@asyncclick.option("--negation", type=Negation, default=Negation.NONE)
@asyncclick.option("--is_correct", type=bool, default=True)
async def create_sentence(
    verb_infinitive: str,
    pronoun: Pronoun = Pronoun.FIRST_PERSON,
    tense: Tense = Tense.PRESENT,
    direct_object: DirectObject = DirectObject.NONE,
    indirect_object: IndirectObject = IndirectObject.NONE,
    negation: Negation = Negation.NONE,
    is_correct: bool = True,
    output_json: bool = False,
    output_format: str = "pretty",
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
    sentence = await sentence_service.generate_sentence(
        verb_id=verb.id,
        pronoun=Pronoun(pronoun),
        tense=Tense(tense),
        direct_object=DirectObject(direct_object),
        indirect_object=IndirectObject(indirect_object),
        negation=Negation(negation),
        is_correct=is_correct,
    )

    formatted_output = format_output(sentence, output_json, output_format)
    asyncclick.echo(formatted_output)


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


@asyncclick.command()
@output_format_options
@asyncclick.argument("quantity", type=int, default=1)
async def create_random_sentence_batch(
    quantity: int, output_json: bool, output_format: str, **kwargs
):
    """Create a batch of random sentences."""
    max_concurrent = min(10, quantity)

    # Create coroutines for parallel execution
    tasks = [create_random_sentence(**kwargs) for _ in range(quantity)]

    # Execute in batches of max_concurrent with error handling
    results = []
    for i in range(0, len(tasks), max_concurrent):
        batch = tasks[i : i + max_concurrent]
        try:
            batch_results = await asyncio.gather(*batch, return_exceptions=True)

            # Filter out exceptions and collect successful results
            for result in batch_results:
                if isinstance(result, Exception):
                    print(f"Warning: Failed to generate sentence: {result}")
                else:
                    results.append(result)

            # Small delay between batches to avoid overwhelming the API
            if i + max_concurrent < len(tasks):
                await asyncio.sleep(0.5)

        except Exception as ex:
            print(f"Batch failed: {ex}")

    # Print results for successful downloads
    for result in results:
        formatted_output = format_output(result, output_json, output_format)
        asyncclick.echo(formatted_output)
