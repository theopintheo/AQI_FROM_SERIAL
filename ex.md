Step 1: The Sensing (Hardware Level)
The process begins in the physical world.

Sensor Reading: The MQ-135 sensor detects gas particles and outputs an analog voltage.
ADC Conversion: The ESP32's Analog-to-Digital Converter (ADC) converts this voltage into a digital integer (0 to 4095).
Calculation: The ESP32 code takes that raw number and converts it into a meaningful AQI value using a mathematical formula (e.g.,
(raw / 4095) \* 500
).
Step 2: The Packaging (JSON Construction)
The ESP32 cannot send raw voltages to a website; it must package them in a format the web server understands: JSON.

The ArduinoJson library creates a "package" (an array of objects).
It includes a unique sensor_id (like ESP32-STATION-01) so the server knows which device is talking.
It also adds temperature and humidity values from the DHT sensor.
Step 3: The Handshake (HTTP Transmission)
Now the data is ready to leave the ESP32.

WiFi Connection: The ESP32 connects to your router and gets its own internal IP.
The Request: The ESP32 creates an HTTP POST Request. It acts like a browser "submitting a form."
The Target: It aims for your laptop's IP address on port 8000: http://192.168.x.x:8000/api/readings/bulk-ingest/.
Step 4: The Reception (Django API)
Your laptop receives the request via the Django server.

Routing: The file
aqiproject/urls.py
sees the /api/ prefix and hands it to api/urls.py, which identifies the bulk-ingest path.
The View function: The data enters the function bulk_ingest_readings in api/views.py.
CSRF Bypass: Since this is a machine-to-machine connection, Django is told to bypass the normal "Security Cookie" check (@csrf_exempt).
Step 5: Processing & Auto-Onboarding
This is where the "intelligence" of your project lives:

Identification: The code looks at the sensor_id inside the JSON.
Smart Registration:
If the ID is new, Django automatically creates a new Sensor entry in the database.
If it exists, it links the data to the existing sensor.
Validation: The ReadingSerializer checks if the data is clean (e.g., no negative humidity or missing fields).
Step 6: Storage & Logging
Database: Once validated, the data is saved as a new row in your db.sqlite3 file.
Terminal Log: The server immediately writes a text line to static/sensor_logs.json.
Example: [LIVE] ESP32-STATION-01 | AQI: 45 | Temp: 28°C
Step 7: The Visualization (Frontend)
Your web browser is open to the Dashboard.

Polling: Every 2-3 seconds, the JavaScript in your dashboard (frontend) sends a "GET" request to /api/logs/.
Update: When it sees the new entry in the log file, it creates a new "Log Line" in the IoT Terminal on your screen.
Charts: When you refresh or switch to the Analytics page, the frontend calls /api/sensors/XYZ/readings/, and Django retrieves all those stored database rows to draw the charts.
Technical Summary Chart
Stage Technology Key File
Sensing ADC / C++ ESP32 Sketch
Packaging ArduinoJson ESP32 Sketch
Transport HTTP POST WiFi / TCP-IP
Routing Django URLs api/urls.py
Logic Python / DRF api/views.py
Storage SQLite3 core/models.py
Display JS / Fetch API Dashboard UI
