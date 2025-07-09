
from asyncio import sleep

import logging
import random
import traceback

from typing import List

from cli.ai.client import AsyncChatGPTClient

from cli.sentences.create import create_sentence
from cli.sentences.models import DirectObject, IndirectPronoun, Negation, Sentence
from cli.sentences.utils import problem_formatter

async def create_random_problem_with_delay(openai_client: AsyncChatGPTClient=AsyncChatGPTClient(), display=True):
    await create_random_problem(openai_client=openai_client, display=display)
    await sleep(random.uniform(1.5, 2.0))

async def create_random_problem(openai_client: AsyncChatGPTClient=AsyncChatGPTClient(), display=False):

    #   This will generate all four sentences sequentially to start and be parallelized later.
    answer: int = random.randrange(0, 4)
    openai_client: AsyncChatGPTClient = AsyncChatGPTClient() if openai_client is None else openai_client

    responses: List[Sentence] = []

    try:
        for i in range(4):
            # responses.append(await create_random_sentence(i is answer, openai_client))
            responses.append(await create_sentence("", "", "",
                direct_object    = DirectObject.random,
                indirect_pronoun = IndirectPronoun.random,
                negation         = Negation.none if random.randint(0, 2) == 0 else Negation.random, 
                is_correct       = i is answer))

    except Exception as ex:
        logging.error(traceback.format_exc())

    if display:
        print(problem_formatter(responses))

    return responses
