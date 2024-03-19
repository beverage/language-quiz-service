import enum
from enum import Enum, auto

from sqlalchemy import Table, Column, Enum, Integer, String, MetaData, create_engine
from sqlalchemy.ext.automap import automap_base

# verb_table = Table(
#     "verbs",
#     mapper_registry.metadata,
#     Column("id", Integer, primary_key=True),
#     # Column('group_id', ForeignKey('verb_groups.id')),
#     Column('infinitive', String()),
#     Column('auxiliary', String()),
#     Column('is_reflexive', Boolean())
# )