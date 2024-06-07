from sqlalchemy import MetaData
from sqlalchemy.ext.automap import automap_base

metadata = MetaData()

Base = automap_base()
Base.metadata = metadata