import asyncio
import uuid
from datetime import datetime
from typing import List, Dict, Any, Tuple, Optional
from dataclasses import dataclass

try:
    from db.models import Signal, SignalSource
except ImportError:
    from .see.mocks.db.models import Signal, SignalSource

try:
    from src.ingestion.services.news_normalization import normalize_news_signal
except ImportError:
    from .see.mocks.src.ingestion.services.news_normalization import normalize_news_signal

try:
    from src.ingestion.services.options_normalization import normalize_options_signal
except ImportError:
    from .see.mocks.src.ingestion.services.options_normalization import normalize_options_signal

try:
    from src.ingestion.services.sentiment_normalization import normalize_sentiment_signal
except ImportError:
    from .see.mocks.src.ingestion.services.sentiment_normalization import normalize_sentiment_signal

from .repository import SignalRepository
from .connectors.providers import CryptoPanicConnector, LunarCrushConnector, SantimentConnector

SOURCE_WEIGHTS = {
    'options': 0.5,
    'sentiment': 0.3,
    'news': 0.2
}

class WeightedSignalEngine:
    def __init__(self, repository: Optional[SignalRepository] = None):
        self.repository = repository or SignalRepository()

    def _get_sentiment_label(self, score: float) -> str:
        if score > 0.2:
            return 'BUY'
        elif score < -0.2:
            return 'SELL'
        return 'HOLD'

    def generate_signal(self, ticker: str, data_feeds: Dict[str, List[Dict[str, Any]]]) -> Signal:
        total_weighted_score = 0.0
        total_weight_used = 0.0
        processed_sources = []

        normalizers = {
            'news': normalize_news_signal,
            'options': normalize_options_signal,
            'sentiment': normalize_sentiment_signal
        }

        source_count = 0
        for source_type, feeds in data_feeds.items():
            weight = SOURCE_WEIGHTS.get(source_type, 0.1)
            normalizer = normalizers.get(source_type)
            if not normalizer:
                continue

            if source_type == 'options' and feeds:
                result = normalizer(feeds[0])
            else:
                result = normalizer(feeds)

            if isinstance(result, tuple):
                norm_score = result[0]
            else:
                norm_score = result

            total_weighted_score += norm_score * weight
            total_weight_used += weight

            for feed in feeds:
                processed_sources.append({
                    'source_type': source_type,
                    'url': feed.get('url', ''),
                    'snippet': feed.get('snippet', ''),
                    'weight': weight
                })
                source_count += 1

        final_score = 0.0
        if total_weight_used > 0:
            final_score = total_weighted_score / total_weight_used

        final_score = max(min(final_score, 1.0), -1.0)
        sentiment_label = self._get_sentiment_label(final_score)

        signal_id = self.repository.save_signal(
            ticker=ticker,
            score=final_score,
            sentiment_label=sentiment_label,
            source_count=source_count,
            weighted_score=final_score
        )

        for src in processed_sources:
            self.repository.save_signal_source(
                signal_id=signal_id,
                **src
            )

        return Signal(
            id=signal_id,
            ticker=ticker,
            score=final_score,
            sentiment_label=sentiment_label,
            source_count=source_count
        )

class SignalPipelineCoordinator:
    def __init__(self, engine: WeightedSignalEngine, repository: SignalRepository):
        self.engine = engine
        self.repository = repository
        self.connectors = [
            CryptoPanicConnector(),
            LunarCrushConnector(),
            SantimentConnector()
        ]

    async def process_watchlist(self, user_id: str) -> List[Signal]:
        symbols = self.repository.get_watchlist_symbols(user_id)
        if not symbols:
            return []

        results = []
        for symbol in symbols:
            tasks = [connector.fetch_sentiment(symbol) for connector in self.connectors]
            sentiments = await asyncio.gather(*tasks, return_exceptions=True)

            valid_sentiments = []
            for s in sentiments:
                if not isinstance(s, Exception) and s:
                    valid_sentiments.append(s)

            data_feeds = {'sentiment': valid_sentiments}
            signal = self.engine.generate_signal(symbol, data_feeds)
            results.append(signal)

        return results
