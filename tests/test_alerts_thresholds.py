import pytest
from fastapi.testclient import TestClient
from main import app
from db.models import Base, WatchList, User
from fastapi_test_db import engine, SessionLocal, get_db
from sqlalchemy.orm import Session

# Override the dependency
def override_get_db():
    try:
        db = SessionLocal()
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db

@pytest.fixture
def client():
    # Create tables
    Base.metadata.create_all(bind=engine)
    # Initialize some data
    db = SessionLocal()
    user = User(email="test@example.com")
    db.add(user)
    db.commit()
    db.add(WatchList(user_id=user.id, ticker="AAPL"))
    db.commit()
    db.close()
    
    with TestClient(app) as c:
        yield c
    
    # Drop tables after test
    Base.metadata.drop_all(bind=engine)

def test_valid_threshold_update(client):
    response = client.patch("/api/alerts/thresholds", json={"ticker": "AAPL", "threshold": 0.8})
    assert response.status_code == 200
    
    db = SessionLocal()
    watchlist_entry = db.query(WatchList).filter(WatchList.ticker == "AAPL").first()
    assert watchlist_entry.alert_threshold == 0.8
    db.close()

def test_invalid_threshold_value(client):
    response = client.patch("/api/alerts/thresholds", json={"ticker": "AAPL", "threshold": "invalid"})
    assert response.status_code == 422 # FastAPI returns 422 for validation errors by default

def test_missing_fields(client):
    response = client.patch("/api/alerts/thresholds", json={"ticker": "AAPL"})
    # If threshold is optional, this might be 200. But the requirements say 400 if threshold missing.
    # Let's check if we should make threshold required for the PATCH.
    # The API contract says "request (required): ticker: string*, threshold: number*"
    # This means both are required.
    assert response.status_code == 422

def test_email_preference_toggle(client):
    response = client.patch("/api/alerts/thresholds", json={"ticker": "AAPL", "threshold": 0.5, "notify_email": False})
    assert response.status_code == 200
    
    db = SessionLocal()
    watchlist_entry = db.query(WatchList).filter(WatchList.ticker == "AAPL").first()
    assert watchlist_entry.notify_email is False
    db.close()
