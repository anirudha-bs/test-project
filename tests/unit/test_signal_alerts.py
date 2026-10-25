import pytest
from unittest.mock import MagicMock, patch
from app.engine.signal_monitor import SignalMonitor
from app.mocks.notification_service import notification_service
from app.mocks.trading_signal import signal_provider
from db.models import WatchList

def test_transition_detection():
    """Verify that Neutral -> Bullish transition triggers an alert."""
    db_session = MagicMock()
    mock_item = MagicMock(spec=WatchList)
    mock_item.user_id = 1
    mock_item.ticker = "AAPL"
    mock_item.alert_threshold = None
    
    db_session.query.return_value.all.return_value = [mock_item]
    
    # Mock Signal Provider
    signal_provider.set_signal("AAPL", 0.0, "Neutral")
    
    monitor = SignalMonitor(db_session)
    # First check - establish Neutral state
    monitor.check_signals()
    
    # Clear sent notifications to focus on transition
    notification_service.sent_notifications.clear()
    
    # Transition to Bullish
    signal_provider.set_signal("AAPL", 0.8, "Bullish")
    monitor.check_signals()
    
    assert len(notification_service.sent_notifications) == 1
    notif = notification_service.sent_notifications[0]
    assert notif["ticker"] == "AAPL"
    assert notif["transition_type"] == "Neutral to Bullish"
    assert notif["score"] == 0.8

def test_threshold_breach():
    """Verify that score > alert_threshold triggers an alert."""
    db_session = MagicMock()
    mock_item = MagicMock(spec=WatchList)
    mock_item.user_id = 2
    mock_item.ticker = "TSLA"
    mock_item.alert_threshold = 0.7
    
    db_session.query.return_value.all.return_value = [mock_item]
    
    signal_provider.set_signal("TSLA", 0.8, "Neutral")
    
    notification_service.sent_notifications.clear()
    monitor = SignalMonitor(db_session)
    monitor.check_signals()
    
    assert len(notification_service.sent_notifications) == 1
    notif = notification_service.sent_notifications[0]
    assert notif["transition_type"] == "Threshold Breach"
    assert notif["score"] == 0.8

def test_duplicate_suppression():
    """Verify that the same transition doesn't trigger multiple alerts."""
    db_session = MagicMock()
    mock_item = MagicMock(spec=WatchList)
    mock_item.user_id = 3
    mock_item.ticker = "BTC"
    mock_item.alert_threshold = None
    
    db_session.query.return_value.all.return_value = [mock_item]
    
    signal_provider.set_signal("BTC", 0.8, "Bullish")
    
    notification_service.sent_notifications.clear()
    monitor = SignalMonitor(db_session)
    
    monitor.check_signals()
    monitor.check_signals()
    
    assert len(notification_service.sent_notifications) == 1

def test_email_opt_out():
    """Verify that if notify_email is False and session inactive, no alert is sent."""
    db_session = MagicMock()
    mock_item = MagicMock(spec=WatchList)
    mock_item.user_id = 4
    mock_item.ticker = "AAPL"
    mock_item.alert_threshold = None
    mock_item.notify_email = False
    
    db_session.query.return_value.all.return_value = [mock_item]
    
    # User is inactive
    notification_service.set_active_session(4, False)
    
    signal_provider.set_signal("AAPL", 0.8, "Bullish")
    
    notification_service.sent_notifications.clear()
    monitor = SignalMonitor(db_session)
    
    # Need to modify SignalMonitor.check_signals or _process_watchlist_item to respect notify_email
    # Let's see if it does.
    monitor.check_signals()
    
    # According to current SignalMonitor implementation, it doesn't check notify_email yet.
    # This test should fail if the implementation is missing the check.
    assert len(notification_service.sent_notifications) == 0

def test_boundary_timing():
    """Verify multiple tickers are processed in one loop."""
    db_session = MagicMock()
    mock_item1 = MagicMock(spec=WatchList)
    mock_item1.user_id = 1
    mock_item1.ticker = "AAPL"
    mock_item1.alert_threshold = None
    
    mock_item2 = MagicMock(spec=WatchList)
    mock_item2.user_id = 2
    mock_item2.ticker = "TSLA"
    mock_item2.alert_threshold = None
    
    db_session.query.return_value.all.return_value = [mock_item1, mock_item2]
    
    signal_provider.set_signal("AAPL", 0.8, "Bullish")
    signal_provider.set_signal("TSLA", 0.8, "Bullish")
    
    notification_service.sent_notifications.clear()
    monitor = SignalMonitor(db_session)
    monitor.check_signals()
    
    assert len(notification_service.sent_notifications) == 2
