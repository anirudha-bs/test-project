from .base import SentimentConnector
from typing import Dict, Any
import random
import asyncio

class CryptoPanicConnector(SentimentConnector):
    @property
    def provider_name(self) -> str:
        return "cryptopanic"

    async def fetch_sentiment(self, symbol: str) -> Dict[str, Any]:
        # Mocking API call to CryptoPanic
        await asyncio.sleep(0.1)
        return {
            "provider": self.provider_name,
            "symbol": symbol,
            "score": random.uniform(-1.0, 1.0)
        }

class LunarCrushConnector(SentimentConnector):
    @property
    def provider_name(self) -> str:
        return "lunarcrush"

    async def fetch_sentiment(self, symbol: str) -> Dict[str, Any]:
        # Mocking API call to LunarCrush
        await asyncio.sleep(0.1)
        return {
            "provider": self.provider_name,
            "symbol": symbol,
            "score": random.uniform(-1.0, 1.0)
        }

class SantimentConnector(SentimentConnector):
    @property
    def provider_name(self) -> str:
        return "santiment"

    async def fetch_sentiment(self, symbol: str) -> Dict[str, Any]:
        # Mocking API call to Santiment
        await asyncio.sleep(0.1)
        return {
            "provider": self.provider_name,
            "symbol": symbol,
            "score": random.uniform(-1.0, 1.0)
        }
