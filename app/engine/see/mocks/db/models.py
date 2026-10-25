import uuid
from datetime import datetime
from dataclasses import dataclass, field

@dataclass
class Signal:
    id: uuid.UUID
    ticker: str
    score: float
    sentiment_label: str
    source_count: int
    weighted_score: float = 0.0
    updated_at: datetime = field(default_factory=datetime.utcnow)

@dataclass
class SignalSource:
    id: uuid.UUID
    signal_id: uuid.UUID
    source_type: str
    url: str
    snippet: str
    weight: float

@dataclass
class Watchlist:
    id: uuid.UUID
    user_id: str
    symbol: str
    created_at: datetime = field(default_factory=datetime.utcnow)

class SessionLocal:
    def __init__(self):
        self._data = {}
        self._watchlists = []

    def query(self, model):
        return self

    def filter(self, **kwargs):
        return self

    def all(self):
        if self._data:
            return list(self._data.values())
        return self._watchlists

    def add(self, obj):
        if isinstance(obj, Signal):
            self._data[obj.id] = obj
        elif isinstance(obj, Watchlist):
            self._watchlists.append(obj)

    def commit(self):
        pass
