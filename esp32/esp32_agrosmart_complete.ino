#include <WiFi.h>
#include <HTTPClient.h>
#include <DHT.h>
#include <WebServer.h>
#include <ArduinoJson.h>

#define DHTPIN 27
#define DHTTYPE DHT11
#define SOIL_PIN 34
#define WATER_PIN 32
#define RAIN_PIN 33
#define RELAY_PIN 26

// WiFi Configuration - UPDATE THESE WITH YOUR VALUES
const char* ssid = "KAAVYA";
const char* password = "mahes_123";
const char* serverName = "http://<YOUR_PC_IP>:5000/api/sensors"; // Replace <YOUR_PC_IP>

DHT dht(DHTPIN, DHTTYPE);
WebServer server(80);

// State variables
bool pumpRunning = false;
bool rainDetected = false;
bool previousRainState = false;
unsigned long pumpStartTime = 0;
unsigned long pumpDuration = 0;
unsigned long lastSensorSend = 0;

void setup() {
  Serial.begin(115200);
  Serial.println("AgroSmart ESP32 Rain Management System Starting...");

  // Connect to WiFi
  WiFi.begin(ssid, password);
  int attempts = 0;
  while (WiFi.status() != WL_CONNECTED && attempts < 30) {
    delay(1000);
    attempts++;
    Serial.println("Connecting to WiFi... Attempt " + String(attempts));
  }

  if (WiFi.status() == WL_CONNECTED) {
    Serial.println("WiFi Connected Successfully!");
    Serial.println("ESP32 IP Address: " + WiFi.localIP().toString());
  } else {
    Serial.println("WiFi Connection Failed!");
  }

  // Initialize hardware
  dht.begin();
  pinMode(RELAY_PIN, OUTPUT);
  digitalWrite(RELAY_PIN, HIGH); // Relay OFF initially
  pinMode(RAIN_PIN, INPUT_PULLUP);

  // Setup web server endpoints
  server.on("/pump/start", HTTP_POST, handlePumpStart);
  server.on("/pump/stop", HTTP_POST, handlePumpStop);
  server.on("/status", HTTP_GET, handleStatus);

  server.begin();
  Serial.println("ESP32 Web Server Started on port 80");
  Serial.println("System Ready - Monitoring sensors and rain...");
}

void loop() {
  server.handleClient();

  // Monitor rain state changes for immediate alerts
  bool currentRainState = digitalRead(RAIN_PIN) == LOW;
  if (currentRainState != previousRainState) {
    rainDetected = currentRainState;
    previousRainState = currentRainState;

    if (rainDetected) {
      Serial.println("🌧️ RAIN DETECTED - Sending immediate alert!");
      sendRainAlert(true);
      if (pumpRunning) {
        Serial.println("⏸️ Pausing pump due to rain...");
        digitalWrite(RELAY_PIN, HIGH); // Turn OFF but keep pumpRunning = true
      }
    } else {
      Serial.println("☀️ RAIN STOPPED - Notifying server...");
      sendRainAlert(false);
    }
  }

  // Check pump timer completion
  if (pumpRunning && millis() - pumpStartTime >= pumpDuration) {
    stopPump();
    Serial.println("⏰ Pump timer completed - stopping pump");
  }

  // Send regular sensor data every 10 seconds
  if (millis() - lastSensorSend >= 10000) {
    sendSensorData();
    lastSensorSend = millis();
  }

  delay(100);
}

void sendSensorData() {
  if (WiFi.status() != WL_CONNECTED) {
    Serial.println("❌ WiFi disconnected - cannot send data");
    return;
  }

  float temperature = dht.readTemperature();
  float humidity = dht.readHumidity();
  int soilRaw = analogRead(SOIL_PIN);
  int waterRaw = analogRead(WATER_PIN);

  if (isnan(temperature) || isnan(humidity)) {
    Serial.println("❌ DHT sensor error - retrying next cycle");
    return;
  }

  int soilMoisture = map(soilRaw, 0, 4095, 100, 0);
  int waterLevel = map(waterRaw, 0, 4095, 0, 1000);
  bool currentRain = digitalRead(RAIN_PIN) == LOW;

  HTTPClient http;
  http.begin(serverName);
  http.addHeader("Content-Type", "application/json");

  DynamicJsonDocument doc(1024);
  doc["temperature"] = round(temperature * 10) / 10.0;
  doc["humidity"] = round(humidity * 10) / 10.0;
  doc["soil_moisture"] = soilMoisture;
  doc["water_level"] = waterLevel;
  doc["rain_detected"] = currentRain;
  doc["pump_running"] = pumpRunning;
  doc["esp32_ip"] = WiFi.localIP().toString();
  doc["timestamp"] = millis();

  String jsonString;
  serializeJson(doc, jsonString);

  int httpResponseCode = http.POST(jsonString);

  if (httpResponseCode > 0) {
    Serial.println("📡 Data sent successfully: " + String(httpResponseCode));
  } else {
    Serial.println("❌ Error sending data: " + String(httpResponseCode));
  }

  http.end();

  // Debug output
  Serial.println("--- Current Readings ---");
  Serial.println("🌡️  Temperature: " + String(temperature) + "°C");
  Serial.println("💧 Humidity: " + String(humidity) + "%");
  Serial.println("🌱 Soil Moisture: " + String(soilMoisture) + "%");
  Serial.println("🚰 Water Level: " + String(waterLevel) + "L");
  Serial.println("🌧️  Rain: " + String(currentRain ? "YES" : "NO"));
  Serial.println("⚡ Pump: " + String(pumpRunning ? "ON" : "OFF"));
  Serial.println("------------------------");
}

void sendRainAlert(bool isRaining) {
  if (WiFi.status() != WL_CONNECTED) return;

  HTTPClient http;
  String endpoint = isRaining ? "/api/rain/alert" : "/api/rain/stopped";
  String url = "http://<YOUR_PC_IP>:5000" + endpoint; // Replace <YOUR_PC_IP>

  http.begin(url);
  http.addHeader("Content-Type", "application/json");

  DynamicJsonDocument doc(512);
  doc["rain_detected"] = isRaining;
  doc["timestamp"] = millis();
  doc["esp32_ip"] = WiFi.localIP().toString();

  if (isRaining) {
    doc["pump_was_running"] = pumpRunning;
  } else {
    doc["soil_moisture"] = map(analogRead(SOIL_PIN), 0, 4095, 100, 0);
  }

  String jsonString;
  serializeJson(doc, jsonString);

  int httpResponseCode = http.POST(jsonString);
  Serial.println("🌧️ Rain alert sent: " + String(httpResponseCode));

  http.end();
}

void handlePumpStart() {
  String body = server.arg("plain");
  Serial.println("🚀 Pump start request: " + body);

  DynamicJsonDocument doc(512);
  DeserializationError error = deserializeJson(doc, body);

  if (error) {
    server.send(400, "application/json", "{\"success\":false,\"error\":\"Invalid JSON\"}");
    return;
  }

  int duration = doc["duration"] | 10;

  if (digitalRead(RAIN_PIN) == LOW) {
    Serial.println("❌ Cannot start pump - rain detected");
    server.send(400, "application/json", "{\"success\":false,\"error\":\"Rain detected\"}");
    return;
  }

  startPump(duration);
  server.send(200, "application/json", "{\"success\":true,\"message\":\"Pump started\"}");
}

void handlePumpStop() {
  Serial.println("🛑 Pump stop request");
  stopPump();
  server.send(200, "application/json", "{\"success\":true,\"message\":\"Pump stopped\"}");
}

void handleStatus() {
  DynamicJsonDocument doc(512);
  doc["pump_running"] = pumpRunning;
  doc["rain_detected"] = digitalRead(RAIN_PIN) == LOW;
  doc["ip_address"] = WiFi.localIP().toString();
  doc["uptime"] = millis();

  if (pumpRunning) {
    doc["remaining_time"] = max(0, (int)((pumpDuration - (millis() - pumpStartTime)) / 1000));
  } else {
    doc["remaining_time"] = 0;
  }

  String jsonString;
  serializeJson(doc, jsonString);

  server.send(200, "application/json", jsonString);
}

void startPump(int durationMinutes) {
  Serial.println("🚀 Starting pump for " + String(durationMinutes) + " minutes");

  pumpRunning = true;
  pumpStartTime = millis();
  pumpDuration = durationMinutes * 60 * 1000;

  digitalWrite(RELAY_PIN, LOW); // Turn relay ON

  Serial.println("✅ Pump is now ON");
}

void stopPump() {
  Serial.println("🛑 Stopping pump");

  pumpRunning = false;
  digitalWrite(RELAY_PIN, HIGH); // Turn relay OFF

  Serial.println("✅ Pump is now OFF");
}