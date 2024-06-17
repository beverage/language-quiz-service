# from asyncio import Lock, Event
import logging
import traceback

from typing import AsyncGenerator
from contextlib import asynccontextmanager
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker

from .metadata import Base

async_engine = create_async_engine("postgresql+asyncpg://postgres:postgres@localhost/language_app")

# reflection_lock: Lock  = Lock()
# reflection_done: Event = Event()

AsyncSessionLocal = async_sessionmaker(
    bind=async_engine,
    class_=AsyncSession,
    expire_on_commit=False
)

@asynccontextmanager
async def get_async_session() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception as e:
            await session.rollback()
            logging.error(traceback.format_exc())
            raise e
        finally:
            await session.close()

async def reflect_tables():
    #   There could be sublte race conditions depending on table loading.
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.prepare, reflect=True)

    # global reflection_lock
    # async with reflection_lock:
    #     if not reflection_done:
    #         async with async_engine.begin() as conn:
    #             await conn.run_sync(metadata.reflect)
    #             await conn.run_sync(Base.prepare)
    #         reflection_done.set()

# async def get_orm():
#     reflection_done.wait()
#     return Base.classes
