from dbtest.database.metadata import Base

from dbtest.ai.client import AsyncChatGPTClient

from dbtest.database.conjugations import Tense
from dbtest.database.engine import get_async_session
from dbtest.database.sentences import Pronoun

from dbtest.sentances.features import SentenceFeatures
from dbtest.sentances.prompts import SentencePromptGenerator
from dbtest.verbs.get import get_random_verb

from dbtest.utils.console import Answers, Color, Style

import json
import logging
import random

def select_verb():
    Conjugation = Base.classes.conjugations
    Verb = Base.classes.verbs
    pass

def create_sentence(verb: str):
    Conjugation = Base.classes.conjugations
    Verb = Base.classes.verbs
    pass

async def create_random_sentence(is_correct: bool=True, openapi_client: AsyncChatGPTClient=AsyncChatGPTClient()):

    Verb = Base.classes.verbs
    Sentence = Base.classes.sentences

    db_session = get_async_session()
    verb: Verb = await get_random_verb(db_session)

    sentence: Sentence = Sentence()
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
    response_json = json.loads(response)
    # logging.info(response_json)

    sentence.content     = response_json["sentence"]
    sentence.translation = response_json["translation"]

    return sentence

async def create_random_problem(openapi_client: AsyncChatGPTClient=AsyncChatGPTClient()):

    #   This will generate all four sentences sequentially to start and be parallelized later.
    Sentence = Base.classes.sentences

    answer: int = random.randrange(0, 4)
    openapi_client: AsyncChatGPTClient=AsyncChatGPTClient()

    print(Style.BOLD + f"Answer will be {answer + 1}:\n" + Style.RESET)
    responses: [Sentence] = []

    for i in range(4):
        responses.append(await create_random_sentence(True if i is answer else False, openapi_client))

    return responses

def problem_formatter(sentences) -> str:

    output: str = ""

    for sentence in sentences:
        output = output + " ".join(
            [Answers.CORRECT if sentence.is_correct is True else Answers.INCORRECT,
             sentence.content,
             f"{Color.BRIGHT_BLUE}({sentence.translation}){Style.RESET}" if sentence.is_correct else "",
            '\n'])

    return output
