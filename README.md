
# 💧 AquaSense – Water Management System

AquaSense is a web-based water management system built using Flask, Python, SQLite, HTML, CSS, and JavaScript. It helps users monitor water usage, track readings, analyze consumption patterns, and identify potential issues through alerts and interactive dashboards.

## 🚀 Features

- **Dashboard:** View water usage summaries and key metrics.
- **Water Readings:** Record and manage water readings.
- **History:** Track historical water usage data.
- **Analytics:** Analyze water consumption trends.
- **Alerts:** Identify potential water-related issues.
- **REST API:** Access readings, zones, summaries, and analytics.

## 🛠️ Technologies Used

- Python
- Flask
- SQLite
- HTML5
- CSS3
- JavaScript
- Chart.js (if used in the project)

## 📁 Project Structure

```text
AquaSense/
├── app.py
├── config.py
├── database/
├── services/
├── templates/
├── static/
├── tests/
├── requirements.txt
└── README.md
```

## ⚙️ Installation and Setup

### 1. Clone the repository

```bash
git clone <YOUR_GITHUB_REPOSITORY_URL>
cd AquaSense
```

### 2. Create a virtual environment

```bash
python -m venv venv
```

### 3. Activate the virtual environment

**Windows PowerShell:**

```powershell
.\venv\Scripts\Activate.ps1
```

### 4. Install dependencies

```bash
pip install -r requirements.txt
```

### 5. Run the application

```bash
python app.py
```

Open your browser and visit:

http://127.0.0.1:5000

## 🧪 Running Tests

```bash
python -m pytest
```

## 🗄️ Database

AquaSense uses SQLite to store water management data. The database should be initialized according to the application's database setup.

## 🔮 Future Improvements

- Live sensor integration
- Water leakage detection
- Advanced consumption forecasting
- Cloud database integration
- Deployment to a cloud hosting platform

## 👩‍💻 Author

Developed as a Python and Flask project focused on water usage monitoring and analytics.