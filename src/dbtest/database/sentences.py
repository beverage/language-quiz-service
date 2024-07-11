import enum
from enum import Enum, auto

from dbtest.database.conjugations import Tense

from sqlalchemy import Enum, Table, Column, Integer, String, Boolean
from sqlalchemy.orm import registry

from .metadata import metadata

mapper_registry = registry(metadata=metadata)

class Pronoun(enum.Enum):
    first_person         = auto(),
    second_person        = auto(),
    third_person         = auto(),
    first_person_plural  = auto(),
    second_person_plural = auto(),
    third_person_plural  = auto()

class DirectObject(enum.Enum):
    none      = auto(),
    masculine = auto(),
    feminine  = auto(),
    plural    = auto()
    
class IndirectObject(enum.Enum):
    none     = auto(),
    singular = auto(),
    plural   = auto()
    
class ReflexivePronoun(enum.Enum):
    none = auto(),
    me = auto(),
    te = auto(),
    se = auto()
    
class Negation(enum.Enum):
    none     = auto(),
    pas      = auto(),
    jamais   = auto(),
    rien     = auto(),
    personne = auto(),
    plus     = auto(),
    aucun    = auto(),
    encore   = auto()

sentence_table = Table("sentences", metadata,
    Column("id", Integer, primary_key=True),
    # Column('group_id', ForeignKey('verb_groups.id')),
    Column('infinitive',        String(),               nullable=False),
    Column('auxiliary',         String(),               nullable=False),
    Column('pronoun',           Enum(Pronoun),          nullable=False, default=Pronoun.first_person),
    Column('tense',             Enum(Tense),            nullable=False, default=Tense.present),
    Column('direct_object',     Enum(DirectObject),     nullable=False, default=DirectObject.none),
    Column('indirect_object',   Enum(IndirectObject),   nullable=False, default=IndirectObject.none),
    Column('reflexive_pronoun', Enum(ReflexivePronoun), nullable=False, default=ReflexivePronoun.none),
    Column('negation',          Enum(Negation),         nullable=False, default=Negation.none),
    Column('content',           String(),               nullable=False),
    Column('translation',       String(),               nullable=False),
    Column('is_correct',        Boolean(),              nullable=False, default=True),
    extend_existing=False
)

class Sentence:
    pass

mapper_registry.map_imperatively(Sentence, sentence_table)
