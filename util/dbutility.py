from models.base import Base
from models.base import engine
from models.base import Session

def sessionCommit(session):
    try:  
        session.commit()
    except Exception as e:
        #print(e)
        session.rollback()
        raise e

def addDataToDB(session, obj):
  obj = session.add(obj)
  sessionCommit(session)


def createTableIfNotExit():
    return Base.metadata.create_all(engine)