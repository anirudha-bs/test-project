from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from db.database import get_db
from db.models import Watchlist
from app.schemas import WatchlistAdd, WatchlistItem
import uuid

router = APIRouter(prefix="/api/watchlist", tags=["watchlist"])

@router.post("/", response_model=WatchlistItem, status_code=status.HTTP_201_CREATED)
def add_to_watchlist(item: WatchlistAdd, db: Session = Depends(get_db)):
    # In a real app, user_id would come from auth. Using a constant for now.
    user_id = "00000000-0000-0000-0000-000000000000"

    db_item = Watchlist(
        id=str(uuid.uuid4()),
        user_id=user_id,
        symbol=item.symbol
    )
    db.add(db_item)
    db.commit()
    db.refresh(db_item)
    return db_item
