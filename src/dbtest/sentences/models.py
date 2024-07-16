from enum import auto
from sqlalchemy import Enum, Table, Column, Integer, String, Boolean

from dbtest.database.engine import async_engine
from dbtest.database.metadata import metadata
from dbtest.utils.prompt_enum import PromptEnum
from dbtest.verbs.models import Tense

class Pronoun(PromptEnum):
    first_person         = auto()
    second_person        = auto()
    third_person         = auto()
    first_person_plural  = auto()
    second_person_plural = auto()
    third_person_plural  = auto()

class DirectObject(PromptEnum):
    none      = auto()
    masculine = auto()
    feminine  = auto()
    plural    = auto()

class IndirectPronoun(PromptEnum):
    none      = auto()
    masculine = auto()
    feminine  = auto()
    plural    = auto()

class ReflexivePronoun(PromptEnum):
    none          = auto()
    first_person  = auto()
    second_person = auto()
    third_person  = auto()

class Negation(PromptEnum):
    none     = auto()
    pas      = auto()
    jamais   = auto()
    rien     = auto()
    personne = auto()
    plus     = auto()
    aucun    = auto()
    encore   = auto()

sentence_table = Table("sentences", metadata,
    Column("id", Integer, primary_key=True),
    # Column('group_id', ForeignKey('verb_groups.id')),
    Column('infinitive',        String(),               nullable=False),
    Column('auxiliary',         String(),               nullable=False),
    Column('pronoun',           Enum(Pronoun),          nullable=False, default=Pronoun.first_person),
    Column('tense',             Enum(Tense),            nullable=False, default=Tense.present),
    Column('direct_object',     Enum(DirectObject),     nullable=False, default=DirectObject.none),
    Column('indirect_object',   Enum(IndirectPronoun),  nullable=False, default=IndirectPronoun.none),
    Column('reflexive_pronoun', Enum(ReflexivePronoun), nullable=False, default=ReflexivePronoun.none),
    Column('negation',          Enum(Negation),         nullable=False, default=Negation.none),
    Column('content',           String(),               nullable=False),
    Column('translation',       String(),               nullable=False),
    Column('is_correct',        Boolean(),              nullable=False, default=True),
    extend_existing=False
)

class Sentence: # pylint: disable=too-few-public-methods
    __table__ = Table('sentences', metadata, autoload=True, autoload_with=async_engine)
