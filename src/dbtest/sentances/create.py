from asyncio import sleep

from dbtest.ai.client import AsyncChatGPTClient

from dbtest.database.engine import get_async_session
from dbtest.database.metadata import Base

from dbtest.sentances.features import SentenceFeatures
from dbtest.sentances.models import Pronoun, DirectObject, IndirectPronoun
from dbtest.sentances.prompts import SentencePromptGenerator

from dbtest.verbs.get import get_random_verb
from dbtest.verbs.models import Tense

from dbtest.utils.console import Answers, Color, Style

import json
import logging
import random

def select_verb():
    pass

def create_sentence(verb: str):
    pass

async def create_random_sentence(is_correct: bool=True, openapi_client: AsyncChatGPTClient=AsyncChatGPTClient()):

    Sentence = Base.classes.sentences

    db_session = get_async_session()
    verb = await get_random_verb(db_session)

    sentence = Sentence()
    sentence.is_correct = is_correct

    sentence.infinitive = verb.infinitive
    sentence.auxiliary = verb.auxiliary
    sentence.pronoun = random.choice([p for p in Pronoun])

    # This raises the question as to if we even need participles if we are just
    # going to feed the tense right into ChatGTP:
    sentence.tense = random.choice([t for t in Tense if t is not Tense.participle])

    features: SentenceFeatures = SentenceFeatures()
    sentence = features.randomize(sentence)

    generator: SentencePromptGenerator = SentencePromptGenerator()
    prompt: str = generator.generate_sentence_prompt(sentence)
    # logging.info(prompt)

    response: str = await openapi_client.handle_request(prompt=prompt)
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

async def create_random_problem_with_delay(openapi_client: AsyncChatGPTClient=AsyncChatGPTClient(), display=True):
    await create_random_problem(display=display)
    await sleep(random.uniform(0.5, 2.0))

async def create_random_problem(openapi_client: AsyncChatGPTClient=AsyncChatGPTClient(), display=False):

    #   This will generate all four sentences sequentially to start and be parallelized later.
    Sentence = Base.classes.sentences

    answer: int = random.randrange(0, 4)
    openapi_client: AsyncChatGPTClient=AsyncChatGPTClient()

    responses: [Sentence] = []

    for i in range(4):
        responses.append(await create_random_sentence(True if i is answer else False, openapi_client))

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
