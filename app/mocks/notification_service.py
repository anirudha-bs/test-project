import logging

# TODO(mock): replace when Notification delivery infrastructure exists
class NotificationService:
    """Mocks the notification delivery system."""
    
    def __init__(self):
        self.sent_notifications = []
        self.active_sessions = set() # user_ids of users with active WebSocket sessions

    def set_active_session(self, user_id, active=True):
        if active:
            self.active_sessions.add(user_id)
        else:
            self.active_sessions.discard(user_id)

    def send(self, user_id, ticker, score, transition_type):
        method = "WebSocket" if user_id in self.active_sessions else "Email"
        notification = {
            "user_id": user_id,
            "ticker": ticker,
            "score": score,
            "transition_type": transition_type,
            "method": method
        }
        self.sent_notifications.append(notification)
        logging.info(f"Notification sent to user {user_id} via {method}: {ticker} {transition_type} ({score})")
        return True

# Global instance for singleton-like access in mocks
notification_service = NotificationService()
