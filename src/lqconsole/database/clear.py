from sqlalchemy import delete

from lqconsole.database.engine import get_async_session
from lqconsole.verbs.models import Verb

async def clear_database():

    async with get_async_session() as session:
        await session.execute(delete(Verb))
