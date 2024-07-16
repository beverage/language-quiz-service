from sqlalchemy import delete

from dbtest.database.engine import get_async_session
from dbtest.verbs.models import Verb

async def clear_database():

    async with get_async_session() as session:
        await session.execute(delete(Verb))
