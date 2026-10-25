from pydantic import BaseModel, Field
from uuid import UUID
from datetime import datetime

class WatchlistAdd(BaseModel):
    symbol: str = Field(..., min_length=1)

class WatchlistItem(BaseModel):
    id: UUID
    symbol: str

    class Config:
        from_attributes = True
