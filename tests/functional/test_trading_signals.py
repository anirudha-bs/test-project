import pytest
from fastapi.testclient import TestClient
from app.main import app, get_db
from db.database import SessionLocal, engine
from db.models import Base, WatchList, Signal, SignalSource

def override_get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db
client = TestClient(app)

@pytest.fixture(autouse=True)
def setup_db():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)

def test_watchlist_persistence():
    """A user can add a ticker to their watch list and it is persisted."""
    response = client.post("/api/v1/watchlist", json={"ticker": "MSFT"})
    assert response.status_code == 201

    db = SessionLocal()
    ticker = db.query(WatchList).filter(WatchList.ticker == "MSFT").first()
    assert ticker is not None
    db.close()

def test_signal_generation_storage():
    """Consolidated sentiment scores are generated and stored in signals table."""
    db = SessionLocal()
    signal = Signal(
        ticker="MSFT",
        score=0.85,
        sentiment_label="Bullish",
        source_count=5
    )
    db.add(signal)
    db.commit()

    retrieved = db.query(Signal).filter(Signal.ticker == "MSFT").first()
    assert retrieved is not None
    assert retrieved.score == 0.85
    db.close()

def test_signal_source_attribution():
    """Signal sources include attribution URLs and snippets in signal_sources table."""
    db = SessionLocal()
    signal = Signal(ticker="MSFT", score=0.85, sentiment_label="Bullish", source_count=1)
    db.add(signal)
    db.commit()

    source = SignalSource(
        signal_id=signal.id,
        source_type="news",
        url="https://example.com/news/1",
        snippet="MSFT is growing fast",
        weight=0.5
    )
    db.add(source)
    db.commit()

    retrieved_source = db.query(SignalSource).filter(SignalSource.signal_id == signal.id).first()
    assert retrieved_source is not None
    assert retrieved_source.url == "https://example.com/news/1"
    db.close()

def test_signal_source_referential_integrity():
    """A record cannot be inserted into signal_sources without a valid signal_id."""
    db = SessionLocal()
    from sqlalchemy.exc import IntegrityError

    with pytest.raises(IntegrityError):
        source = SignalSource(
            signal_id="non-existent-uuid",
            source_type="news",
            url="https://example.com",
            snippet="fail",
            weight=0.1
        )
        db.add(source)
        db.commit()
    db.close()
