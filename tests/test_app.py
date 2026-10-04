
import sqlite3
import pytest
from app import app
from database.db import initialize_database


@pytest.fixture
def client(tmp_path, monkeypatch):
    # Create a separate temporary database for testing
    test_db = tmp_path / "test_aquasense.db"

    def get_test_connection():
        connection = sqlite3.connect(test_db)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")
        return connection

    monkeypatch.setattr(
        "app.get_connection",
        get_test_connection
    )

    # Create the required tables in the temporary database
    connection = get_test_connection()
    try:
        connection.executescript("""
            CREATE TABLE water_zones (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE,
                location TEXT NOT NULL,
                daily_limit_liters REAL NOT NULL
                    CHECK (daily_limit_liters > 0)
            );

            CREATE TABLE readings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                zone_id INTEGER NOT NULL,
                consumption_liters REAL NOT NULL
                    CHECK (consumption_liters >= 0),
                recorded_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (zone_id) REFERENCES water_zones(id)
            );

            CREATE TABLE alerts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                zone_id INTEGER NOT NULL,
                message TEXT NOT NULL,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                resolved INTEGER NOT NULL DEFAULT 0,
                FOREIGN KEY (zone_id) REFERENCES water_zones(id)
            );

            INSERT INTO water_zones
                (name, location, daily_limit_liters)
            VALUES
                ('College Building', 'Main Campus', 5000),
                ('Hostel Block', 'Student Hostel', 8000),
                ('Library', 'Central Library', 2000);
        """)
        connection.commit()
    finally:
        connection.close()

    app.config["TESTING"] = True

    with app.test_client() as test_client:
        yield test_client


def test_home_page(client):
    response = client.get("/")
    assert response.status_code == 200
    assert b"Welcome to AquaSense" in response.data


def test_dashboard_page(client):
    response = client.get("/dashboard")
    assert response.status_code == 200


def test_health_api(client):
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json["status"] == "healthy"
    assert response.json["application"] == "AquaSense"


def test_zones_api(client):
    response = client.get("/api/zones")
    assert response.status_code == 200
    assert len(response.json) == 3


def test_summary_api(client):
    response = client.get("/api/summary")
    assert response.status_code == 200
    assert len(response.json) == 3

    for zone in response.json:
        assert "zone_name" in zone
        assert "total_consumption_liters" in zone
        assert "remaining_liters" in zone
        assert "usage_percentage" in zone
        assert "status" in zone


def test_reading_rejects_invalid_data(client):
    response = client.post(
        "/api/readings",
        json={
            "zone_id": -1,
            "consumption_liters": -100
        }
    )
    assert response.status_code == 400


def test_reading_rejects_missing_fields(client):
    response = client.post("/api/readings", json={})
    assert response.status_code == 400


def test_add_reading_invalid_zone(client):
    response = client.post(
        "/api/readings",
        json={
            "zone_id": 999999,
            "consumption_liters": 100
        }
    )
    assert response.status_code == 404
    assert response.json["error"] == "Water zone not found."


def test_alerts_api(client):
    response = client.get("/api/alerts")

    assert response.status_code == 200
    assert isinstance(response.json, list)

    for alert in response.json:
        assert "zone_name" in alert
        assert "level" in alert
        assert alert["level"] in ["warning", "critical"]
        assert "message" in alert
        assert "usage_percentage" in alert
