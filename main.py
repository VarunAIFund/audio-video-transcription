#!/usr/bin/env python3
"""
MP4 to Transcript Backend Test
Simple Python script that transcribes MP4 files using OpenAI's Whisper API.
"""

import os
import time
import tempfile
from pathlib import Path
from dotenv import load_dotenv
import ffmpeg
from openai import OpenAI
from pyannote.audio import Pipeline
import torch

# Load environment variables
load_dotenv()

# Constants
MAX_FILE_SIZE_MB = 25
WHISPER_SAMPLE_RATE = 16000

def check_file_exists(file_path):
    """Check if the MP4 file exists and is readable."""
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"File not found: {file_path}")
    if not os.access(file_path, os.R_OK):
        raise PermissionError(f"Cannot read file: {file_path}")
    return True

def check_file_size(file_path):
    """Check if file size is within Whisper API limits."""
    file_size_mb = os.path.getsize(file_path) / (1024 * 1024)
    if file_size_mb > MAX_FILE_SIZE_MB:
        print(f"⚠️  Warning: File size ({file_size_mb:.1f}MB) exceeds Whisper API limit of {MAX_FILE_SIZE_MB}MB")
        return False
    print(f"✅ File size: {file_size_mb:.1f}MB (within limits)")
    return True

def extract_audio_from_mp4(mp4_path, output_path):
    """Extract audio from MP4 and convert to WAV format for Whisper."""
    try:
        print(f"🎵 Extracting audio from: {mp4_path}")
        
        # Use ffmpeg to extract audio and convert to WAV (16kHz mono)
        (
            ffmpeg
            .input(mp4_path)
            .output(
                output_path,
                acodec='pcm_s16le',  # 16-bit PCM
                ac=1,                # Mono
                ar=WHISPER_SAMPLE_RATE  # 16kHz sample rate
            )
            .overwrite_output()
            .run(quiet=True, capture_stdout=True)
        )
        
        print(f"✅ Audio extracted to: {output_path}")
        return True
        
    except ffmpeg.Error as e:
        print(f"❌ FFmpeg error: {e.stderr.decode() if e.stderr else str(e)}")
        return False
    except FileNotFoundError as e:
        if 'ffmpeg' in str(e):
            print("❌ FFmpeg not found! Please install it:")
            print("   macOS: brew install ffmpeg")
            print("   Ubuntu/Debian: sudo apt install ffmpeg")
            print("   Windows: Download from https://ffmpeg.org/download.html")
        else:
            print(f"❌ File not found error: {str(e)}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error during audio extraction: {str(e)}")
        return False

def perform_speaker_diarization(audio_path):
    """Perform speaker diarization to identify different speakers."""
    try:
        print("👥 Performing speaker diarization...")
        
        # Try pyannote first (if available)
        try:
            from pyannote.audio import Pipeline
            
            # Check for HuggingFace token
            hf_token = os.getenv('HF_TOKEN')
            
            if hf_token:
                # Try models in order of preference
                models_to_try = [
                    "pyannote/speaker-diarization-3.1",
                    "pyannote/speaker-diarization"
                ]
                
                pipeline = None
                for model_name in models_to_try:
                    try:
                        print(f"🔄 Trying pyannote model: {model_name}")
                        pipeline = Pipeline.from_pretrained(model_name, use_auth_token=hf_token)
                        
                        # Test the pipeline
                        diarization = pipeline(audio_path)
                        
                        # Convert to list of tuples (start_time, end_time, speaker_label)
                        speaker_segments = []
                        for turn, _, speaker in diarization.itertracks(yield_label=True):
                            speaker_segments.append((turn.start, turn.end, speaker))
                        
                        print(f"✅ PyAnnote completed - Found {len(set(seg[2] for seg in speaker_segments))} speakers")
                        return speaker_segments
                        
                    except Exception as e:
                        print(f"❌ PyAnnote model {model_name} failed: {str(e)[:100]}...")
                        continue
        
        except ImportError:
            print("⚠️  PyAnnote not available")
        
        # Fallback to simple speaker detection
        print("🔄 Using simple speaker detection fallback...")
        return simple_speaker_detection_fallback(audio_path)
        
    except Exception as e:
        print(f"❌ Speaker diarization error: {str(e)}")
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
        
        print(f"✅ Simple speaker detection completed - Found {len(set(seg[2] for seg in segments))} speakers")
        return segments
        
    except Exception as e:
        print(f"❌ Simple speaker detection failed: {str(e)}")
        return None

def transcribe_audio(audio_path, client):
    """Send audio file to OpenAI Whisper API for transcription with timestamps."""
    try:
        print("🎤 Sending audio to Whisper API...")
        
        with open(audio_path, "rb") as audio_file:
            transcript = client.audio.transcriptions.create(
                model="whisper-1",
                file=audio_file,
                response_format="verbose_json",
                timestamp_granularities=["word"]
            )
        
        print("✅ Transcription completed")
        return transcript
        
    except Exception as e:
        print(f"❌ Whisper API error: {str(e)}")
        return None

def align_speakers_with_transcript(transcript_data, speaker_segments):
    """Align speaker segments with transcript segments to create speaker-labeled transcript."""
    try:
        print("🔄 Aligning speakers with transcript...")
        
        if not speaker_segments:
            # If no speaker diarization, return transcript as single speaker
            return transcript_data.text, [{"speaker": "Speaker 1", "text": transcript_data.text, "start": 0, "end": transcript_data.words[-1].end if transcript_data.words else 0}]
        
        # Create speaker-labeled segments
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
                    "text": word_text.strip(),  # Remove leading/trailing spaces for first word
                    "start": word_start,
                    "end": word_end
                }
            else:
                # Same speaker, append to current segment with proper spacing
                current_segment["text"] += word_text
                current_segment["end"] = word_end
        
        # Add the last segment
        if current_segment["speaker"] is not None:
            speaker_transcript_segments.append(current_segment)
        
        # Create formatted transcript
        formatted_transcript = ""
        for segment in speaker_transcript_segments:
            formatted_transcript += f"{segment['speaker']}: {segment['text'].strip()}\n\n"
        
        print("✅ Speaker alignment completed")
        return formatted_transcript.strip(), speaker_transcript_segments
        
    except Exception as e:
        print(f"❌ Speaker alignment error: {str(e)}")
        # Fallback to original text without speaker labels
        return transcript_data.text, [{"speaker": "Speaker 1", "text": transcript_data.text, "start": 0, "end": 0}]

def translate_text(text, target_language, client):
    """Translate text using OpenAI GPT-4."""
    try:
        language_map = {
            'spanish': 'Spanish',
            'chinese': 'Simplified Chinese',
            'es': 'Spanish',
            'zh': 'Simplified Chinese'
        }
        
        target_lang = language_map.get(target_language.lower(), target_language)
        
        print(f"🌍 Translating to {target_lang}...")
        
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {
                    "role": "system",
                    "content": f"You are a professional translator. Translate the following text to {target_lang}. Maintain the original meaning and tone. Only respond with the translated text, no additional comments."
                },
                {
                    "role": "user",
                    "content": text
                }
            ],
            temperature=0.1
        )
        
        translated_text = response.choices[0].message.content.strip()
        print(f"✅ Translation to {target_lang} completed")
        return translated_text
        
    except Exception as e:
        print(f"❌ Translation error for {target_language}: {str(e)}")
        return None

def generate_summary(transcript, client):
    """Generate a structured summary with action items using GPT-4."""
    try:
        print("📋 Generating structured summary with action items...")
        
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
        
        summary = response.choices[0].message.content.strip()
        print("✅ Summary generation completed")
        return summary
        
    except Exception as e:
        print(f"❌ Summary generation error: {str(e)}")
        return None

def save_transcript(transcript, output_path):
    """Save transcript to a text file."""
    try:
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(transcript)
        print(f"💾 Transcript saved to: {output_path}")
        return True
    except Exception as e:
        print(f"❌ Error saving transcript: {str(e)}")
        return False

def save_translations(original_transcript, translations, mp4_path, summary=None):
    """Save original transcript, translations, and summary to separate files."""
    mp4_path = Path(mp4_path)
    results = {}
    
    # Save original transcript
    original_path = mp4_path.with_suffix('.txt')
    if save_transcript(original_transcript, original_path):
        results['original'] = original_path
    
    # Save translations
    language_suffixes = {
        'spanish': '_es',
        'chinese': '_zh'
    }
    
    language_flags = {
        'spanish': '🇪🇸',
        'chinese': '🇨🇳'
    }
    
    for language, translated_text in translations.items():
        if translated_text:
            # Create filename with language suffix
            base_name = mp4_path.stem  # filename without extension
            suffix = language_suffixes.get(language, f'_{language}')
            translation_filename = f"{base_name}{suffix}.txt"
            translation_path = mp4_path.parent / translation_filename
            flag = language_flags.get(language, '🌍')
            
            try:
                with open(translation_path, 'w', encoding='utf-8') as f:
                    f.write(translated_text)
                print(f"💾 {flag} {language.capitalize()} translation saved to: {translation_path}")
                results[language] = translation_path
            except Exception as e:
                print(f"❌ Error saving {language} translation: {str(e)}")
    
    # Save summary if provided
    if summary:
        base_name = mp4_path.stem
        summary_filename = f"{base_name}_summary.md"
        summary_path = mp4_path.parent / summary_filename
        
        try:
            with open(summary_path, 'w', encoding='utf-8') as f:
                f.write(summary)
            print(f"💾 📋 Summary saved to: {summary_path}")
            results['summary'] = summary_path
        except Exception as e:
            print(f"❌ Error saving summary: {str(e)}")
    
    return results

def process_mp4(mp4_file_path):
    """Main function to process MP4 file and generate transcript."""
    start_time = time.time()
    
    print("=" * 60)
    print("🎬 MP4 to Transcript Processor")
    print("=" * 60)
    
    try:
        # Validate OpenAI API key
        api_key = os.getenv('OPENAI_API_KEY')
        if not api_key or api_key == 'your_openai_api_key_here':
            raise ValueError("Please set your OPENAI_API_KEY in the .env file")
        
        # Initialize OpenAI client
        client = OpenAI(api_key=api_key)
        
        # Validate input file
        print(f"📁 Processing file: {mp4_file_path}")
        check_file_exists(mp4_file_path)
        check_file_size(mp4_file_path)
        
        # Create output paths
        mp4_path = Path(mp4_file_path)
        transcript_path = mp4_path.with_suffix('.txt')
        
        # Create temporary WAV file
        with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as temp_audio:
            temp_audio_path = temp_audio.name
        
        try:
            # Extract audio from MP4
            if not extract_audio_from_mp4(mp4_file_path, temp_audio_path):
                return None
            
            # Transcribe audio using Whisper API with timestamps
            transcript_data = transcribe_audio(temp_audio_path, client)
            if not transcript_data:
                return None
            
            # Perform speaker diarization (optional)
            speaker_segments = perform_speaker_diarization(temp_audio_path)
            
            # Align speakers with transcript
            speaker_transcript, speaker_segments_data = align_speakers_with_transcript(transcript_data, speaker_segments)
            
            # Translate to Spanish and Chinese
            translations = {}
            target_languages = ['spanish', 'chinese']
            
            for language in target_languages:
                translated_text = translate_text(speaker_transcript, language, client)
                if translated_text:
                    translations[language] = translated_text
            
            # Generate structured summary with action items
            summary = generate_summary(speaker_transcript, client)
            
            # Save original transcript, translations, and summary
            saved_files = save_translations(speaker_transcript, translations, mp4_file_path, summary)
            
            # Print transcript to console
            print("\n" + "=" * 60)
            print("📝 SPEAKER-LABELED TRANSCRIPT:")
            print("=" * 60)
            print(speaker_transcript)
            print("=" * 60)
            
            # Print translations to console
            language_flags = {'spanish': '🇪🇸', 'chinese': '🇨🇳'}
            for language, translated_text in translations.items():
                if translated_text:
                    flag = language_flags.get(language, '🌍')
                    print(f"\n{flag} {language.upper()} TRANSLATION:")
                    print("=" * 60)
                    print(translated_text)
                    print("=" * 60)
            
            # Print summary to console
            if summary:
                print("\n📋 STRUCTURED SUMMARY & ACTION ITEMS:")
                print("=" * 60)
                print(summary)
                print("=" * 60)
            
            # Calculate processing time
            processing_time = time.time() - start_time
            print(f"⏱️  Processing completed in {processing_time:.2f} seconds")
            
            # Return results summary
            return {
                'original': speaker_transcript,
                'translations': translations,
                'summary': summary,
                'speaker_segments': speaker_segments_data,
                'files': saved_files
            }
            
        finally:
            # Clean up temporary audio file
            if os.path.exists(temp_audio_path):
                os.unlink(temp_audio_path)
                print("🧹 Temporary audio file cleaned up")
    
    except FileNotFoundError as e:
        print(f"❌ File error: {str(e)}")
        return None
    except PermissionError as e:
        print(f"❌ Permission error: {str(e)}")
        return None
    except ValueError as e:
        print(f"❌ Configuration error: {str(e)}")
        return None
    except Exception as e:
        print(f"❌ Unexpected error: {str(e)}")
        return None

def main():
    """Main entry point for testing."""
    # Example usage - update this path to test with your audio/video file
    # Supports: MP4, MP3, WAV, M4A, AAC, FLAC, OGG, and many other formats
    audio_file = "test_files/dailylife002.mp3"  # Change to .mp3 or other format as needed
    
    print("🚀 Starting audio/video transcription process...")
    
    # Check if test file exists, otherwise provide helpful message
    if not os.path.exists(audio_file):
        print(f"📁 Test file not found: {audio_file}")
        print("💡 To test this script:")
        print("   1. Place an audio/video file in the test_files/ directory")
        print("   2. Update the audio_file variable in main() function") 
        print("   3. Supported formats: MP4, MP3, WAV, M4A, AAC, FLAC, OGG")
        print("   4. Set your OPENAI_API_KEY in the .env file")
        print("   5. Run: python main.py")
        return
    
    # Process the audio/video file
    result = process_mp4(audio_file)
    
    if result:
        print("🎉 Transcription and translation successful!")
        if isinstance(result, dict) and 'files' in result:
            print("📁 Files created:")
            for file_type, file_path in result['files'].items():
                print(f"   - {file_type}: {file_path}")
    else:
        print("💥 Transcription failed. Check the error messages above.")

if __name__ == "__main__":
    main()