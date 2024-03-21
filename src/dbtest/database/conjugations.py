import enum
from enum import Enum, auto

from sqlalchemy import Table, Column, Enum, Integer, String, MetaData, create_engine
from sqlalchemy.ext.automap import automap_base

#   This highly suggests that temporal-ness should be a property in itself:
class Tense(enum.Enum):
    present       = auto()
    passe_compose = auto()
    imparfait     = auto()
    future_simple = auto()
    participle    = auto()

engine   = create_engine("postgresql://postgres:postgres@localhost/language_app")
metadata = MetaData()

metadata.reflect(engine, only=["conjugations"], extend_existing=True)

conjugation_table = Table("conjugations", metadata,
    Column("id", Integer, primary_key=True),
    # Column("verb_id", ForeignKey('verbs.id')),
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
    extend_existing=True
)

Base = automap_base(metadata=metadata)
Base.prepare()

Conjugation = Base.classes.conjugations
