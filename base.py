# coding=utf-8

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy_utils import create_database, database_exists
from config import config

db_type = config.get("db").get("type")
db_file = config.get("db").get("file")
full_url = db_type+':///'+db_file
engine = create_engine(full_url)
if not database_exists(engine.url):
    create_database(engine.url)
#engine = create_engine(full_url)
Session = sessionmaker(bind=engine)
Base = declarative_base()
Base.metadata.create_all(engine)