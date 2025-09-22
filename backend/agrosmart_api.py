# AgroSmart AI Backend API Server with Full Functionality
from flask import Flask, request, jsonify
from flask_cors import CORS
import json
import datetime
import random
import time
import threading

app = Flask(__name__)
CORS(app)

# In-memory data storage
sensor_data = {
    "temperature": 25.5,
    "soil_moisture": 37.2,
    "humidity": 68,
    "water_level": 750,
    "rain_detected": False,
    "last_updated": datetime.datetime.now().isoformat()
}

irrigation_log = []
active_irrigation = None
ai_decisions = []
chat_history = []
schedules = []

# Farming Knowledge Base for Chatbot
farming_knowledge = {
    "irrigation": {
        "keywords": ["irrigation", "watering", "water", "drip", "sprinkler"],
        "responses": [
            "For efficient irrigation: 1) Water early morning or evening 2) Use drip irrigation to save water 3) Check soil moisture before watering 4) Adjust based on weather conditions",
            "Drip irrigation saves 30-50% water compared to traditional methods. Install drip lines near plant roots for best results.",
            "Monitor soil moisture levels. Most crops need water when soil moisture drops below 30%. Over-watering can harm plants."
        ]
    },
    "crops": {
        "keywords": ["crop", "crops", "plant", "plants", "grow", "growing"],
        "responses": [
            "For healthy crop growth: 1) Choose varieties suitable for your climate 2) Ensure proper soil preparation 3) Follow recommended planting distances 4) Monitor for pests regularly",
            "Crop rotation helps maintain soil health. Rotate nitrogen-fixing crops with heavy feeders to improve soil fertility.",
            "Consider local climate and season. Plant crops that are well-adapted to your region for better yields."
        ]
    },
    "soil": {
        "keywords": ["soil", "earth", "ground", "fertilizer", "compost"],
        "responses": [
            "Healthy soil needs: 1) Good drainage 2) Proper pH (6.0-7.0 for most crops) 3) Organic matter 4) Regular testing",
            "Add compost regularly to improve soil structure and fertility. Organic matter helps retain moisture and nutrients.",
            "Test soil pH annually. Most vegetables prefer slightly acidic to neutral soil (pH 6.0-7.0)."
        ]
    },
    "pests": {
        "keywords": ["pest", "insects", "bugs", "disease", "fungus"],
        "responses": [
            "Integrated Pest Management: 1) Regular monitoring 2) Use beneficial insects 3) Organic pesticides when needed 4) Proper crop rotation",
            "Common organic pest control: Neem oil for insects, copper fungicides for diseases, companion planting for natural protection.",
            "Prevention is key: Maintain plant health, remove diseased plants promptly, ensure good air circulation."
        ]
    }
}

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
            "light": 10,
            "moderate": 20,
            "heavy": 30
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

        if sensors.get("rain_detected", False):
            decision["reason"] = "Rain detected - irrigation paused"
            decision["reasoning"] = "Natural irrigation occurring, manual irrigation not needed"
            return decision

        if sensors.get("water_level", 0) < self.thresholds["water_level_min"]:
            decision["reason"] = "Water tank level too low for irrigation"
            decision["reasoning"] = "Insufficient water supply in tank for safe irrigation"
            return decision

        soil_moisture = sensors.get("soil_moisture", 100)
        temperature = sensors.get("temperature", 20)
        humidity = sensors.get("humidity", 60)

        if soil_moisture <= self.thresholds["soil_moisture_critical"]:
            decision["should_irrigate"] = True
            decision["duration"] = self.irrigation_durations["heavy"]
            decision["reason"] = "Critical: Immediate irrigation needed"
            decision["reasoning"] = f"Soil moisture at critical level ({soil_moisture}%). Extended irrigation recommended."
            decision["urgency"] = "critical"
        elif soil_moisture <= self.thresholds["soil_moisture_min"]:
            duration = self.irrigation_durations["moderate"]

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

class FarmingChatbot:
    def __init__(self):
        self.knowledge = farming_knowledge
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

        message_lower = message.lower()
        best_topic = None
        max_matches = 0

        for topic, data in self.knowledge.items():
            matches = sum(1 for keyword in data['keywords'] if keyword.lower() in message_lower)
            if matches > max_matches:
                max_matches = matches
                best_topic = topic

        if best_topic and max_matches > 0:
            responses = self.knowledge[best_topic]['responses']
            return random.choice(responses)

        return "That's a great farming question! For specific advice on irrigation, crop management, soil health, pest control, or sustainable farming practices, please provide more details about your particular situation."

# Initialize AI engines
ai_engine = IrrigationAI()
chatbot = FarmingChatbot()

@app.route('/')
def home():
    return {
        "message": "AgroSmart AI API Server",
        "version": "3.0.0",
        "status": "running",
        "endpoints": [
            "GET /api/sensors - Get current sensor data",
            "POST /api/sensors - Update sensor data", 
            "GET /api/ai/analyze - Get AI irrigation decision",
            "POST /api/irrigation/control - Control irrigation",
            "GET /api/irrigation/status - Get irrigation status",
            "GET /api/motor-log - Get irrigation history",
            "POST /api/chat - Chat with farming AI assistant",
            "GET /api/schedules - Get irrigation schedules",
            "POST /api/schedules - Add irrigation schedule"
        ]
    }

@app.route('/api/sensors', methods=['GET'])
def get_sensors():
    """Get current sensor data"""
    return jsonify(sensor_data)

@app.route('/api/sensors', methods=['POST'])
def update_sensors():
    """Update sensor data (from ESP32)"""
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

    sensor_data.update({
        "temperature": round(random.uniform(15, 35), 1),
        "soil_moisture": round(random.uniform(20, 80), 1),
        "humidity": random.randint(40, 90),
        "water_level": random.randint(100, 1000),
        "rain_detected": random.random() < 0.1,
        "last_updated": datetime.datetime.now().isoformat()
    })

    return jsonify({"success": True, "data": sensor_data})

@app.route('/api/ai/analyze', methods=['GET'])
def ai_analyze():
    """Get AI irrigation decision"""
    global ai_decisions

    decision = ai_engine.analyze(sensor_data)
    ai_decisions.append(decision)
    ai_decisions = ai_decisions[-50:]  # Keep last 50

    return jsonify(decision)

@app.route('/api/chat', methods=['POST'])
def chat_with_ai():
    """Chat with farming AI assistant"""
    global chat_history

    try:
        data = request.get_json()
        message = data.get('message', '')
        language = data.get('language', 'en')
        user_id = data.get('user_id', 'anonymous')

        if not message:
            return jsonify({"success": False, "error": "No message provided"}), 400

        response = chatbot.get_response(message, language)

        chat_entry = {
            "user_id": user_id,
            "user_message": message,
            "bot_response": response,
            "language": language,
            "timestamp": datetime.datetime.now().isoformat(),
            "is_farming_related": chatbot.is_farming_related(message)
        }

        chat_history.append(chat_entry)
        chat_history = chat_history[-1000:]  # Keep last 1000

        return jsonify({
            "success": True,
            "response": response,
            "is_farming_related": chatbot.is_farming_related(message),
            "timestamp": chat_entry["timestamp"]
        })

    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/irrigation/control', methods=['POST'])
def irrigation_control():
    """Control irrigation system"""
    global active_irrigation, irrigation_log

    try:
        data = request.get_json()
        action = data.get('action')
        duration = data.get('duration', 10)
        zone = data.get('zone', 'zone1')
        irrigation_type = data.get('type', 'manual')

        if action == 'start':
            active_irrigation = {
                "type": irrigation_type,
                "zone": zone,
                "duration": duration,
                "start_time": datetime.datetime.now().isoformat(),
                "remaining_seconds": duration * 60,
                "status": "active"
            }

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
    recent_logs = irrigation_log[-100:] if len(irrigation_log) > 100 else irrigation_log

    return jsonify({
        "logs": recent_logs,
        "total": len(recent_logs)
    })

@app.route('/api/schedules', methods=['GET', 'POST'])
def handle_schedules():
    """Handle irrigation schedules"""
    global schedules

    if request.method == 'GET':
        return jsonify({"schedules": schedules})

    elif request.method == 'POST':
        data = request.get_json()
        schedule = {
            "id": len(schedules) + 1,
            "time": data.get('time'),
            "duration": data.get('duration'),
            "zone": data.get('zone'),
            "active": data.get('active', True),
            "created_at": datetime.datetime.now().isoformat()
        }
        schedules.append(schedule)
        return jsonify({"success": True, "schedule": schedule})

# Background task to update irrigation status
def update_irrigation_status():
    global active_irrigation
    while True:
        if active_irrigation and active_irrigation["status"] == "active":
            active_irrigation["remaining_seconds"] -= 1

            if active_irrigation["remaining_seconds"] <= 0:
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
threading.Thread(target=update_irrigation_status, daemon=True).start()

if __name__ == '__main__':
    print("🚀 Starting AgroSmart AI API Server...")
    print("📡 Frontend connects to: http://localhost:5000")
    print("🤖 AI Engine: Ready")
    print("💬 Farming Chatbot: Ready")
    print("💧 Irrigation Control: Active")
    print("📊 Sensor Simulation: Available")
    app.run(debug=True, host='0.0.0.0', port=5000)
