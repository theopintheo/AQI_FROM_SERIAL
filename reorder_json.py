import json
import os

def reorder_json_fields(file_path):
    if not os.path.exists(file_path):
        print(f"File {file_path} not found.")
        return

    order = [
        "timestamp",
        "slave_id",
        "temperature",
        "humidity",
        "air_quality",
        "aqi_category",
        "aqi_color",
        "co_level",
        "no_level",
        "smoke",
        "latitude",
        "longitude"
    ]

    try:
        with open(file_path, 'r') as f:
            data = json.load(f)
        
        if not isinstance(data, list):
            print(f"File {file_path} is not a JSON list.")
            return

        reordered_data = []
        for entry in data:
            reordered_entry = {}
            for key in order:
                if key in entry:
                    reordered_entry[key] = entry[key]
            # Add any extra keys that might be missed
            for key in entry:
                if key not in reordered_entry:
                    reordered_entry[key] = entry[key]
            reordered_data.append(reordered_entry)

        with open(file_path, 'w') as f:
            json.dump(reordered_data, f, indent=4)
        
        print(f"Successfully reordered {file_path}")

    except Exception as e:
        print(f"Error processing {file_path}: {e}")

if __name__ == "__main__":
    reorder_json_fields("d:/projects/python pro/AQI_DATA/sensor_data.json")
    reorder_json_fields("d:/projects/python pro/AQI_DATA/slave1_data.json")
