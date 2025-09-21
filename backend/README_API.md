# AgroSmart AI Backend API

## 🚀 Quick Start

### 1. Install Python Dependencies
```bash
pip install -r requirements.txt
```

### 2. Run the API Server
```bash
python agrosmart_api.py
```

The server will start at: `http://localhost:5000`

## 🤖 AI Features

### Smart Irrigation Engine
- **Soil moisture analysis** - Monitors soil conditions
- **Environmental factors** - Considers temperature, humidity, rain
- **Water level checks** - Ensures sufficient water supply
- **Intelligent timing** - Calculates optimal irrigation duration

### Decision Logic
- **Critical Level (≤20%)**: 30-minute heavy irrigation
- **Low Level (≤30%)**: 20-minute moderate irrigation  
- **Optimal Level (>30%)**: No irrigation needed
- **Rain Detection**: Automatic pause
- **Low Water Tank**: Safety stop

## 📡 API Endpoints

### Sensor Data
- `GET /api/sensors` - Get current sensor readings
- `POST /api/sensors` - Update sensor data (from ESP32)
- `POST /api/sensors/simulate` - Simulate sensor data for testing

### AI Analysis
- `GET /api/ai/analyze` - Get AI irrigation recommendation

### Irrigation Control
- `POST /api/irrigation/control` - Start/stop irrigation
  ```json
  {
    "action": "start",
    "duration": 20,
    "zone": "zone1", 
    "type": "ai"
  }
  ```

### Status & Logging
- `GET /api/irrigation/status` - Current system status
- `GET /api/motor-log` - Irrigation history

## 🔧 Frontend Configuration

In your webapp, set API Base to:
```
http://localhost:5000
```

## 🌐 Deployment Options

### Local Development
```bash
python agrosmart_api.py
```

### Production (Azure/AWS)
- Deploy as Flask app
- Use production WSGI server (gunicorn)
- Set up database for persistence
- Configure environment variables

## 📊 ESP32 Integration

Your ESP32 can send sensor data:
```cpp
// POST to /api/sensors
{
  "temperature": 25.5,
  "soil_moisture": 45,
  "humidity": 68,
  "water_level": 750,
  "rain_detected": false
}
```

## 🎯 AI Decision Example

Request: `GET /api/ai/analyze`

Response:
```json
{
  "should_irrigate": true,
  "duration": 20,
  "reason": "Irrigation needed based on soil moisture",
  "reasoning": "Soil moisture below optimal (28%). Moderate irrigation recommended.",
  "urgency": "moderate",
  "timestamp": "2025-09-21T22:26:00"
}
```

## 🔒 Security Notes

- Add authentication for production
- Validate all input data
- Use HTTPS in production
- Implement rate limiting
- Secure database connections

---

**AgroSmart AI** - Intelligence meets agriculture! 🌾🤖
