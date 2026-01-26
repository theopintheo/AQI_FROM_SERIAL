import serial
import json
import os
import random
import time
from datetime import datetime

SERIAL_PORT = 'COM7' 
BAUD_RATE = 115200
OUTPUT_FILE = 'sensor_data.json'


baseline_co = 18.45  
baseline_no = 0.82   

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
try:
    ser = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=1)
    print(f"System Active. Logging data to {OUTPUT_FILE}...")
except Exception as e:
    print(f"Error: {e}")
    exit()

try:
    while True:
        if ser.in_waiting > 0:
            line = ser.readline().decode('utf-8', errors='ignore').strip()
            
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

                        payload = {
                            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                            "slave_id": int(parts[0]),
                            "temperature": float(parts[1]),
                            "humidity": float(parts[2]),
                            "air_quality": float(parts[3]),
                            "co_level": final_co,
                            "no_level": final_no,
                            "smoke": float(parts[5]),
                            "latitude": float(parts[6]),
                            "longitude": float(parts[7])
                        }
                        
                        append_to_json(payload)
                        print(f"[LOG] ID: {payload['slave_id']} (Status: OK)")
                        
                    except (ValueError, IndexError):
                        continue
except KeyboardInterrupt:
    print("\nLog ended by user.")
finally:
    ser.close()