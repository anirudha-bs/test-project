import uuid
from datetime import datetime
from dataclasses import dataclass, field
from typing import Optional

@dataclass
class Signal:
    id: uuid.UUID
    ticker: str
    score: float
    sentiment_label: str
    source_count: int
    updated_at: datetime = field(default_factory=datetime.utcnow)
    weighted_score: Optional[float] = None

@dataclass
class SignalSource:
    id: uuid.UUID
    signal_id: uuid.UUID
    source_type: str
    url: str
    snippet: str
    weight: float

class MockSession:
    def __init__(self):
        self.signals = {}
        self.sources = {}

    def query(self, model):
        return self

    def filter(self, **kwargs):
        return self

    def all(self):
        return list(self.signals.values())

    def add(self, obj):
        if isinstance(obj, Signal):
            self.signals[obj.id] = obj
        elif isinstance(obj, SignalSource):
            self.sources[obj.id] = obj

    def commit(self):
        pass

SessionLocal = MockSession
