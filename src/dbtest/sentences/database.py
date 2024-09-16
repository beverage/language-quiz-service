
from ..database.engine import AsyncSession, get_async_session
from .models import Pronoun, Sentence, Tense, DirectObject, IndirectPronoun, Negation

async def get_sentence(verb_infinitive:  str,
                       pronoun:          Pronoun         = Pronoun.first_person,   # Pronoun and tense will remain both random
                       tense:            Tense           = Tense.present,          # and correct for now.  These values will be
                       direct_object:    DirectObject    = DirectObject.none,      # ignored.
                       indirect_pronoun: IndirectPronoun = IndirectPronoun.none,
                       negation:         Negation        = Negation.none,
                       is_correct:       bool            = True,                   # This cannot be guaranteed until the AI has responded.
                       openai_client:    AsyncSession    = get_async_session()):

    async with get_async_session() as session:
        # The sentence is returned as a DTO.
        pass

async def save_sentence(sentence: Sentence):
    async with get_async_session() as session:
        session.add(sentence)
        await session.commit()
