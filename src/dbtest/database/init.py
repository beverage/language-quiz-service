from asyncio import gather, Semaphore
from dbtest.ai.client import AsyncChatGPTClient
from dbtest.verbs.get import download_verb

# Hardcore some verbs for now.  We will load verb lists later.
auxiliaries: list[str] = ["avoir", "être"]
irregulars: list[str] = ["aller", "devoir", "dire", "faire", "pouvoir", "prendre", "savoir", "venir", "voir", "vouloir"]
pronominals: list[str] = ["se sentir", "se souvenir"]

# Artificial lower bound for testing.  Will make this high enough for the hard coded verbs for now.
limit = Semaphore(17)

async def rate_limited_verb_fetch(verb: str, openapi_client: AsyncChatGPTClient):
    async with limit:
        await download_verb(requested_verb=verb, openapi_client=openapi_client)

async def init_auxiliaries(with_common_verbs=False):
    openapi_client: AsyncChatGPTClient = AsyncChatGPTClient()
    verbs = auxiliaries + irregulars + pronominals if with_common_verbs else auxiliaries
    tasks = [rate_limited_verb_fetch(verb=verb, openapi_client=openapi_client) for verb in verbs]
    await gather(*tasks, return_exceptions=True)
