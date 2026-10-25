import pytest
from unittest.mock import MagicMock
from app.engine.signal_generator import WeightedSignalEngine
from app.engine.repository import SignalRepository

@pytest.fixture
def mock_repo():
    return MagicMock(spec=SignalRepository)

@pytest.fixture
def engine(mock_repo):
    return WeightedSignalEngine(repository=mock_repo)

def test_scoring_accuracy(engine, mock_repo):
    # Provide sentiment data from 3 mocked providers
    # We assume the normalizers are mocked or the data is pre-normalized for this unit test
    # If we want to test the WeightedSignalEngine's internal logic,
    # we need to control what normalize_sentiment_signal returns.

    # For simplicity in this unit test, we'll mock the data_feeds and the
    # internal normalizers if possible, or provide data that we know how normalizers handle.
    # However, the engine uses functions imported from other modules.

    # Let's mock the normalizers.
    import app.engine.signal_generator
    original_norm = app.engine.signal_generator.normalize_sentiment_signal
    app.engine.signal_generator.normalize_sentiment_signal = MagicMock(return_value=0.8)

    data_feeds = {
        'sentiment': [{'url': 'api1', 'snippet': 'good'}, {'url': 'api2', 'snippet': 'great'}]
    }

    # weight for sentiment is 0.3
    # total_weighted_score = 0.8 * 0.3 = 0.24
    # total_weight_used = 0.3
    # final_score = 0.24 / 0.3 = 0.8

    signal = engine.generate_signal("AAPL", data_feeds)
    assert signal.score == 0.8
    app.engine.signal_generator.normalize_sentiment_signal = original_norm

def test_label_mapping(engine, mock_repo):
    # Verify that specific score ranges map correctly to 'buy', 'hold', and 'sell' signals.
    # Requirements specify 'buy', 'hold', 'sell'.
    # Current code uses 'Bullish', 'Bearish', 'Neutral'.

    # Test Buy
    import app.engine.signal_generator
    original_norm = app.engine.signal_generator.normalize_sentiment_signal

    app.engine.signal_generator.normalize_sentiment_signal = MagicMock(return_value=0.8)
    signal = engine.generate_signal("AAPL", {'sentiment': [{}]})
    assert signal.sentiment_label == 'buy'

    # Test Sell
    app.engine.signal_generator.normalize_sentiment_signal = MagicMock(return_value=-0.8)
    signal = engine.generate_signal("AAPL", {'sentiment': [{}]})
    assert signal.sentiment_label == 'sell'

    # Test Hold
    app.engine.signal_generator.normalize_sentiment_signal = MagicMock(return_value=0.0)
    signal = engine.generate_signal("AAPL", {'sentiment': [{}]})
    assert signal.sentiment_label == 'hold'

    app.engine.signal_generator.normalize_sentiment_signal = original_norm

def test_edge_cases_zero_providers(engine, mock_repo):
    data_feeds = {}
    signal = engine.generate_signal("AAPL", data_feeds)
    assert signal.score == 0.0
    assert signal.sentiment_label == 'hold'

def test_edge_cases_null_sentiment(engine, mock_repo):
    import app.engine.signal_generator
    original_norm = app.engine.signal_generator.normalize_sentiment_signal
    app.engine.signal_generator.normalize_sentiment_signal = MagicMock(return_value=None)

    # This might crash the current implementation (norm_score * weight) if norm_score is None
    # The test should verify it handles it gracefully.
    try:
        signal = engine.generate_signal("AAPL", {'sentiment': [{}]})
        assert signal.score == 0.0
    except TypeError:
        pytest.fail("Engine crashed on None sentiment score")
    finally:
        app.engine.signal_generator.normalize_sentiment_signal = original_norm
