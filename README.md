# AgroSmart ESP32 Hardware Integration

Complete system for ESP32-based smart irrigation with real-time sensor monitoring and AI control.

## Quick Start:
1. Wire ESP32 sensors according to SETUP_GUIDE.md
2. Upload esp32/esp32_agrosmart.ino to ESP32 (update IP address first!)
3. Run backend: `python backend/agrosmart_api.py`
4. Open frontend/index.html in browser
5. Set API Base to http://localhost:5000

## Features:
- Real-time sensor data from ESP32 hardware
- AI automatic irrigation control  
- Manual pump control via webapp
- Complete irrigation logging
- Hardware status monitoring
- Professional farming chatbot

See SETUP_GUIDE.md for detailed instructions.
