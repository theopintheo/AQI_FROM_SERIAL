
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

# Test cases
test_values = [10, 50, 51, 100, 101, 150, 151, 200, 201, 300, 301, 500]
print(f"{'AQI':<5} | {'Category':<32} | {'Color':<10}")
print("-" * 55)
for v in test_values:
    cat, col = get_aqi_info(v)
    print(f"{v:<5} | {cat:<32} | {col:<10}")
