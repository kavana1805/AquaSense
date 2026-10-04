
"use strict";

let analyticsChart = null;

async function loadAnalytics() {
    const message = document.getElementById("analytics-message");
    const zoneContainer = document.getElementById("zone-analytics");

    try {
        message.textContent = "Loading analytics...";

        const response = await fetch("/api/analytics");

        if (!response.ok) {
            throw new Error(`Server error: ${response.status}`);
        }

        const data = await response.json();

        console.log("Analytics data received:", data);

        document.getElementById("total-consumption").textContent =
            `${Number(data.total_consumption_liters).toLocaleString()} L`;

        document.getElementById("average-consumption").textContent =
            `${Number(data.average_consumption_liters).toLocaleString()} L`;

        document.getElementById("total-readings").textContent =
            Number(data.total_readings).toLocaleString();

        zoneContainer.replaceChildren();

        if (!Array.isArray(data.zones)) {
            throw new Error("The API response does not contain a valid zones array.");
        }

        if (data.zones.length === 0) {
            zoneContainer.textContent = "No zone data available.";
        } else {
            data.zones.forEach((zone) => {
                const card = document.createElement("article");
                card.className = "zone-card";

                const heading = document.createElement("h3");
                heading.textContent = zone.zone_name;

                const consumption = document.createElement("p");
                consumption.textContent =
                    `Total consumption: ${
                        Number(zone.total_consumption_liters).toLocaleString()
                    } L`;

                const count = document.createElement("p");
                count.textContent =
                    `Number of readings: ${zone.reading_count}`;

                card.append(heading, consumption, count);
                zoneContainer.appendChild(card);
            });
        }

        drawAnalyticsChart(data.zones);

        message.textContent = "Analytics loaded successfully.";

    } catch (error) {
        console.error("Analytics loading error:", error);

        message.textContent =
            `Could not load analytics: ${error.message}`;
    }
}

function drawAnalyticsChart(zones) {
    const canvas = document.getElementById("analytics-chart");

    if (!canvas) {
        console.error("Analytics chart canvas was not found.");
        return;
    }

    if (typeof Chart === "undefined") {
        console.error("Chart.js could not be loaded.");
        return;
    }

    if (analyticsChart) {
        analyticsChart.destroy();
    }

    analyticsChart = new Chart(canvas, {
        type: "bar",
        data: {
            labels: zones.map((zone) => zone.zone_name),
            datasets: [{
                label: "Total Consumption (Litres)",
                data: zones.map(
                    (zone) => Number(zone.total_consumption_liters)
                ),
                backgroundColor: "#0284c7",
                borderRadius: 6
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: true,
            plugins: {
                legend: {
                    display: true,
                    position: "top"
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    title: {
                        display: true,
                        text: "Consumption in Litres"
                    }
                },
                x: {
                    title: {
                        display: true,
                        text: "Water Zones"
                    }
                }
            }
        }
    });
}

document.addEventListener("DOMContentLoaded", loadAnalytics);