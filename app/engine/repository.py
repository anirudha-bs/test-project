import uuid
from datetime import datetime
from typing import List, Optional

try:
    from db.models import Signal, SignalSource, SessionLocal, Watchlist
except ImportError:
    from .see.mocks.db.models import Signal, SignalSource, SessionLocal, Watchlist


class SignalRepository:
    def __init__(self, session=None):
        self.session = session or SessionLocal()

    def get_watchlist_symbols(self, user_id: str) -> List[str]:
        # Implementation for getting symbols from watchlists table
        res = self.session.query(Watchlist).filter(user_id=user_id).all()
        return [item.symbol for item in res]

    def get_signal_by_ticker(self, ticker: str) -> Optional[Signal]:

        # Simplified mock query behavior
        res = self.session.query(Signal).filter(ticker=ticker).all()
        return res[0] if res else None

    def save_signal(self, ticker: str, score: float, sentiment_label: str, source_count: int, weighted_score: float = None) -> uuid.UUID:
        signal = Signal(
            id=uuid.uuid4(),
            ticker=ticker,
            score=score,
            sentiment_label=sentiment_label,
            source_count=source_count,
            weighted_score=weighted_score if weighted_score is not None else score,
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
