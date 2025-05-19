from json.decoder import JSONDecodeError

import logging
import random

from lqconsole.ai.client import AsyncChatGPTClient

from lqconsole.database.engine import get_async_session

from lqconsole.sentences.database import save_sentence
from lqconsole.sentences.models import Pronoun, DirectObject, IndirectPronoun, Negation, Sentence
from lqconsole.sentences.prompts import SentencePromptGenerator
from lqconsole.sentences.utils import clean_json_output

from lqconsole.verbs.get import get_random_verb, get_verb
from lqconsole.verbs.models import Tense, Verb

async def create_sentence(verb_infinitive:  str,
                          pronoun:          Pronoun         = Pronoun.first_person,   # Pronoun and tense will remain both random
                          tense:            Tense           = Tense.present,          # and correct for now.  These values will be
                          direct_object:    DirectObject    = DirectObject.none,      # ignored.
                          indirect_pronoun: IndirectPronoun = IndirectPronoun.none,
                          negation:         Negation        = Negation.none,
                          is_correct:       bool            = True,                   # This cannot be guaranteed until the AI has responded.
                          openai_client: AsyncChatGPTClient = AsyncChatGPTClient()):

    async with get_async_session() as db_session:

        verb: Verb = None

        if verb_infinitive == "":
            verb = await get_random_verb(database_session=db_session)
        else:
            verb = await get_verb(requested_verb=verb_infinitive, database_session=db_session)

        sentence = Sentence()

        # Sentence basics:
        sentence.infinitive = verb.infinitive
        sentence.auxiliary  = verb.auxiliary
        sentence.pronoun    = random.choice(list(Pronoun))
        sentence.tense      = random.choice([t for t in Tense if t is not Tense.participle])
        sentence.is_correct = is_correct

        # Sentence features.  These may be overwritten by the response json.  (Always will for 'random'.)
        sentence.direct_object    = direct_object
        sentence.indirect_pronoun = indirect_pronoun
        sentence.negation         = negation

        generator: SentencePromptGenerator = SentencePromptGenerator()

        prompt:   str = generator.generate_sentence_prompt(sentence)

        logging.debug(prompt)

        response: str = await openai_client.handle_request(prompt=prompt)

        try:
            response_json = clean_json_output(response)
        except JSONDecodeError as ex:
            logging.error(f"Unable to decode json response: {response}")
            raise ex

        sentence.content     = response_json["sentence"]
        sentence.translation = response_json["translation"]

        # The Promptable extension requires the full base enum name so we have to do this here.  That can be changed later.
        sentence.tense   = str(sentence.tense)
        sentence.pronoun = str(sentence.pronoun)

        sentence.negation          = response_json["negation"]
        sentence.direct_object     = response_json["direct_object"]
        sentence.indirect_pronoun  = response_json["indirect_pronoun"]
        sentence.reflexive_pronoun = "none" # Temporarily set this to none to not break things before removed, unless kept.

        # If a sentence is supposed to be correct, double check it, as the prompts to generate it are overly complicated right now.
        if is_correct:

            correctness_response = await openai_client.handle_request(prompt=generator.validate_french_sentence_prompt(sentence))
            is_actually_correct: bool = correctness_response.strip() == "True"

            logging.debug(f"Checked that '{sentence.content}' is well formed: {is_actually_correct}")

            if is_actually_correct == False:

                logging.debug(f"Sentence {sentence.content} is not well formed, and will be updated.")
                correction = await openai_client.handle_request(prompt=generator.correct_sentence_prompt(sentence))

                try:
                    correction_json = clean_json_output(correction)
                except JSONDecodeError as ex:
                    logging.error(f"Unable to decode json response: {correction}")
                    raise ex

                sentence.content     = correction_json["corrected_sentence"]
                sentence.translation = correction_json["corrected_translation"]

                logging.debug(f"Sentence was updated to '{sentence.content}'")

        await save_sentence(sentence=sentence)

        return sentence

async def create_random_sentence(is_correct: bool=True, openai_client: AsyncChatGPTClient=AsyncChatGPTClient()):

    return await create_sentence("", "", "",    # Verb, pronoun, and tense remain fully random for now.
        direct_object       = DirectObject.random, 
        indirect_pronoun    = IndirectPronoun.random, 
        negation         = Negation.none if random.randint(0, 2) == 0 else Negation.random, 
        is_correct          = is_correct, 
        openai_client       = openai_client)
