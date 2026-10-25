import uuid
from datetime import datetime
from typing import List, Optional

try:
    from db.models import Signal, SignalSource, SessionLocal
except ImportError:
    from .see.mocks.db.models import Signal, SignalSource, SessionLocal

class SignalRepository:
    def __init__(self, session=None):
        self.session = session or SessionLocal()

    def get_signal_by_ticker(self, ticker: str) -> Optional[Signal]:
        # Simplified mock query behavior
        res = self.session.query(Signal).filter(ticker=ticker).all()
        return res[0] if res else None

    def save_signal(self, ticker: str, score: float, sentiment_label: str, source_count: int) -> uuid.UUID:
        signal = Signal(
            id=uuid.uuid4(),
            ticker=ticker,
            score=score,
            weighted_score=score,
            sentiment_label=sentiment_label,
            source_count=source_count,
            updated_at=datetime.utcnow()
        )
        self.session.add(signal)
        self.session.commit()
        return signal.id

    def save_signal_source(self, signal_id: uuid.UUID, source_type: str, url: str, snippet: str, weight: float):
        source = SignalSource(
            id=uuid.uuid4(),
            signal_id=signal_id,
            source_type=source_type,
            url=url,
            snippet=snippet,
            weight=weight
        )
        self.session.add(source)
        self.session.commit()
