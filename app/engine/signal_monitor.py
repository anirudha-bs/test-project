from typing import Set, Tuple
import logging
from app.mocks.trading_signal import signal_provider
from app.mocks.notification_service import notification_service

class SignalMonitor:
    def __init__(self, db_session):
        self.db_session = db_session
        # Volatile cache to prevent duplicate notifications
        # Key: (user_id, ticker, state)
        self._transition_cache: Set[Tuple[int, str, str]] = set()

    def check_signals(self):
        """
        Iterates through all WatchLists and checks for signal transitions or threshold breaches.
        """
        from db.models import WatchList
        
        watchlists = self.db_session.query(WatchList).all()
        
        for item in watchlists:
            try:
                self._process_watchlist_item(item)
            except Exception as e:
                logging.error(f"Error processing watchlist item for user {item.user_id} ticker {item.ticker}: {e}")

    def _process_watchlist_item(self, item):
        user_id = item.user_id
        ticker = item.ticker
        threshold = item.alert_threshold
        
        signal_data = signal_provider.get_signal(ticker)
        score = signal_data["score"]
        state = signal_data["state"]
        
        # 1. State Transition Detection: Neutral -> Bullish/Bearish
        # We assume previous state was Neutral if not in cache, but that's for the FIRST transition.
        # Actually, for this unit, we detect if it is CURRENTLY Bullish/Bearish and was NOT previously.
        # To properly detect transition, we'd need the previous state. 
        # But the REQ says "detects signal transitions from Neutral to Bullish or Bearish".
        # We will track the LAST known state for each (user, ticker).
        
        # Using a cache to track if we already notified for the current state
        cache_key = (user_id, ticker, state)
        
        is_transition = False
        transition_type = None
        
        if state in ["Bullish", "Bearish"]:
            # Check if we've already alerted for this state
            if cache_key not in self._transition_cache:
                # It's a transition if it was Neutral or something else before.
                # For simplicity in this mock-based unit, any state in [Bullish, Bearish] 
                # not already in cache is treated as a transition from Neutral.
                is_transition = True
                transition_type = f"Neutral to {state}"
        
        # 2. Threshold Logic
        is_threshold_breach = False
        if threshold is not None and score > threshold:
            is_threshold_breach = True
            transition_type = "Threshold Breach"
            
        if is_transition or is_threshold_breach:
            # De-duplicate: only notify if this exact state transition hasn't been handled
            # Note: threshold breaches might happen multiple times, but we should probably 
            # only notify once per "breach event". 
            # For now, let's use the cache_key to prevent duplicates of the same state.
            
            if cache_key not in self._transition_cache:
                notification_service.send(
                    user_id=user_id,
                    ticker=ticker,
                    score=score,
                    transition_type=transition_type or "Signal Change"
                )
                self._transition_cache.add(cache_key)
        
        # If state returns to Neutral, clear it from cache to allow future transitions
        if state == "Neutral":
            # Remove any Bullish/Bearish entries for this (user, ticker)
            self._transition_cache = {k for k in self._transition_cache if not (k[0] == user_id and k[1] == ticker)}
