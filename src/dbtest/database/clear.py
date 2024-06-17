from sqlalchemy import delete

from .engine import get_async_session
from .metadata import Base

async def clear_database():

    Verb = Base.classes.verbs

    async with get_async_session() as session:
        await session.execute(delete(Verb))
