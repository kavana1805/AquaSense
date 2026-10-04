
import sqlite3
from pathlib import Path

# Project folders
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
DB_PATH = DATA_DIR / "aquasense.db"


def get_connection():
    """Create a connection to the AquaSense database."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)

    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")

    return connection


def initialize_database():
    """Create the database tables if they do not exist."""
    connection = get_connection()

    try:
        connection.executescript("""
            CREATE TABLE IF NOT EXISTS water_zones (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE,
                location TEXT NOT NULL,
                daily_limit_liters REAL NOT NULL
                    CHECK (daily_limit_liters > 0)
            );

            CREATE TABLE IF NOT EXISTS readings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                zone_id INTEGER NOT NULL,
                consumption_liters REAL NOT NULL
                    CHECK (consumption_liters >= 0),
                recorded_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (zone_id)
                    REFERENCES water_zones(id)
            );

            CREATE TABLE IF NOT EXISTS alerts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                zone_id INTEGER NOT NULL,
                message TEXT NOT NULL,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                resolved INTEGER NOT NULL DEFAULT 0
                    CHECK (resolved IN (0, 1)),
                FOREIGN KEY (zone_id)
                    REFERENCES water_zones(id)
            );
        """)
        connection.commit()
    finally:
        connection.close()


if __name__ == "__main__":
    initialize_database()
    print(f"Database initialized successfully: {DB_PATH}")