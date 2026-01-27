import json
import os
import random

def get_aqi_info(aqi_value):
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

def cleanup_file(file_path):
    if not os.path.exists(file_path):
        return

    order = [
        "timestamp", "slave_id", "temperature", "humidity", "air_quality",
        "aqi_category", "aqi_color", "co_level", "no_level", "smoke",
        "latitude", "longitude"
    ]

    ranges = [
        (0, 50), (51, 100), (101, 150), 
        (151, 200), (201, 300), (301, 500)
    ]
    weights = [0.10, 0.10, 0.35, 0.35, 0.07, 0.03]

    try:
        with open(file_path, 'r') as f:
            data = json.load(f)
        
        updated_data = []
        for entry in data:
            # Fix AQI if it's over 500 or in the "thousands" as requested
            if entry.get("air_quality", 0) > 500:
                chosen_range = random.choices(ranges, weights=weights)[0]
                new_aqi = float(random.randint(chosen_range[0], chosen_range[1]))
                entry["air_quality"] = new_aqi
                cat, color = get_aqi_info(new_aqi)
                entry["aqi_category"] = cat
                entry["aqi_color"] = color

            # Ensure order
            reordered = {key: entry[key] for key in order if key in entry}
            updated_data.append(reordered)

        with open(file_path, 'w') as f:
            json.dump(updated_data, f, indent=4)
        print(f"Cleaned up {file_path}")

    except Exception as e:
        print(f"Error cleaning {file_path}: {e}")

if __name__ == "__main__":
    cleanup_file("d:/projects/python pro/AQI_DATA/sensor_data.json")
    cleanup_file("d:/projects/python pro/AQI_DATA/slave1_data.json")
