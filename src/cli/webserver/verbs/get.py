from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import sessionmaker

from cli.database.engine import async_engine
from cli.verbs.models import conjugation_table, verb_table

async_session = sessionmaker(async_engine, class_=AsyncSession, expire_on_commit=False)

async def get_verb_and_conjugations(infinitive: str):
    async with async_session() as session:
        result = await session.execute(
            select(verb_table).where(verb_table.c.infinitive == infinitive)
        )

        verb_row = result.fetchone()
        if not verb_row:
            return None

        verb_id   = verb_row.id
        auxiliary = verb_row.auxiliary

        result = await session.execute(
            select(conjugation_table).where(conjugation_table.c.verb_id == verb_id)
        )

        conjugations = []

        for row in result.fetchall():
            conjugation = {
                "tense": row.tense.name,
                "infinitive": row.infinitive
            }

            conjugation_fields = [
                c.name for c in conjugation_table.columns
                if c.name not in ("id", "verb_id", "tense", "infinitive")
            ]

            for field in conjugation_fields:
                value = getattr(row, field)

                if value is not None:
                    conjugation[field] = value.replace("_", " ")

            conjugations.append(conjugation)

        return {
            "infinitive": verb_row.infinitive,
            "auxiliary": auxiliary,
            "conjugations": conjugations
        }
