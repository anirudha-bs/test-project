from abc import ABC, abstractmethod
from typing import List, Dict, Any

class SentimentProvider(ABC):
    @abstractmethod
    def fetch_sentiment(self, symbol: str) -> Dict[str, Any]:
        """
        Fetch sentiment data for a given symbol.
        Returns a dictionary containing the score and metadata.
        """
        pass

class CryptoPanicProvider(SentimentProvider):
    def fetch_sentiment(self, symbol: str) -> Dict[str, Any]:
        # Mock implementation of CryptoPanic API
        return {
            'symbol': symbol,
            'score': 0.7, # Mock score
            'provider': 'CryptoPanic',
            'url': f'https://cryptopanic.com/news/{symbol}',
            'snippet': 'Positive sentiment observed on CryptoPanic'
        }

class LunarCrushProvider(SentimentProvider):
    def fetch_sentiment(self, symbol: str) -> Dict[str, Any]:
        # Mock implementation of LunarCrush API
        return {
            'symbol': symbol,
            'score': 0.4, # Mock score
            'provider': 'LunarCrush',
            'url': f'https://lunarcrush.com/{symbol}',
            'snippet': 'Neutral to positive sentiment on LunarCrush'
        }

class SentimentAPIProvider(SentimentProvider):
    def fetch_sentiment(self, symbol: str) -> Dict[str, Any]:
        # Mock implementation of a generic Sentiment API
        return {
            'symbol': symbol,
            'score': -0.2, # Mock score
            'provider': 'GenericSentimentAPI',
            'url': f'https://sentimentapi.com/{symbol}',
            'snippet': 'Slightly bearish sentiment on GenericSentimentAPI'
        }
