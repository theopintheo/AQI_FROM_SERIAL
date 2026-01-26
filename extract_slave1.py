import json
import os

INPUT_FILE = 'sensor_data.json'
OUTPUT_FILE = 'slave1_data.json'
TARGET_ID = 1

def extract_data():
    if not os.path.exists(INPUT_FILE):
        print(f"Error: {INPUT_FILE} not found.")
        return

    try:
        with open(INPUT_FILE, 'r') as f:
            data = json.load(f)
        
        if not isinstance(data, list):
            print(f"Error: {INPUT_FILE} does not contain a list.")
            return

        # Filter for slave_id 1
        filtered_data = [item for item in data if item.get('slave_id') == TARGET_ID]

        with open(OUTPUT_FILE, 'w') as f:
            json.dump(filtered_data, f, indent=4)

        print(f"Successfully extracted {len(filtered_data)} records for Slave ID {TARGET_ID} to {OUTPUT_FILE}.")

    except json.JSONDecodeError:
        print(f"Error: Failed to decode JSON from {INPUT_FILE}.")
    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    extract_data()
