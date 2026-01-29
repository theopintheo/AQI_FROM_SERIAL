import serial
import json
import os
import random
import time
from datetime import datetime

SERIAL_PORT = 'COM7' 
BAUD_RATE = 115200
OUTPUT_FILE = 'sensor_data.json'

# Set to True to test without Arduino
SIMULATION_MODE = True

baseline_co = 18.45  
baseline_no = 0.82   

def get_aqi_info(aqi_value):
    """Returns (Category, Color) based on AQI value."""
    if aqi_value <= 50:
        return "Good", "Green"
    elif aqi_value <= 100:
        return "Moderate", "Yellow"
    elif aqi_value <= 150:
        return "Unhealthy for Sensitive Groups", "Orange"
    elif aqi_value <= 200:
        return "Unhealthy", "Red"
    elif aqi_value <= 300:
        return "Very Unhealthy", "Purple"
    else:
        return "Hazardous", "Maroon"

def append_to_json(new_data):
    data_list = []
    if os.path.exists(OUTPUT_FILE):
        try:
            with open(OUTPUT_FILE, 'r') as f:
                data_list = json.load(f)
        except json.JSONDecodeError:
            data_list = []
    data_list.append(new_data)
    with open(OUTPUT_FILE, 'w') as f:
        json.dump(data_list, f, indent=4)

# Initialize
ser = None
if not SIMULATION_MODE:
    try:
        ser = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=1)
        print(f"System Active. Logging data to {OUTPUT_FILE}...")
    except Exception as e:
        print(f"Error: {e}")
        exit()
else:
    print(f"SIMULATION MODE ACTIVE. Generating synthetic data for all slaves...")

try:
    while True:
        line = ""
        if not SIMULATION_MODE:
            if ser.in_waiting > 0:
                line = ser.readline().decode('utf-8', errors='ignore').strip()
        else:
            time.sleep(5) # Simulate delay
            # Generate fake Slave 1 data string
            # Format: ID, Temp, Hum, AQI, ?, Smoke, Lat, Lon
            fake_aqi = random.uniform(20, 100)
            line = f"1,{random.uniform(25,35):.1f},{random.uniform(50,80):.1f},{fake_aqi:.1f},0,{random.uniform(0,50):.1f},0,0"

        if line:
            parts = line.split(',')
            if len(parts) == 8:
                    try:
                        noise_co = random.uniform(-0.08, 0.08)
                        noise_no = random.uniform(-0.005, 0.005)

                        baseline_co += random.uniform(-0.02, 0.02)
                        baseline_no += random.uniform(-0.001, 0.001)

                        final_co = round(baseline_co + noise_co, 3)
                        final_no = round(baseline_no + noise_no, 4)
                        
                        # Coordinates
                        coord_s1 = {"lat": 13.0856, "lon": 80.2379}
                        coord_s2 = {"lat": 13.0774, "lon": 80.2425}
                        coord_s3 = {"lat": 13.0856, "lon": 80.2379}

                        # --- Process Slave 1 (Real) ---
                        # Force slave 1 coordinates as requested
                        lat_s1 = coord_s1["lat"]
                        lon_s1 = coord_s1["lon"]
                        
                        air_quality = float(parts[3])
                        aqi_category, aqi_color = get_aqi_info(air_quality)

                        # Parse other raw values
                        temp = float(parts[1])
                        hum = float(parts[2])
                        smoke = float(parts[5])

                        payload_s1 = {
                            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                            "slave_id": int(parts[0]),
                            "temperature": temp,
                            "humidity": hum,
                            "air_quality": air_quality,
                            "aqi_category": aqi_category,
                            "aqi_color": aqi_color,
                            "co_level": final_co,
                            "no_level": final_no,
                            "smoke": smoke,
                            "latitude": lat_s1,
                            "longitude": lon_s1
                        }
                        
                        append_to_json(payload_s1)
                        print(f"[LOG] ID: {payload_s1['slave_id']} (Real) - AQI: {air_quality}")

                        # --- Generate Slave 2 (Fake) ---
                        # AQI 140-170 random
                        aqi_s2 = float(random.randint(140, 170))
                        cat_s2, col_s2 = get_aqi_info(aqi_s2)
                        
                        payload_s2 = {
                            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                            "slave_id": 2,
                            "temperature": temp, # Copy
                            "humidity": hum,     # Copy
                            "air_quality": aqi_s2,
                            "aqi_category": cat_s2,
                            "aqi_color": col_s2,
                            "co_level": round(final_co * random.uniform(0.9, 1.1), 3), # Similar
                            "no_level": round(final_no * random.uniform(0.9, 1.1), 4), # Similar
                            "smoke": round(smoke * random.uniform(0.9, 1.1), 1),       # Similar
                            "latitude": coord_s2["lat"],
                            "longitude": coord_s2["lon"]
                        }
                        append_to_json(payload_s2)
                        print(f"[LOG] ID: 2 (Fake) - AQI: {aqi_s2}")

                        # --- Generate Slave 3 (Fake) ---
                        # AQI 140-170 random
                        aqi_s3 = float(random.randint(140, 170))
                        cat_s3, col_s3 = get_aqi_info(aqi_s3)

                        payload_s3 = {
                            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                            "slave_id": 3,
                            "temperature": temp, # Copy
                            "humidity": hum,     # Copy
                            "air_quality": aqi_s3,
                            "aqi_category": cat_s3,
                            "aqi_color": col_s3,
                            "co_level": round(final_co * random.uniform(0.9, 1.1), 3), # Similar
                            "no_level": round(final_no * random.uniform(0.9, 1.1), 4), # Similar
                            "smoke": round(smoke * random.uniform(0.9, 1.1), 1),       # Similar
                            "latitude": coord_s3["lat"], # Duplicate of S1 as requested
                            "longitude": coord_s3["lon"]
                        }
                        append_to_json(payload_s3)
                        print(f"[LOG] ID: 3 (Fake) - AQI: {aqi_s3}")
                        
                    except (ValueError, IndexError):
                        continue
except KeyboardInterrupt:
    print("\nLog ended by user.")
finally:
    ser.close()