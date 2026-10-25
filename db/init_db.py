from db.database import engine, Base
from db.models import WatchList, Signal, SignalSource

def init_db():
    Base.metadata.create_all(bind=engine)
