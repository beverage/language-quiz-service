from dbtest.database.metadata import Base

from dbtest.ai.client import AsyncChatGPTClient

from dbtest.database.conjugations import Tense
from dbtest.database.engine import get_async_session
from dbtest.database.metadata import metadata
from dbtest.database.sentences import Pronoun

from dbtest.sentances.prompts import SentencePromptGenerator
from dbtest.verbs.get import get_random_verb

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

async def create_random_problem(openapi_client: AsyncChatGPTClient=AsyncChatGPTClient()):

    #   This will generate all four sentences sequentially to start and be parallelized later.
    Sentence = Base.classes.sentences

    answer: int = random.randrange(0, 4)
    openapi_client: AsyncChatGPTClient=AsyncChatGPTClient()

    print(f"Answer {answer} will be correct.")
    responses: [Sentence] = []

    for i in range(4):
        responses.append(await create_random_sentence(True if i is answer else False, openapi_client))

    return responses

def problem_formatter(sentences) -> str:

    output: str = ""

    for sentence in sentences:
        output = output + f"""[{"X" if sentence.is_correct is True else " "}] {sentence.content}\n"""

    return output

async def create_random_sentence(is_correct: bool=True, openapi_client: AsyncChatGPTClient=AsyncChatGPTClient()):

    Verb = Base.classes.verbs
    Sentence = Base.classes.sentences

    db_session = get_async_session()
    verb: Verb = await get_random_verb(db_session)

    sentence: Sentence = Sentence()
    sentence.infinitive = verb.infinitive
    sentence.auxiliary = verb.auxiliary
    sentence.pronoun = random.choice([p for p in Pronoun])

    # This raises the question as to if we even need participles if we are just
    # going to feed the tense right into ChatGTP:
    sentence.tense = random.choice([t for t in Tense if t is not Tense.participle])

    sentence.is_correct = is_correct

    generator: SentencePromptGenerator = SentencePromptGenerator()
    prompt: str = generator.generate_sentence_prompt(sentence)
    logging.debug(prompt)

    response: str = await openapi_client.handle_request(prompt=prompt)
    response_json = json.loads(response)
    logging.debug(response_json)

    sentence.content = response_json["sentence"]
    return sentence
