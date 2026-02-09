import serial
import json
import os
import random
import time
from datetime import datetime

# --- Configuration ---
SERIAL_PORT = 'COM7' 
BAUD_RATE = 115200
OUTPUT_FILE = 'sensor_data.json'
SIMULATION_MODE = True  # Enabled for web preview

# Station Names
STATION_NAMES = {
    1: "Kilpauk (Master)",
    2: "North Chennai",
    3: "South Chennai"
}

def print_live_status(station_name, aqi, co, smoke, temp, hum, lat, lng):
    """Prints the sensor data in a clean JSON format for terminal monitoring."""
    log_entry = {
        "timestamp": datetime.now().strftime("%H:%M:%S"),
        "level": "DATA",
        "message": f"[LIVE] {station_name} | AQI: {aqi:.1f} | CO: {co:.2f} | Smoke: {smoke:.2f} | Temp: {temp:.1f}°C | Lat: {lat:.4f}, Lng: {lng:.4f}"
    }
    print(json.dumps([log_entry], indent=2))

def get_aqi_info(aqi_value):
    """Returns Category and Color based on AQI value."""
    if aqi_value <= 50: return "Good", "Green"
    elif aqi_value <= 100: return "Moderate", "Yellow"
    elif aqi_value <= 150: return "Unhealthy for Sensitive Groups", "Orange"
    elif aqi_value <= 200: return "Unhealthy", "Red"
    elif aqi_value <= 300: return "Very Unhealthy", "Purple"
    else: return "Hazardous", "Maroon"

def append_to_json(new_data):
    data_list = []
    if os.path.exists(OUTPUT_FILE):
        try:
            with open(OUTPUT_FILE, 'r') as f:
                data_list = json.load(f)
        except (json.JSONDecodeError, FileNotFoundError):
            data_list = []
    
    # Keep only the last 2000 records to prevent file bloating
    data_list.append(new_data)
    if len(data_list) > 2000:
        data_list = data_list[-2000:]
        
    with open(OUTPUT_FILE, 'w') as f:
        json.dump(data_list, f, indent=4)

# Initialize
ser = None
if not SIMULATION_MODE:
    try:
        ser = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=1)
        print(f"--- Sentinel Air Active ---")
        print(f"Listening on {SERIAL_PORT}...")
    except Exception as e:
        print(f"Error connecting to Serial: {e}")
        exit()
else:
    print(f"SIMULATION MODE ACTIVE (Generating Multi-Station Data)")

# For multi-slave simulation
sim_slave_id = 1

try:
    while True:
        line = ""
        if not SIMULATION_MODE:
            if ser.in_waiting > 0:
                line = ser.readline().decode('utf-8', errors='ignore').strip()
        else:
            # Cycle through slaves 1, 2, 3
            time.sleep(2)
            raw_adc = random.uniform(200, 1800)
            
            # Different coordinates and baseline for different stations
            coords = {
                1: (13.0856, 80.2379), # Central
                2: (13.1250, 80.2100), # North
                3: (13.0400, 80.2500)  # South
            }
            lat, lng = coords.get(sim_slave_id, (13.0, 80.0))
            
            # Format: ID, Temp, Hum, RawAQI, CO, Smoke, Lat, Lng
            line = f"{sim_slave_id},{random.uniform(26,34):.1f},{random.uniform(45,75):.1f},{raw_adc:.1f},{random.uniform(0.1,6.0):.2f},{random.uniform(2,60):.2f},{lat:.4f},{lng:.4f}"
            
            # Increment and wrap sim_slave_id
            sim_slave_id = (sim_slave_id % 3) + 1

        if line:
            parts = line.split(',')
            if len(parts) >= 8:
                try:
                    slave_id = int(parts[0])
                    temp = float(parts[1])
                    hum = float(parts[2])
                    raw_aqi = float(parts[3])
                    co_val = float(parts[4])
                    smoke_val = float(parts[5])
                    latitude = float(parts[6])
                    longitude = float(parts[7])

                    # Enhanced AQI Calculation
                    air_quality = (raw_aqi / 4095.0) * 500.0
                    aqi_category, aqi_color = get_aqi_info(air_quality)

                    payload = {
                        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                        "slave_id": slave_id,
                        "station_name": STATION_NAMES.get(slave_id, f"Station {slave_id}"),
                        "temperature": temp,
                        "humidity": hum,
                        "air_quality": round(air_quality, 2),
                        "aqi_category": aqi_category,
                        "aqi_color": aqi_color,
                        "co_level": co_val,
                        "smoke": smoke_val,
                        "no_level": round(random.uniform(0.1, 1.2), 3), # Added missing NO field
                        "latitude": latitude,
                        "longitude": longitude
                    }
                    
                    append_to_json(payload)
                    print_live_status(
                        payload['station_name'],
                        payload['air_quality'],
                        payload['co_level'],
                        payload['smoke'],
                        payload['temperature'],
                        payload['humidity'],
                        payload['latitude'],
                        payload['longitude']
                    )
                except (ValueError, IndexError) as e:
                    continue
except KeyboardInterrupt:
    print("\nSystem stopped.")
finally:
    if ser:
        ser.close()

