@echo off
echo 🚀 Setting up AgroSmart AI System...

cd backend
echo 📦 Installing Python dependencies...
pip install -r requirements.txt

echo 🤖 Starting AI API Server...
start python agrosmart_api.py

echo ✅ Backend running on http://localhost:5000
echo 📱 Open frontend/index.html in browser  
echo 🔧 Set API Base to: http://localhost:5000
echo.
echo 🌟 AgroSmart AI is ready!
pause
