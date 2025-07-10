"""
CLI sentence operations - MIGRATED.

Migrated to use Supabase services instead of SQLAlchemy.
Maintained for backward compatibility.
"""

import logging
import random
from json.decoder import JSONDecodeError

from cli.ai.client import AsyncChatGPTClient
from cli.sentences.prompts import SentencePromptGenerator
from cli.sentences.utils import clean_json_output
from schemas.sentence import (
    SentenceCreate,
    Pronoun,
    DirectObject,
    IndirectPronoun,
    Negation,
)
from schemas.verb import Tense
from services.sentence_service import SentenceService
from services.verb_service import VerbService


async def create_sentence(
    verb_infinitive: str,
    pronoun: Pronoun = Pronoun.FIRST_PERSON,
    tense: Tense = Tense.PRESENT,
    direct_object: DirectObject = DirectObject.NONE,
    indirect_pronoun: IndirectPronoun = IndirectPronoun.NONE,
    negation: Negation = Negation.NONE,
    is_correct: bool = True,
    openai_client: AsyncChatGPTClient = None,
):
    """Create a sentence using AI - migrated to use Supabase services."""

    if openai_client is None:
        openai_client = AsyncChatGPTClient()

    verb_service = VerbService()
    sentence_service = SentenceService()

    # Get verb
    if verb_infinitive == "":
        verb = await verb_service.get_random_verb()
    else:
        verb = await verb_service.get_verb_by_infinitive(verb_infinitive)

    if not verb:
        raise ValueError(f"Verb {verb_infinitive} not found")

    # Create sentence structure
    sentence_data = {
        "infinitive": verb.infinitive,
        "auxiliary": verb.auxiliary,
        "pronoun": random.choice(list(Pronoun)),
        "tense": random.choice([t for t in Tense if t != Tense.PARTICIPLE]),
        "is_correct": is_correct,
        "direct_object": direct_object,
        "indirect_pronoun": indirect_pronoun,
        "negation": negation,
    }

    # Generate prompt
    generator = SentencePromptGenerator()

    # Create a temporary sentence object for the prompt
    class TempSentence:
        def __init__(self, data):
            for key, value in data.items():
                setattr(self, key, value)

    temp_sentence = TempSentence(sentence_data)
    prompt = generator.generate_sentence_prompt(temp_sentence)

    logging.debug(prompt)

    # Get AI response
    response = await openai_client.handle_request(prompt=prompt)

    try:
        response_json = clean_json_output(response)
    except JSONDecodeError as ex:
        logging.error(f"Unable to decode json response: {response}")
        raise ex

    # Update sentence with AI response
    sentence_data.update(
        {
            "content": response_json["sentence"],
            "translation": response_json["translation"],
            "tense": sentence_data["tense"].value,  # Convert enum to string value
            "pronoun": sentence_data["pronoun"].value,  # Convert enum to string value
            "negation": response_json["negation"],
            "direct_object": response_json["direct_object"],
            "indirect_pronoun": response_json["indirect_pronoun"],
            "reflexive_pronoun": "none",  # Temporarily set to none
        }
    )

    # Validate correctness if needed
    if is_correct:
        # Create a new temp sentence with content for validation
        temp_sentence_with_content = TempSentence(sentence_data)
        correctness_response = await openai_client.handle_request(
            prompt=generator.validate_french_sentence_prompt(temp_sentence_with_content)
        )
        is_actually_correct = correctness_response.strip() == "True"

        logging.debug(
            f"Checked that '{sentence_data['content']}' is well formed: {is_actually_correct}"
        )

        if not is_actually_correct:
            logging.debug(
                f"Sentence {sentence_data['content']} is not well formed, and will be updated."
            )
            correction = await openai_client.handle_request(
                prompt=generator.correct_sentence_prompt(temp_sentence_with_content)
            )

            try:
                correction_json = clean_json_output(correction)
            except JSONDecodeError as ex:
                logging.error(f"Unable to decode json response: {correction}")
                raise ex

            sentence_data.update(
                {
                    "content": correction_json["corrected_sentence"],
                    "translation": correction_json["corrected_translation"],
                }
            )

            logging.debug(f"Sentence was updated to '{sentence_data['content']}'")

    # Save sentence using the service
    sentence_create = SentenceCreate(**sentence_data)
    saved_sentence = await sentence_service.create_sentence(sentence_create)

    return saved_sentence


async def create_random_sentence(
    is_correct: bool = True, openai_client: AsyncChatGPTClient = None
):
    """Create a random sentence - migrated to use Supabase services."""

    return await create_sentence(
        "",
        "",
        "",  # Verb, pronoun, and tense remain fully random for now.
        direct_object=DirectObject.NONE,  # Use correct enum values
        indirect_pronoun=IndirectPronoun.NONE,
        negation=Negation.NONE
        if random.randint(0, 2) == 0
        else random.choice([n for n in Negation if n != Negation.NONE]),
        is_correct=is_correct,
        openai_client=openai_client,
    )
