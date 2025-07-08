# 🎬 Audio/Video Transcription Web Application

A full-stack web application that converts audio/video files into transcripts with speaker identification, translations, and AI-generated summaries.

## Features

- 🎵 **Multi-format Support**: MP4, MP3, WAV, M4A, AAC, FLAC, OGG, WebM, AVI, MOV
- 👥 **Speaker Diarization**: Automatic speaker identification and labeling
- 🎤 **AI Transcription**: OpenAI Whisper API for accurate transcription
- 🌍 **Multi-language Translation**: Any language translations using GPT-4 (50+ predefined languages + custom input)
- 📋 **Smart Summaries**: Structured summaries with action items and key points
- 📱 **Modern UI**: Responsive React frontend with real-time progress tracking
- ⬇️ **File Downloads**: Download all results as text/markdown files

## Architecture

- **Backend**: Flask API with background job processing
- **Frontend**: React TypeScript application
- **AI Services**: OpenAI Whisper API + GPT-4
- **Speaker Detection**: PyAnnote.audio + Librosa fallback

## Setup Instructions

### Prerequisites

1. **Python 3.8+** installed
2. **Node.js 16+** and npm installed
3. **FFmpeg** installed:
   ```bash
   # macOS
   brew install ffmpeg
   
   # Ubuntu/Debian
   sudo apt install ffmpeg
   
   # Windows - download from https://ffmpeg.org/download.html
   ```

### Backend Setup

1. **Install Python dependencies**:
   ```bash
   pip install -r backend-requirements.txt
   ```

2. **Configure environment variables**:
   ```bash
   # Copy your existing .env file or create a new one
   # Make sure it contains:
   OPENAI_API_KEY=your_openai_api_key_here
   HF_TOKEN=your_huggingface_token_here  # Optional for PyAnnote
   ```

3. **Create required directories**:
   ```bash
   mkdir uploads results
   ```

### Frontend Setup

1. **Navigate to frontend directory**:
   ```bash
   cd frontend
   ```

2. **Install npm dependencies**:
   ```bash
   npm install
   ```

### Running the Application

#### Start Backend (Terminal 1)
```bash
# From project root directory
python app.py
```
Backend will run on: `http://localhost:5000`

#### Start Frontend (Terminal 2)
```bash
# From frontend directory
cd frontend
npm start
```
Frontend will run on: `http://localhost:3000`

### Usage

1. **Open your browser** to `http://localhost:3000`
2. **Select translation languages** (optional): Choose from 12 popular languages or add any custom language
3. **Choose summary option** (optional): Generate structured summary with action items
4. **Upload your file**: Drag & drop or click to select audio/video file (max 25MB)
5. **Monitor progress**: Real-time progress tracking with status updates
6. **View results**: Tabbed interface showing transcript, translations, and summary
7. **Download files**: Individual downloads or all files at once

## API Endpoints

### Backend API (`http://localhost:5000`)

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/health` | GET | Health check |
| `/api/upload` | POST | Upload file and start processing |
| `/api/status/<job_id>` | GET | Get job status and progress |
| `/api/results/<job_id>` | GET | Get processing results |
| `/api/download/<job_id>/<content_type>` | GET | Download specific result file |

### Upload Parameters

- `file`: Audio/video file (multipart/form-data)
- `languages`: Array of language codes or names (e.g., `spanish`, `french`, `thai`, `sv`, `korean`)
- `include_summary`: Boolean string (`true`/`false`)

## Language Support

### Popular Languages (Pre-configured with Flags)
- Spanish (🇪🇸), Chinese (🇨🇳), French (🇫🇷), German (🇩🇪)
- Italian (🇮🇹), Portuguese (🇵🇹), Russian (🇷🇺), Japanese (🇯🇵)
- Korean (🇰🇷), Arabic (🇸🇦), Hindi (🇮🇳), Dutch (🇳🇱)

### Custom Language Input
- **Any Language**: Type any language name (e.g., "Swedish", "Thai", "Urdu")
- **Language Codes**: Use ISO codes (e.g., "sv", "th", "ur") 
- **Case Insensitive**: Works with any capitalization
- **Dynamic Tabs**: Automatically creates tabs for selected languages
- **Smart Downloads**: Generates appropriate file names for any language

### Language Examples
```
Popular: spanish, french, german, japanese, korean
Codes: es, fr, de, ja, ko, th, vi, sv, no
Custom: Swedish, Thai, Vietnamese, Norwegian, Swahili
Mixed: es, French, thai, GERMAN, hindi
```

### Translation Quality
- Powered by OpenAI GPT-4 for high-quality translations
- Preserves speaker labels and dialogue structure
- Maintains original meaning, tone, and style
- Handles technical terms and proper nouns appropriately

## File Structure

```
project-10/
├── app.py                     # Flask API backend
├── main.py                    # Original CLI script
├── backend-requirements.txt   # Python dependencies
├── .env                      # Environment variables
├── uploads/                  # Uploaded files (auto-created)
├── results/                  # Generated results (auto-created)
├── frontend/                 # React application
│   ├── src/
│   │   ├── App.tsx           # Main application component
│   │   ├── App.css           # Global styles
│   │   └── components/       # React components
│   │       ├── FileUpload.tsx
│   │       ├── LanguageSelector.tsx
│   │       ├── ProgressTracker.tsx
│   │       ├── ResultsDisplay.tsx
│   │       └── *.css         # Component styles
│   ├── package.json
│   └── public/
└── test_files/               # Sample audio files
```

## Components Overview

### FileUpload Component
- Drag & drop file upload
- File type and size validation
- Upload progress indication
- Error handling

### LanguageSelector Component
- Language selection for translations
- Summary generation toggle
- Selection summary display

### ProgressTracker Component
- Real-time progress updates
- Processing step visualization
- Elapsed time tracking
- Status polling

### ResultsDisplay Component
- Tabbed results interface
- Speaker statistics
- Individual file downloads
- Formatted transcript display

## Technology Stack

### Backend
- **Flask**: Web framework
- **OpenAI**: Whisper API + GPT-4
- **PyAnnote.audio**: Speaker diarization
- **Librosa**: Audio processing fallback
- **FFmpeg**: Audio extraction
- **Threading**: Background job processing

### Frontend
- **React**: UI framework
- **TypeScript**: Type safety
- **CSS3**: Modern styling with animations
- **Fetch API**: HTTP requests

## Error Handling

- File validation (type, size)
- API error responses
- Network error handling
- Processing failure recovery
- User-friendly error messages

## Performance Features

- Background processing for long jobs
- Real-time progress updates
- Efficient file streaming
- Temporary file cleanup
- Memory-optimized audio processing

## Local-Only Operation

This application is designed to run entirely locally:
- No external hosting required
- All data stays on your machine
- Files processed locally
- Results stored locally

## Troubleshooting

### Common Issues

1. **FFmpeg not found**: Install FFmpeg using system package manager
2. **OpenAI API errors**: Check API key in .env file
3. **PyAnnote access denied**: Verify HuggingFace token or use fallback
4. **File too large**: Maximum file size is 25MB (Whisper API limit)
5. **CORS errors**: Ensure Flask backend is running on port 5000

### Port Conflicts

If ports 3000 or 5000 are in use:
- Frontend: Set `PORT=3001` environment variable
- Backend: Modify `app.run(port=5001)` in app.py and update frontend fetch URLs

### Performance Tips

- Use MP3 or WAV files for faster processing
- Smaller files process faster
- Speaker diarization adds processing time
- Translations require additional API calls

## Support

For issues or questions:
1. Check the troubleshooting section
2. Verify all dependencies are installed
3. Ensure environment variables are set correctly
4. Check console logs for detailed error messages