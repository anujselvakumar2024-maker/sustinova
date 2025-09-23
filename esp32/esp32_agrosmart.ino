#include <WiFi.h>
#include <HTTPClient.h>
#include <DHT.h>
#include <WebServer.h>

#define DHTPIN 27
#define DHTTYPE DHT11
#define SOIL_PIN 34
#define WATER_PIN 32
#define RAIN_PIN 33
#define RELAY_PIN 26

const char* ssid = "KAAVYA";
const char* password = "mahes_123";
const char* serverName = "http://<YOUR_PC_IP>:5000/api/sensors"; // Replace with your PC IP
const char* irrigationControlUrl = "http://<YOUR_PC_IP>:5000/api/irrigation/esp32/status";

DHT dht(DHTPIN, DHTTYPE);
WebServer server(80); // ESP32 web server for receiving commands

bool pumpRunning = false;
unsigned long pumpStartTime = 0;
unsigned long pumpDuration = 0; // in milliseconds

void setup() {
  Serial.begin(115200);

  // Connect to WiFi
  WiFi.begin(ssid, password);
  while (WiFi.status() != WL_CONNECTED) {
    delay(1000);
    Serial.println("Connecting to WiFi...");
  }
  Serial.println("Connected to WiFi");
  Serial.println("IP address: " + WiFi.localIP().toString());

  // Initialize sensors
  dht.begin();
  pinMode(RELAY_PIN, OUTPUT);
  digitalWrite(RELAY_PIN, HIGH); // Relay OFF (pump off) - assuming active LOW relay
  pinMode(RAIN_PIN, INPUT_PULLUP);

  // Setup web server endpoints for receiving commands from backend
  server.on("/pump/start", HTTP_POST, handlePumpStart);
  server.on("/pump/stop", HTTP_POST, handlePumpStop);
  server.on("/status", HTTP_GET, handleStatus);

  server.begin();
  Serial.println("ESP32 Web Server Started");
}

void loop() {
  server.handleClient(); // Handle incoming web requests

  // Check pump timer
  if (pumpRunning && millis() - pumpStartTime >= pumpDuration) {
    stopPump();
    Serial.println("Pump timer expired - stopping pump");
  }

  // Send sensor data every 10 seconds
  static unsigned long lastSensorSend = 0;
  if (millis() - lastSensorSend >= 10000) {
    sendSensorData();
    lastSensorSend = millis();
  }

  delay(100);
}

void sendSensorData() {
  if (WiFi.status() == WL_CONNECTED) {
    float temperature = dht.readTemperature();
    float humidity = dht.readHumidity();
    int soilRaw = analogRead(SOIL_PIN);
    int waterRaw = analogRead(WATER_PIN);

    // Check for sensor errors
    if (isnan(temperature) || isnan(humidity)) {
      Serial.println("DHT sensor error!");
      return;
    }

    int soilMoisture = map(soilRaw, 0, 4095, 100, 0); // Convert to percentage
    int waterLevel = map(waterRaw, 0, 4095, 0, 1000); // Convert to liters
    bool rainDetected = digitalRead(RAIN_PIN) == LOW;

    HTTPClient http;
    http.begin(serverName);
    http.addHeader("Content-Type", "application/json");

    String json = "{";
    json += "\"temperature\":" + String(temperature, 1) + ",";
    json += "\"humidity\":" + String(humidity, 1) + ",";
    json += "\"soil_moisture\":" + String(soilMoisture) + ",";
    json += "\"water_level\":" + String(waterLevel) + ",";
    json += "\"rain_detected\":" + String(rainDetected ? "true" : "false") + ",";
    json += "\"pump_running\":" + String(pumpRunning ? "true" : "false") + ",";
    json += "\"esp32_ip\":\"" + WiFi.localIP().toString() + "\"";
    json += "}";

    int httpResponseCode = http.POST(json);

    if (httpResponseCode > 0) {
      String response = http.getString();
      Serial.println("Sensor data sent successfully: " + String(httpResponseCode));
    } else {
      Serial.println("Error sending sensor data: " + String(httpResponseCode));
    }

    http.end();
  } else {
    Serial.println("WiFi not connected!");
  }
}

void handlePumpStart() {
  String body = server.arg("plain");
  Serial.println("Received pump start command: " + body);

  // Parse duration from JSON body
  int durationStart = body.indexOf("\"duration\":") + 11;
  int durationEnd = body.indexOf(",", durationStart);
  if (durationEnd == -1) durationEnd = body.indexOf("}", durationStart);

  if (durationStart > 11 && durationEnd > durationStart) {
    int duration = body.substring(durationStart, durationEnd).toInt();
    startPump(duration);

    server.send(200, "application/json", "{\"success\":true,\"message\":\"Pump started for " + String(duration) + " minutes\"}");
  } else {
    server.send(400, "application/json", "{\"success\":false,\"error\":\"Invalid duration\"}");
  }
}

void handlePumpStop() {
  stopPump();
  server.send(200, "application/json", "{\"success\":true,\"message\":\"Pump stopped\"}");
}

void handleStatus() {
  String json = "{";
  json += "\"pump_running\":" + String(pumpRunning ? "true" : "false") + ",";
  json += "\"remaining_time\":" + String(pumpRunning ? (pumpDuration - (millis() - pumpStartTime)) / 1000 : 0) + ",";
  json += "\"ip_address\":\"" + WiFi.localIP().toString() + "\"";
  json += "}";

  server.send(200, "application/json", json);
}

void startPump(int durationMinutes) {
  Serial.println("Starting pump for " + String(durationMinutes) + " minutes");

  pumpRunning = true;
  pumpStartTime = millis();
  pumpDuration = durationMinutes * 60 * 1000; // Convert to milliseconds

  digitalWrite(RELAY_PIN, LOW); // Turn relay ON (assuming active LOW relay)

  Serial.println("Pump ON - Duration: " + String(durationMinutes) + " minutes");
}

void stopPump() {
  Serial.println("Stopping pump");

  pumpRunning = false;
  digitalWrite(RELAY_PIN, HIGH); // Turn relay OFF

  Serial.println("Pump OFF");
}