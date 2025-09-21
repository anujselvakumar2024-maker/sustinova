#!/bin/bash
# AgroSmart AI Setup Script

echo "🚀 Setting up AgroSmart AI System..."

# Setup backend
cd backend
echo "📦 Installing Python dependencies..."
pip install -r requirements.txt

echo "🤖 Starting AI API Server..."
python agrosmart_api.py &

echo "✅ Backend running on http://localhost:5000"
echo "📱 Open frontend/index.html in browser"
echo "🔧 Set API Base to: http://localhost:5000"
echo ""
echo "🌟 AgroSmart AI is ready!"
