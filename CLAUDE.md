# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

A full-stack web application for audio/video transcription with speaker diarization, multi-language translation, and AI-generated summaries.

- **Backend**: Flask REST API (`app.py`) — handles file uploads, background job processing, and result delivery
- **Frontend**: React TypeScript SPA (`frontend/`) — drag-and-drop upload, real-time progress tracking, tabbed results display
- **CLI script**: `main.py` — standalone script for direct file processing without the web interface

## Development Commands

### Backend

```bash
# Install Python dependencies
pip install -r backend-requirements.txt

# Create environment file
cp .env.example .env  # then add OPENAI_API_KEY and optionally HF_TOKEN

# Run the Flask API (port 5000)
python app.py
```

### Frontend

```bash
cd frontend

# Install Node dependencies
npm install

# Start development server (port 3000)
npm start

# Build for production
npm run build
```

### Run both with one command

```bash
./start-app.sh
```

### CLI usage (no web server required)

```bash
# Edit the audio_file path in main() then run:
python main.py
```

## Architecture

### Backend (`app.py`)

- `POST /api/upload` — saves file, initialises a job dict, spawns a `threading.Thread`
- `GET  /api/status/<job_id>` — returns progress (0–100) and status string
- `GET  /api/results/<job_id>` — returns transcript, translations, summary JSON
- `GET  /api/download/<job_id>/<type>` — streams a result file

**Background job pipeline** (in `process_transcription_job`):
1. Validate file size
2. Extract audio with ffmpeg → 16 kHz mono WAV (`extract_audio_from_mp4`)
3. Speaker diarization via PyAnnote or librosa fallback (`perform_speaker_diarization`)
4. Transcribe with Whisper API, verbose_json + word timestamps (`transcribe_audio`)
5. Align speaker segments to word timestamps (`align_speakers_with_transcript`)
6. Translate each requested language with GPT-4 (`translate_text`)
7. Generate structured summary with GPT-4 (`generate_summary`)

Job state is stored in the module-level `jobs` dict — suitable for single-process local use. For multi-process or production deployments, replace with Redis or a database.

### Frontend (`frontend/src/`)

- `App.tsx` — root component; owns `currentJob` and `results` state, coordinates view transitions
- `components/FileUpload.tsx` — drag-and-drop with MIME/size validation; POSTs multipart form to backend
- `components/LanguageSelector.tsx` — pre-configured language chips + free-text custom language input
- `components/ProgressTracker.tsx` — polls `/api/status` every 2 s; transitions to results on completion
- `components/ResultsDisplay.tsx` — tabbed view (Transcript / per-language / Summary), speaker stats, download buttons

## Configuration

Environment variables (`.env` file in project root):

| Variable | Required | Description |
|---|---|---|
| `OPENAI_API_KEY` | Yes | Used for Whisper transcription and GPT-4 calls |
| `HF_TOKEN` | No | HuggingFace token for PyAnnote diarization; falls back to librosa if absent |

## Key Constraints

- Whisper API file size limit: **25 MB**
- Frontend API base URL is hardcoded to `http://localhost:5000` in `FileUpload.tsx` and `ProgressTracker.tsx`
- `numpy<2.0` pin in `backend-requirements.txt` is required for librosa compatibility

## Dependencies

### Python (backend-requirements.txt)
- `Flask`, `Flask-CORS`, `Werkzeug` — web framework
- `openai` — Whisper + GPT-4
- `ffmpeg-python` — audio extraction
- `pyannote.audio`, `torch` — neural speaker diarization
- `librosa`, `scikit-learn`, `numpy` — fallback speaker detection
- `python-dotenv` — env var loading

### Node (frontend/package.json)
- `react`, `react-dom` (v19), `typescript`
- `react-scripts` (Create React App)
- `axios` (available but the app uses the native Fetch API)
