import pytest
from fastapi.testclient import TestClient
from unittest.mock import MagicMock, patch
from app.main import app, get_db
from db.models import Signal, WatchList
from datetime import datetime

client = TestClient(app)

@pytest.fixture
def setup_db():
    mock_db = MagicMock()
    app.dependency_overrides[get_db] = lambda: mock_db
    yield mock_db
    app.dependency_overrides = {}

def test_positive_sentiment_buy_signal(setup_db):
    """Symbols with high positive sentiment across providers return a "BUY" signal with a positive score."""
    db = setup_db
    btc_item = MagicMock(spec=WatchList)
    btc_item.ticker = 'BTC'
    db.query.return_value.filter.return_value.all.return_value = [btc_item]

    with patch('app.engine.repository.SignalRepository.get_signal_by_ticker', return_value=None), \
         patch('app.engine.signal_generator.WeightedSignalEngine.generate_signal') as mock_gen:

        mock_gen.return_value = Signal(ticker='BTC', score=0.8, sentiment_label='Bullish', updated_at=datetime.utcnow())

        response = client.get("/api/signals")

        assert response.status_code == 200
        data = response.json()
        assert len(data) > 0
        assert data[0]['symbol'] == 'BTC'
        assert data[0]['signal'] == 'BUY'
        assert data[0]['score'] == 0.8

def test_negative_sentiment_sell_signal(setup_db):
    """Symbols with high negative sentiment across providers return a "SELL" signal with a negative score."""
    db = setup_db
    eth_item = MagicMock(spec=WatchList)
    eth_item.ticker = 'ETH'
    db.query.return_value.filter.return_value.all.return_value = [eth_item]

    with patch('app.engine.repository.SignalRepository.get_signal_by_ticker', return_value=None), \
         patch('app.engine.signal_generator.WeightedSignalEngine.generate_signal') as mock_gen:

        mock_gen.return_value = Signal(ticker='ETH', score=-0.7, sentiment_label='Bearish', updated_at=datetime.utcnow())

        response = client.get("/api/signals")

        assert response.status_code == 200
        data = response.json()
        assert len(data) > 0
        assert data[0]['symbol'] == 'ETH'
        assert data[0]['signal'] == 'SELL'
        assert data[0]['score'] == -0.7

def test_mixed_sentiment_hold_signal(setup_db):
    """Symbols with conflicting or low-confidence sentiment return a "HOLD" signal."""
    db = setup_db
    sol_item = MagicMock(spec=WatchList)
    sol_item.ticker = 'SOL'
    db.query.return_value.filter.return_value.all.return_value = [sol_item]

    with patch('app.engine.repository.SignalRepository.get_signal_by_ticker', return_value=None), \
         patch('app.engine.signal_generator.WeightedSignalEngine.generate_signal') as mock_gen:

        mock_gen.return_value = Signal(ticker='SOL', score=0.05, sentiment_label='Neutral', updated_at=datetime.utcnow())

        response = client.get("/api/signals")

        assert response.status_code == 200
        data = response.json()
        assert len(data) > 0
        assert data[0]['symbol'] == 'SOL'
        assert data[0]['signal'] == 'HOLD'

def test_empty_watchlist_returns_empty_array(setup_db):
    """GET /api/signals returns 200 and an empty array when no symbols are tracked."""
    db = setup_db
    db.query.return_value.filter.return_value.all.return_value = []

    response = client.get("/api/signals")
    assert response.status_code == 200
    assert response.json() == []
