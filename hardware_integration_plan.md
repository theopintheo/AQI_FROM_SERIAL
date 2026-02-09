# IoT Integration Guide: ESP32 & Sensors

This guide provides a comprehensive walkthrough for connecting physical hardware to your Air Quality Index (AQI) dashboard.

---

## 📋 Implementation Phases

### Phase 1: Preparation
- [x] **Components**: ESP32 DevKit, MQ-135 (Gas), DHT11/22 (Temp), Breadboard.
- [x] **Arduino IDE Libraries**: 
    - `ArduinoJson` (by Benoit Blanchon)
    - `DHT sensor library` (by Adafruit)
- [ ] **Network**: Laptop and ESP32 must be on the same WiFi.

---

## 🔗 API Reference (Endpoints)

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| **POST** | `/api/readings/bulk-ingest/` | **Primary IoT Endpoint.** Use this for ESP32 sensors. |
| **POST** | `/api/readings/ingest/` | Send data from a single sensor. |
| **GET** | `/api/sensors/` | View all active sensors and their latest status. |
| **GET** | `/api/sensors/{id}/readings/` | Get historical data for a specific sensor. |
| **GET** | `/api/sensors/{id}/forecast/` | Get 24-hour predictions for a sensor. |
| **POST** | `/api/simulation/start/` | Start the backend background simulation. |
| **POST** | `/api/simulation/stop/` | Stop the background simulation. |
| **GET** | `/api/simulation_status/` | Check status of simulation and DB sync. |
| **GET** | `/api/logs/` | View recent system and data logs. |

---

### Phase 2: Server Configuration
1. **Find Laptop IP**: Run `ipconfig` in CMD. Note your IPv4 (e.g., `192.168.1.15`).
2. **Start Django**: You **must** run the server with `0.0.0.0` to allow WiFi connections:
   ```bash
   python manage.py runserver 0.0.0.0:8000
   ```

### Phase 3: Hardware Wiring
| Component | Pin | ESP32 Pin |
| :--- | :--- | :--- |
| **MQ-135** | VCC | **VIN (5V)** |
| **MQ-135** | AO | **GPIO 34** |
| **DHT11** | VCC | **3V3** |
| **DHT11** | DATA | **GPIO 4** |
| **Common** | GND | **GND** |

---

## 💻 ESP32 IoT Code

Copy the code below into your Arduino IDE. Update the WiFi credentials and the `serverUrl` with your laptop's IP.

```cpp
#include <WiFi.h>
#include <HTTPClient.h>
#include <ArduinoJson.h>
#include <DHT.h>

// --- WIFI CONFIGURATION ---
const char* ssid = "YOUR_WIFI_NAME";
const char* password = "YOUR_WIFI_PASSWORD";

// --- SERVER URL (Use your Laptop's IP) ---
const char* serverUrl = "http://192.168.x.x:8000/api/readings/bulk-ingest/";

// --- HARDWARE PINS ---
#define DHTPIN 4
#define DHTTYPE DHT11
#define MQ135_PIN 34

DHT dht(DHTPIN, DHTTYPE);

void setup() {
  Serial.begin(115200);
  dht.begin();
  WiFi.begin(ssid, password);
  while (WiFi.status() != WL_CONNECTED) { delay(500); Serial.print("."); }
  Serial.println("\n✅ WiFi Connected!");
}

void loop() {
  if (WiFi.status() == WL_CONNECTED) {
    float h = dht.readHumidity();
    float t = dht.readTemperature();
    int raw_aqi = analogRead(MQ135_PIN);
    float aqi_val = (raw_aqi / 4095.0) * 500.0;

    if (isnan(h) || isnan(t)) return;

    // Build Bulk JSON Payload
    StaticJsonDocument<512> doc;
    JsonArray root = doc.to<JsonArray>();
    JsonObject s1 = root.createNestedObject();
    
    s1["sensor_id"] = "ESP32-HARDWARE";
    s1["slave_id"] = 1;
    s1["temperature"] = t;
    s1["humidity"] = h;
    s1["air_quality"] = aqi_val;
    s1["aqi_category"] = (aqi_val <= 100) ? "Good" : "Unhealthy";
    s1["aqi_color"] = (aqi_val <= 100) ? "Green" : "Red";

    String payload;
    serializeJson(doc, payload);

    HTTPClient http;
    http.begin(serverUrl);
    http.addHeader("Content-Type", "application/json");
    int code = http.POST(payload);
    
    Serial.println("Sent: " + payload);
    Serial.println("Response: " + String(code));
    http.end();
  }
  delay(30000); // Send data every 30 seconds
}
```

---

## 🌟 Advanced Project Features

Your project includes several "Automated" features you should be aware of:

### 1. Zero-Config Sensor Onboarding
You do **not** need to manually add sensors in the Django Admin. 
*   If your ESP32 sends a `sensor_id` that the system hasn't seen before (e.g., `OFFICE-NODE-99`), the application will **automatically create** that sensor in the database.
*   It will immediately start appearing on your Dashboard.

### 2. Built-in AQI Forecasting
The project has a new forecasting engine. Once your physical sensor has sent data for at least **48 hours**, you can access its prediction via:
*   **Endpoint**: `/api/sensors/YOUR_SENSOR_ID/forecast/`
*   This uses historical trends to predict AQI for the next 24 hours.

### 3. Extended Data Fields
The database is ready for more than just Temperature. You can include these fields in your JSON to see them in the "Analytics" tab:
*   `co_level`: Carbon Monoxide
*   `no_level`: Nitrogen Oxide
*   `smoke`: Particulate/Smoke levels
*   `latitude` / `longitude`: To show the specific sensor location on the Map.

---

## 🛠️ Internal Project Code Changes

To enable seamless IoT integration, the following parts of the project codebase were modified:

### 1. Database Model (`core/models.py`)
The `Reading` model was expanded to support high-fidelity sensor data, including pollutants like Carbon Monoxide and Nitrogen Oxide.

```python
class Reading(models.Model):
    # raw slave id from device
    slave_id = models.IntegerField(null=True, blank=True)

    # optional FK mapping
    sensor = models.ForeignKey(
        Sensor,
        on_delete=models.SET_NULL,
        related_name="readings",
        null=True,
        blank=True
    )
    timestamp = models.DateTimeField(default=timezone.now)
    temperature = models.FloatField(null=True, blank=True)
    humidity = models.FloatField(null=True, blank=True)
    air_quality = models.FloatField(null=True, blank=True)
    aqi_category = models.CharField(max_length=50, blank=True)
    aqi_color = models.CharField(max_length=20, blank=True)
    co_level = models.FloatField(null=True, blank=True)
    no_level = models.FloatField(null=True, blank=True)
    smoke = models.FloatField(null=True, blank=True)
    latitude = models.FloatField(null=True, blank=True)
    longitude = models.FloatField(null=True, blank=True)

    class Meta:
        ordering = ["-timestamp"]
```

### 2. API Layer (`api/views.py`)
The `bulk_ingest_readings` function handles data from multiple sensors in a single request. It includes **Auto-Registration** logic that creates a new Sensor entry if the hardware ID has never been seen before.

```python
@api_view(['POST'])
def bulk_ingest_readings(request):
    readings_data = request.data if isinstance(request.data, list) else [request.data]
    
    created_readings = []
    errors = []
    
    for idx, reading_data in enumerate(readings_data):
        try:
            payload = reading_data.copy()
            
            # Extract sensor identifier
            sensor_id = payload.pop('sensor_id', None) or payload.get('sensor')
            
            if sensor_id:
                sensor = Sensor.objects.filter(sensor_id=str(sensor_id)).first()
                # AUTO-REGISTRATION: Create sensor if it doesn't exist
                if not sensor:
                    sensor_name = payload.pop('sensor_name', str(sensor_id))
                    sensor = Sensor.objects.create(
                        sensor_id=str(sensor_id),
                        name=sensor_name,
                        is_active=True
                    )
                payload['sensor'] = sensor.id
            
            serializer = ReadingSerializer(data=payload)
            if serializer.is_valid():
                reading = serializer.save()
                created_readings.append(reading.id)
            else:
                errors.append({'index': idx, 'errors': serializer.errors})
        
        except Exception as e:
            errors.append({'index': idx, 'error': str(e)})
    
    return Response({
        'created_count': len(created_readings),
        'error_count': len(errors),
        'created_ids': created_readings
    }, status=status.HTTP_201_CREATED)
```

### 3. Routing (`api/urls.py`)
Hardware endpoints are mapped in the API routing table.

```python
urlpatterns = router.urls + [
    path('readings/ingest/', ingest_reading, name='ingest-reading'),
    path('readings/bulk-ingest/', bulk_ingest_readings, name='bulk-ingest-reading'),
    
    # Sensor-specific analytics
    path('sensors/<str:sensor_id>/readings/', get_sensor_readings, name='sensor_readings'),
    path('sensors/<str:sensor_id>/forecast/', get_sensor_forecast, name='sensor_forecast'),
]
```

---

## ⚠️ Challenges & Solutions (WiFi IoT)

| Challenge | Impact | Solution Implementation |
| :--- | :--- | :--- |
| **Connection Drops** | Data gaps when the WiFi router resets or signal flickers. | **Code Cache**: Use a reconnection loop (`WiFi.reconnect()`) to restore the link before skipping data points. |
| **Power Consumption** | WiFi hardware is "always-on," draining batteries in hours. | **Deep Sleep**: Use `esp_deep_sleep_start()` between readings to wake for 5s and sleep for 10+ mins. |
| **IP Management** | Changing router IPs makes the server hard to find. | **Static IP/DNS**: Assign a static IP to your laptop/server in the router settings, or use a service like No-IP. |
| **Security** | Data visible to others on the same network. | **HTTPS**: Move from `http://` to `https://` and add an `Authorization` header to your requests. |

---

## 🔍 Testing & Verification
1. Open **Serial Monitor** (115200) to see if the ESP32 says `Response: 201`.
2. Open your dashboard at `http://localhost:8000`.
3. Locate the card named **ESP32-HARDWARE**.
4. Blow on the AQI sensor to watch the live graphs jump!