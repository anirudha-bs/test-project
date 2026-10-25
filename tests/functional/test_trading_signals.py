import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.main import app
from db.database import Base, SessionLocal
from db.models import Watchlist, Signal
import uuid

# Setup test database
TEST_DATABASE_URL = "sqlite:///./test_functional.db"
engine = create_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def setup_module():
    Base.metadata.create_all(bind=engine)

def teardown_module():
    Base.metadata.drop_all(bind=engine)

client = TestClient(app)

def test_add_symbol_to_watchlist():
    """A user adding a symbol to their watchlist sees it persisted."""
    symbol = "AAPL"

    # Use dependency override to use test db
    from app.api.watchlist import get_db as api_get_db
    app.dependency_overrides[api_get_db] = lambda: TestingSessionLocal()

    response = client.post("/api/watchlist/", json={"symbol": symbol})
    app.dependency_overrides.clear()

    assert response.status_code == 201
    data = response.json()
    assert "id" in data
    assert data["symbol"] == symbol

    # Verify persistence
    db = TestingSessionLocal()
    item = db.query(Watchlist).filter(Watchlist.symbol == symbol).first()
    assert item is not None
    assert item.symbol == symbol
    db.close()

def test_add_symbol_invalid_request():
    """An invalid request body returns 422 Unprocessable Entity."""
    # Empty symbol
    response = client.post("/api/watchlist/", json={"symbol": ""})
    assert response.status_code == 422

    # Missing symbol
    response = client.post("/api/watchlist/", json={})
    assert response.status_code == 422

def test_signal_aggregation_and_persistence():
    """Signals are aggregated from providers and persisted with a weighted score."""
    from app.engine.signal_generator import WeightedSignalEngine
    from app.engine.repository import SignalRepository
    from unittest.mock import patch

    db = TestingSessionLocal()
    repo = SignalRepository(session=db)
    engine = WeightedSignalEngine(repository=repo)

    ticker = "TSLA"
    data_feeds = {
        'options': [{'score': 0.8}],
        'sentiment': [{'score': 0.6}],
        'news': [{'score': 0.4}]
    }

    with patch('app.engine.signal_generator.normalize_options_signal', return_value=0.8), \
         patch('app.engine.signal_generator.normalize_sentiment_signal', return_value=0.6), \
         patch('app.engine.signal_generator.normalize_news_signal', return_value=0.4):

        signal = engine.generate_signal(ticker, data_feeds)

        assert signal.score == pytest.approx(0.66)

        db_signal = db.query(Signal).filter(Signal.ticker == ticker).first()
        assert db_signal is not None
        assert db_signal.score == pytest.approx(0.66)
        assert db_signal.sentiment_label == 'Bullish'

    db.close()
