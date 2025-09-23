# AgroSmart AI Backend API Server with ESP32 Hardware Integration
from flask import Flask, request, jsonify
from flask_cors import CORS
import json
import datetime
import random
import time
import threading
import requests

app = Flask(__name__)
CORS(app)

# Global variables
sensor_data = {
    "temperature": 25.5,
    "soil_moisture": 37.2,
    "humidity": 68,
    "water_level": 750,
    "rain_detected": False,
    "pump_running": False,
    "esp32_ip": None,
    "last_updated": datetime.datetime.now().isoformat()
}

irrigation_log = []
active_irrigation = None
ai_decisions = []
chat_history = []
esp32_ip = None

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
            "light": 5,     # 5 minutes
            "moderate": 10, # 10 minutes  
            "heavy": 15     # 15 minutes
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

        # Check if pump is already running
        if sensors.get("pump_running", False):
            decision["reason"] = "Pump already running"
            decision["reasoning"] = "Irrigation currently in progress"
            return decision

        # Check water level
        if sensors.get("water_level", 0) < self.thresholds["water_level_min"]:
            decision["reason"] = "Water tank level too low for irrigation"
            decision["reasoning"] = f"Water level ({sensors.get('water_level', 0)}L) below minimum threshold ({self.thresholds['water_level_min']}L)"
            return decision

        soil_moisture = sensors.get("soil_moisture", 100)
        temperature = sensors.get("temperature", 20)
        humidity = sensors.get("humidity", 60)

        # Analyze soil moisture and environmental conditions
        if soil_moisture <= self.thresholds["soil_moisture_critical"]:
            decision["should_irrigate"] = True
            decision["duration"] = self.irrigation_durations["heavy"]
            decision["reason"] = "Critical: Immediate irrigation needed"
            decision["reasoning"] = f"Soil moisture at critical level ({soil_moisture}%). Extended irrigation recommended."
            decision["urgency"] = "critical"
        elif soil_moisture <= self.thresholds["soil_moisture_min"]:
            duration = self.irrigation_durations["moderate"]

            # Increase duration if hot and dry conditions
            if (temperature > self.thresholds["temperature_max"] and 
                humidity < self.thresholds["humidity_min"]):
                duration = self.irrigation_durations["heavy"]
                decision["reasoning"] = f"Low soil moisture ({soil_moisture}%) with high temperature ({temperature}°C) and low humidity ({humidity}%). Extended irrigation needed."
            else:
                decision["reasoning"] = f"Soil moisture below optimal level ({soil_moisture}%). Moderate irrigation recommended."

            decision["should_irrigate"] = True
            decision["duration"] = duration
            decision["reason"] = "Irrigation needed based on soil moisture"
            decision["urgency"] = "moderate"
        else:
            decision["reason"] = "Soil conditions are optimal"
            decision["reasoning"] = f"Soil moisture level is adequate ({soil_moisture}%). No irrigation required at this time."

        return decision

class FarmingChatbot:
    def __init__(self):
        self.farming_keywords = [
            'farm', 'crop', 'plant', 'grow', 'soil', 'water', 'irrigation', 'pest', 'fertilizer',
            'seed', 'harvest', 'agriculture', 'organic', 'compost', 'weather', 'season',
            'disease', 'insect', 'vegetable', 'fruit', 'grain', 'rice', 'wheat', 'corn'
        ]

    def is_farming_related(self, message):
        message_lower = message.lower()
        return any(keyword.lower() in message_lower for keyword in self.farming_keywords)

    def get_response(self, message, language='en'):
        if not self.is_farming_related(message):
            return "I'm specialized in farming and agriculture. Please ask me about irrigation, crops, soil management, pest control, or other farming topics!"

        msg = message.lower()
        if 'irrigation' in msg or 'water' in msg:
            return "For efficient irrigation: Water early morning or evening, use drip irrigation to save water, and check soil moisture before watering. Your AI system will automatically manage optimal watering schedules!"
        elif 'soil' in msg:
            return "Healthy soil needs good drainage, proper pH (6.0-7.0), organic matter, and regular testing. Your sensor data shows current soil moisture levels for optimal irrigation timing."
        elif 'pest' in msg:
            return "Use Integrated Pest Management: Regular monitoring, beneficial insects, organic pesticides when needed, and proper crop rotation."
        else:
            return "That's a great farming question! Your AgroSmart system monitors temperature, humidity, soil moisture, and water levels to provide optimal irrigation recommendations."

# Initialize AI engines
ai_engine = IrrigationAI()
chatbot = FarmingChatbot()

@app.route('/')
def home():
    return {
        "message": "AgroSmart AI API Server with ESP32 Integration",
        "version": "4.0.0",
        "status": "running",
        "esp32_connected": esp32_ip is not None,
        "esp32_ip": esp32_ip,
        "endpoints": [
            "GET /api/sensors - Get current sensor data",
            "POST /api/sensors - Update sensor data from ESP32", 
            "GET /api/ai/analyze - Get AI irrigation decision",
            "POST /api/irrigation/control - Control irrigation manually",
            "POST /api/irrigation/esp32/control - Control ESP32 pump",
            "GET /api/irrigation/status - Get irrigation status",
            "GET /api/motor-log - Get irrigation history",
            "POST /api/chat - Chat with farming AI assistant"
        ]
    }

@app.route('/api/sensors', methods=['GET'])
def get_sensors():
    """Get current sensor data"""
    return jsonify(sensor_data)

@app.route('/api/sensors', methods=['POST'])
def update_sensors():
    """Update sensor data from ESP32"""
    global sensor_data, esp32_ip
    try:
        data = request.get_json()
        print(f"Received sensor data: {data}")

        # Update sensor data
        sensor_data.update(data)
        sensor_data["last_updated"] = datetime.datetime.now().isoformat()

        # Store ESP32 IP for future communication
        if "esp32_ip" in data:
            esp32_ip = data["esp32_ip"]
            print(f"ESP32 IP updated: {esp32_ip}")

        # Run AI analysis if in automatic mode
        run_automatic_irrigation_check()

        return jsonify({"success": True, "data": sensor_data})
    except Exception as e:
        print(f"Error updating sensors: {str(e)}")
        return jsonify({"success": False, "error": str(e)}), 400

def run_automatic_irrigation_check():
    """Run AI analysis and start irrigation if needed"""
    global ai_decisions, active_irrigation

    try:
        decision = ai_engine.analyze(sensor_data)
        ai_decisions.append(decision)
        ai_decisions = ai_decisions[-50:]  # Keep last 50 decisions

        print(f"AI Decision: {decision}")

        # If AI recommends irrigation and no irrigation is currently active
        if decision["should_irrigate"] and not active_irrigation:
            success = start_esp32_irrigation(decision["duration"], "ai_automatic")

            if success:
                active_irrigation = {
                    "type": "ai_automatic",
                    "duration": decision["duration"],
                    "start_time": datetime.datetime.now().isoformat(),
                    "reason": decision["reason"],
                    "status": "active"
                }

                # Log the irrigation start
                irrigation_log.append({
                    "timestamp": datetime.datetime.now().isoformat(),
                    "action": "ai_start",
                    "type": "ai_automatic", 
                    "duration": decision["duration"],
                    "reason": decision["reason"],
                    "soil_moisture": sensor_data.get("soil_moisture", 0),
                    "temperature": sensor_data.get("temperature", 0)
                })

                print(f"AI started irrigation for {decision['duration']} minutes")
            else:
                print("Failed to start ESP32 irrigation")

    except Exception as e:
        print(f"Error in automatic irrigation check: {str(e)}")

def start_esp32_irrigation(duration_minutes, irrigation_type="manual"):
    """Send irrigation start command to ESP32"""
    global esp32_ip

    if not esp32_ip:
        print("ESP32 IP not available")
        return False

    try:
        url = f"http://{esp32_ip}/pump/start"
        payload = {"duration": duration_minutes, "type": irrigation_type}

        response = requests.post(url, json=payload, timeout=5)

        if response.status_code == 200:
            print(f"Successfully started ESP32 pump for {duration_minutes} minutes")
            return True
        else:
            print(f"Failed to start ESP32 pump: {response.status_code}")
            return False

    except Exception as e:
        print(f"Error communicating with ESP32: {str(e)}")
        return False

def stop_esp32_irrigation():
    """Send irrigation stop command to ESP32"""
    global esp32_ip

    if not esp32_ip:
        print("ESP32 IP not available")
        return False

    try:
        url = f"http://{esp32_ip}/pump/stop"
        response = requests.post(url, timeout=5)

        if response.status_code == 200:
            print("Successfully stopped ESP32 pump")
            return True
        else:
            print(f"Failed to stop ESP32 pump: {response.status_code}")
            return False

    except Exception as e:
        print(f"Error communicating with ESP32: {str(e)}")
        return False

@app.route('/api/ai/analyze', methods=['GET'])
def ai_analyze():
    """Get AI irrigation decision"""
    decision = ai_engine.analyze(sensor_data)
    return jsonify(decision)

@app.route('/api/irrigation/control', methods=['POST'])
def irrigation_control():
    """Control irrigation system manually"""
    global active_irrigation

    try:
        data = request.get_json()
        action = data.get('action')
        duration = data.get('duration', 10)
        irrigation_type = data.get('type', 'manual')

        if action == 'start':
            success = start_esp32_irrigation(duration, irrigation_type)

            if success:
                active_irrigation = {
                    "type": irrigation_type,
                    "duration": duration,
                    "start_time": datetime.datetime.now().isoformat(),
                    "status": "active"
                }

                irrigation_log.append({
                    "timestamp": datetime.datetime.now().isoformat(),
                    "action": "manual_start",
                    "type": irrigation_type,
                    "duration": duration
                })

                return jsonify({"success": True, "message": f"Irrigation started for {duration} minutes"})
            else:
                return jsonify({"success": False, "error": "Failed to start ESP32 pump"}), 500

        elif action == 'stop':
            success = stop_esp32_irrigation()

            if success:
                if active_irrigation:
                    irrigation_log.append({
                        "timestamp": datetime.datetime.now().isoformat(),
                        "action": "manual_stop",
                        "type": active_irrigation.get("type", "unknown"),
                        "duration_completed": active_irrigation.get("duration", 0)
                    })

                active_irrigation = None
                return jsonify({"success": True, "message": "Irrigation stopped"})
            else:
                return jsonify({"success": False, "error": "Failed to stop ESP32 pump"}), 500
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
        "esp32_connected": esp32_ip is not None,
        "esp32_ip": esp32_ip,
        "last_ai_decision": ai_decisions[-1] if ai_decisions else None
    })

@app.route('/api/motor-log', methods=['GET'])
def motor_log():
    """Get irrigation history"""
    days = request.args.get('days', 7, type=int)
    recent_logs = irrigation_log[-50:] if len(irrigation_log) > 50 else irrigation_log

    return jsonify({
        "logs": recent_logs,
        "total": len(recent_logs),
        "esp32_connected": esp32_ip is not None
    })

@app.route('/api/chat', methods=['POST'])
def chat_with_ai():
    """Chat with farming AI assistant"""
    global chat_history

    try:
        data = request.get_json()
        message = data.get('message', '')
        language = data.get('language', 'en')

        if not message:
            return jsonify({"success": False, "error": "No message provided"}), 400

        response = chatbot.get_response(message, language)

        chat_entry = {
            "user_message": message,
            "bot_response": response,
            "language": language,
            "timestamp": datetime.datetime.now().isoformat(),
            "is_farming_related": chatbot.is_farming_related(message)
        }

        chat_history.append(chat_entry)
        chat_history = chat_history[-100:]  # Keep last 100

        return jsonify({
            "success": True,
            "response": response,
            "is_farming_related": chatbot.is_farming_related(message),
            "timestamp": chat_entry["timestamp"]
        })

    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

# Background task to monitor irrigation completion
def monitor_irrigation():
    global active_irrigation

    while True:
        try:
            if active_irrigation and esp32_ip:
                # Check ESP32 status
                response = requests.get(f"http://{esp32_ip}/status", timeout=3)
                if response.status_code == 200:
                    status = response.json()
                    if not status.get("pump_running", False):
                        # Pump stopped, mark irrigation as complete
                        if active_irrigation:
                            irrigation_log.append({
                                "timestamp": datetime.datetime.now().isoformat(),
                                "action": "completed",
                                "type": active_irrigation.get("type", "unknown"),
                                "duration_completed": active_irrigation.get("duration", 0)
                            })
                            print(f"Irrigation completed: {active_irrigation['type']}")

                        active_irrigation = None
        except Exception as e:
            print(f"Error monitoring irrigation: {str(e)}")

        time.sleep(30)  # Check every 30 seconds

# Start background monitoring
threading.Thread(target=monitor_irrigation, daemon=True).start()

if __name__ == '__main__':
    print("🚀 Starting AgroSmart AI API Server with ESP32 Integration...")
    print("📡 Frontend connects to: http://localhost:5000")
    print("🤖 AI Engine: Ready")
    print("💬 Farming Chatbot: Ready") 
    print("🔧 ESP32 Hardware Integration: Ready")
    print("💧 Automatic Irrigation Control: Active")
    app.run(debug=True, host='0.0.0.0', port=5000)
