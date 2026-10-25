import random

# TODO(mock): replace when trading signal exists
class TradingSignalProvider:
    """Mocks the external trading signal source."""
    
    def __init__(self):
        # Initial signals for some tickers
        self.signals = {
            "AAPL": {"score": 0.0, "state": "Neutral"},
            "TSLA": {"score": 0.0, "state": "Neutral"},
            "BTC": {"score": 0.0, "state": "Neutral"},
        }

    def get_signal(self, ticker):
        return self.signals.get(ticker, {"score": 0.0, "state": "Neutral"})

    def set_signal(self, ticker, score, state):
        self.signals[ticker] = {"score": score, "state": state}

# Global instance for singleton-like access in mocks
signal_provider = TradingSignalProvider()
