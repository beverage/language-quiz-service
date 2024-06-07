import enum
from enum import Enum, auto

from sqlalchemy import Table, Column, Enum, Integer, String

from .metadata import metadata

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

# Verb = Base.classes.verbs
