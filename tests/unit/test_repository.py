import pytest
from unittest.mock import MagicMock
from app.engine.repository import SignalRepository

@pytest.fixture
def mock_session():
    return MagicMock()

@pytest.fixture
def repo(mock_session):
    return SignalRepository(session=mock_session)

def test_persistence_weighted_score(repo, mock_session):
    # Save a signal using SignalRepository and verify the 'weighted_score' float is stored
    # Requirement: "extend existing SignalRepository to include weighted_score float"

    ticker = "AAPL"
    score = 0.75
    label = "buy"
    count = 5

    # The current save_signal takes (ticker, score, sentiment_label, source_count)
    # We need to check if it saves 'weighted_score'.
    # Since the current implementation uses 'score' as the name,
    # the requirement might mean renaming 'score' to 'weighted_score' or adding it.
    # Given the context, 'weighted_score' is likely the final aggregated score.

    repo.save_signal(ticker, score, label, count)

    # Verify the call to the session.add() was made with a Signal object containing weighted_score
    args, _ = mock_session.add.call_args
    signal = args[0]

    # We expect the Signal object to have a weighted_score attribute
    assert hasattr(signal, 'weighted_score')
    assert signal.weighted_score == score
