import React from 'react';
import { Globe, X, ExternalLink, Radio } from 'lucide-react';

export default function NeuralUrlCard({
  matchUrl,
  onUrlChange,
  onClearUrl,
  onRunAnalysis,
  isLive
}) {
  const handleKeyDown = (e) => {
    if (e.key === 'Enter') {
      e.preventDefault();
      if (onRunAnalysis) {
        onRunAnalysis();
      }
    }
  };

  return (
    <div
      className={`neural-url-panel ${isLive ? 'live-active' : ''}`}
      id="neural-url-section"
      style={{ padding: '0.65rem 0.9rem' }}
    >
      <div className="neural-url-input-container">
        {isLive ? (
          <Radio size={15} color="var(--red)" style={{ flexShrink: 0 }} />
        ) : (
          <Globe size={15} color="var(--cyan)" style={{ flexShrink: 0 }} />
        )}
        <input
          id="neural-match-url-input"
          type="text"
          className="neural-url-input"
          value={matchUrl || ''}
          onChange={(e) => onUrlChange && onUrlChange(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="URL del partido en vivo (Flashscore, Sofascore) — opcional..."
          autoComplete="off"
          spellCheck="false"
        />

        {Boolean(matchUrl && matchUrl.trim()) && (
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.3rem', flexShrink: 0, position: 'relative', zIndex: 5 }}>
            <a
              href={matchUrl.trim().startsWith('http') ? matchUrl.trim() : `https://${matchUrl.trim()}`}
              target="_blank"
              rel="noopener noreferrer"
              className="neural-url-clear-btn"
              title="Abrir enlace en vivo"
            >
              <ExternalLink size={13} />
            </a>
            <button
              type="button"
              className="neural-url-clear-btn"
              onMouseDown={(e) => {
                e.preventDefault();
                e.stopPropagation();
              }}
              onClick={(e) => {
                e.preventDefault();
                e.stopPropagation();
                if (onClearUrl) onClearUrl();
              }}
              title="Limpiar URL"
            >
              <X size={15} />
            </button>
          </div>
        )}
      </div>
    </div>
  );
}
