
"use strict";

// ============================================
// AquaSense - Smart Water Monitoring Dashboard
// ============================================

const summary = document.getElementById("summary");
const zoneSelect = document.getElementById("zone-id");
const readingForm = document.getElementById("reading-form");
const formMessage = document.getElementById("form-message");
const alertsContainer = document.getElementById("alerts");
const chartCanvas = document.getElementById("usage-chart");

let usageChart = null;

// ============================================
// Safely display text in HTML
// ============================================

function escapeHTML(value) {
    return String(value ?? "").replace(/[&<>"']/g, character => {
        const entities = {
            "&": "&amp;",
            "<": "&lt;",
            ">": "&gt;",
            '"': "&quot;",
            "'": "&#39;"
        };

        return entities[character];
    });
}

// ============================================
// Display messages
// ============================================

function showFormMessage(message, isError = false) {
    if (!formMessage) return;

    formMessage.textContent = message;
    formMessage.style.color = isError ? "#dc2626" : "#15803d";
}

// ============================================
// Load water zones into the form
// ============================================

async function loadZones() {
    if (!zoneSelect) return;

    try {
        const response = await fetch("/api/zones");

        if (!response.ok) {
            throw new Error("Could not load water zones.");
        }

        const zones = await response.json();

        zoneSelect.innerHTML =
            '<option value="">Select a zone</option>';

        zones.forEach(zone => {
            const option = document.createElement("option");

            option.value = zone.id;
            option.textContent =
                `${zone.name} - ${zone.location}`;

            zoneSelect.appendChild(option);
        });
    } catch (error) {
        console.error("Zone loading error:", error);

        zoneSelect.innerHTML =
            '<option value="">Unable to load zones</option>';
    }
}

// ============================================
// Load and display water summary
// ============================================

async function loadWaterSummary() {
    if (!summary) return;

    try {
        const response = await fetch("/api/summary");

        if (!response.ok) {
            throw new Error("Could not load water summary.");
        }

        const zones = await response.json();

        renderUsageChart(zones);

        if (zones.length === 0) {
            summary.textContent = "No water zones found.";
            return;
        }

        summary.innerHTML = zones.map(zone => {
            const percentage = Number(zone.usage_percentage);
            const used = Number(zone.total_consumption_liters);
            const remaining = Number(zone.remaining_liters);
            const limit = Number(zone.daily_limit_liters);

            let statusClass = "safe";

            if (percentage >= 100) {
                statusClass = "critical";
            } else if (percentage >= 80) {
                statusClass = "warning";
            }

            const progress = Math.min(
                Math.max(percentage, 0),
                100
            );

            return `
                <article class="zone-card">
                    <h3>${escapeHTML(zone.zone_name)}</h3>

                    <p class="location">
                        ${escapeHTML(zone.location)}
                    </p>

                    <p class="usage">
                        ${percentage.toFixed(2)}%
                    </p>

                    <p>Daily water limit used</p>

                    <div class="progress-track">
                        <div
                            class="progress-bar ${statusClass}"
                            style="width: ${progress}%"
                        ></div>
                    </div>

                    <p>${used.toLocaleString()} L used</p>

                    <p>
                        ${remaining.toLocaleString()} L remaining
                    </p>

                    <p>
                        Limit: ${limit.toLocaleString()} L
                    </p>

                    <p class="status ${statusClass}">
                        ${escapeHTML(zone.status)}
                    </p>
                </article>
            `;
        }).join("");

    } catch (error) {
        console.error("Summary loading error:", error);

        summary.textContent =
            "Unable to load water data. Please refresh the page.";
    }
}

// ============================================
// Draw water consumption chart
// ============================================

function renderUsageChart(zones) {
    if (!chartCanvas) return;

    if (typeof Chart === "undefined") {
        console.error(
            "Chart.js is unavailable. Check your internet connection."
        );
        return;
    }

    if (usageChart) {
        usageChart.destroy();
    }

    const labels = zones.map(zone => zone.zone_name);

    const consumption = zones.map(zone =>
        Number(zone.total_consumption_liters)
    );

    const limits = zones.map(zone =>
        Number(zone.daily_limit_liters)
    );

    usageChart = new Chart(chartCanvas, {
        type: "bar",

        data: {
            labels: labels,

            datasets: [
                {
                    label: "Water Used (Litres)",
                    data: consumption,
                    backgroundColor: "#0284c7",
                    borderRadius: 5
                },
                {
                    label: "Daily Limit (Litres)",
                    data: limits,
                    backgroundColor: "#a7d8f0",
                    borderRadius: 5
                }
            ]
        },

        options: {
            responsive: true,
            maintainAspectRatio: true,

            scales: {
                y: {
                    beginAtZero: true,
                    title: {
                        display: true,
                        text: "Litres"
                    }
                },

                x: {
                    title: {
                        display: true,
                        text: "Water Zones"
                    }
                }
            },

            plugins: {
                legend: {
                    display: true,
                    position: "top"
                },

                tooltip: {
                    enabled: true
                }
            }
        }
    });
}

// ============================================
// Load and display water alerts
// ============================================

async function loadAlerts() {
    if (!alertsContainer) return;

    try {
        const response = await fetch("/api/alerts");

        if (!response.ok) {
            throw new Error("Could not load alerts.");
        }

        const alerts = await response.json();

        if (alerts.length === 0) {
            alertsContainer.innerHTML = `
                <p class="no-alerts">
                    All zones are within safe usage limits.
                </p>
            `;

            return;
        }

        alertsContainer.innerHTML = alerts.map(alert => `
            <article class="alert-card ${escapeHTML(alert.level)}">
                <strong>
                    ${escapeHTML(alert.level.toUpperCase())}
                </strong>

                <p>${escapeHTML(alert.message)}</p>

                <p>
                    Usage: ${Number(alert.usage_percentage)}%
                </p>
            </article>
        `).join("");

    } catch (error) {
        console.error("Alert loading error:", error);

        alertsContainer.textContent =
            "Unable to load water alerts.";
    }
}

// ============================================
// Submit a new water reading
// ============================================

if (readingForm) {
    readingForm.addEventListener("submit", async event => {
        event.preventDefault();

        const zoneId = Number(zoneSelect.value);

        const consumptionInput =
            document.getElementById("consumption");

        const consumption = Number(consumptionInput.value);

        if (
            !zoneSelect.value ||
            !Number.isInteger(zoneId) ||
            zoneId <= 0
        ) {
            showFormMessage(
                "Please select a valid water zone.",
                true
            );
            return;
        }

        if (
            consumptionInput.value.trim() === "" ||
            !Number.isFinite(consumption) ||
            consumption < 0
        ) {
            showFormMessage(
                "Enter a valid, non-negative water consumption.",
                true
            );
            return;
        }

        const submitButton =
            readingForm.querySelector('button[type="submit"]');

        if (submitButton) {
            submitButton.disabled = true;
            submitButton.textContent = "Saving...";
        }

        showFormMessage("Saving water reading...");

        try {
            const response = await fetch("/api/readings", {
                method: "POST",

                headers: {
                    "Content-Type": "application/json"
                },

                body: JSON.stringify({
                    zone_id: zoneId,
                    consumption_liters: consumption
                })
            });

            const result = await response.json();

            if (!response.ok) {
                throw new Error(
                    result.error || "Failed to save reading."
                );
            }

            showFormMessage(
                "Water reading saved successfully!"
            );

            readingForm.reset();

            await Promise.all([
                loadWaterSummary(),
                loadAlerts()
            ]);

        } catch (error) {
            console.error("Reading submission error:", error);

            showFormMessage(
                error.message || "Unable to save reading.",
                true
            );
        } finally {
            if (submitButton) {
                submitButton.disabled = false;
                submitButton.textContent = "Save Reading";
            }
        }
    });
}

// ============================================
// Start the dashboard
// ============================================

async function initializeDashboard() {
    await Promise.all([
        loadZones(),
        loadWaterSummary(),
        loadAlerts()
    ]);
}

initializeDashboard();
