import React, { useState, useRef } from 'react';
import { JobStatus } from '../App';
import './FileUpload.css';

interface FileUploadProps {
  selectedLanguages: string[];
  includeSummary: boolean;
  onUpload: (jobStatus: JobStatus) => void;
}

const FileUpload: React.FC<FileUploadProps> = ({
  selectedLanguages,
  includeSummary,
  onUpload
}) => {
  const [isDragging, setIsDragging] = useState(false);
  const [isUploading, setIsUploading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const allowedExtensions = [
    'mp4', 'mp3', 'wav', 'm4a', 'aac', 'flac', 'ogg', 'webm', 'avi', 'mov'
  ];

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(true);
  };

  const handleDragLeave = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
    
    const files = Array.from(e.dataTransfer.files);
    if (files.length > 0) {
      handleFileSelection(files[0]);
    }
  };

  const handleFileInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = e.target.files;
    if (files && files.length > 0) {
      handleFileSelection(files[0]);
    }
  };

  const handleFileSelection = async (file: File) => {
    setError(null);

    // Validate file type
    const fileExtension = file.name.split('.').pop()?.toLowerCase();
    if (!fileExtension || !allowedExtensions.includes(fileExtension)) {
      setError(`File type not supported. Please use: ${allowedExtensions.join(', ')}`);
      return;
    }

    // Validate file size (25MB limit)
    const maxSize = 25 * 1024 * 1024;
    if (file.size > maxSize) {
      setError('File size too large. Maximum size: 25MB');
      return;
    }

    setIsUploading(true);

    try {
      const formData = new FormData();
      formData.append('file', file);
      
      // Add selected languages
      selectedLanguages.forEach(lang => {
        formData.append('languages', lang);
      });
      
      // Add summary preference
      formData.append('include_summary', includeSummary.toString());

      const response = await fetch('http://localhost:5000/api/upload', {
        method: 'POST',
        body: formData,
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.error || 'Upload failed');
      }

      const result = await response.json();
      
      // Call onUpload with initial job status
      onUpload({
        job_id: result.job_id,
        status: 'queued',
        progress: 0,
        message: result.message,
        filename: result.filename
      });

    } catch (err) {
      setError(err instanceof Error ? err.message : 'Upload failed');
    } finally {
      setIsUploading(false);
    }
  };

  const handleUploadClick = () => {
    fileInputRef.current?.click();
  };

  // Utility function for file size formatting (future use)
  // const formatFileSize = (bytes: number): string => {
  //   if (bytes === 0) return '0 Bytes';
  //   const k = 1024;
  //   const sizes = ['Bytes', 'KB', 'MB', 'GB'];
  //   const i = Math.floor(Math.log(bytes) / Math.log(k));
  //   return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  // };

  return (
    <div className="file-upload-container">
      <div
        className={`file-upload-area ${isDragging ? 'dragging' : ''} ${isUploading ? 'uploading' : ''}`}
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
        onClick={handleUploadClick}
      >
        <input
          ref={fileInputRef}
          type="file"
          accept={allowedExtensions.map(ext => `.${ext}`).join(',')}
          onChange={handleFileInputChange}
          style={{ display: 'none' }}
        />
        
        {isUploading ? (
          <div className="upload-status">
            <div className="spinner"></div>
            <p>Uploading file...</p>
          </div>
        ) : (
          <div className="upload-prompt">
            <div className="upload-icon">📁</div>
            <h3>Drop your audio/video file here</h3>
            <p>or click to select a file</p>
            <div className="supported-formats">
              <p>Supported formats:</p>
              <span>{allowedExtensions.join(', ').toUpperCase()}</span>
            </div>
            <div className="file-limit">
              <p>Maximum file size: 25MB</p>
            </div>
          </div>
        )}
      </div>

      {error && (
        <div className="error-message">
          <span>❌ {error}</span>
        </div>
      )}

      <div className="upload-info">
        <h4>What happens after upload:</h4>
        <ul>
          <li>🎵 Audio extraction and processing</li>
          <li>👥 Speaker identification and diarization</li>
          <li>🎤 AI-powered transcription with OpenAI Whisper</li>
          {selectedLanguages.length > 0 && (
            <li>🌍 Translation to {selectedLanguages.join(' and ')}</li>
          )}
          {includeSummary && (
            <li>📋 Structured summary with action items</li>
          )}
        </ul>
      </div>
    </div>
  );
};

export default FileUpload;