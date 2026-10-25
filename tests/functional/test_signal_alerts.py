import pytest
import os
from app.mocks.trading_signal import signal_provider
from app.mocks.notification_service import notification_service
from app.engine.signal_monitor import SignalMonitor
from db.models import WatchList, User

def test_signal_transition_triggers_notification(db_session):
    """A user receives a notification when a signal moves from Neutral to Bullish or Bearish."""
    notification_service.sent_notifications.clear()
    
    user = User(id=1, email="user1@example.com")
    db_session.add(user)
    watchlist_item = WatchList(user_id=1, ticker="AAPL", alert_threshold=None)
    db_session.add(watchlist_item)
    db_session.commit()
    
    signal_provider.set_signal("AAPL", 0.0, "Neutral")
    monitor = SignalMonitor(db_session)
    monitor.check_signals()
    
    signal_provider.set_signal("AAPL", 0.8, "Bullish")
    monitor.check_signals()
    
    assert len(notification_service.sent_notifications) == 1
    notification = notification_service.sent_notifications[0]
    assert notification["ticker"] == "AAPL"
    assert notification["transition_type"] == "Neutral to Bullish"
    assert notification["score"] == 0.8
    
    try:
        with open(os.path.join(".see", "e2e-artifacts", "transition_alert.txt"), "w") as f:
            f.write(f"Notification sent: {notification}")
    except FileNotFoundError:
        pass

def test_threshold_breach_triggers_notification(db_session):
    """A user receives a notification when a signal exceeds their custom threshold."""
    notification_service.sent_notifications.clear()
    
    user = User(id=2, email="user2@example.com")
    db_session.add(user)
    watchlist_item = WatchList(user_id=2, ticker="TSLA", alert_threshold=0.7)
    db_session.add(watchlist_item)
    db_session.commit()
    
    signal_provider.set_signal("TSLA", 0.8, "Neutral")
    monitor = SignalMonitor(db_session)
    monitor.check_signals()
    
    assert len(notification_service.sent_notifications) == 1
    notification = notification_service.sent_notifications[0]
    assert notification["ticker"] == "TSLA"
    assert notification["transition_type"] == "Threshold Breach"
    assert notification["score"] == 0.8
    
    try:
        with open(os.path.join(".see", "e2e-artifacts", "threshold_alert.txt"), "w") as f:
            f.write(f"Notification sent: {notification}")
    except FileNotFoundError:
        pass

def test_delivery_routing(db_session):
    """Active WebSocket sessions receive priority alerts, inactive users receive email."""
    notification_service.sent_notifications.clear()
    notification_service.active_sessions.clear()
    
    user_a = User(id=10, email="a@example.com")
    db_session.add(user_a)
    watchlist_a = WatchList(user_id=10, ticker="AAPL", alert_threshold=None)
    db_session.add(watchlist_a)
    
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
    
    notif_a = next(n for n in notification_service.sent_notifications if n["user_id"] == 10)
    notif_b = next(n for n in notification_service.sent_notifications if n["user_id"] == 20)
    
    assert notif_a["method"] == "WebSocket"
    assert notif_b["method"] == "Email"
    
    try:
        with open(os.path.join(".see", "e2e-artifacts", "routing_alert.txt"), "w") as f:
            f.write(f"User A (Active): {notif_a['method']}, User B (Inactive): {notif_b['method']}")
    except FileNotFoundError:
        pass

def test_deduplication(db_session):
    """Duplicate notifications are suppressed for the same signal transition event."""
    notification_service.sent_notifications.clear()
    
    user = User(id=4, email="user4@example.com")
    db_session.add(user)
    watchlist_item = WatchList(user_id=4, ticker="AAPL", alert_threshold=None)
    db_session.add(watchlist_item)
    db_session.commit()
    
    signal_provider.set_signal("AAPL", 0.8, "Bullish")
    monitor = SignalMonitor(db_session)
    
    monitor.check_signals()
    monitor.check_signals()
    
    assert len(notification_service.sent_notifications) == 1
    
    try:
        with open(os.path.join(".see", "e2e-artifacts", "dedup_alert.txt"), "w") as f:
            f.write("Only one notification sent for duplicate event")
    except FileNotFoundError:
        pass
