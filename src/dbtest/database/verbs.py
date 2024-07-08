import enum
from enum import Enum, auto

from sqlalchemy import Table, Column, Integer, String
from sqlalchemy.orm import registry

from .metadata import metadata

mapper_registry = registry(metadata=metadata)

verb_table = Table("verbs", metadata,
    Column("id", Integer, primary_key=True),
    # Column('group_id', ForeignKey('verb_groups.id')),
    Column('infinitive', String()),
    Column('auxiliary', String()),
    extend_existing=False
)

class Verb:
    pass

mapper_registry.map_imperatively(Verb, verb_table)
