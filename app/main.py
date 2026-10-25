from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel
import uuid
from sqlalchemy.orm import Session
from db.database import SessionLocal, engine
from db.models import WatchList, Signal
from db.init_db import init_db
from typing import List
from datetime import datetime
from app.engine.repository import SignalRepository
from app.engine.signal_generator import WeightedSignalEngine

app = FastAPI()

# Initialize DB on startup
init_db()

# Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

class WatchlistRequest(BaseModel):
    ticker: str

class WatchlistEntry(BaseModel):
    id: str
    ticker: str

class TradingSignal(BaseModel):
    symbol: str
    signal: str
    score: float
    timestamp: str

@app.post("/api/v1/watchlist", status_code=201, response_model=WatchlistEntry)
def add_to_watchlist(request: WatchlistRequest, db: Session = Depends(get_db)):
    if not request.ticker or not request.ticker.strip():
        raise HTTPException(status_code=400, detail="Invalid ticker")

    # For this build unit, we assume a constant user_id as no auth is implemented
    user_id = "test-user-uuid"

    # Check for duplicates for the same user
    existing = db.query(WatchList).filter(WatchList.user_id == user_id, WatchList.ticker == request.ticker).first()
    if existing:
        return WatchlistEntry(id=existing.id, ticker=existing.ticker)

    new_entry = WatchList(
        id=str(uuid.uuid4()),
        user_id=user_id,
        ticker=request.ticker.strip().upper()
    )
    db.add(new_entry)
    db.commit()
    db.refresh(new_entry)

    return WatchlistEntry(id=new_entry.id, ticker=new_entry.ticker)

@app.get("/api/signals", response_model=List[TradingSignal])
def get_signals(db: Session = Depends(get_db)):
    user_id = "test-user-uuid"
    watchlist = db.query(WatchList).filter(WatchList.user_id == user_id).all()

    if not watchlist:
        return []

    repo = SignalRepository(session=db)
    engine = WeightedSignalEngine(repository=repo)

    results = []
    for item in watchlist:
        ticker = item.ticker

        # Check if we have a recent signal in the repo
        existing_signal = repo.get_signal_by_ticker(ticker)

        if existing_signal:
            signal_obj = existing_signal
        else:
            # Simulate fetching from 3+ open-source providers
            # In a real scenario, these would be actual API calls
            mock_data = {
                'news': [{'url': 'http://news.com', 'snippet': 'Positive news about ' + ticker}],
                'options': [{'strike': 100, 'expiry': '2026-12-31', 'sentiment': 0.8}],
                'sentiment': [{'source': 'Twitter', 'score': 0.7}]
            }
            signal_obj = engine.generate_signal(ticker, mock_data)

        # Map sentiment label to Trading Signal enum
        mapping = {
            'Bullish': 'BUY',
            'Bearish': 'SELL',
            'Neutral': 'HOLD'
        }

        results.append(TradingSignal(
            symbol=ticker,
            signal=mapping.get(signal_obj.sentiment_label, 'HOLD'),
            score=signal_obj.score,
            timestamp=signal_obj.updated_at.isoformat() if hasattr(signal_obj, 'updated_at') else datetime.utcnow().isoformat()
        ))

    return results
