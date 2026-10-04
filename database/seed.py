
from database.db import get_connection, initialize_database

# Make sure the database tables exist
initialize_database()

connection = get_connection()

try:
    # Add sample water zones
    zones = [
        ("College Building", "Main Campus", 5000),
        ("Hostel Block", "Student Hostel", 8000),
        ("Library", "Central Library", 2000),
    ]

    for name, location, daily_limit in zones:
        connection.execute(
            """
            INSERT OR IGNORE INTO water_zones
                (name, location, daily_limit_liters)
            VALUES (?, ?, ?)
            """,
            (name, location, daily_limit),
        )

    connection.commit()

    # Get zone IDs
    saved_zones = connection.execute(
        "SELECT id, name FROM water_zones"
    ).fetchall()

    zone_ids = {zone["name"]: zone["id"] for zone in saved_zones}

    # Add sample readings only if no readings exist yet
    existing_readings = connection.execute(
        "SELECT COUNT(*) FROM readings"
    ).fetchone()[0]

    if existing_readings == 0:
        readings = [
            (zone_ids["College Building"], 1200),
            (zone_ids["College Building"], 1500),
            (zone_ids["Hostel Block"], 2500),
            (zone_ids["Hostel Block"], 3000),
            (zone_ids["Library"], 600),
            (zone_ids["Library"], 450),
        ]

        for zone_id, consumption in readings:
            connection.execute(
                """
                INSERT INTO readings (zone_id, consumption_liters)
                VALUES (?, ?)
                """,
                (zone_id, consumption),
            )

        connection.commit()
        print("Sample readings added successfully!")
    else:
        print("Sample readings already exist. Skipping insertion.")

finally:
    connection.close()
