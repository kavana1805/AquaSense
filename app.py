
from datetime import datetime
import math

from flask import Flask, jsonify, render_template, request

from database.db import get_connection, initialize_database


app = Flask(__name__)

# Create database tables if they do not exist
initialize_database()


# ============================================
# HOME PAGE
# ============================================

@app.route("/")
def home():
    return render_template("index.html")


# ============================================
# DASHBOARD PAGE
# ============================================

@app.route("/dashboard")
def dashboard():
    return render_template("dashboard.html")


# ============================================
# HISTORY PAGE
# ============================================

@app.route("/history")
def history_page():
    return render_template("history.html")


# ============================================
# ANALYTICS PAGE
# ============================================

@app.route("/analytics")
def analytics_page():
    return render_template("analytics.html")


# ============================================
# API HEALTH CHECK
# ============================================

@app.route("/api/health")
def health():
    return jsonify({
        "status": "healthy",
        "application": "AquaSense"
    })


# ============================================
# GET ALL WATER ZONES
# ============================================

@app.route("/api/zones")
def get_zones():
    connection = get_connection()

    try:
        zones = connection.execute("""
            SELECT
                id,
                name,
                location,
                daily_limit_liters
            FROM water_zones
            ORDER BY id
        """).fetchall()

        return jsonify([
            dict(zone) for zone in zones
        ])

    finally:
        connection.close()


# ============================================
# TODAY'S WATER CONSUMPTION SUMMARY
# ============================================

@app.route("/api/summary")
def water_summary():
    connection = get_connection()

    try:
        zones = connection.execute("""
            SELECT
                z.id,
                z.name,
                z.location,
                z.daily_limit_liters,
                COALESCE(
                    SUM(
                        CASE
                            WHEN date(r.recorded_at, 'localtime') =
                                 date('now', 'localtime')
                            THEN r.consumption_liters
                            ELSE 0
                        END
                    ),
                    0
                ) AS total_consumption
            FROM water_zones z
            LEFT JOIN readings r
                ON z.id = r.zone_id
            GROUP BY
                z.id,
                z.name,
                z.location,
                z.daily_limit_liters
            ORDER BY z.id
        """).fetchall()

        results = []

        for zone in zones:
            used = float(zone["total_consumption"])
            limit = float(zone["daily_limit_liters"])

            remaining = max(limit - used, 0)

            percentage = (
                round((used / limit) * 100, 2)
                if limit > 0 else 0
            )

            if percentage >= 100:
                status = "Limit exceeded"
            elif percentage >= 80:
                status = "High usage"
            else:
                status = "Within limit"

            results.append({
                "zone_id": zone["id"],
                "zone_name": zone["name"],
                "location": zone["location"],
                "daily_limit_liters": limit,
                "total_consumption_liters": round(used, 2),
                "remaining_liters": round(remaining, 2),
                "usage_percentage": percentage,
                "status": status
            })

        return jsonify(results)

    finally:
        connection.close()


# ============================================
# WATER CONSUMPTION ALERTS
# ============================================

@app.route("/api/alerts")
def get_alerts():
    connection = get_connection()

    try:
        zones = connection.execute("""
            SELECT
                z.id,
                z.name,
                z.daily_limit_liters,
                COALESCE(
                    SUM(
                        CASE
                            WHEN date(r.recorded_at, 'localtime') =
                                 date('now', 'localtime')
                            THEN r.consumption_liters
                            ELSE 0
                        END
                    ),
                    0
                ) AS total_consumption
            FROM water_zones z
            LEFT JOIN readings r
                ON z.id = r.zone_id
            GROUP BY
                z.id,
                z.name,
                z.daily_limit_liters
            ORDER BY z.id
        """).fetchall()

        alerts = []

        for zone in zones:
            used = float(zone["total_consumption"])
            limit = float(zone["daily_limit_liters"])

            percentage = (
                (used / limit) * 100
                if limit > 0 else 0
            )

            if percentage >= 100:
                level = "critical"
                message = (
                    f"{zone['name']} has reached or exceeded "
                    "its daily water limit."
                )

            elif percentage >= 80:
                level = "warning"
                message = (
                    f"{zone['name']} has reached "
                    f"{percentage:.1f}% of its daily water limit."
                )

            else:
                continue

            alerts.append({
                "zone_id": zone["id"],
                "zone_name": zone["name"],
                "level": level,
                "message": message,
                "usage_percentage": round(percentage, 2)
            })

        return jsonify(alerts)

    finally:
        connection.close()


# ============================================
# ADD A WATER CONSUMPTION READING
# ============================================

@app.route("/api/readings", methods=["POST"])
def add_reading():
    data = request.get_json(silent=True) or {}

    try:
        zone_id = int(data["zone_id"])
        consumption = float(data["consumption_liters"])

        if (
            zone_id <= 0
            or not math.isfinite(consumption)
            or consumption < 0
        ):
            raise ValueError

    except (KeyError, TypeError, ValueError, OverflowError):
        return jsonify({
            "error": (
                "Provide a valid zone_id and "
                "non-negative consumption_liters."
            )
        }), 400

    connection = get_connection()

    try:
        zone = connection.execute(
            "SELECT id FROM water_zones WHERE id = ?",
            (zone_id,)
        ).fetchone()

        if zone is None:
            return jsonify({
                "error": "Water zone not found."
            }), 404

        cursor = connection.execute("""
            INSERT INTO readings (
                zone_id,
                consumption_liters
            )
            VALUES (?, ?)
        """, (zone_id, consumption))

        connection.commit()

        return jsonify({
            "message": "Water reading added successfully.",
            "reading_id": cursor.lastrowid,
            "zone_id": zone_id,
            "consumption_liters": consumption
        }), 201

    finally:
        connection.close()


# ============================================
# WATER USAGE HISTORY WITH FILTERS
# ============================================

@app.route("/api/history")
def get_reading_history():
    zone_id = request.args.get("zone_id", type=int)
    selected_date = request.args.get("date", "").strip()

    if zone_id is not None and zone_id <= 0:
        return jsonify({
            "error": "Invalid zone ID."
        }), 400

    if selected_date:
        try:
            datetime.strptime(selected_date, "%Y-%m-%d")
        except ValueError:
            return jsonify({
                "error": "Invalid date format. Use YYYY-MM-DD."
            }), 400

    connection = get_connection()

    try:
        query = """
            SELECT
                r.id,
                r.zone_id,
                z.name AS zone_name,
                z.location,
                r.consumption_liters,
                r.recorded_at
            FROM readings r
            JOIN water_zones z
                ON z.id = r.zone_id
            WHERE 1 = 1
        """

        parameters = []

        if zone_id is not None:
            query += " AND r.zone_id = ?"
            parameters.append(zone_id)

        if selected_date:
            query += " AND date(r.recorded_at) = date(?)"
            parameters.append(selected_date)

        query += """
            ORDER BY r.recorded_at DESC, r.id DESC
        """

        rows = connection.execute(
            query, parameters
        ).fetchall()

        return jsonify([
            {
                "id": row["id"],
                "zone_id": row["zone_id"],
                "zone_name": row["zone_name"],
                "location": row["location"],
                "consumption_liters": row["consumption_liters"],
                "recorded_at": row["recorded_at"]
            }
            for row in rows
        ])

    finally:
        connection.close()


# ============================================
# ANALYTICS API
# ============================================


@app.route("/api/analytics")
def get_analytics():
    start_date = request.args.get("start_date", "").strip()
    end_date = request.args.get("end_date", "").strip()

    # Validate the selected dates
    try:
        if start_date:
            datetime.strptime(start_date, "%Y-%m-%d")

        if end_date:
            datetime.strptime(end_date, "%Y-%m-%d")

    except ValueError:
        return jsonify({
            "error": "Dates must use YYYY-MM-DD format."
        }), 400

    if start_date and end_date and start_date > end_date:
        return jsonify({
            "error": "Start date cannot be after end date."
        }), 400

    connection = get_connection()

    try:
        # Build the date filter safely
        conditions = []
        parameters = []

        if start_date:
            conditions.append("date(r.recorded_at) >= date(?)")
            parameters.append(start_date)

        if end_date:
            conditions.append("date(r.recorded_at) <= date(?)")
            parameters.append(end_date)

        date_filter = ""

        if conditions:
            date_filter = " AND " + " AND ".join(conditions)

        # Overall statistics for the selected period
        totals_query = f"""
            SELECT
                COUNT(*) AS total_readings,
                COALESCE(SUM(r.consumption_liters), 0)
                    AS total_consumption,
                COALESCE(AVG(r.consumption_liters), 0)
                    AS average_consumption
            FROM readings r
            WHERE 1 = 1
            {date_filter}
        """

        totals = connection.execute(
            totals_query, parameters
        ).fetchone()

        # Consumption grouped by water zone
        zones_query = f"""
            SELECT
                z.id AS zone_id,
                z.name AS zone_name,
                COALESCE(
                    SUM(r.consumption_liters), 0
                ) AS total_consumption,
                COUNT(r.id) AS reading_count
            FROM water_zones z
            LEFT JOIN readings r
                ON z.id = r.zone_id
                {date_filter.replace('r.recorded_at', 'r.recorded_at')}
            GROUP BY z.id, z.name
            ORDER BY total_consumption DESC
        """

        zones = connection.execute(
            zones_query, parameters
        ).fetchall()

        return jsonify({
            "start_date": start_date or None,
            "end_date": end_date or None,
            "total_readings": totals["total_readings"],
            "total_consumption_liters": round(
                float(totals["total_consumption"]), 2
            ),
            "average_consumption_liters": round(
                float(totals["average_consumption"]), 2
            ),
            "zones": [
                {
                    "zone_id": zone["zone_id"],
                    "zone_name": zone["zone_name"],
                    "total_consumption_liters": round(
                        float(zone["total_consumption"]), 2
                    ),
                    "reading_count": zone["reading_count"]
                }
                for zone in zones
            ]
        })

    finally:
        connection.close()


# ============================================
# RUN THE APPLICATION
# ============================================

if __name__ == "__main__":
    app.run(debug=True)