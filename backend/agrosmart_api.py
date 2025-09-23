# Backend with rain check already.
from flask import Flask, request, jsonify
from flask_cors import CORS
import datetime, random, time, threading, requests

app = Flask(__name__)
CORS(app)

sensor_data = {"temperature":25,"soil_moisture":40,"humidity":60,"water_level":800,"rain_detected":False,"pump_running":False}
active_irrigation=None

@app.route('/api/sensors',methods=['GET'])
def get_sensors():
    return jsonify(sensor_data)

@app.route('/api/sensors',methods=['POST'])
def update_sensors():
    global sensor_data
    data=request.get_json();sensor_data.update(data)
    sensor_data['last_updated']=datetime.datetime.now().isoformat()
    return jsonify(success=True)

@app.route('/api/irrigation/control',methods=['POST'])
def irrigation_control():
    global active_irrigation
    data=request.get_json();action=data.get('action');duration=data.get('duration',10)
    if sensor_data.get('rain_detected') and action=='start':
        return jsonify(success=False,error='Rain detected. Pump blocked.'),400
    if action=='start':
        sensor_data['pump_running']=True
        active_irrigation={'duration':duration,'start':time.time()}
        return jsonify(success=True)
    elif action=='stop':
        sensor_data['pump_running']=False;active_irrigation=None
        return jsonify(success=True)
    return jsonify(success=False,error='Bad action'),400

if __name__=='__main__':
    app.run(port=5000,debug=True)
