
from ..database.engine import AsyncSession, get_async_session

from .models import Pronoun, DirectObject, IndirectPronoun, Negation, Sentence
from ..verbs.models import Tense

from sqlalchemy import select
from sqlalchemy.sql.expression import func

async def get_random_sentence(
                    quantity:         int,
                    verb_infinitive:  str,
                    pronoun:          Pronoun         = Pronoun.first_person,   # Pronoun and tense will remain both random
                    tense:            Tense           = Tense.present,          # and correct for now.  These values will be
                    direct_object:    DirectObject    = DirectObject.none,      # ignored.
                    indirect_pronoun: IndirectPronoun = IndirectPronoun.none,
                    negation:         Negation        = Negation.none,
                    is_correct:       bool            = True):                   # This cannot be guaranteed until the AI has responded.

    async with get_async_session() as session:

        stmt = (
            select(Sentence)
                .where(Sentence.infinitive == verb_infinitive)
                .where(Sentence.is_correct == is_correct)
                .order_by(func.random())
                .limit(quantity)
        )

        return await session.scalars(stmt)

async def save_sentence(sentence: Sentence):
    async with get_async_session() as session:
        session.add(sentence)
        await session.commit()
