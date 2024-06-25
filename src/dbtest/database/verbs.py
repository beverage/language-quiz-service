import enum
from enum import Enum, auto

from sqlalchemy import Table, Column, Enum, Integer, String
from sqlalchemy.orm import registry

from .metadata import metadata

mapper_registry = registry(metadata=metadata)

class Reflexivity(enum.Enum):
    no          = auto()
    conditional = auto()
    mandatory   = auto()

verb_table = Table("verbs", metadata,
    Column("id", Integer, primary_key=True),
    # Column('group_id', ForeignKey('verb_groups.id')),
    Column('infinitive', String()),
    Column('auxiliary', String()),
    Column('reflexivity', Enum(Reflexivity), nullable=False, default=Reflexivity.no),
    extend_existing=False
)

class Verb:
    pass

mapper_registry.map_imperatively(Verb, verb_table)
# Verb = Base.classes.verbs
