from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
import os

class SentimentConnector(ABC):
    """Base class for sentiment API connectors."""

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv(f"{self.provider_name.upper()}_API_KEY")

    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Name of the API provider."""
        pass

    @abstractmethod
    async def fetch_sentiment(self, symbol: str) -> Dict[str, Any]:
        """
        Fetch sentiment for a given symbol.
        Returns a dictionary containing at least 'score' (float between -1.0 and 1.0).
        """
        pass
