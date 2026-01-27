import random
from collections import Counter

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

def simulate_distribution(iterations=1000):
    ranges = [
        (0, 50), (51, 100), (101, 150), 
        (151, 200), (201, 300), (301, 500)
    ]
    weights = [0.10, 0.10, 0.35, 0.35, 0.07, 0.03]
    
    results = []
    for _ in range(iterations):
        chosen_range = random.choices(ranges, weights=weights)[0]
        air_quality = random.randint(chosen_range[0], chosen_range[1])
        category, _ = get_aqi_info(air_quality)
        results.append(category)
    
    counts = Counter(results)
    print(f"Simulation results ({iterations} iterations):")
    for cat, count in counts.items():
        percentage = (count / iterations) * 100
        print(f"{cat}: {count} ({percentage:.1f}%)")

if __name__ == "__main__":
    simulate_distribution()
