from ..verbs.get import fetch_verb

from sqlalchemy import create_engine, and_
from sqlalchemy.orm import Session, sessionmaker

engine  = create_engine("postgresql+asyncpg://postgres:postgres@localhost/language_app")
Session = sessionmaker(bind = engine)
session = Session()
