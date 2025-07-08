import React, { useState } from 'react';
import './App.css';
import FileUpload from './components/FileUpload';
import LanguageSelector from './components/LanguageSelector';
import ProgressTracker from './components/ProgressTracker';
import ResultsDisplay from './components/ResultsDisplay';

export interface JobStatus {
  job_id: string;
  status: 'queued' | 'processing' | 'completed' | 'failed';
  progress: number;
  message: string;
  filename: string;
  error?: string;
}

export interface TranscriptionResults {
  original: string;
  translations: {
    [language: string]: string;  // Allow any language as key
  };
  summary?: string;
  speaker_segments: Array<{
    speaker: string;
    text: string;
    start: number;
    end: number;
  }>;
}

function App() {
  const [selectedLanguages, setSelectedLanguages] = useState<string[]>([]);
  const [includeSummary, setIncludeSummary] = useState<boolean>(true);
  const [currentJob, setCurrentJob] = useState<JobStatus | null>(null);
  const [results, setResults] = useState<TranscriptionResults | null>(null);

  const handleFileUpload = (jobStatus: JobStatus) => {
    setCurrentJob(jobStatus);
    setResults(null);
  };

  const handleJobUpdate = (jobStatus: JobStatus) => {
    setCurrentJob(jobStatus);
  };

  const handleResultsReceived = (transcriptionResults: TranscriptionResults) => {
    setResults(transcriptionResults);
  };

  const handleReset = () => {
    setCurrentJob(null);
    setResults(null);
    setSelectedLanguages([]);
    setIncludeSummary(true);
  };

  return (
    <div className="App">
      <header className="App-header">
        <h1>🎬 Audio/Video Transcription Service</h1>
        <p>Upload your audio or video file to get transcriptions, translations, and summaries</p>
      </header>

      <main className="App-main">
        {!currentJob && !results && (
          <>
            <FileUpload
              selectedLanguages={selectedLanguages}
              includeSummary={includeSummary}
              onUpload={handleFileUpload}
            />
            
            <LanguageSelector
              selectedLanguages={selectedLanguages}
              onLanguageChange={setSelectedLanguages}
              includeSummary={includeSummary}
              onSummaryChange={setIncludeSummary}
            />
          </>
        )}

        {currentJob && currentJob.status !== 'completed' && currentJob.status !== 'failed' && (
          <ProgressTracker
            jobStatus={currentJob}
            onJobUpdate={handleJobUpdate}
            onResultsReceived={handleResultsReceived}
          />
        )}

        {currentJob && currentJob.status === 'failed' && (
          <div className="error-container">
            <h2>❌ Processing Failed</h2>
            <p>{currentJob.error || currentJob.message}</p>
            <button onClick={handleReset} className="reset-button">
              Try Again
            </button>
          </div>
        )}

        {results && (
          <ResultsDisplay
            results={results}
            jobId={currentJob?.job_id || ''}
            onReset={handleReset}
          />
        )}
      </main>

      <footer className="App-footer">
        <p>Powered by OpenAI Whisper API • Supports MP4, MP3, WAV, M4A, and more</p>
      </footer>
    </div>
  );
}

export default App;
