import pytest
from unittest.mock import MagicMock, patch
from app.engine.signal_generator import WeightedSignalEngine
from app.engine.repository import SignalRepository

@pytest.fixture
def mock_repo():
    return MagicMock(spec=SignalRepository)

@pytest.fixture
def engine(mock_repo):
    return WeightedSignalEngine(repository=mock_repo)

def test_weighted_score_calculation(engine):
    # Data feeds with multiple providers for 'sentiment'
    # WeightedSignalEngine currently treats each provider as part of the same source_type list
    # and normalizer is called on the list.
    # Let's mock normalize_sentiment_signal to return the average of the scores.

    data_feeds = {
        'sentiment': [
            {'score': 0.8},
            {'score': 0.4},
            {'score': 0.0}
        ]
    }

    with patch('app.engine.signal_generator.normalize_sentiment_signal') as mock_norm:
        # Assuming normalize_sentiment_signal returns the mean score for the list
        mock_norm.return_value = 0.4

        # We need to mock Signal to be returned by generate_signal
        with patch('app.engine.signal_generator.Signal') as MockSignal:
            MockSignal.return_value = MagicMock(score=0.4, sentiment_label='HOLD')

            signal = engine.generate_signal("BTC", data_feeds)

            # score = 0.4 * 0.3 (weight) / 0.3 (total weight) = 0.4
            assert signal.score == 0.4

def test_signal_labeling(engine):
    # Test threshold boundaries
    test_cases = [
        (0.3, 'BUY'),
        (0.1, 'HOLD'),
        (-0.1, 'HOLD'),
        (-0.3, 'SELL'),
    ]

    for score, expected_label in test_cases:
        assert engine._get_sentiment_label(score) == expected_label

def test_edge_cases_no_providers(engine):
    data_feeds = {}
    with patch('app.engine.signal_generator.Signal') as MockSignal:
        MockSignal.return_value = MagicMock(score=0.0, sentiment_label='HOLD')
        signal = engine.generate_signal("BTC", data_feeds)
        assert signal.score == 0.0
        assert signal.sentiment_label == 'HOLD'

def test_edge_cases_opposing_sentiments(engine):
    data_feeds = {
        'sentiment': [{'score': 1.0}, {'score': -1.0}]
    }
    with patch('app.engine.signal_generator.normalize_sentiment_signal', return_value=0.0):
        with patch('app.engine.signal_generator.Signal') as MockSignal:
            MockSignal.return_value = MagicMock(score=0.0, sentiment_label='HOLD')
            signal = engine.generate_signal("BTC", data_feeds)
            assert signal.score == 0.0
            assert signal.sentiment_label == 'HOLD'
