#!/usr/bin/env python3
"""
Flask API Backend for MP4 to Transcript Application
Converts main.py logic into REST API endpoints for React frontend.
"""

import os
import uuid
import time
import tempfile
import threading
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv
import ffmpeg
from openai import OpenAI
from pyannote.audio import Pipeline
import torch

from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
from werkzeug.utils import secure_filename
from werkzeug.exceptions import RequestEntityTooLarge

# Load environment variables
load_dotenv()

# Initialize Flask app
app = Flask(__name__)
CORS(app)  # Enable CORS for React frontend

# Configuration
app.config['MAX_CONTENT_LENGTH'] = 25 * 1024 * 1024  # 25MB limit
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['RESULTS_FOLDER'] = 'results'

# Constants
MAX_FILE_SIZE_MB = 25
WHISPER_SAMPLE_RATE = 16000
ALLOWED_EXTENSIONS = {
    'mp4', 'mp3', 'wav', 'm4a', 'aac', 'flac', 'ogg', 'webm', 'avi', 'mov'
}

# Create directories
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(app.config['RESULTS_FOLDER'], exist_ok=True)

# Global job storage (in production, use Redis or database)
jobs = {}

# Import functions from main.py logic
def check_file_size(file_path):
    """Check if file size is within Whisper API limits."""
    file_size_mb = os.path.getsize(file_path) / (1024 * 1024)
    if file_size_mb > MAX_FILE_SIZE_MB:
        return False, f"File size ({file_size_mb:.1f}MB) exceeds {MAX_FILE_SIZE_MB}MB limit"
    return True, f"File size: {file_size_mb:.1f}MB"

def extract_audio_from_mp4(mp4_path, output_path):
    """Extract audio from video/audio file and convert to WAV format for Whisper."""
    try:
        (
            ffmpeg
            .input(mp4_path)
            .output(
                output_path,
                acodec='pcm_s16le',
                ac=1,
                ar=WHISPER_SAMPLE_RATE
            )
            .overwrite_output()
            .run(quiet=True, capture_stdout=True)
        )
        return True, "Audio extracted successfully"
        
    except ffmpeg.Error as e:
        return False, f"FFmpeg error: {e.stderr.decode() if e.stderr else str(e)}"
    except Exception as e:
        return False, f"Audio extraction error: {str(e)}"

def perform_speaker_diarization(audio_path):
    """Perform speaker diarization to identify different speakers."""
    try:
        # Try pyannote first (if available)
        try:
            from pyannote.audio import Pipeline
            
            hf_token = os.getenv('HF_TOKEN')
            
            if hf_token:
                models_to_try = [
                    "pyannote/speaker-diarization-3.1",
                    "pyannote/speaker-diarization"
                ]
                
                for model_name in models_to_try:
                    try:
                        pipeline = Pipeline.from_pretrained(model_name, use_auth_token=hf_token)
                        diarization = pipeline(audio_path)
                        
                        speaker_segments = []
                        for turn, _, speaker in diarization.itertracks(yield_label=True):
                            speaker_segments.append((turn.start, turn.end, speaker))
                        
                        return speaker_segments
                        
                    except Exception:
                        continue
        
        except ImportError:
            pass
        
        # Fallback to simple speaker detection
        return simple_speaker_detection_fallback(audio_path)
        
    except Exception as e:
        return None

def simple_speaker_detection_fallback(audio_path, num_speakers=2):
    """Simple speaker detection fallback using librosa"""
    try:
        import librosa
        import numpy as np
        from sklearn.cluster import KMeans
        
        # Load audio
        y, sr = librosa.load(audio_path, sr=16000)
        
        # Extract features
        mfccs = librosa.feature.mfcc(y=y, sr=sr, n_mfcc=13)
        spectral_centroids = librosa.feature.spectral_centroid(y=y, sr=sr)[0]
        chroma = librosa.feature.chroma_stft(y=y, sr=sr)
        
        # Combine features
        features = np.vstack([
            mfccs,
            spectral_centroids.reshape(1, -1),
            chroma
        ])
        
        # Window the features
        window_size = 50
        hop_size = 25
        
        windowed_features = []
        times = []
        
        for i in range(0, features.shape[1] - window_size, hop_size):
            window = features[:, i:i+window_size]
            windowed_features.append(window.mean(axis=1))
            times.append(i * 512 / sr)
        
        windowed_features = np.array(windowed_features)
        
        # Cluster features
        if len(windowed_features) < num_speakers:
            num_speakers = 1
        
        if num_speakers == 1:
            labels = np.zeros(len(windowed_features))
        else:
            kmeans = KMeans(n_clusters=num_speakers, random_state=42, n_init=10)
            labels = kmeans.fit_predict(windowed_features)
        
        # Create speaker segments
        segments = []
        current_speaker = labels[0]
        segment_start = times[0]
        
        for i in range(1, len(labels)):
            if labels[i] != current_speaker:
                segment_end = times[i]
                segments.append((segment_start, segment_end, f"SPEAKER_{current_speaker:02d}"))
                current_speaker = labels[i]
                segment_start = times[i]
        
        # Add final segment
        if len(times) > 0:
            segments.append((segment_start, times[-1], f"SPEAKER_{current_speaker:02d}"))
        
        return segments
        
    except Exception as e:
        return None

def transcribe_audio(audio_path, client):
    """Send audio file to OpenAI Whisper API for transcription with timestamps."""
    try:
        with open(audio_path, "rb") as audio_file:
            transcript = client.audio.transcriptions.create(
                model="whisper-1",
                file=audio_file,
                response_format="verbose_json",
                timestamp_granularities=["word"]
            )
        
        return transcript
        
    except Exception as e:
        return None

def align_speakers_with_transcript(transcript_data, speaker_segments):
    """Align speaker segments with transcript segments to create speaker-labeled transcript."""
    try:
        if not speaker_segments:
            return transcript_data.text, [{"speaker": "Speaker 1", "text": transcript_data.text, "start": 0, "end": transcript_data.words[-1].end if transcript_data.words else 0}]
        
        speaker_transcript_segments = []
        current_segment = {"speaker": None, "text": "", "start": None, "end": None}
        
        for word_info in transcript_data.words:
            word_start = word_info.start
            word_end = word_info.end
            word_text = word_info.word
            
            # Clean up word text - ensure proper spacing
            if word_text and not word_text.startswith(' '):
                word_text = ' ' + word_text
            
            # Find which speaker is speaking at this time
            speaker_at_time = None
            for seg_start, seg_end, speaker_label in speaker_segments:
                if seg_start <= word_start <= seg_end:
                    speaker_at_time = speaker_label
                    break
            
            if speaker_at_time is None:
                speaker_at_time = "Unknown"
            
            # Convert speaker label to more readable format
            speaker_name = f"Speaker {speaker_at_time.split('_')[-1]}" if "_" in speaker_at_time else speaker_at_time
            
            # If this is a new speaker, save the current segment and start a new one
            if current_segment["speaker"] != speaker_name:
                if current_segment["speaker"] is not None:
                    speaker_transcript_segments.append(current_segment)
                
                current_segment = {
                    "speaker": speaker_name,
                    "text": word_text.strip(),
                    "start": word_start,
                    "end": word_end
                }
            else:
                current_segment["text"] += word_text
                current_segment["end"] = word_end
        
        # Add the last segment
        if current_segment["speaker"] is not None:
            speaker_transcript_segments.append(current_segment)
        
        # Create formatted transcript
        formatted_transcript = ""
        for segment in speaker_transcript_segments:
            formatted_transcript += f"{segment['speaker']}: {segment['text'].strip()}\n\n"
        
        return formatted_transcript.strip(), speaker_transcript_segments
        
    except Exception as e:
        return transcript_data.text, [{"speaker": "Speaker 1", "text": transcript_data.text, "start": 0, "end": 0}]

def translate_text(text, target_language, client):
    """Translate text using OpenAI GPT-4 to any specified language."""
    try:
        # Extended language map with common language codes and names
        language_map = {
            # Predefined languages
            'spanish': 'Spanish',
            'chinese': 'Simplified Chinese',
            'es': 'Spanish',
            'zh': 'Simplified Chinese',
            'zh-cn': 'Simplified Chinese',
            'zh-tw': 'Traditional Chinese',
            
            # Common language codes
            'en': 'English',
            'fr': 'French',
            'de': 'German',
            'it': 'Italian',
            'pt': 'Portuguese',
            'ru': 'Russian',
            'ja': 'Japanese',
            'ko': 'Korean',
            'ar': 'Arabic',
            'hi': 'Hindi',
            'th': 'Thai',
            'vi': 'Vietnamese',
            'nl': 'Dutch',
            'sv': 'Swedish',
            'no': 'Norwegian',
            'da': 'Danish',
            'fi': 'Finnish',
            'pl': 'Polish',
            'tr': 'Turkish',
            'he': 'Hebrew',
            'cs': 'Czech',
            'hu': 'Hungarian',
            'ro': 'Romanian',
            'bg': 'Bulgarian',
            'hr': 'Croatian',
            'sk': 'Slovak',
            'sl': 'Slovenian',
            'et': 'Estonian',
            'lv': 'Latvian',
            'lt': 'Lithuanian',
            'uk': 'Ukrainian',
            'el': 'Greek',
            'id': 'Indonesian',
            'ms': 'Malay',
            'tl': 'Filipino',
            'bn': 'Bengali',
            'ta': 'Tamil',
            'te': 'Telugu',
            'mr': 'Marathi',
            'gu': 'Gujarati',
            'kn': 'Kannada',
            'ml': 'Malayalam',
            'pa': 'Punjabi',
            'ur': 'Urdu',
            'fa': 'Persian',
            'sw': 'Swahili',
            'am': 'Amharic',
            'zu': 'Zulu',
            'af': 'Afrikaans',
            
            # Full language names (case insensitive)
            'french': 'French',
            'german': 'German',
            'italian': 'Italian',
            'portuguese': 'Portuguese',
            'russian': 'Russian',
            'japanese': 'Japanese',
            'korean': 'Korean',
            'arabic': 'Arabic',
            'hindi': 'Hindi',
            'thai': 'Thai',
            'vietnamese': 'Vietnamese',
            'dutch': 'Dutch',
            'swedish': 'Swedish',
            'norwegian': 'Norwegian',
            'danish': 'Danish',
            'finnish': 'Finnish',
            'polish': 'Polish',
            'turkish': 'Turkish',
            'hebrew': 'Hebrew',
            'czech': 'Czech',
            'hungarian': 'Hungarian',
            'romanian': 'Romanian',
            'bulgarian': 'Bulgarian',
            'croatian': 'Croatian',
            'slovak': 'Slovak',
            'slovenian': 'Slovenian',
            'estonian': 'Estonian',
            'latvian': 'Latvian',
            'lithuanian': 'Lithuanian',
            'ukrainian': 'Ukrainian',
            'greek': 'Greek',
            'indonesian': 'Indonesian',
            'malay': 'Malay',
            'filipino': 'Filipino',
            'bengali': 'Bengali',
            'tamil': 'Tamil',
            'telugu': 'Telugu',
            'marathi': 'Marathi',
            'gujarati': 'Gujarati',
            'kannada': 'Kannada',
            'malayalam': 'Malayalam',
            'punjabi': 'Punjabi',
            'urdu': 'Urdu',
            'persian': 'Persian',
            'swahili': 'Swahili',
            'amharic': 'Amharic',
            'zulu': 'Zulu',
            'afrikaans': 'Afrikaans'
        }
        
        # Get the proper language name, defaulting to the input if not found
        target_lang = language_map.get(target_language.lower(), target_language.title())
        
        # Enhanced system prompt for better translation quality
        system_prompt = f"""You are a professional translator with expertise in multiple languages. 
        
        Translate the following text to {target_lang}. 

        Requirements:
        1. Maintain the original meaning, tone, and style
        2. Preserve speaker labels (e.g., "Speaker 1:", "Speaker 00:") in their original format
        3. Keep the dialogue structure and formatting intact
        4. Ensure natural, fluent translation that sounds native to {target_lang}
        5. If technical terms or proper nouns appear, translate appropriately for the target language
        6. Only respond with the translated text, no additional comments or explanations

        If the target language is not a real language or cannot be translated to, respond with "TRANSLATION_ERROR: Unsupported language"."""
        
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {
                    "role": "system",
                    "content": system_prompt
                },
                {
                    "role": "user",
                    "content": text
                }
            ],
            temperature=0.1
        )
        
        result = response.choices[0].message.content.strip()
        
        # Check if translation failed
        if result.startswith("TRANSLATION_ERROR:"):
            print(f"Translation error for {target_language}: {result}")
            return None
            
        return result
        
    except Exception as e:
        print(f"Translation error for {target_language}: {str(e)}")
        return None

def generate_summary(transcript, client):
    """Generate a structured summary with action items using GPT-4."""
    try:
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {
                    "role": "system",
                    "content": """You are an expert meeting summarizer. Create a structured summary of the following transcript with these sections:

## EXECUTIVE SUMMARY
Brief overview of the main topics discussed (2-3 sentences)

## SPEAKER OVERVIEW
• Identify the speakers and their main contributions
• Note speaking time distribution if apparent
• Highlight key insights from each speaker

## KEY POINTS
• List the main discussion points and decisions made
• Use bullet points for clarity
• Focus on important information and outcomes
• Attribute points to speakers when clear

## DECISIONS MADE
• List any firm decisions or agreements reached
• Include who is responsible if mentioned
• Note which speaker made or agreed to each decision

## ACTION ITEMS
• Extract specific tasks, assignments, or follow-ups mentioned
• Format as: "Action: [Task] - Owner: [Person/Team] - Due: [Date if mentioned]"
• If no owner or due date is mentioned, use "Owner: TBD" or "Due: TBD"
• Include which speaker assigned or agreed to each action

## NEXT STEPS
• Outline what should happen next based on the discussion
• Include any scheduled follow-up meetings or deadlines

Format the output in clean markdown. Be concise but comprehensive. Pay special attention to speaker-specific information."""
                },
                {
                    "role": "user",
                    "content": f"Please create a structured summary of this speaker-labeled transcript:\n\n{transcript}"
                }
            ],
            temperature=0.2
        )
        
        return response.choices[0].message.content.strip()
        
    except Exception as e:
        return None

def allowed_file(filename):
    """Check if file has allowed extension."""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def process_transcription_job(job_id, file_path, languages, include_summary):
    """Background job for processing transcription."""
    try:
        # Update job status
        jobs[job_id]['status'] = 'processing'
        jobs[job_id]['progress'] = 10
        jobs[job_id]['message'] = 'Validating file...'
        
        # Validate OpenAI API key
        api_key = os.getenv('OPENAI_API_KEY')
        if not api_key:
            raise ValueError("OpenAI API key not configured")
        
        client = OpenAI(api_key=api_key)
        
        # Check file size
        size_valid, size_message = check_file_size(file_path)
        if not size_valid:
            raise ValueError(size_message)
        
        jobs[job_id]['progress'] = 20
        jobs[job_id]['message'] = 'Extracting audio...'
        
        # Create temporary audio file
        with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as temp_audio:
            temp_audio_path = temp_audio.name
        
        try:
            # Extract audio
            success, message = extract_audio_from_mp4(file_path, temp_audio_path)
            if not success:
                raise ValueError(message)
            
            jobs[job_id]['progress'] = 40
            jobs[job_id]['message'] = 'Performing speaker diarization...'
            
            # Speaker diarization
            speaker_segments = perform_speaker_diarization(temp_audio_path)
            
            jobs[job_id]['progress'] = 60
            jobs[job_id]['message'] = 'Transcribing audio...'
            
            # Transcribe audio
            transcript_data = transcribe_audio(temp_audio_path, client)
            if not transcript_data:
                raise ValueError("Transcription failed")
            
            # Align speakers with transcript
            speaker_transcript, speaker_segments_data = align_speakers_with_transcript(transcript_data, speaker_segments)
            
            jobs[job_id]['progress'] = 70
            jobs[job_id]['message'] = 'Processing translations...'
            
            # Translate if requested
            translations = {}
            if languages:
                for language in languages:
                    # Remove restriction to specific languages - allow any language
                    translated_text = translate_text(speaker_transcript, language, client)
                    if translated_text:
                        translations[language] = translated_text
            
            jobs[job_id]['progress'] = 85
            jobs[job_id]['message'] = 'Generating summary...'
            
            # Generate summary if requested
            summary = None
            if include_summary:
                summary = generate_summary(speaker_transcript, client)
            
            jobs[job_id]['progress'] = 100
            jobs[job_id]['status'] = 'completed'
            jobs[job_id]['message'] = 'Processing completed'
            
            # Store results
            jobs[job_id]['results'] = {
                'original': speaker_transcript,
                'translations': translations,
                'summary': summary,
                'speaker_segments': speaker_segments_data
            }
            
        finally:
            # Clean up temporary files
            if os.path.exists(temp_audio_path):
                os.unlink(temp_audio_path)
            
    except Exception as e:
        jobs[job_id]['status'] = 'failed'
        jobs[job_id]['error'] = str(e)
        jobs[job_id]['message'] = f'Error: {str(e)}'

# API Routes

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint."""
    return jsonify({'status': 'healthy'})

@app.route('/api/upload', methods=['POST'])
def upload_file():
    """Handle file upload and start transcription job."""
    try:
        # Check if file is present
        if 'file' not in request.files:
            return jsonify({'error': 'No file provided'}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        # Validate file type
        if not allowed_file(file.filename):
            return jsonify({'error': f'File type not allowed. Supported: {", ".join(ALLOWED_EXTENSIONS)}'}), 400
        
        # Get form data
        languages = request.form.getlist('languages')  # ['spanish', 'chinese']
        include_summary = request.form.get('include_summary', 'false').lower() == 'true'
        
        # Generate job ID
        job_id = str(uuid.uuid4())
        
        # Save uploaded file
        filename = secure_filename(file.filename)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        unique_filename = f"{timestamp}_{filename}"
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
        file.save(file_path)
        
        # Initialize job
        jobs[job_id] = {
            'status': 'queued',
            'progress': 0,
            'message': 'Job queued for processing',
            'created_at': datetime.now().isoformat(),
            'filename': filename
        }
        
        # Start background processing
        thread = threading.Thread(
            target=process_transcription_job,
            args=(job_id, file_path, languages, include_summary)
        )
        thread.daemon = True
        thread.start()
        
        return jsonify({
            'job_id': job_id,
            'message': 'File uploaded successfully. Processing started.',
            'filename': filename
        })
        
    except RequestEntityTooLarge:
        return jsonify({'error': f'File too large. Maximum size: {MAX_FILE_SIZE_MB}MB'}), 413
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/status/<job_id>', methods=['GET'])
def get_job_status(job_id):
    """Get job processing status."""
    if job_id not in jobs:
        return jsonify({'error': 'Job not found'}), 404
    
    job = jobs[job_id]
    response = {
        'job_id': job_id,
        'status': job['status'],
        'progress': job['progress'],
        'message': job['message'],
        'created_at': job['created_at'],
        'filename': job['filename']
    }
    
    if job['status'] == 'failed':
        response['error'] = job.get('error', 'Unknown error')
    
    return jsonify(response)

@app.route('/api/results/<job_id>', methods=['GET'])
def get_job_results(job_id):
    """Get job results."""
    if job_id not in jobs:
        return jsonify({'error': 'Job not found'}), 404
    
    job = jobs[job_id]
    
    if job['status'] != 'completed':
        return jsonify({'error': 'Job not completed yet'}), 400
    
    return jsonify({
        'job_id': job_id,
        'results': job['results']
    })

@app.route('/api/download/<job_id>/<content_type>', methods=['GET'])
def download_result(job_id, content_type):
    """Download specific result as file."""
    if job_id not in jobs:
        return jsonify({'error': 'Job not found'}), 404
    
    job = jobs[job_id]
    
    if job['status'] != 'completed':
        return jsonify({'error': 'Job not completed yet'}), 400
    
    results = job['results']
    
    # Determine content and filename
    if content_type == 'original':
        content = results['original']
        filename = f"{job['filename']}_transcript.txt"
    elif content_type == 'summary':
        content = results['summary']
        filename = f"{job['filename']}_summary.md"
    else:
        # Check if it's a translation language
        content = results['translations'].get(content_type)
        if content:
            # Create filename with language code or name
            lang_code = content_type[:2] if len(content_type) > 2 else content_type
            filename = f"{job['filename']}_{lang_code}.txt"
        else:
            return jsonify({'error': f'Translation for {content_type} not available'}), 404
    
    if not content:
        return jsonify({'error': f'{content_type} not available'}), 404
    
    # Create temporary file for download
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt', encoding='utf-8') as f:
        f.write(content)
        temp_path = f.name
    
    return send_file(
        temp_path,
        as_attachment=True,
        download_name=filename,
        mimetype='text/plain'
    )

if __name__ == '__main__':
    app.run(debug=True, port=5000)