import enum
from enum import Enum, auto

from dbtest.utils.prompt_enum import PromptEnum

from sqlalchemy import Table, Column, ForeignKey, Enum, Integer, String

from .metadata import metadata

#   This highly suggests that temporal-ness should be a property in itself:
class Tense(PromptEnum):
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

# Conjugation = Base.classes.conjugations
