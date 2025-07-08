import React, { useState } from 'react';
import { TranscriptionResults } from '../App';
import './ResultsDisplay.css';

interface ResultsDisplayProps {
  results: TranscriptionResults;
  jobId: string;
  onReset: () => void;
}

const ResultsDisplay: React.FC<ResultsDisplayProps> = ({
  results,
  jobId,
  onReset
}) => {
  const [activeTab, setActiveTab] = useState<string>('transcript');
  const [downloadStatus, setDownloadStatus] = useState<Record<string, 'idle' | 'downloading' | 'success' | 'error'>>({});

  const handleDownload = async (contentType: string, filename: string) => {
    setDownloadStatus(prev => ({ ...prev, [contentType]: 'downloading' }));
    
    try {
      const response = await fetch(`http://localhost:5000/api/download/${jobId}/${contentType}`);
      
      if (!response.ok) {
        throw new Error('Download failed');
      }

      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.style.display = 'none';
      a.href = url;
      a.download = filename;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);

      setDownloadStatus(prev => ({ ...prev, [contentType]: 'success' }));
      
      // Reset status after 2 seconds
      setTimeout(() => {
        setDownloadStatus(prev => ({ ...prev, [contentType]: 'idle' }));
      }, 2000);

    } catch (error) {
      console.error('Download error:', error);
      setDownloadStatus(prev => ({ ...prev, [contentType]: 'error' }));
      
      // Reset status after 3 seconds
      setTimeout(() => {
        setDownloadStatus(prev => ({ ...prev, [contentType]: 'idle' }));
      }, 3000);
    }
  };

  const getDownloadButtonText = (contentType: string, defaultText: string) => {
    const status = downloadStatus[contentType] || 'idle';
    switch (status) {
      case 'downloading': return 'Downloading...';
      case 'success': return '✅ Downloaded';
      case 'error': return '❌ Failed';
      default: return defaultText;
    }
  };

  const getDownloadButtonClass = (contentType: string) => {
    const status = downloadStatus[contentType] || 'idle';
    return `download-btn ${status}`;
  };

  // Helper function to get language display info
  const getLanguageInfo = (langCode: string) => {
    const languageMap: Record<string, { name: string; flag: string }> = {
      'spanish': { name: 'Spanish', flag: '🇪🇸' },
      'chinese': { name: 'Chinese', flag: '🇨🇳' },
      'french': { name: 'French', flag: '🇫🇷' },
      'german': { name: 'German', flag: '🇩🇪' },
      'italian': { name: 'Italian', flag: '🇮🇹' },
      'portuguese': { name: 'Portuguese', flag: '🇵🇹' },
      'russian': { name: 'Russian', flag: '🇷🇺' },
      'japanese': { name: 'Japanese', flag: '🇯🇵' },
      'korean': { name: 'Korean', flag: '🇰🇷' },
      'arabic': { name: 'Arabic', flag: '🇸🇦' },
      'hindi': { name: 'Hindi', flag: '🇮🇳' },
      'dutch': { name: 'Dutch', flag: '🇳🇱' },
      'thai': { name: 'Thai', flag: '🇹🇭' },
      'vietnamese': { name: 'Vietnamese', flag: '🇻🇳' },
      'swedish': { name: 'Swedish', flag: '🇸🇪' },
      'norwegian': { name: 'Norwegian', flag: '🇳🇴' },
      'danish': { name: 'Danish', flag: '🇩🇰' },
      'finnish': { name: 'Finnish', flag: '🇫🇮' },
      'polish': { name: 'Polish', flag: '🇵🇱' },
      'turkish': { name: 'Turkish', flag: '🇹🇷' },
      'hebrew': { name: 'Hebrew', flag: '🇮🇱' },
      'czech': { name: 'Czech', flag: '🇨🇿' },
      'hungarian': { name: 'Hungarian', flag: '🇭🇺' },
      'ukrainian': { name: 'Ukrainian', flag: '🇺🇦' },
      'greek': { name: 'Greek', flag: '🇬🇷' },
      'indonesian': { name: 'Indonesian', flag: '🇮🇩' },
      'malay': { name: 'Malay', flag: '🇲🇾' },
      'filipino': { name: 'Filipino', flag: '🇵🇭' },
      'bengali': { name: 'Bengali', flag: '🇧🇩' },
      'tamil': { name: 'Tamil', flag: '🇱🇰' },
      'urdu': { name: 'Urdu', flag: '🇵🇰' },
      'persian': { name: 'Persian', flag: '🇮🇷' },
      'swahili': { name: 'Swahili', flag: '🇰🇪' }
    };
    
    const info = languageMap[langCode.toLowerCase()];
    return info || { 
      name: langCode.charAt(0).toUpperCase() + langCode.slice(1), 
      flag: '🌍' 
    };
  };

  // Create dynamic tabs based on available translations
  const tabs = [
    { id: 'transcript', label: 'Original Transcript', icon: '🎤', available: true },
    ...Object.keys(results.translations).map(langCode => {
      const langInfo = getLanguageInfo(langCode);
      return {
        id: langCode,
        label: `${langInfo.name} Translation`,
        icon: langInfo.flag,
        available: true
      };
    }),
    { id: 'summary', label: 'Summary & Action Items', icon: '📋', available: !!results.summary }
  ];

  const formatTranscript = (text: string) => {
    return text.split('\n\n').map((segment, index) => {
      const [speaker, ...textParts] = segment.split(': ');
      const content = textParts.join(': ');
      
      return (
        <div key={index} className="transcript-segment">
          <span className="speaker-label">{speaker}:</span>
          <span className="speaker-text">{content}</span>
        </div>
      );
    });
  };

  const renderContent = () => {
    if (activeTab === 'transcript') {
      return (
        <div className="content-panel">
          <div className="content-header">
            <h3>🎤 Original Transcript with Speaker Identification</h3>
            <button
              onClick={() => handleDownload('original', 'transcript.txt')}
              className={getDownloadButtonClass('original')}
              disabled={downloadStatus.original === 'downloading'}
            >
              {getDownloadButtonText('original', '⬇️ Download TXT')}
            </button>
          </div>
          <div className="transcript-content">
            {formatTranscript(results.original)}
          </div>
        </div>
      );
    }

    if (activeTab === 'summary') {
      return (
        <div className="content-panel">
          <div className="content-header">
            <h3>📋 Structured Summary & Action Items</h3>
            <button
              onClick={() => handleDownload('summary', 'summary.md')}
              className={getDownloadButtonClass('summary')}
              disabled={downloadStatus.summary === 'downloading'}
            >
              {getDownloadButtonText('summary', '⬇️ Download MD')}
            </button>
          </div>
          <div className="summary-content">
            {results.summary ? (
              <div dangerouslySetInnerHTML={{ 
                __html: results.summary
                  .replace(/\n/g, '<br>')
                  .replace(/## (.*)/g, '<h2>$1</h2>')
                  .replace(/• (.*)/g, '<li>$1</li>')
                  .replace(/(<li>.*<\/li>)/g, '<ul>$1</ul>')
              }} />
            ) : (
              <p>Summary not available</p>
            )}
          </div>
        </div>
      );
    }

    // Handle dynamic language translations
    const translationText = results.translations[activeTab];
    if (translationText) {
      const langInfo = getLanguageInfo(activeTab);
      const langCode = activeTab.length <= 3 ? activeTab : activeTab.substring(0, 2);
      
      return (
        <div className="content-panel">
          <div className="content-header">
            <h3>{langInfo.flag} {langInfo.name} Translation</h3>
            <button
              onClick={() => handleDownload(activeTab, `transcript_${langCode}.txt`)}
              className={getDownloadButtonClass(activeTab)}
              disabled={downloadStatus[activeTab] === 'downloading'}
            >
              {getDownloadButtonText(activeTab, '⬇️ Download TXT')}
            </button>
          </div>
          <div className="transcript-content">
            {formatTranscript(translationText)}
          </div>
        </div>
      );
    }

    return (
      <div className="content-panel">
        <p>Content not available</p>
      </div>
    );
  };

  return (
    <div className="results-display-container">
      <div className="results-header">
        <h2>✅ Processing Complete!</h2>
        <button onClick={onReset} className="new-file-btn">
          📁 Process New File
        </button>
      </div>

      <div className="speaker-stats">
        <h3>👥 Speaker Analysis</h3>
        <div className="speaker-grid">
          {results.speaker_segments.reduce((acc, segment) => {
            const existing = acc.find(item => item.speaker === segment.speaker);
            if (existing) {
              existing.count++;
              existing.totalTime += (segment.end - segment.start);
            } else {
              acc.push({
                speaker: segment.speaker,
                count: 1,
                totalTime: segment.end - segment.start
              });
            }
            return acc;
          }, [] as Array<{ speaker: string; count: number; totalTime: number }>).map(speakerStat => (
            <div key={speakerStat.speaker} className="speaker-stat">
              <span className="speaker-name">{speakerStat.speaker}</span>
              <span className="speaker-time">{Math.round(speakerStat.totalTime)}s</span>
              <span className="speaker-segments">{speakerStat.count} segments</span>
            </div>
          ))}
        </div>
      </div>

      <div className="results-tabs">
        {tabs.filter(tab => tab.available).map(tab => (
          <button
            key={tab.id}
            onClick={() => setActiveTab(tab.id)}
            className={`tab-btn ${activeTab === tab.id ? 'active' : ''}`}
          >
            <span className="tab-icon">{tab.icon}</span>
            <span className="tab-label">{tab.label}</span>
          </button>
        ))}
      </div>

      <div className="results-content">
        {renderContent()}
      </div>

      <div className="download-all-section">
        <h3>📦 Download All Files</h3>
        <div className="download-grid">
          <button
            onClick={() => handleDownload('original', 'transcript.txt')}
            className={getDownloadButtonClass('original')}
            disabled={downloadStatus.original === 'downloading'}
          >
            {getDownloadButtonText('original', '🎤 Original Transcript')}
          </button>
          
          {Object.keys(results.translations).map(langCode => {
            const langInfo = getLanguageInfo(langCode);
            const fileName = `transcript_${langCode.length <= 3 ? langCode : langCode.substring(0, 2)}.txt`;
            
            return (
              <button
                key={langCode}
                onClick={() => handleDownload(langCode, fileName)}
                className={getDownloadButtonClass(langCode)}
                disabled={downloadStatus[langCode] === 'downloading'}
              >
                {getDownloadButtonText(langCode, `${langInfo.flag} ${langInfo.name}`)}
              </button>
            );
          })}
          
          {results.summary && (
            <button
              onClick={() => handleDownload('summary', 'summary.md')}
              className={getDownloadButtonClass('summary')}
              disabled={downloadStatus.summary === 'downloading'}
            >
              {getDownloadButtonText('summary', '📋 Summary & Actions')}
            </button>
          )}
        </div>
      </div>
    </div>
  );
};

export default ResultsDisplay;