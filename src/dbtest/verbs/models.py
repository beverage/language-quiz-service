from enum import auto

from sqlalchemy import Enum, Table, Column, Integer, String, ForeignKey

from dbtest.database.engine import async_engine
from dbtest.database.metadata import Base, metadata
from dbtest.database.utils import DatabaseStringEnum

from dbtest.utils.prompt_enum import PromptEnum

class Tense(DatabaseStringEnum, PromptEnum):
    present       = auto()
    passe_compose = auto()
    imparfait     = auto()
    future_simple = auto()
    participle    = auto()

conjugation_table = Table("conjugations", metadata,
    Column("id", Integer, primary_key=True),
    # relationship("verbs", cascade="all"),
    Column("verb_id", ForeignKey('verbs.id')),
    # Column('group_id', ForeignKey('verb_groups.id')),
    # Column('mode', Enum(Mode), nullable=False),
    Column('tense', Enum(Tense), nullable=False),
    Column('infinitive', String()),
    Column('first_person_singular', String()),
    Column('second_person_singular', String()),
    Column('third_person_singular', String()),
    Column('first_person_plural', String()),
    Column('second_person_formal', String()),
    Column('third_person_plural', String()),
    extend_existing=False
)

class Conjugation(Base): # pylint: disable=too-few-public-methods
    __table__ = Table('conjugations', metadata, autoload=True, autoload_with=async_engine)

verb_table = Table("verbs", metadata,
    Column("id", Integer, primary_key=True),
    # Column('group_id', ForeignKey('verb_groups.id')),
    Column('infinitive', String()),
    Column('auxiliary', String()),
    extend_existing=False
)

class Verb(Base): # pylint: disable=too-few-public-methods
    __table__ = Table('verbs', metadata, autoload=True, autoload_with=async_engine)
