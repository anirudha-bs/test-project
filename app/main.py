from fastapi import FastAPI
from db.database import engine, Base
from app.api import watchlist

# Create database tables
Base.metadata.create_all(bind=engine)

app = FastAPI(title="Trading Signals API")

app.include_router(watchlist.router)

@app.get("/")
def root():
    return {"message": "Welcome to Trading Signals API"}
