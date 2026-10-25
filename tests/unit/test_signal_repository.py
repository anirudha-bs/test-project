import pytest
import uuid
from unittest.mock import MagicMock, patch
from app.engine.repository import SignalRepository

class MockSignal:
    def __init__(self, **kwargs):
        for k, v in kwargs.items():
            setattr(self, k, v)

class MockSession:
    def __init__(self):
        self.data = {}
    def add(self, obj):
        self.data[obj.id] = obj
    def commit(self):
        pass
    def query(self, model):
        return self
    def filter(self, **kwargs):
        return self
    def all(self):
        return list(self.data.values())

@pytest.fixture
def repo():
    session = MockSession()
    return SignalRepository(session=session)

def test_save_signal_persistence(repo):
    ticker = "BTC"
    score = 0.5
    label = "BUY"
    count = 3
    weighted_score = 0.5

    # Mock Signal class to use MockSignal
    with patch('app.engine.repository.Signal', side_effect=MockSignal):
        signal_id = repo.save_signal(ticker, score, label, count, weighted_score)

        # Verify it was saved in the mock session
        saved_signal = repo.session.data[signal_id]
        assert saved_signal.ticker == ticker
        assert saved_signal.score == score
        assert saved_signal.sentiment_label == label
        assert saved_signal.weighted_score == weighted_score
        assert isinstance(saved_signal.weighted_score, float)

def test_save_signal_source_persistence(repo):
    signal_id = uuid.uuid4()
    source_type = "sentiment"
    url = "http://test.com"
    snippet = "test snippet"
    weight = 0.3

    with patch('app.engine.repository.SignalSource') as MockSource:
        MockSource.return_value = MagicMock(id=uuid.uuid4())
        repo.save_signal_source(signal_id, source_type, url, snippet, weight)
        MockSource.assert_called_once()
