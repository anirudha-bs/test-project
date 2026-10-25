import pytest
from unittest.mock import MagicMock
from app.mocks.trading_signal import signal_provider
from app.mocks.notification_service import notification_service
from app.engine.signal_monitor import SignalMonitor
from db.models import WatchList, User

def test_state_transition(db_session):
    """Test transition from Neutral to Bullish/Bearish triggers notification."""
    notification_service.sent_notifications.clear()
    
    # Setup: User and WatchList
    user = User(id=1, email="user1@example.com")
    db_session.add(user)
    watchlist_item = WatchList(user_id=1, ticker="AAPL", alert_threshold=None)
    db_session.add(watchlist_item)
    db_session.commit()
    
    # Initial state: Neutral
    signal_provider.set_signal("AAPL", 0.1, "Neutral")
    monitor = SignalMonitor(db_session)
    monitor.check_signals()
    assert len(notification_service.sent_notifications) == 0
    
    # Transition: Neutral -> Bullish
    signal_provider.set_signal("AAPL", 0.8, "Bullish")
    monitor.check_signals()
    
    assert len(notification_service.sent_notifications) == 1
    notification = notification_service.sent_notifications[0]
    assert notification["ticker"] == "AAPL"
    assert notification["transition_type"] == "Neutral to Bullish"
    assert notification["score"] == 0.8

def test_threshold_breach(db_session):
    """Test that score exceeding alert_threshold triggers notification."""
    notification_service.sent_notifications.clear()
    
    user = User(id=2, email="user2@example.com")
    db_session.add(user)
    watchlist_item = WatchList(user_id=2, ticker="TSLA", alert_threshold=0.7)
    db_session.add(watchlist_item)
    db_session.commit()
    
    # Below threshold
    signal_provider.set_signal("TSLA", 0.5, "Neutral")
    monitor = SignalMonitor(db_session)
    monitor.check_signals()
    assert len(notification_service.sent_notifications) == 0
    
    # Breach threshold
    signal_provider.set_signal("TSLA", 0.8, "Neutral")
    monitor.check_signals()
    
    assert len(notification_service.sent_notifications) == 1
    notification = notification_service.sent_notifications[0]
    assert notification["ticker"] == "TSLA"
    assert notification["transition_type"] == "Threshold Breach"
    assert notification["score"] == 0.8

def test_below_threshold(db_session):
    """Test that score below alert_threshold does NOT trigger notification."""
    notification_service.sent_notifications.clear()
    
    user = User(id=3, email="user3@example.com")
    db_session.add(user)
    watchlist_item = WatchList(user_id=3, ticker="BTC", alert_threshold=0.9)
    db_session.add(watchlist_item)
    db_session.commit()
    
    signal_provider.set_signal("BTC", 0.8, "Neutral")
    monitor = SignalMonitor(db_session)
    monitor.check_signals()
    assert len(notification_service.sent_notifications) == 0

def test_duplicate_prevention(db_session):
    """Test that same transition doesn't trigger duplicate notifications."""
    notification_service.sent_notifications.clear()
    
    user = User(id=4, email="user4@example.com")
    db_session.add(user)
    watchlist_item = WatchList(user_id=4, ticker="AAPL", alert_threshold=None)
    db_session.add(watchlist_item)
    db_session.commit()
    
    signal_provider.set_signal("AAPL", 0.8, "Bullish")
    monitor = SignalMonitor(db_session)
    
    # Trigger once
    monitor.check_signals()
    # Trigger twice
    monitor.check_signals()
    
    assert len(notification_service.sent_notifications) == 1

def test_dispatch_routing(db_session):
    """Test routing to WebSocket for active and Email for inactive users."""
    notification_service.sent_notifications.clear()
    notification_service.active_sessions.clear()
    
    # User A: Active WebSocket
    user_a = User(id=10, email="a@example.com")
    db_session.add(user_a)
    watchlist_a = WatchList(user_id=10, ticker="AAPL", alert_threshold=None)
    db_session.add(watchlist_a)
    
    # User B: Inactive (Email)
    user_b = User(id=20, email="b@example.com")
    db_session.add(user_b)
    watchlist_b = WatchList(user_id=20, ticker="AAPL", alert_threshold=None)
    db_session.add(watchlist_b)
    
    db_session.commit()
    
    notification_service.set_active_session(10, True)
    notification_service.set_active_session(20, False)
    
    signal_provider.set_signal("AAPL", 0.8, "Bullish")
    monitor = SignalMonitor(db_session)
    monitor.check_signals()
    
    # Find notifications for each user
    notif_a = next(n for n in notification_service.sent_notifications if n["user_id"] == 10)
    notif_b = next(n for n in notification_service.sent_notifications if n["user_id"] == 20)
    
    assert notif_a["method"] == "WebSocket"
    assert notif_b["method"] == "Email"
