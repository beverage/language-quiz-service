import aiohttp
from asyncio import ensure_future, gather
from ..verbs.get import fetch_verb

auxiliaries: list[str] = ["avoir", "être"]
irregulars: list[str] = ["aller", "faire", "pouvoir", "savoir", "vouloir"]

#   Still under construction:
async def init_auxiliaries():
    async with aiohttp.ClientSession() as session:
        tasks = []
        
        for auxiliare in auxiliaries:
            task = ensure_future(fetch_verb(async_session=session, requested_verb=auxiliare, save_verb=True))
            tasks.append(task)
            
        await gather(*tasks, return_exceptions=True)

