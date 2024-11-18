from enum import auto

from sqlalchemy.ext.asyncio import AsyncAttrs

from dbtest.database.metadata import Base
from dbtest.database.utils import DatabaseStringEnum

from dbtest.utils.prompt_enum import PromptEnum

class Pronoun(DatabaseStringEnum, PromptEnum):
    first_person         = auto()
    second_person        = auto()
    third_person         = auto()
    first_person_plural  = auto()
    second_person_plural = auto()
    third_person_plural  = auto()

class DirectObject(DatabaseStringEnum, PromptEnum):
    none      = auto()
    masculine = auto()
    feminine  = auto()
    plural    = auto()
    random    = auto()

class IndirectPronoun(DatabaseStringEnum, PromptEnum):
    none      = auto()
    masculine = auto()
    feminine  = auto()
    plural    = auto()
    random    = auto()

class ReflexivePronoun(DatabaseStringEnum, PromptEnum):
    none          = auto()
    first_person  = auto()
    second_person = auto()
    third_person  = auto()

class Negation(DatabaseStringEnum, PromptEnum):
    none     = auto()
    pas      = auto()
    jamais   = auto()
    rien     = auto()
    personne = auto()
    plus     = auto()
    aucun    = auto()
    aucune   = auto()
    encore   = auto()
    random   = auto()

class Sentence(AsyncAttrs, Base): # pylint: disable=too-few-public-methods
    __tablename__ = "sentences"
