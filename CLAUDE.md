# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a simple MP4 to transcript backend test that uses OpenAI's Whisper API to transcribe video files. The project consists of a single Python script that extracts audio from MP4 files and sends it to the Whisper API for transcription.

## Development Commands

### Setup and Installation
```bash
# Install dependencies
pip install -r requirements.txt

# Set up environment variables
cp .env .env.local  # Then edit .env.local with your actual API key
```

### Running the Application
```bash
# Run the main script
python main.py

# Test with a specific MP4 file (modify mp4_file variable in main.py)
python main.py
```

## Architecture

### Core Components
- `main.py`: Single entry point containing all functionality
- `process_mp4()`: Main processing function that orchestrates the transcription workflow
- `extract_audio_from_mp4()`: Uses ffmpeg to convert MP4 to WAV format
- `transcribe_audio()`: Sends audio to OpenAI Whisper API
- `save_transcript()`: Saves transcript to text file

### Data Flow
1. MP4 file validation (existence, size, permissions)
2. Audio extraction using ffmpeg (converts to 16kHz mono WAV)
3. Temporary file creation for audio processing
4. API call to OpenAI Whisper
5. Transcript saving and console output
6. Cleanup of temporary files

### Configuration
- Environment variables loaded from `.env` file
- OpenAI API key required in `OPENAI_API_KEY` environment variable
- File size limit: 25MB (Whisper API constraint)
- Audio format: 16kHz mono WAV for optimal processing

### Error Handling
The script includes comprehensive error handling for:
- Missing or unreadable files
- File size violations
- FFmpeg processing errors
- OpenAI API errors
- File system operations

### Dependencies
- `openai`: For Whisper API integration
- `ffmpeg-python`: For audio extraction from MP4
- `python-dotenv`: For environment variable management