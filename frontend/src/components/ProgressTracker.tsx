import React, { useEffect, useState } from 'react';
import { JobStatus, TranscriptionResults } from '../App';
import './ProgressTracker.css';

interface ProgressTrackerProps {
  jobStatus: JobStatus;
  onJobUpdate: (jobStatus: JobStatus) => void;
  onResultsReceived: (results: TranscriptionResults) => void;
}

const ProgressTracker: React.FC<ProgressTrackerProps> = ({
  jobStatus,
  onJobUpdate,
  onResultsReceived
}) => {
  const [currentStatus, setCurrentStatus] = useState<JobStatus>(jobStatus);
  const [elapsedTime, setElapsedTime] = useState(0);

  useEffect(() => {
    const timer = setInterval(() => {
      setElapsedTime(prev => prev + 1);
    }, 1000);

    return () => clearInterval(timer);
  }, []);

  useEffect(() => {
    let pollInterval: NodeJS.Timeout;

    const pollJobStatus = async () => {
      try {
        const response = await fetch(`http://localhost:5000/api/status/${jobStatus.job_id}`);
        
        if (!response.ok) {
          throw new Error('Failed to fetch job status');
        }

        const updatedStatus: JobStatus = await response.json();
        setCurrentStatus(updatedStatus);
        onJobUpdate(updatedStatus);

        // If job is completed, fetch results
        if (updatedStatus.status === 'completed') {
          const resultsResponse = await fetch(`http://localhost:5000/api/results/${jobStatus.job_id}`);
          
          if (resultsResponse.ok) {
            const resultsData = await resultsResponse.json();
            onResultsReceived(resultsData.results);
          }
        }

        // Stop polling if job is completed or failed
        if (updatedStatus.status === 'completed' || updatedStatus.status === 'failed') {
          clearInterval(pollInterval);
        }

      } catch (error) {
        console.error('Error polling job status:', error);
        // Continue polling on error, as it might be temporary
      }
    };

    // Start polling immediately
    pollJobStatus();

    // Set up polling interval (every 2 seconds)
    pollInterval = setInterval(pollJobStatus, 2000);

    return () => clearInterval(pollInterval);
  }, [jobStatus.job_id, onJobUpdate, onResultsReceived]);

  const formatTime = (seconds: number): string => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  const getProgressSteps = () => {
    const steps = [
      { label: 'File Uploaded', threshold: 0, icon: '📁' },
      { label: 'Validating File', threshold: 10, icon: '🔍' },
      { label: 'Extracting Audio', threshold: 20, icon: '🎵' },
      { label: 'Speaker Detection', threshold: 40, icon: '👥' },
      { label: 'Transcribing', threshold: 60, icon: '🎤' },
      { label: 'Translating', threshold: 70, icon: '🌍' },
      { label: 'Generating Summary', threshold: 85, icon: '📋' },
      { label: 'Finalizing', threshold: 100, icon: '✅' }
    ];

    return steps.map(step => ({
      ...step,
      completed: currentStatus.progress >= step.threshold,
      active: currentStatus.progress >= step.threshold && 
              currentStatus.progress < (steps[steps.indexOf(step) + 1]?.threshold || 101)
    }));
  };

  return (
    <div className="progress-tracker-container">
      <div className="progress-header">
        <h2>🔄 Processing Your File</h2>
        <div className="file-info">
          <p><strong>File:</strong> {currentStatus.filename}</p>
          <p><strong>Status:</strong> {currentStatus.status}</p>
          <p><strong>Elapsed Time:</strong> {formatTime(elapsedTime)}</p>
        </div>
      </div>

      <div className="progress-bar-container">
        <div className="progress-bar">
          <div 
            className="progress-fill"
            style={{ width: `${currentStatus.progress}%` }}
          ></div>
        </div>
        <div className="progress-percentage">
          {currentStatus.progress}%
        </div>
      </div>

      <div className="current-message">
        <p>{currentStatus.message}</p>
      </div>

      <div className="progress-steps">
        {getProgressSteps().map((step, index) => (
          <div 
            key={index} 
            className={`progress-step ${step.completed ? 'completed' : ''} ${step.active ? 'active' : ''}`}
          >
            <div className="step-icon">
              {step.completed ? '✅' : step.active ? step.icon : '⏳'}
            </div>
            <div className="step-label">
              {step.label}
            </div>
          </div>
        ))}
      </div>

      <div className="processing-info">
        <div className="info-grid">
          <div className="info-item">
            <div className="info-icon">🤖</div>
            <div className="info-text">
              <strong>AI Processing</strong>
              <p>Using OpenAI Whisper for transcription</p>
            </div>
          </div>
          
          <div className="info-item">
            <div className="info-icon">👥</div>
            <div className="info-text">
              <strong>Speaker Detection</strong>
              <p>Identifying different speakers automatically</p>
            </div>
          </div>
          
          <div className="info-item">
            <div className="info-icon">🌍</div>
            <div className="info-text">
              <strong>Multi-language</strong>
              <p>Translating to selected languages</p>
            </div>
          </div>
          
          <div className="info-item">
            <div className="info-icon">📊</div>
            <div className="info-text">
              <strong>Smart Analysis</strong>
              <p>Generating insights and summaries</p>
            </div>
          </div>
        </div>
      </div>

      {currentStatus.status === 'failed' && (
        <div className="error-details">
          <h3>❌ Processing Failed</h3>
          <p>{currentStatus.error || currentStatus.message}</p>
        </div>
      )}
    </div>
  );
};

export default ProgressTracker;