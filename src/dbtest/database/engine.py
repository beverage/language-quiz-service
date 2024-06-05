from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.ext.automap import automap_base
from sqlalchemy.ext.declarative import declarative_base

from .metadata import metadata

async_engine = create_async_engine("postgresql+asyncpg://postgres:postgres@localhost/language_app")

Base = automap_base()
Base.metadata = metadata
# Session = sessionmaker(bind=async_engine, class_=AsyncSession)

# metadata = Base.metadata
# metadata.bind = async_engine
# metadata.reflect(bind=async_engine)

# Base.metadata.reflect(async_engine)

async def reflect_tables():
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.prepare, reflect=True)
        
    Conjugations = Base.classes.conjugations
    Verbs = Base.classes.verbs
            