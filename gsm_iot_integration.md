# IoT Integration Guide: GSM/SIM Card Transmission

This guide explains how to build a remote Air Quality monitoring station that transmits data over cellular networks (GSM/GPRS) using a SIM card. This is ideal for locations without WiFi.

---

## 📋 Hardware Requirements

| Component | Description |
| :--- | :--- |
| **ESP32 DevKit** | The main microcontroller. |
| **SIM800L Module** | GSM/GPRS module (supports 2G). *Note: Ensure your SIM card supports 2G/GPRS.* |
| **Sensors** | MQ-135, DHT11/22 (same as WiFi version). |
| **Power Supply** | SIM800L requires 3.7V - 4.2V (at least 2A peak current). A Li-ion battery or high-quality Buck converter is recommended. |
| **Antenna** | Usually comes with the SIM800L. |

---

## 🔗 GSM Wiring (ESP32 to SIM800L)

| SIM800L Pin | ESP32 Pin | Note |
| :--- | :--- | :--- |
| **VCC** | **External 4V** | **Do NOT use ESP32 3.3V/5V pins!** GSM modules need high current. |
| **GND** | **GND** | Connect all GNDs together. |
| **TX** | **GPIO 16 (RX2)** | Serial communication. |
| **RX** | **GPIO 17 (TX2)** | Serial communication. |
| **RST** | **GPIO 5** | Optional (for hardware reset). |

---

## 📲 ESP32 GSM IoT Code

This code uses the **TinyGSM** library. It initializes the GPRS connection using your SIM card's APN and sends data to the Django API.

```cpp
#define TINY_GSM_MODEM_SIM800
#include <TinyGsmClient.h>
#include <ArduinoJson.h>
#include <DHT.h>

// --- GSM CONFIGURATION ---
const char apn[]      = "YOUR_SIM_APN"; // e.g., "internet" or "airtelgprs.com"
const char gprsUser[] = "";
const char gprsPass[] = "";

// --- SERVER CONFIGURATION ---
const char server[]   = "YOUR_SERVER_IP_OR_DOMAIN"; 
const char resource[] = "/api/readings/bulk-ingest/";
const int  port       = 80; // or 443 for HTTPS

// --- HARDWARE PINS ---
#define SerialAT Serial2
#define DHTPIN 4
#define DHTTYPE DHT11
#define MQ135_PIN 34

DHT dht(DHTPIN, DHTTYPE);
TinyGsm modem(SerialAT);
TinyGsmClient client(modem);

void setup() {
  Serial.begin(115200);
  delay(10);
  SerialAT.begin(9600, SERIAL_8N1, 16, 17); // SIM800L RX, TX
  
  Serial.println("Initializing modem...");
  modem.restart();
  
  Serial.print("Connecting to network...");
  if (!modem.waitForNetwork()) {
    Serial.println(" fail");
    while (true);
  }
  Serial.println(" success");

  Serial.print("Connecting to GPRS...");
  if (!modem.gprsConnect(apn, gprsUser, gprsPass)) {
    Serial.println(" fail");
    while (true);
  }
  Serial.println(" success");
  
  dht.begin();
}

void loop() {
  float h = dht.readHumidity();
  float t = dht.readTemperature();
  int raw_aqi = analogRead(MQ135_PIN);
  float aqi_val = (raw_aqi / 4095.0) * 500.0;

  if (!isnan(h) && !isnan(t)) {
    // Build Payload
    StaticJsonDocument<256> doc;
    JsonArray root = doc.to<JsonArray>();
    JsonObject s1 = root.createNestedObject();
    
    s1["sensor_id"] = "GSM-NODE-01";
    s1["temperature"] = t;
    s1["humidity"] = h;
    s1["air_quality"] = aqi_val;

    String payload;
    serializeJson(doc, payload);

    // Send HTTP POST
    if (client.connect(server, port)) {
      client.print(String("POST ") + resource + " HTTP/1.1\r\n");
      client.print(String("Host: ") + server + "\r\n");
      client.print("Content-Type: application/json\r\n");
      client.print("Content-Length: " + String(payload.length()) + "\r\n");
      client.print("Connection: close\r\n\r\n");
      client.print(payload);
      
      unsigned long timeout = millis();
      while (client.connected() && millis() - timeout < 10000) {
        if (client.available()) {
          String response = client.readString();
          Serial.println("Response: " + response);
        }
      }
      client.stop();
    }
  }
  
  delay(60000); // Send data every 60 seconds (save data/power)
}
```

---

## 💡 Important Considerations for GSM

### 1. External Power
The ESP32 cannot provide enough current for a GSM module during network searches. Use a dedicated **3.7V Li-ion battery** or a power module that can deliver at least **2 Amps**.

### 2. Network Compatibility
Most SIM800L modules only support **2G**. Ensure:
*   Your SIM card is not 4G/5G-only (it must support fallback to 2G).
*   Your carrier still provides 2G coverage in your area.

### 3. Data Usage
Sending data every minute uses roughly **5-10 KB** per hour. Over a month, this is approx **7 MB**. A small data pack is sufficient.

### 4. Public IP/DNS
For the GSM device to reach your Django server, the server must be:
*   Hosted on a **Cloud Server** (AWS, Heroku, DigitalOcean).
*   OR reachable via a **Static IP** with port forwarding.
*   OR reachable via **Ngrok** (for testing).

---

---

## 🛠️ Internal Project Code Support

To support remote GSM nodes without manual configuration, the following backend systems were implemented:

### 1. Unified Ingestion View (`api/views.py`)
The `bulk_ingest_readings` function is designed to be protocol-agnostic. It processes standard HTTP POST requests sent via GPRS identical to those sent via WiFi.

```python
@api_view(['POST'])
def bulk_ingest_readings(request):
    # This view handles the JSON payload from the GSM modem
    readings_data = request.data if isinstance(request.data, list) else [request.data]
    for reading_data in readings_data:
        sensor_id = reading_data.get('sensor_id')
        
        # AUTO-REGISTRATION: Essential for remote GSM nodes
        sensor = Sensor.objects.filter(sensor_id=str(sensor_id)).first()
        if not sensor:
            sensor = Sensor.objects.create(
                sensor_id=str(sensor_id),
                name=reading_data.get('sensor_name', f"GSM-{sensor_id}"),
                is_active=True
            )
        # ... validation and save
```

### 2. High-Fidelity Pollutant Tracking (`core/models.py`)
Remote stations often monitor more pollutants. The database was modified to support these additional IoT fields:

```python
class Reading(models.Model):
    # Standard Fields
    temperature = models.FloatField(null=True)
    humidity = models.FloatField(null=True)
    
    # GSM/High-Fidelity Fields
    co_level = models.FloatField(null=True)   # Carbon Monoxide
    no_level = models.FloatField(null=True)   # Nitrogen Oxide
    smoke = models.FloatField(null=True)      # Particulate/Smoke
    latitude = models.FloatField(null=True)   # GPS from GSM module
    longitude = models.FloatField(null=True)
```

---

## 🔍 How it syncs to Dashboard
Because of the **Auto-Registration** logic in your Django backend, as soon as your GSM device sends its first packet:
1. The backend sees `sensor_id: "GSM-NODE-01"`.
2. It automatically creates a new sensor entry using the logic shown above.
3. The dashboard immediately starts showing the cellular sensor's data in the "Live Monitoring" section.

---

## 💰 SIM Card Options & Market Context

When selecting a SIM card for your remote station, consider these cost-effective IoT models:

### 🔄 Pay-As-You-Go / No Subscription Fees
Providers like **Things Mobile** or **Onomondo** offer SIMs with no fixed monthly costs. You only pay for the data actually used, which is ideal for sensors sending small packets.

### ⏳ "No-Expiry" Data Packages
Providers such as **Keepgo** or **Capestone** offer "lifetime" SIM cards. You make a one-time purchase, and the data remains valid for a very long time (e.g., 12 months or until fully used), avoiding the hassle of monthly recharges.

### 🧪 Trial & Test SIMs
Some providers offer free SIM cards for testing purposes. These are usually limited by time (e.g., 180 days) or data volume (e.g., 50MB), which is more than enough for initial project verification.

### 💤 No Inactive Fees
Certain providers (e.g., **Onomondo**) do not charge for the SIM if it is not sending data. This allows you to keep a stock of inactive SIMs for future deployment without incurring ongoing costs.

### 🇮🇳 Indian Market Context
While most mainstream Indian IoT/M2M SIMs (Airtel, Vi, BSNL) typically require a yearly subscription or activation fee, some models are tailored for industrial use:
*   **Annual Renewals**: Often preferred over monthly recharges for set-and-forget deployment.
*   **M2M Specific Plans**: Request "M2M" or "IoT" SIMs specifically, as they often have lower data rates but much higher longevity and network priority for small data bursts.

---

## ⚠️ Challenges & Solutions (GSM IoT)

| Challenge | Impact | Solution Implementation |
| :--- | :--- | :--- |
| **Peak Power Bursts** | GSM modules pull up to **2A** during network searches, causing brownouts. | **Hardware Fix**: Add a **1000µF+ capacitor** across the SIM800L VCC and GND pins. |
| **Modem Freezing** | GPRS modems can hang if signal is lost for too long. | **Watchdog**: Implement a reset function in code if no response is received after 5 attempts. |
| **Latency/Timeouts** | GPRS is slow, causing HTTP requests to fail. | **Extended Timeouts**: Set HTTP client timeout to **20s** (`http.setTimeout(20000)`). |
| **Data Cost** | Frequent JSON payloads increase SIM bills. | **Payload Optimization**: Use the `bulk-ingest` API to send bundles of data every 10-20 minutes. |
| **Carrier CGNAT** | Private IPs prevent incoming server communication. | **Client-Initiated**: Your project uses the **Push model** where the device starts the talk. |

---
