# Audio/Video Transcription Service

[![Python](https://img.shields.io/badge/Python-3.8%2B-3776AB?style=flat&logo=python&logoColor=white)](https://python.org)
[![Flask](https://img.shields.io/badge/Flask-2.3-000000?style=flat&logo=flask&logoColor=white)](https://flask.palletsprojects.com)
[![React](https://img.shields.io/badge/React-19-61DAFB?style=flat&logo=react&logoColor=black)](https://react.dev)
[![TypeScript](https://img.shields.io/badge/TypeScript-4.9-3178C6?style=flat&logo=typescript&logoColor=white)](https://typescriptlang.org)
[![OpenAI](https://img.shields.io/badge/OpenAI-Whisper%20%2B%20GPT--4-412991?style=flat&logo=openai&logoColor=white)](https://openai.com)

A full-stack web application that transcribes audio and video files with automatic speaker identification, multi-language translation, and AI-generated summaries — all running locally on your machine.

---

## Features

- **Multi-format support** — Accepts MP4, MP3, WAV, M4A, AAC, FLAC, OGG, WebM, AVI, MOV
- **Speaker diarization** — Automatically identifies and labels distinct speakers using PyAnnote.audio, with a librosa/k-means fallback
- **AI transcription** — High-accuracy transcription via OpenAI Whisper API with word-level timestamps
- **Multi-language translation** — Translate transcripts into 50+ languages (predefined or custom input) using GPT-4, with speaker labels preserved
- **Structured summaries** — GPT-4 generates an executive summary, key points, decisions made, and action items
- **Real-time progress tracking** — React frontend polls job status and renders a live progress bar through each processing stage
- **Downloadable results** — Export the transcript, any translation, and the summary as individual text/markdown files

---

## Architecture

```
┌─────────────────────────┐        ┌──────────────────────────────────┐
│   React Frontend        │        │   Flask Backend                  │
│   (TypeScript)          │        │                                  │
│                         │  HTTP  │  POST /api/upload                │
│  FileUpload       ──────┼───────►│    └─ saves file                 │
│  LanguageSelector       │        │    └─ spawns background thread   │
│  ProgressTracker  ◄─────┼────────│                                  │
│  ResultsDisplay         │  poll  │  GET  /api/status/<job_id>       │
│                         │        │  GET  /api/results/<job_id>      │
│  localhost:3000         │        │  GET  /api/download/<job_id>/... │
└─────────────────────────┘        │                                  │
                                   │  Background Thread               │
                                   │    1. Validate & extract audio   │
                                   │       (FFmpeg → 16 kHz WAV)      │
                                   │    2. Speaker diarization        │
                                   │       (PyAnnote or librosa)      │
                                   │    3. Transcribe (Whisper API)   │
                                   │    4. Align speakers + words     │
                                   │    5. Translate (GPT-4)          │
                                   │    6. Summarise (GPT-4)          │
                                   │                                  │
                                   │  localhost:5000                  │
                                   └──────────────────────────────────┘
```

Job state is held in-process (Python dict). The React frontend polls `/api/status` every 2 seconds and transitions from the upload view → progress view → results view automatically.

---

## Supported Formats

| Type  | Extensions                                        |
|-------|---------------------------------------------------|
| Video | MP4, AVI, MOV, WebM                               |
| Audio | MP3, WAV, M4A, AAC, FLAC, OGG                     |

Maximum file size: **25 MB** (OpenAI Whisper API constraint).

---

## Prerequisites

| Dependency | Version | Install |
|---|---|---|
| Python | 3.8+ | [python.org](https://python.org) |
| Node.js | 16+ | [nodejs.org](https://nodejs.org) |
| FFmpeg | any recent | see below |

**Install FFmpeg:**

```bash
# macOS
brew install ffmpeg

# Ubuntu / Debian
sudo apt install ffmpeg

# Windows
# Download from https://ffmpeg.org/download.html and add to PATH
```

---

## Setup

### 1. Clone the repository

```bash
git clone <repo-url>
cd audio-video-transcription
```

### 2. Backend

```bash
# Install Python dependencies
pip install -r backend-requirements.txt

# Create a .env file with your API keys
cat > .env << 'EOF'
OPENAI_API_KEY=your_openai_api_key_here
HF_TOKEN=your_huggingface_token_here   # Optional — enables PyAnnote diarization
EOF
```

> **HF_TOKEN** is optional. Without it the app falls back to a librosa/k-means speaker detection approach. To use PyAnnote, create a free token at [huggingface.co](https://huggingface.co/settings/tokens) and accept the [pyannote/speaker-diarization-3.1](https://huggingface.co/pyannote/speaker-diarization-3.1) model terms.

### 3. Frontend

```bash
cd frontend
npm install
```

---

## Running the Application

### Option A — one command (recommended)

```bash
./start-app.sh
```

This script checks dependencies, starts the Flask backend in the background, then launches the React dev server. Press `Ctrl+C` to stop both.

### Option B — two terminals

**Terminal 1 — backend:**

```bash
python app.py
# Listening on http://localhost:5000
```

**Terminal 2 — frontend:**

```bash
cd frontend
npm start
# Opens http://localhost:3000
```

---

## Usage

1. Open **http://localhost:3000** in your browser.
2. **(Optional)** Select one or more translation languages from the dropdown — choose from 12 pre-configured languages with flags, or type any language name / ISO code (e.g. `Swedish`, `th`, `Urdu`).
3. **(Optional)** Toggle the summary switch to generate a structured meeting summary.
4. Drag and drop your audio/video file onto the upload zone, or click to browse.
5. Watch real-time progress as the file moves through extraction → diarization → transcription → translation → summary.
6. View results in a tabbed interface: **Transcript**, one tab per language, and **Summary**.
7. Download any individual result or all files at once.

---

## API Reference

Base URL: `http://localhost:5000`

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/health` | Health check |
| `POST` | `/api/upload` | Upload a file and start a transcription job |
| `GET` | `/api/status/<job_id>` | Poll job progress (`0–100`) and status |
| `GET` | `/api/results/<job_id>` | Retrieve completed results (transcript, translations, summary) |
| `GET` | `/api/download/<job_id>/<type>` | Stream a result file (`original`, `summary`, or a language key) |

**Upload form fields:**

| Field | Type | Description |
|-------|------|-------------|
| `file` | `File` | The audio/video file (multipart) |
| `languages` | `string[]` | Language codes or names — repeat for multiple |
| `include_summary` | `"true"` / `"false"` | Whether to generate a summary |

---

## Language Support

**12 pre-configured languages** (shown with flags in the UI):

Spanish, Chinese, French, German, Italian, Portuguese, Russian, Japanese, Korean, Arabic, Hindi, Dutch

**Custom input** — type any of the following and the app resolves it automatically:

- Full name: `Swedish`, `Thai`, `Vietnamese`, `Swahili`
- ISO 639-1 code: `sv`, `th`, `vi`, `sw`
- Mixed case: `GERMAN`, `hindi`, `Ko`

Translations are performed by GPT-4 with a prompt that explicitly preserves speaker labels and dialogue structure.

---

## Tech Stack

### Backend

| Library | Purpose |
|---------|---------|
| Flask + Flask-CORS | REST API and CORS handling |
| OpenAI (`whisper-1`) | Speech-to-text with word timestamps |
| OpenAI (`gpt-4`) | Translation and structured summarisation |
| PyAnnote.audio | Neural speaker diarization |
| librosa + scikit-learn | Fallback speaker detection via MFCC + k-means |
| ffmpeg-python | Audio extraction and resampling to 16 kHz mono WAV |
| python-dotenv | Environment variable management |
| Python `threading` | Non-blocking background job processing |

### Frontend

| Library | Purpose |
|---------|---------|
| React 19 | Component-based UI |
| TypeScript | End-to-end type safety |
| Fetch API | HTTP communication with the backend |
| CSS3 | Animations, responsive layout, drag-and-drop states |

---

## Project Structure

```
audio-video-transcription/
├── app.py                      # Flask API — routes and background processing
├── main.py                     # CLI script for direct file processing
├── backend-requirements.txt    # Python dependencies (pinned)
├── requirements.txt            # Minimal CLI requirements
├── start-app.sh                # Convenience startup script
├── .env                        # API keys (git-ignored)
├── uploads/                    # Uploaded files (auto-created, git-ignored)
├── results/                    # Generated results (auto-created, git-ignored)
└── frontend/
    ├── public/
    └── src/
        ├── App.tsx             # Root component + shared TypeScript interfaces
        ├── App.css
        └── components/
            ├── FileUpload.tsx       # Drag-and-drop upload with validation
            ├── LanguageSelector.tsx # Language + summary toggle controls
            ├── ProgressTracker.tsx  # Polling, progress bar, step visualiser
            └── ResultsDisplay.tsx   # Tabbed results, speaker stats, downloads
```

---

## Troubleshooting

**FFmpeg not found**
Install FFmpeg and ensure it is on your `PATH`. Verify with `ffmpeg -version`.

**OpenAI API errors**
Check that `OPENAI_API_KEY` is set in `.env` and that your account has access to `whisper-1` and `gpt-4`.

**PyAnnote access denied**
Either omit `HF_TOKEN` (the app will use the librosa fallback) or accept the model terms at [huggingface.co/pyannote/speaker-diarization-3.1](https://huggingface.co/pyannote/speaker-diarization-3.1).

**File too large**
The Whisper API enforces a 25 MB limit. Compress or trim the file before uploading.

**CORS errors in the browser**
Ensure the Flask backend is running on port 5000. The frontend hardcodes `http://localhost:5000` as the API base URL.

**Port conflicts**
- Backend: edit the `app.run(port=...)` call in `app.py`.
- Frontend: set the `PORT` environment variable before running `npm start`.

---

## Local-Only Operation

This application is designed to run entirely on your local machine. Uploaded files and generated results are written to the `uploads/` and `results/` directories and never sent to any third-party service other than the OpenAI API calls you explicitly trigger.
