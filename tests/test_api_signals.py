import pytest
from fastapi.testclient import TestClient
from unittest.mock import MagicMock, patch
from app.main import app, get_db
from db.models import Signal, WatchList
from datetime import datetime

client = TestClient(app)

def test_get_signals_success():
    """Successful Retrieval: Request signals for a valid watchlist; assert status_code == 200 and response is a list of TradingSignal objects."""
    mock_db = MagicMock()
    btc_item = MagicMock()
    btc_item.ticker = 'BTC'
    eth_item = MagicMock()
    eth_item.ticker = 'ETH'
    mock_db.query.return_value.filter.return_value.all.return_value = [btc_item, eth_item]

    app.dependency_overrides[get_db] = lambda: mock_db
    try:
        with patch('app.engine.repository.SignalRepository.get_signal_by_ticker') as mock_get_signal:
            mock_get_signal.side_effect = [
                Signal(ticker='BTC', score=0.8, sentiment_label='Bullish', updated_at=datetime.utcnow()),
                Signal(ticker='ETH', score=-0.5, sentiment_label='Bearish', updated_at=datetime.utcnow()),
            ]

            response = client.get("/api/signals")

            assert response.status_code == 200
            data = response.json()
            assert isinstance(data, list)
            assert len(data) == 2

            for item in data:
                assert 'symbol' in item
                assert 'signal' in item
                assert 'score' in item
                assert 'timestamp' in item
                assert item['signal'] in ['BUY', 'HOLD', 'SELL']
    finally:
        app.dependency_overrides = {}

def test_get_signals_schema_validation():
    """Schema Validation: Verify each object in the response contains required fields with correct types."""
    mock_db = MagicMock()
    btc_item = MagicMock()
    btc_item.ticker = 'BTC'
    mock_db.query.return_value.filter.return_value.all.return_value = [btc_item]

    app.dependency_overrides[get_db] = lambda: mock_db
    try:
        with patch('app.engine.repository.SignalRepository.get_signal_by_ticker') as mock_get_signal:
            mock_get_signal.return_value = Signal(ticker='BTC', score=0.5, sentiment_label='Bullish', updated_at=datetime.utcnow())

            response = client.get("/api/signals")
            data = response.json()[0]

            assert isinstance(data['symbol'], str)
            assert data['signal'] in ['BUY', 'HOLD', 'SELL']
            assert isinstance(data['score'], (int, float))
            datetime.fromisoformat(data['timestamp'].replace('Z', '+00:00'))
    finally:
        app.dependency_overrides = {}

def test_get_signals_empty_watchlist():
    """Empty Watchlist: Request signals for a user with no symbols; assert status_code == 200 and response is []."""
    mock_db = MagicMock()
    mock_db.query.return_value.filter.return_value.all.return_value = []

    app.dependency_overrides[get_db] = lambda: mock_db
    try:
        response = client.get("/api/signals")
        assert response.status_code == 200
        assert response.json() == []
    finally:
        app.dependency_overrides = {}

def test_get_signals_resolution():
    """Signal Resolution: Verify that the score returned in the API matches the weighted_score stored in the repository."""
    mock_db = MagicMock()
    btc_item = MagicMock()
    btc_item.ticker = 'BTC'
    mock_db.query.return_value.filter.return_value.all.return_value = [btc_item]

    app.dependency_overrides[get_db] = lambda: mock_db
    try:
        with patch('app.engine.repository.SignalRepository.get_signal_by_ticker') as mock_get_signal:
            expected_score = 0.75
            mock_get_signal.return_value = Signal(ticker='BTC', score=expected_score, sentiment_label='Bullish', updated_at=datetime.utcnow())

            response = client.get("/api/signals")
            data = response.json()[0]
            assert data['score'] == expected_score
    finally:
        app.dependency_overrides = {}
