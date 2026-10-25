from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from db.models import WatchList
from typing import Optional
from pydantic import BaseModel
from fastapi_test_db import get_db

router = APIRouter()

class ThresholdUpdate(BaseModel):
    ticker: str
    threshold: Optional[float] = None
    notify_email: Optional[bool] = None

@router.patch("/thresholds")
async def update_thresholds(payload: ThresholdUpdate, db: Session = Depends(get_db)):
    if not payload.ticker:
        raise HTTPException(status_code=400, detail="Ticker is missing")
    
    # Pydantic handles the numeric check for 'threshold' via the type hint 'float'
    # But we can add an explicit check if we want to be absolutely sure about types
    # when receiving raw data, although FastAPI/Pydantic typically does this.
    
    watchlist_entry = db.query(WatchList).filter(WatchList.ticker == payload.ticker).first()
    if not watchlist_entry:
        raise HTTPException(status_code=400, detail="Ticker not found in WatchList")
    
    if payload.threshold is not None:
        watchlist_entry.alert_threshold = payload.threshold
    
    if payload.notify_email is not None:
        watchlist_entry.notify_email = payload.notify_email
    
    db.commit()
    db.refresh(watchlist_entry)
    
    return {"message": "Updated successfully"}
