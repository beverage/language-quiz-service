from asyncio import sleep

import json
import logging
import random
import traceback

from typing import List

from dbtest.ai.client import AsyncChatGPTClient

from dbtest.database.engine import get_async_session

from dbtest.sentences.features import SentenceFeatures, SentenceFeaturesOld, DirectObjectFeature, IndirectPronounFeature, NegationFeature
from dbtest.sentences.models import Pronoun, DirectObject, IndirectPronoun, Negation, Sentence
from dbtest.sentences.prompts import SentencePromptGenerator

from dbtest.verbs.get import get_random_verb, get_verb
from dbtest.verbs.models import Tense, Verb

from dbtest.utils.console import Answers, Color, Style

async def create_sentence(verb_infinitive: str,
                          pronoun:                  Pronoun=Pronoun.first_person,   # Pronoun and tense will remain both random
                          tense:                      Tense=Tense.present,          # and correct for now.  These values will be
                          direct_object:       DirectObject=DirectObject.none,      # ignored.
                          indirect_pronoun: IndirectPronoun=IndirectPronoun.none,
                          negation:                Negation=Negation.none,
                          is_correct:                  bool=True,                   # This cannot be guaranteed until the AI has responded.
                          openai_client: AsyncChatGPTClient=AsyncChatGPTClient()):

    async with get_async_session() as db_session:

        verb: Verb = None

        if verb_infinitive is None:
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

        # Sentence features:
        sentence.direct_object    = direct_object
        sentence.indirect_pronoun = indirect_pronoun
        sentence.negation         = negation

        generator: SentencePromptGenerator = SentencePromptGenerator()
        prompt: str = generator.generate_sentence_prompt(sentence)

        response: str = await openai_client.handle_request(prompt=prompt)
        logging.debug(response)
        response_json = json.loads(response)

        sentence.content     = response_json["sentence"]
        sentence.translation = response_json["translation"]

        if response_json["has_direct_object"] is False:
            sentence.direct_object = DirectObject.none

        if response_json["has_indirect_pronoun"] is False:
            sentence.indirect_pronoun = IndirectPronoun.none

        return sentence


async def create_random_sentence(is_correct: bool=True, openai_client: AsyncChatGPTClient=AsyncChatGPTClient()):

    async with get_async_session() as session:

        verb = await get_random_verb(database_session=session)

        sentence = Sentence()
        sentence.is_correct = is_correct

        sentence.infinitive = verb.infinitive
        sentence.auxiliary = verb.auxiliary
        sentence.pronoun = random.choice(list(Pronoun))

        # This raises the question as to if we even need participles if we are just
        # going to feed the tense right into ChatGTP:
        sentence.tense = random.choice([t for t in Tense if t is not Tense.participle])

        features: SentenceFeaturesOld = SentenceFeaturesOld()
        sentence = features.randomize(sentence)

        generator: SentencePromptGenerator = SentencePromptGenerator()
        prompt: str = generator.generate_sentence_prompt(sentence)
        logging.debug(prompt)

        response: str = await openai_client.handle_request(prompt=prompt)
        logging.debug(response)
        response_json = json.loads(response)

        sentence.content     = response_json["sentence"]
        sentence.translation = response_json["translation"]

        # It is not always possible to generate a sentence with a COD or a COI (or both)
        # for certain verbs.  Rather than trying to force the issue with whitelists or
        # blacklists, lets just store the results as it will be sometime else querying
        # for sentences from the database by features anyways.  We will take it as the best
        # the AI can do:

        if response_json["has_direct_object"] is False:
            sentence.direct_object = DirectObject.none

        if response_json["has_indirect_pronoun"] is False:
            sentence.indirect_pronoun = IndirectPronoun.none

        return sentence

async def create_random_problem_with_delay(openai_client: AsyncChatGPTClient=AsyncChatGPTClient(), display=True):
    await create_random_problem(openai_client=openai_client, display=display)
    await sleep(random.uniform(0.5, 2.0))

async def create_random_problem(openai_client: AsyncChatGPTClient=AsyncChatGPTClient(), display=False):

    #   This will generate all four sentences sequentially to start and be parallelized later.
    answer: int = random.randrange(0, 4)
    openai_client: AsyncChatGPTClient = AsyncChatGPTClient() if openai_client is None else openai_client

    responses: List[Sentence] = []

    try:
        for i in range(4):
            # responses.append(await create_random_sentence(i is answer, openai_client))
            responses.append(await create_sentence(verb_infinitive="savoir", is_correct=i is answer))
    except Exception as ex:
        logging.error(traceback.format_exc())

    if display:
        print(problem_formatter(responses))

    return responses

def problem_formatter(sentences) -> str:

    output: str = ""

    for sentence in sentences:
        output = output + " ".join(
            [Answers.CORRECT if sentence.is_correct is True else Answers.INCORRECT,
             f"{Color.LIGHT_GRAY}{"COD" if sentence.direct_object is not DirectObject.none else "---"}{Style.RESET}",
             f"{Color.LIGHT_GRAY}{"COI" if sentence.indirect_pronoun is not IndirectPronoun.none else "---"}{Style.RESET}",
             sentence.content,
             f"{Color.BRIGHT_BLUE}({sentence.translation}){Style.RESET}" if sentence.is_correct else "",
            '\n'])

    return output
