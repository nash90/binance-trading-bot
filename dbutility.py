from base import Base
from base import engine
from base import Session

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