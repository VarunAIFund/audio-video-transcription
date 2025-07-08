#!/bin/bash

# Audio/Video Transcription App Startup Script
# This script starts both the Flask backend and React frontend

echo "🎬 Starting Audio/Video Transcription Application"
echo "=================================================="

# Check if we're in the right directory
if [ ! -f "app.py" ]; then
    echo "❌ Error: app.py not found. Please run this script from the project root directory."
    exit 1
fi

# Check if frontend directory exists
if [ ! -d "frontend" ]; then
    echo "❌ Error: frontend directory not found."
    exit 1
fi

# Function to check if a port is in use
check_port() {
    local port=$1
    if lsof -Pi :$port -sTCP:LISTEN -t >/dev/null 2>&1; then
        return 0  # Port is in use
    else
        return 1  # Port is free
    fi
}

# Check if ports are available
if check_port 5000; then
    echo "⚠️  Port 5000 is already in use. Please stop the service using port 5000 or modify app.py to use a different port."
    exit 1
fi

if check_port 3000; then
    echo "⚠️  Port 3000 is already in use. The React app will try to use a different port."
fi

echo "🔧 Checking dependencies..."

# Check Python dependencies
python3 -c "import flask, flask_cors, openai, ffmpeg" 2>/dev/null
if [ $? -ne 0 ]; then
    echo "❌ Missing Python dependencies. Please install:"
    echo "   pip3 install flask flask-cors openai ffmpeg-python"
    exit 1
fi

# Check Node.js dependencies
if [ ! -d "frontend/node_modules" ]; then
    echo "❌ Node.js dependencies not installed. Please run:"
    echo "   cd frontend && npm install"
    exit 1
fi

echo "✅ Dependencies check passed"

# Create log directory
mkdir -p logs

echo ""
echo "🚀 Starting Backend (Flask API)..."
echo "   Backend will run on: http://localhost:5000"

# Start Flask backend in background
python3 app.py > logs/backend.log 2>&1 &
BACKEND_PID=$!

# Wait a moment for backend to start
sleep 3

# Check if backend started successfully
if ! kill -0 $BACKEND_PID 2>/dev/null; then
    echo "❌ Backend failed to start. Check logs/backend.log for details."
    exit 1
fi

# Test backend health
python3 -c "
import requests
import time
time.sleep(2)
try:
    response = requests.get('http://localhost:5000/api/health', timeout=5)
    if response.status_code == 200:
        print('✅ Backend started successfully')
    else:
        print('❌ Backend health check failed')
        exit(1)
except Exception as e:
    print(f'❌ Backend connection failed: {e}')
    exit(1)
"

if [ $? -ne 0 ]; then
    echo "❌ Backend health check failed"
    kill $BACKEND_PID 2>/dev/null
    exit 1
fi

echo ""
echo "🎨 Starting Frontend (React App)..."
echo "   Frontend will run on: http://localhost:3000"
echo ""

# Function to cleanup on exit
cleanup() {
    echo ""
    echo "🛑 Shutting down..."
    echo "   Stopping backend (PID: $BACKEND_PID)"
    kill $BACKEND_PID 2>/dev/null
    echo "   Stopping frontend"
    kill %1 2>/dev/null
    echo "✅ Cleanup complete"
    exit 0
}

# Set up signal handlers
trap cleanup SIGINT SIGTERM

# Start React frontend
cd frontend
npm start &

# Wait for React to start and show success message
sleep 5

echo ""
echo "🎉 Application started successfully!"
echo "=================================================="
echo "📱 Frontend: http://localhost:3000"
echo "🔧 Backend:  http://localhost:5000"
echo "📋 API Docs: http://localhost:5000/api/health"
echo ""
echo "📝 Features available:"
echo "   • Upload audio/video files (MP4, MP3, WAV, etc.)"
echo "   • Speaker identification and diarization"
echo "   • Multi-language translation (Spanish, Chinese)"
echo "   • AI-powered summaries with action items"
echo "   • Download all results as text files"
echo ""
echo "🔄 Processing uses:"
echo "   • OpenAI Whisper API for transcription"
echo "   • GPT-4 for translations and summaries"
echo "   • PyAnnote.audio for speaker detection"
echo ""
echo "Press Ctrl+C to stop both servers"
echo "=================================================="

# Wait for frontend process
wait