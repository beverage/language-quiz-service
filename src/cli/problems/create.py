"""
CLI problem creation - UPDATED.

Updated to use migrated sentence functions.
"""

from asyncio import sleep
import logging
import random
import traceback

from cli.ai.client import AsyncChatGPTClient
from cli.sentences.create import create_sentence
from cli.sentences.utils import problem_formatter
from schemas.sentence import DirectObject, IndirectPronoun, Negation


async def create_random_problem_with_delay(
    openai_client: AsyncChatGPTClient = None, display=True
):
    await create_random_problem(openai_client=openai_client, display=display)
    await sleep(random.uniform(1.5, 2.0))


async def create_random_problem(
    openai_client: AsyncChatGPTClient = None, display=False
):
    """Create a random problem with 4 sentences."""

    # This will generate all four sentences sequentially to start and be parallelized later.
    answer: int = random.randrange(0, 4)
    openai_client: AsyncChatGPTClient = (
        AsyncChatGPTClient() if openai_client is None else openai_client
    )

    responses = []

    try:
        for i in range(4):
            sentence = await create_sentence(
                "",
                "",
                "",  # Verb, pronoun, and tense remain fully random for now.
                direct_object=DirectObject.NONE,  # Use correct enum values
                indirect_pronoun=IndirectPronoun.NONE,
                negation=Negation.NONE
                if random.randint(0, 2) == 0
                else random.choice([n for n in Negation if n != Negation.NONE]),
                is_correct=(i == answer),
                openai_client=openai_client,
            )
            responses.append(sentence)

    except Exception:
        logging.error(traceback.format_exc())

    if display:
        print(problem_formatter(responses))

    return responses
