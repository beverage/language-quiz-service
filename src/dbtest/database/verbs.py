import enum
from enum import Enum, auto

from sqlalchemy import Table, Column, Enum, Integer, String, MetaData, create_engine
from sqlalchemy.ext.automap import automap_base

class Reflexivity(enum.Enum):
    no          = auto()
    conditional = auto()
    mandatory   = auto()

engine   = create_engine("postgresql://postgres:postgres@localhost/language_app")
metadata = MetaData()

metadata.reflect(engine, only=["verbs"], extend_existing=True)

verb_table = Table("verbs", metadata,
    Column("id", Integer, primary_key=True),
    # Column('group_id', ForeignKey('verb_groups.id')),
    Column('infinitive', String()),
    Column('auxiliary', String()),
    Column('reflexivity', Enum(Reflexivity), nullable=False, default=Reflexivity.no),
    extend_existing=True
)

Base = automap_base(metadata=metadata)
Base.prepare()

Verb = Base.classes.verbs
