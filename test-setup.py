#!/usr/bin/env python3
"""
Test script to verify the Flask backend setup and basic functionality.
"""

import os
import sys
import time
import threading
import requests
from pathlib import Path

def test_imports():
    """Test that all required imports work."""
    print("🔍 Testing imports...")
    
    try:
        import flask
        print(f"  ✅ Flask {flask.__version__}")
    except ImportError as e:
        print(f"  ❌ Flask: {e}")
        return False
    
    try:
        import flask_cors
        print("  ✅ Flask-CORS")
    except ImportError as e:
        print(f"  ❌ Flask-CORS: {e}")
        return False
    
    try:
        from openai import OpenAI
        print("  ✅ OpenAI")
    except ImportError as e:
        print(f"  ❌ OpenAI: {e}")
        return False
    
    try:
        import ffmpeg
        print("  ✅ FFmpeg-python")
    except ImportError as e:
        print(f"  ❌ FFmpeg-python: {e}")
        return False
        
    return True

def test_environment():
    """Test environment variables."""
    print("\n🔧 Testing environment...")
    
    # Check .env file
    env_path = Path('.env')
    if env_path.exists():
        print("  ✅ .env file found")
        
        # Load and check variables
        from dotenv import load_dotenv
        load_dotenv()
        
        openai_key = os.getenv('OPENAI_API_KEY')
        if openai_key and openai_key != 'your_openai_api_key_here':
            print("  ✅ OPENAI_API_KEY configured")
        else:
            print("  ❌ OPENAI_API_KEY not configured")
            return False
            
        hf_token = os.getenv('HF_TOKEN')
        if hf_token:
            print("  ✅ HF_TOKEN configured")
        else:
            print("  ⚠️  HF_TOKEN not configured (speaker diarization will use fallback)")
            
    else:
        print("  ❌ .env file not found")
        return False
        
    return True

def test_directories():
    """Test required directories."""
    print("\n📁 Testing directories...")
    
    # Create directories if they don't exist
    for dir_name in ['uploads', 'results']:
        dir_path = Path(dir_name)
        if not dir_path.exists():
            dir_path.mkdir()
            print(f"  ✅ Created {dir_name} directory")
        else:
            print(f"  ✅ {dir_name} directory exists")
    
    return True

def test_flask_app():
    """Test Flask app startup."""
    print("\n🌐 Testing Flask app...")
    
    # Import app
    try:
        import app
        print("  ✅ App module imported successfully")
    except Exception as e:
        print(f"  ❌ App import failed: {e}")
        return False
    
    # Test health endpoint
    def run_server():
        app.app.run(debug=False, port=5001, threaded=True)
    
    # Start server in background
    server_thread = threading.Thread(target=run_server, daemon=True)
    server_thread.start()
    
    # Wait for server to start
    time.sleep(3)
    
    try:
        response = requests.get('http://localhost:5001/api/health', timeout=5)
        if response.status_code == 200:
            print("  ✅ Health endpoint working")
            return True
        else:
            print(f"  ❌ Health endpoint failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"  ❌ Server test failed: {e}")
        return False

def test_sample_file():
    """Test if sample files exist."""
    print("\n🎵 Testing sample files...")
    
    test_files_dir = Path('test_files')
    if test_files_dir.exists():
        audio_files = list(test_files_dir.glob('*.mp3')) + list(test_files_dir.glob('*.mp4'))
        if audio_files:
            print(f"  ✅ Found {len(audio_files)} sample audio files")
            for file in audio_files[:3]:  # Show first 3 files
                print(f"    - {file.name}")
            return True
        else:
            print("  ⚠️  No audio files found in test_files directory")
            return False
    else:
        print("  ⚠️  test_files directory not found")
        return False

def main():
    """Run all tests."""
    print("🚀 Testing Flask + React Transcription App Setup")
    print("=" * 50)
    
    tests = [
        ("Import Dependencies", test_imports),
        ("Environment Variables", test_environment),
        ("Directory Structure", test_directories),
        ("Sample Files", test_sample_file),
        ("Flask Application", test_flask_app),
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"  ❌ {test_name} failed with exception: {e}")
            results.append((test_name, False))
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 Test Results Summary:")
    print("=" * 50)
    
    passed = 0
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status:8} {test_name}")
        if result:
            passed += 1
    
    print(f"\nResults: {passed}/{len(results)} tests passed")
    
    if passed == len(results):
        print("\n🎉 All tests passed! Your setup is ready.")
        print("\nTo start the application:")
        print("1. Terminal 1: python3 app.py")
        print("2. Terminal 2: cd frontend && npm start")
        print("3. Open: http://localhost:3000")
    else:
        print(f"\n⚠️  {len(results) - passed} test(s) failed. Please fix the issues above.")
        
    return passed == len(results)

if __name__ == "__main__":
    sys.exit(0 if main() else 1)