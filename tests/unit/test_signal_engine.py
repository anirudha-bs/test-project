import pytest
from unittest.mock import MagicMock
from app.engine.signal_generator import WeightedSignalEngine
from app.engine.repository import SignalRepository
from db.models import Signal

@pytest.fixture
def mock_repo():
    return MagicMock(spec=SignalRepository)

@pytest.fixture
def engine(mock_repo):
    return WeightedSignalEngine(repository=mock_repo)

def test_weighted_score_calculation(engine, mock_repo):
    """Verify that WeightedSignalEngine correctly aggregates weights from multiple providers."""
    ticker = "BTC"
    # Mock data: options=0.8, sentiment=0.6, news=0.4
    # Weights: options=0.5, sentiment=0.3, news=0.2
    # Expected: (0.8*0.5 + 0.6*0.3 + 0.4*0.2) / (0.5+0.3+0.2) = (0.4 + 0.18 + 0.08) / 1.0 = 0.66
    data_feeds = {
        'options': [{'score': 0.8}],
        'sentiment': [{'score': 0.6}],
        'news': [{'score': 0.4}]
    }

    # Need to mock the normalizers because WeightedSignalEngine calls them.
    # But the current implementation in signal_generator.py imports them.
    # Let's patch them.
    import app.engine.signal_generator
    from unittest.mock import patch

    with patch('app.engine.signal_generator.normalize_options_signal', return_value=0.8), \
         patch('app.engine.signal_generator.normalize_sentiment_signal', return_value=0.6), \
         patch('app.engine.signal_generator.normalize_news_signal', return_value=0.4):

        mock_repo.save_signal.return_value = "some-uuid"

        signal = engine.generate_signal(ticker, data_feeds)

        assert signal.score == pytest.approx(0.66)
        assert signal.sentiment_label == 'Bullish'

def test_label_mapping(engine, mock_repo):
    """Test that scores are correctly mapped to 'Bullish', 'Bearish', or 'Neutral'."""
    # Test Bullish (> 0.2)
    assert engine._get_sentiment_label(0.3) == 'Bullish'
    # Test Bearish (< -0.2)
    assert engine._get_sentiment_label(-0.3) == 'Bearish'
    # Test Neutral
    assert engine._get_sentiment_label(0.1) == 'Neutral'

def test_edge_case_neutral_sentiment(engine, mock_repo):
    """Test behavior when all providers return neutral sentiment."""
    ticker = "BTC"
    data_feeds = {
        'options': [{'score': 0.0}],
        'sentiment': [{'score': 0.0}],
        'news': [{'score': 0.0}]
    }

    import app.engine.signal_generator
    from unittest.mock import patch

    with patch('app.engine.signal_generator.normalize_options_signal', return_value=0.0), \
         patch('app.engine.signal_generator.normalize_sentiment_signal', return_value=0.0), \
         patch('app.engine.signal_generator.normalize_news_signal', return_value=0.0):

        mock_repo.save_signal.return_value = "some-uuid"
        signal = engine.generate_signal(ticker, data_feeds)

        assert signal.score == 0.0
        assert signal.sentiment_label == 'Neutral'
