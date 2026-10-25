import pytest
import asyncio
import uuid
from unittest.mock import MagicMock, patch
from app.engine.signal_generator import WeightedSignalEngine, SignalPipelineCoordinator
from app.engine.repository import SignalRepository

class MockSignal:
    def __init__(self, **kwargs):
        for k, v in kwargs.items():
            setattr(self, k, v)
        if not hasattr(self, 'weighted_score'):
            self.weighted_score = getattr(self, 'score', 0.0)


class MockWatchlist:
    def __init__(self, symbol, user_id):
        self.symbol = symbol
        self.user_id = user_id

class MockSession:
    def __init__(self):
        self.signals = {}
        self.watchlists = []
    def add(self, obj):
        if hasattr(obj, 'id') and not hasattr(obj, 'symbol'): # SignalSource
             pass
        elif hasattr(obj, 'id'): # Signal
            self.signals[obj.id] = obj
    def commit(self):
        pass
    def query(self, model):
        return self
    def filter(self, **kwargs):
        return self
    def all(self):
        if hasattr(self, 'watchlists'):
            return self.watchlists
        return []

@pytest.fixture
def setup_pipeline():
    session = MockSession()
    repo = SignalRepository(session=session)
    engine = WeightedSignalEngine(repository=repo)
    coordinator = SignalPipelineCoordinator(engine, repo)
    return coordinator, repo, session

@pytest.mark.asyncio
async def test_happy_path(setup_pipeline):
    """A user with a watchlist of BTC and ETH receives aggregated signals from all providers."""
    coordinator, repo, session = setup_pipeline
    user_id = "user-123"
    session.watchlists = [MockWatchlist("BTC", user_id), MockWatchlist("ETH", user_id)]

    # Mock connectors to return specific scores
    with patch('app.engine.connectors.providers.CryptoPanicConnector.fetch_sentiment', return_value={'score': 0.8}), \
         patch('app.engine.connectors.providers.LunarCrushConnector.fetch_sentiment', return_value={'score': 0.6}), \
         patch('app.engine.connectors.providers.SantimentConnector.fetch_sentiment', return_value={'score': 0.4}), \
         patch('app.engine.signal_generator.Signal', side_effect=lambda **kwargs: MockSignal(**kwargs)):

        signals = await coordinator.process_watchlist(user_id)

        assert len(signals) == 2
        for signal in signals:
            assert signal.sentiment_label == 'BUY'
            assert signal.weighted_score > 0.2

@pytest.mark.asyncio
async def test_conflicting_sentiment(setup_pipeline):
    """Conflicting sentiments from providers are resolved based on weights."""
    coordinator, repo, session = setup_pipeline
    user_id = "user-123"
    session.watchlists = [MockWatchlist("BTC", user_id)]

    # One very bullish, one very bearish, one neutral
    with patch('app.engine.connectors.providers.CryptoPanicConnector.fetch_sentiment', return_value={'score': 1.0}), \
         patch('app.engine.connectors.providers.LunarCrushConnector.fetch_sentiment', return_value={'score': -1.0}), \
         patch('app.engine.connectors.providers.SantimentConnector.fetch_sentiment', return_value={'score': 0.0}), \
         patch('app.engine.signal_generator.Signal', side_effect=lambda **kwargs: MockSignal(**kwargs)):

        signals = await coordinator.process_watchlist(user_id)

        # Avg = (1.0 + -1.0 + 0.0) / 3 = 0.0 -> HOLD
        assert signals[0].sentiment_label == 'HOLD'

@pytest.mark.asyncio
async def test_empty_watchlist(setup_pipeline):
    """No signals are generated when the watchlist is empty."""
    coordinator, repo, session = setup_pipeline
    user_id = "user-123"
    session.watchlists = []

    signals = await coordinator.process_watchlist(user_id)
    assert len(signals) == 0

@pytest.mark.asyncio
async def test_api_failure(setup_pipeline):
    """The system still generates signals when one provider is down."""
    coordinator, repo, session = setup_pipeline
    user_id = "user-123"
    session.watchlists = [MockWatchlist("BTC", user_id)]

    with patch('app.engine.connectors.providers.CryptoPanicConnector.fetch_sentiment', side_effect=Exception("API Down")), \
         patch('app.engine.connectors.providers.LunarCrushConnector.fetch_sentiment', return_value={'score': 0.8}), \
         patch('app.engine.connectors.providers.SantimentConnector.fetch_sentiment', return_value={'score': 0.6}), \
         patch('app.engine.signal_generator.Signal', side_effect=lambda **kwargs: MockSignal(**kwargs)):

        signals = await coordinator.process_watchlist(user_id)

        # Should still produce a signal from the other 2
        assert len(signals) == 1
        assert signals[0].sentiment_label == 'BUY'
