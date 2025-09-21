# AgroSmart AI Backend API Server
# Run this with: python agrosmart_api.py

from flask import Flask, request, jsonify
from flask_cors import CORS
import json
import datetime
import random
import time

app = Flask(__name__)
CORS(app)  # Enable CORS for frontend communication

# In-memory data storage (use database in production)
sensor_data = {
    "temperature": 25.5,
    "soil_moisture": 45,
    "humidity": 68,
    "water_level": 750,
    "rain_detected": False,
    "last_updated": datetime.datetime.now().isoformat()
}

irrigation_log = []
active_irrigation = None
ai_decisions = []

class IrrigationAI:
    def __init__(self):
        self.thresholds = {
            "soil_moisture_min": 30,
            "soil_moisture_critical": 20,
            "water_level_min": 200,
            "temperature_max": 35,
            "humidity_min": 40
        }

        self.irrigation_durations = {
            "light": 10,    # 10 minutes
            "moderate": 20, # 20 minutes
            "heavy": 30     # 30 minutes
        }

    def analyze(self, sensors):
        decision = {
            "should_irrigate": False,
            "duration": 0,
            "reason": "",
            "reasoning": "",
            "urgency": "low",
            "timestamp": datetime.datetime.now().isoformat()
        }

        # Check if rain is detected
        if sensors.get("rain_detected", False):
            decision["reason"] = "Rain detected - irrigation paused"
            decision["reasoning"] = "Natural irrigation occurring, manual irrigation not needed"
            return decision

        # Check water level
        if sensors.get("water_level", 0) < self.thresholds["water_level_min"]:
            decision["reason"] = "Water tank level too low for irrigation"
            decision["reasoning"] = "Insufficient water supply in tank for safe irrigation"
            return decision

        soil_moisture = sensors.get("soil_moisture", 100)
        temperature = sensors.get("temperature", 20)
        humidity = sensors.get("humidity", 60)

        # Analyze soil moisture
        if soil_moisture <= self.thresholds["soil_moisture_critical"]:
            decision["should_irrigate"] = True
            decision["duration"] = self.irrigation_durations["heavy"]
            decision["reason"] = "Critical: Immediate irrigation needed"
            decision["reasoning"] = f"Soil moisture at critical level ({soil_moisture}%). Extended irrigation recommended."
            decision["urgency"] = "critical"
        elif soil_moisture <= self.thresholds["soil_moisture_min"]:
            duration = self.irrigation_durations["moderate"]

            # Increase duration if hot and dry
            if (temperature > self.thresholds["temperature_max"] and 
                humidity < self.thresholds["humidity_min"]):
                duration = self.irrigation_durations["heavy"]
                decision["reasoning"] = f"Low soil moisture ({soil_moisture}%) with high temperature ({temperature}°C) and low humidity ({humidity}%). Extended irrigation needed."
            else:
                decision["reasoning"] = f"Soil moisture below optimal ({soil_moisture}%). Moderate irrigation recommended."

            decision["should_irrigate"] = True
            decision["duration"] = duration
            decision["reason"] = "Irrigation needed based on soil moisture"
            decision["urgency"] = "moderate"
        else:
            decision["reason"] = "Soil conditions are optimal"
            decision["reasoning"] = f"Soil moisture adequate ({soil_moisture}%). No irrigation required."

        return decision

# Initialize AI engine
ai_engine = IrrigationAI()

@app.route('/')
def home():
    return {
        "message": "AgroSmart AI API Server",
        "version": "1.0.0",
        "endpoints": [
            "GET /api/sensors - Get current sensor data",
            "POST /api/sensors - Update sensor data", 
            "GET /api/ai/analyze - Get AI irrigation decision",
            "POST /api/irrigation/control - Control irrigation",
            "GET /api/irrigation/status - Get irrigation status",
            "GET /api/motor-log - Get irrigation history"
        ]
    }

@app.route('/api/sensors', methods=['GET'])
def get_sensors():
    """Get current sensor data"""
    return jsonify(sensor_data)

@app.route('/api/sensors', methods=['POST'])
def update_sensors():
    """Update sensor data (typically called by ESP32)"""
    global sensor_data
    try:
        data = request.get_json()
        sensor_data.update(data)
        sensor_data["last_updated"] = datetime.datetime.now().isoformat()
        return jsonify({"success": True, "data": sensor_data})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 400

@app.route('/api/sensors/simulate', methods=['POST'])
def simulate_sensors():
    """Simulate sensor data for testing"""
    global sensor_data

    # Simulate realistic hill region data
    sensor_data.update({
        "temperature": round(random.uniform(15, 35), 1),
        "soil_moisture": random.randint(20, 80),
        "humidity": random.randint(40, 90),
        "water_level": random.randint(100, 1000),
        "rain_detected": random.random() < 0.1,  # 10% chance
        "last_updated": datetime.datetime.now().isoformat()
    })

    return jsonify({"success": True, "data": sensor_data})

@app.route('/api/ai/analyze', methods=['GET'])
def ai_analyze():
    """Get AI irrigation decision based on current sensors"""
    global ai_decisions

    decision = ai_engine.analyze(sensor_data)
    ai_decisions.append(decision)

    # Keep only last 50 decisions
    ai_decisions = ai_decisions[-50:]

    return jsonify(decision)

@app.route('/api/irrigation/control', methods=['POST'])
def irrigation_control():
    """Control irrigation system"""
    global active_irrigation, irrigation_log

    try:
        data = request.get_json()
        action = data.get('action')  # 'start', 'stop', 'pause'
        duration = data.get('duration', 10)  # minutes
        zone = data.get('zone', 'zone1')
        irrigation_type = data.get('type', 'manual')  # 'manual', 'automatic', 'ai'

        if action == 'start':
            active_irrigation = {
                "type": irrigation_type,
                "zone": zone,
                "duration": duration,
                "start_time": datetime.datetime.now().isoformat(),
                "remaining_seconds": duration * 60,
                "status": "active"
            }

            # Log the start
            irrigation_log.append({
                "timestamp": datetime.datetime.now().isoformat(),
                "action": "start",
                "type": irrigation_type,
                "zone": zone,
                "duration": duration
            })

            return jsonify({"success": True, "irrigation": active_irrigation})

        elif action == 'stop':
            if active_irrigation:
                # Log the stop
                irrigation_log.append({
                    "timestamp": datetime.datetime.now().isoformat(),
                    "action": "stop",
                    "type": active_irrigation.get("type", "unknown"),
                    "zone": active_irrigation.get("zone", "unknown"),
                    "duration_completed": active_irrigation.get("duration", 0) - (active_irrigation.get("remaining_seconds", 0) / 60)
                })

                active_irrigation = None

            return jsonify({"success": True, "message": "Irrigation stopped"})

        else:
            return jsonify({"success": False, "error": "Invalid action"}), 400

    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 400

@app.route('/api/irrigation/status', methods=['GET'])
def irrigation_status():
    """Get current irrigation status"""
    return jsonify({
        "active_irrigation": active_irrigation,
        "sensor_data": sensor_data,
        "last_ai_decision": ai_decisions[-1] if ai_decisions else None
    })

@app.route('/api/motor-log', methods=['GET'])
def motor_log():
    """Get irrigation history"""
    days = request.args.get('days', 7, type=int)

    # Filter logs by days (simplified for demo)
    recent_logs = irrigation_log[-100:] if len(irrigation_log) > 100 else irrigation_log

    return jsonify({
        "logs": recent_logs,
        "total": len(recent_logs)
    })

@app.route('/api/schedules', methods=['GET', 'POST'])
def schedules():
    """Handle irrigation schedules"""
    if request.method == 'GET':
        # Return stored schedules (implement with database)
        return jsonify({"schedules": []})

    elif request.method == 'POST':
        # Save new schedule (implement with database)
        data = request.get_json()
        return jsonify({"success": True, "message": "Schedule saved"})

# Background task to update irrigation status
def update_irrigation_status():
    global active_irrigation
    while True:
        if active_irrigation and active_irrigation["status"] == "active":
            active_irrigation["remaining_seconds"] -= 1

            if active_irrigation["remaining_seconds"] <= 0:
                # Auto-stop irrigation
                irrigation_log.append({
                    "timestamp": datetime.datetime.now().isoformat(),
                    "action": "auto_stop",
                    "type": active_irrigation.get("type", "unknown"),
                    "zone": active_irrigation.get("zone", "unknown"),
                    "duration_completed": active_irrigation.get("duration", 0)
                })
                active_irrigation = None

        time.sleep(1)

# Start background task
import threading
threading.Thread(target=update_irrigation_status, daemon=True).start()

if __name__ == '__main__':
    print("🚀 Starting AgroSmart AI API Server...")
    print("📡 Frontend should connect to: http://localhost:5000")
    print("🤖 AI Engine: Ready")
    print("💧 Irrigation Control: Active")
    print("📊 Sensor Simulation: Available")
    app.run(debug=True, host='0.0.0.0', port=5000)
