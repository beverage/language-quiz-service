from asyncio import gather, Semaphore
from ..verbs.get import fetch_verb

# Hardcore some verbs for now.  We will load verb lists later.
auxiliaries: list[str] = ["avoir", "être"]
irregulars: list[str] = ["aller", "devoir", "dire", "faire", "pouvoir", "prendre", "savoir", "venir", "voir", "vouloir"]

# Artificial lower bound for testing.  Will make this high enough for the hard coded verbs for now.
limit = Semaphore(15)

async def rate_limited_verb_fetch(verb: str):
    async with limit:
        await fetch_verb(requested_verb=verb)

async def init_auxiliaries(with_common_irregulars=False):

    verbs = auxiliaries + irregulars if with_common_irregulars else auxiliaries
    tasks = [rate_limited_verb_fetch(verb=verb) for verb in verbs]
        
    await gather(*tasks, return_exceptions=True)

