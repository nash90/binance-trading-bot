
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
