
from ..database.engine import AsyncSession, get_async_session, Base
from .models import Pronoun, Tense, DirectObject, IndirectPronoun, Negation, Sentence

from sqlalchemy import inspect
from sqlalchemy import select

import logging

async def get_sentence(quantity:         int,
                       verb_infinitive:  str,
                       pronoun:          Pronoun         = Pronoun.first_person,   # Pronoun and tense will remain both random
                       tense:            Tense           = Tense.present,          # and correct for now.  These values will be
                       direct_object:    DirectObject    = DirectObject.none,      # ignored.
                       indirect_pronoun: IndirectPronoun = IndirectPronoun.none,
                       negation:         Negation        = Negation.none,
                       is_correct:       bool            = True):                   # This cannot be guaranteed until the AI has responded.

    async with get_async_session() as session:

        stmt = select(Sentence).where(Sentence.infinitive == verb_infinitive).limit(quantity)

        logging.info(str(stmt))

        sentence: Sentence = (
            await session.execute(stmt)
        )

        return sentence

async def save_sentence(sentence: Sentence):
    async with get_async_session() as session:
        session.add(sentence)
        await session.commit()
