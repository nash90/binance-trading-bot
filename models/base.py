# coding=utf-8
from configs.config import config

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy_utils import create_database, database_exists

url = config.get("db").get("db_url")
db_type = config.get("db").get("db_type")
username = config.get("db").get("db_username")
password = config.get("db").get("db_password")
full_url = db_type+'://'+username+':'+password + '@'+ url
db_file = 'data.db'
if config.get("db").get("db_type") == "sqlite":
    full_url = db_type+':///'+db_file

engine = create_engine(full_url)
if not database_exists(engine.url):
    create_database(engine.url)
#engine = create_engine(full_url)
Session = sessionmaker(bind=engine)
Base = declarative_base()
Base.metadata.create_all(engine)