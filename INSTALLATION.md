# AIRDON AQI Installation Guide

This guide will walk you through setting up the AIRDON AQI monitoring system on your local machine.

## 🛠 Prerequisites

- **Python 3.8+** installed
- **Git** installed
- **ESP32 Hardware** (Optional, if running in Live mode)

---

## 🚀 Setup Steps

### 1. Clone the Repository

Open your terminal and run:

```bash
git clone https://github.com/theopintheo/AQI_FROM_SERIAL.git
cd AQI_DATA
```

### 2. Set Up Virtual Environment (Recommended)

Create and activate a virtual environment to keep your dependencies isolated.

**Windows:**

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

**macOS/Linux:**

```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 3. Install Dependencies

Install the required Python packages:

```bash
pip install -r requirements.txt
```

---

## 📡 Running the System

### Step A: Start Data Logging

This script reads data from your ESP32 (via Serial) or generates simulated data for testing.

1. Open `air_quality_data_serial.py`.
2. Set `SIMULATION_MODE = True` for testing without hardware.
3. If using hardware, set `SIMULATION_MODE = False` and update `SERIAL_PORT` (e.g., `COM7`).
4. Run the script:
   ```bash
   python air_quality_data_serial.py
   ```

### Step B: Start Dashboard Server

In a **new** terminal window (with the venv activated):

1. Run the dashboard server:
   ```bash
   python start_dashboard.py
   ```
2. The dashboard will be available at: [http://localhost:8001](http://localhost:8001)

---

## 📊 Dashboard Features

- **Real-time Trends**: View AQI, Temperature, Humidity, and Smoke data.
- **Multi-Station**: Switch between Master, North, and South station data.
- **Export**: Use the "Save JSON" button to download current data.
- **Warnings**: The system will alert you if the sensor goes offline for more than 15 seconds.

---

## 🔧 Troubleshooting

- **Serial Error**: Ensure your ESP32 is plugged in and the correct `COM` port is set.
- **Data Not Loading**: Ensure `air_quality_data_serial.py` is running and generating `sensor_data.json`.
- **Port Busy**: If port `8001` is taken, change it in `start_dashboard.py`.
