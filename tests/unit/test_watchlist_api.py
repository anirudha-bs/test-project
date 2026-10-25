import pytest
from fastapi.testclient import TestClient
from app.main import app, get_db
from db.database import SessionLocal, engine
from db.models import Base, WatchList

# Override get_db to use a fresh test database
def override_get_db():
    # Using in-memory sqlite for tests
    test_db = SessionLocal()
    try:
        yield test_db
    finally:
        test_db.close()

app.dependency_overrides[get_db] = override_get_db

client = TestClient(app)

@pytest.fixture(autouse=True)
def setup_db():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)

def test_add_watchlist_success():
    response = client.post("/api/v1/watchlist", json={"ticker": "AAPL"})
    assert response.status_code == 201
    data = response.json()
    assert "id" in data
    assert data["ticker"] == "AAPL"

def test_add_watchlist_invalid_ticker():
    response = client.post("/api/v1/watchlist", json={"ticker": ""})
    assert response.status_code == 400

def test_add_watchlist_empty_ticker():
    response = client.post("/api/v1/watchlist", json={"ticker": "  "})
    assert response.status_code == 400

def test_add_watchlist_duplicate():
    client.post("/api/v1/watchlist", json={"ticker": "TSLA"})
    response = client.post("/api/v1/watchlist", json={"ticker": "TSLA"})
    assert response.status_code == 201
    # Should return existing entry
