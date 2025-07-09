from sqlalchemy import delete

from cli.database.engine import get_async_session
from cli.verbs.models import Verb

async def clear_database():

    async with get_async_session() as session:
        await session.execute(delete(Verb))
