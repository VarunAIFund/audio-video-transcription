import React, { useState } from 'react';
import './LanguageSelector.css';

interface LanguageSelectorProps {
  selectedLanguages: string[];
  onLanguageChange: (languages: string[]) => void;
  includeSummary: boolean;
  onSummaryChange: (include: boolean) => void;
}

const LanguageSelector: React.FC<LanguageSelectorProps> = ({
  selectedLanguages,
  onLanguageChange,
  includeSummary,
  onSummaryChange
}) => {
  const [customLanguage, setCustomLanguage] = useState('');
  const [showCustomInput, setShowCustomInput] = useState(false);

  // Predefined popular languages
  const popularLanguages = [
    { code: 'spanish', name: 'Spanish', flag: '🇪🇸' },
    { code: 'chinese', name: 'Chinese', flag: '🇨🇳' },
    { code: 'french', name: 'French', flag: '🇫🇷' },
    { code: 'german', name: 'German', flag: '🇩🇪' },
    { code: 'italian', name: 'Italian', flag: '🇮🇹' },
    { code: 'portuguese', name: 'Portuguese', flag: '🇵🇹' },
    { code: 'russian', name: 'Russian', flag: '🇷🇺' },
    { code: 'japanese', name: 'Japanese', flag: '🇯🇵' },
    { code: 'korean', name: 'Korean', flag: '🇰🇷' },
    { code: 'arabic', name: 'Arabic', flag: '🇸🇦' },
    { code: 'hindi', name: 'Hindi', flag: '🇮🇳' },
    { code: 'dutch', name: 'Dutch', flag: '🇳🇱' }
  ];

  const handleLanguageToggle = (languageCode: string) => {
    if (selectedLanguages.includes(languageCode)) {
      onLanguageChange(selectedLanguages.filter(lang => lang !== languageCode));
    } else {
      onLanguageChange([...selectedLanguages, languageCode]);
    }
  };

  const handleSelectAll = () => {
    if (selectedLanguages.length === popularLanguages.length) {
      onLanguageChange([]);
    } else {
      onLanguageChange(popularLanguages.map(lang => lang.code));
    }
  };

  const handleCustomLanguageAdd = () => {
    const language = customLanguage.trim().toLowerCase();
    if (language && !selectedLanguages.includes(language)) {
      onLanguageChange([...selectedLanguages, language]);
      setCustomLanguage('');
      setShowCustomInput(false);
    }
  };

  const handleRemoveLanguage = (languageCode: string) => {
    onLanguageChange(selectedLanguages.filter(lang => lang !== languageCode));
  };

  const getLanguageDisplayName = (code: string) => {
    const predefined = popularLanguages.find(lang => lang.code === code);
    return predefined ? predefined.name : code.charAt(0).toUpperCase() + code.slice(1);
  };

  const getLanguageFlag = (code: string) => {
    const predefined = popularLanguages.find(lang => lang.code === code);
    return predefined ? predefined.flag : '🌍';
  };

  return (
    <div className="language-selector-container">
      <div className="selector-section">
        <h3>🌍 Translation Options</h3>
        <p>Select languages for automatic translation (optional)</p>
        
        <div className="language-options">
          <div className="select-all-option">
            <button
              onClick={handleSelectAll}
              className={`select-all-btn ${selectedLanguages.length === popularLanguages.length ? 'selected' : ''}`}
            >
              {selectedLanguages.length === popularLanguages.length ? 'Deselect All' : 'Select Popular Languages'}
            </button>
          </div>

          <h4>Popular Languages</h4>
          <div className="language-grid">
            {popularLanguages.map((language) => (
              <div
                key={language.code}
                className={`language-option ${selectedLanguages.includes(language.code) ? 'selected' : ''}`}
                onClick={() => handleLanguageToggle(language.code)}
              >
                <span className="language-flag">{language.flag}</span>
                <span className="language-name">{language.name}</span>
                <span className="checkmark">{selectedLanguages.includes(language.code) ? '✓' : ''}</span>
              </div>
            ))}
          </div>

          <div className="custom-language-section">
            <h4>Add Custom Language</h4>
            <div className="custom-language-controls">
              {!showCustomInput ? (
                <button
                  onClick={() => setShowCustomInput(true)}
                  className="add-custom-btn"
                >
                  ➕ Add Any Language
                </button>
              ) : (
                <div className="custom-input-group">
                  <input
                    type="text"
                    value={customLanguage}
                    onChange={(e) => setCustomLanguage(e.target.value)}
                    placeholder="Enter language (e.g., Swedish, Thai, Urdu)"
                    className="custom-language-input"
                    onKeyPress={(e) => e.key === 'Enter' && handleCustomLanguageAdd()}
                  />
                  <button
                    onClick={handleCustomLanguageAdd}
                    className="add-btn"
                    disabled={!customLanguage.trim()}
                  >
                    Add
                  </button>
                  <button
                    onClick={() => {
                      setShowCustomInput(false);
                      setCustomLanguage('');
                    }}
                    className="cancel-btn"
                  >
                    Cancel
                  </button>
                </div>
              )}
            </div>
            <p className="custom-language-note">
              💡 You can enter any language name or code (e.g., "Swedish", "Thai", "sv", "th")
            </p>
          </div>

          {selectedLanguages.length > 0 && (
            <div className="selected-languages">
              <h4>Selected for Translation:</h4>
              <div className="selected-languages-list">
                {selectedLanguages.map((langCode) => (
                  <div key={langCode} className="selected-language-tag">
                    <span className="selected-flag">{getLanguageFlag(langCode)}</span>
                    <span className="selected-name">{getLanguageDisplayName(langCode)}</span>
                    <button
                      onClick={() => handleRemoveLanguage(langCode)}
                      className="remove-btn"
                    >
                      ✕
                    </button>
                  </div>
                ))}
              </div>
            </div>
          )}

          {selectedLanguages.length === 0 && (
            <div className="no-translation-note">
              <p>💡 No translations will be generated. Only original transcript will be provided.</p>
            </div>
          )}
        </div>
      </div>

      <div className="selector-section">
        <h3>📋 Summary Options</h3>
        <div className="summary-option">
          <label className="summary-checkbox">
            <input
              type="checkbox"
              checked={includeSummary}
              onChange={(e) => onSummaryChange(e.target.checked)}
            />
            <span className="checkmark-box"></span>
            <span className="summary-text">
              Generate structured summary with action items
            </span>
          </label>
          <p className="summary-description">
            Creates an executive summary, key points, decisions made, and action items using AI analysis.
          </p>
        </div>
      </div>

      <div className="selection-summary">
        <h4>Current Selection:</h4>
        <ul>
          <li>
            <strong>Original Transcript:</strong> ✅ Always included with speaker identification
          </li>
          {selectedLanguages.length > 0 ? (
            <li>
              <strong>Translations:</strong> ✅ {selectedLanguages.map(code => 
                getLanguageDisplayName(code)
              ).join(', ')}
            </li>
          ) : (
            <li>
              <strong>Translations:</strong> ❌ None selected
            </li>
          )}
          <li>
            <strong>Summary:</strong> {includeSummary ? '✅' : '❌'} {includeSummary ? 'Included' : 'Not included'}
          </li>
        </ul>
      </div>
    </div>
  );
};

export default LanguageSelector;