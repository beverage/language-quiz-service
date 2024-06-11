from asyncio import ensure_future, gather
from ..verbs.get import fetch_verb

auxiliaries: list[str] = ["avoir", "être"]
irregulars: list[str] = ["aller", "devoir", "dire", "faire", "pouvoir", "prendre", "savoir", "venir", "voir", "vouloir"]

async def init_auxiliaries(with_common_irregulars=False):

    tasks = []

    verbs = auxiliaries + irregulars if with_common_irregulars else auxiliaries

    for verb in verbs:
        task = ensure_future(fetch_verb(requested_verb=verb))
        tasks.append(task)
        
    await gather(*tasks, return_exceptions=True)

