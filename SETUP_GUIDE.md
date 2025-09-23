# AgroSmart ESP32 Hardware Integration Setup Guide

## 🎯 Complete Setup Instructions

### 📋 **What You'll Get:**
✅ ESP32 sends real-time sensor data to your webapp
✅ Webapp displays live temperature, soil moisture, humidity, water level  
✅ AI automatically controls ESP32 pump when in Automatic mode
✅ Manual pump control from webapp when in Manual mode
✅ Real-time irrigation status and history logging

---

## 🔧 **Hardware Setup**

### **1. ESP32 Wiring:**
```
DHT11 Temperature/Humidity Sensor:
├── VCC → 3.3V
├── GND → GND  
└── DATA → GPIO 27

Soil Moisture Sensor:
├── VCC → 3.3V
├── GND → GND
└── A0 → GPIO 34

Water Level Sensor:  
├── VCC → 3.3V
├── GND → GND
└── A0 → GPIO 32

Rain Sensor:
├── VCC → 3.3V  
├── GND → GND
└── D0 → GPIO 33

Relay Module (for pump):
├── VCC → 5V (external power)
├── GND → Common GND
├── IN → GPIO 26
├── COM → Pump positive wire
└── NO → Power supply positive
```

### **2. Install Arduino Libraries:**
1. Open Arduino IDE
2. Go to **Sketch → Include Library → Manage Libraries**
3. Search and install: **"DHT sensor library" by Adafruit**
4. WiFi and HTTPClient are already included in ESP32 core

---

## 💻 **Software Setup**

### **3. Update ESP32 Code:**
1. Open the provided `esp32_agrosmart.ino` file
2. **CRITICAL**: Replace `<YOUR_PC_IP>` with your computer's actual IP address:
   - **Windows**: Run `ipconfig` in Command Prompt
   - **Mac/Linux**: Run `ifconfig` in Terminal  
   - Find your WiFi IP (usually 192.168.x.x)
3. Update WiFi credentials: `ssid` and `password`
4. Upload code to ESP32

### **4. Start Backend Server:**
1. Install Python dependencies: `pip install -r backend/requirements.txt`
2. Run server: `python backend/agrosmart_api.py`
3. Server starts on `http://localhost:5000`

### **5. Open Frontend Webapp:**
1. Open `frontend/index.html` in browser
2. Set API Base to: `http://localhost:5000`
3. Click **Save Config**

---

## 🚀 **How It Works**

### **Real-time Data Flow:**
```
ESP32 Sensors → WiFi → Backend Server → Webapp Display
     ↓
  Every 10 seconds, ESP32 sends:
  • Temperature (DHT11)
  • Humidity (DHT11)  
  • Soil Moisture (Analog sensor)
  • Water Level (Analog sensor)
  • Rain Detection (Digital sensor)
  • Pump Status (Running/Stopped)
```

### **Automatic Mode (AI Control):**
1. ESP32 sends sensor data to backend
2. **AI analyzes conditions** (soil moisture, temperature, humidity, rain)
3. If irrigation needed, **AI sends pump start command to ESP32**
4. ESP32 turns relay ON → **Pump starts watering**
5. After calculated duration, **AI sends stop command**
6. ESP32 turns relay OFF → **Pump stops**
7. Webapp shows **real-time irrigation status**

### **Manual Mode (User Control):**
1. User clicks **"Start Pump"** in webapp
2. Command sent to backend → **ESP32 receives start command**
3. ESP32 turns relay ON → **Pump starts**
4. User can **stop anytime** from webapp
5. ESP32 immediately turns relay OFF

---

## 📊 **Webapp Features**

### **Live Data Display:**
- **Real-time sensor readings** (updates every 10 seconds)
- **Connection status** (ESP32 connected/disconnected)
- **Pump status** (ON/OFF with visual indicators)
- **Last updated timestamp**

### **AI Irrigation System:**
- **Intelligent analysis** of sensor conditions
- **Automatic pump control** based on soil moisture, temperature, humidity
- **Rain detection** pauses irrigation automatically
- **Water level safety** prevents dry running

### **Manual Controls:**
- **Direct ESP32 pump control** via webapp
- **Adjustable duration** (1-30 minutes)
- **Immediate start/stop** commands
- **Real-time status feedback**

### **Monitoring & Logging:**
- **Irrigation history** with timestamps and reasons
- **AI decision logs** showing why irrigation started/stopped
- **System notifications** for important events
- **Hardware connection status**

---

## 🔍 **Troubleshooting**

### **ESP32 Not Connecting:**
- Check WiFi credentials in code
- Verify IP address is correct
- Ensure ESP32 and computer on same network
- Check serial monitor for connection status

### **No Sensor Data:**
- Verify wiring connections
- Check power supply (3.3V for sensors)
- Test individual sensors with simple code
- Check ADC pins (34, 32) are not used elsewhere

### **Pump Not Working:**  
- Check relay wiring and power supply
- Verify relay triggers with multimeter
- Test GPIO 26 output manually
- Ensure pump power supply adequate

### **Backend Connection Issues:**
- Start backend server first: `python agrosmart_api.py`
- Check firewall allows port 5000
- Verify API base URL in webapp matches server
- Test with `http://localhost:5000` in browser

---

## 🎯 **Success Indicators**

✅ **ESP32 Serial Monitor shows:** "Connected to WiFi" and "IP address: x.x.x.x"
✅ **Webapp shows:** Green connection dot and "ESP32 Connected"  
✅ **Sensor data updates** every 10 seconds with real values
✅ **Manual pump control** works from webapp
✅ **Automatic mode** shows AI decisions and controls pump
✅ **Motor log** shows irrigation history with timestamps

---

## 🚀 **You're All Set!**

Your **AgroSmart ESP32 system** now provides:
- **Real-time hardware sensor monitoring**
- **AI-powered automatic irrigation**  
- **Manual pump control via webapp**
- **Complete irrigation logging and history**
- **Professional farming assistant chatbot**

**Happy Smart Farming!** 🌾💧🤖
