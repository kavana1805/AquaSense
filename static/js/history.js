
"use strict";

const zoneFilter = document.getElementById("zone-filter");
const historyBody = document.getElementById("history-body");
const historyMessage = document.getElementById("history-message");

async function loadHistoryZones() {
    try {
        const response = await fetch("/api/zones");

        if (!response.ok) {
            throw new Error("Unable to load water zones.");
        }

        const zones = await response.json();

        zones.forEach(zone => {
            const option = document.createElement("option");
            option.value = zone.id;
            option.textContent = zone.name;
            zoneFilter.appendChild(option);
        });
    } catch (error) {
        console.error(error);
        historyMessage.textContent = error.message;
    }
}

async function loadHistory() {
    historyMessage.textContent = "Loading reading history...";
    historyBody.replaceChildren();

    try {
        const selectedZone = zoneFilter.value;

        const url = selectedZone
            ? `/api/history?zone_id=${encodeURIComponent(selectedZone)}`
            : "/api/history";

        const response = await fetch(url);

        if (!response.ok) {
            throw new Error("Unable to load reading history.");
        }

        const readings = await response.json();

        if (readings.length === 0) {
            historyMessage.textContent =
                "No water readings found for this selection.";
            return;
        }

        historyMessage.textContent =
            `${readings.length} reading(s) found.`;

        readings.forEach(reading => {
            const row = document.createElement("tr");

            const values = [
                reading.zone_name,
                reading.location,
                `${Number(reading.consumption_liters).toLocaleString()} L`,
                reading.recorded_at
            ];

            values.forEach(value => {
                const cell = document.createElement("td");
                cell.textContent = value ?? "";
                row.appendChild(cell);
            });

            historyBody.appendChild(row);
        });
    } catch (error) {
        console.error(error);
        historyMessage.textContent = error.message;
    }
}

zoneFilter.addEventListener("change", loadHistory);

async function initializeHistory() {
    await loadHistoryZones();
    await loadHistory();
}

initializeHistory();