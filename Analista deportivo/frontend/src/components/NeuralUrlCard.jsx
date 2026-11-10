import React from 'react';
import { Activity, Radio, Globe, X, ExternalLink } from 'lucide-react';

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
    >
      <div className="neural-url-header">
        <div className={`neural-url-title ${isLive ? 'is-live' : 'not-live'}`}>
          {isLive ? (
            <>
              <Radio size={15} color="var(--red)" />
              <span>Red Neuronal LSTM · Rastreo en directo</span>
            </>
          ) : (
            <>
              <Activity size={15} color="var(--cyan)" />
              <span>Red Neuronal LSTM · Entrada de partido</span>
            </>
          )}
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '0.45rem' }}>
          {isLive ? (
            <span className="neural-chip accent" style={{ display: 'inline-flex', alignItems: 'center', gap: '0.4rem' }}>
              <span className="pulse-dot-red"></span>
              <span>Rastreo online (5 min)</span>
            </span>
          ) : (
            <span className="neural-chip" style={{ display: 'inline-flex', alignItems: 'center', gap: '0.4rem' }}>
              <span className="pulse-dot-green"></span>
              <span>Modo pre-partido</span>
            </span>
          )}
        </div>
      </div>

      <div className="neural-url-input-container">
        <Globe size={15} color={isLive ? 'var(--red)' : 'var(--cyan)'} style={{ flexShrink: 0 }} />
        <input
          id="neural-match-url-input"
          type="text"
          className="neural-url-input"
          value={matchUrl || ''}
          onChange={(e) => onUrlChange && onUrlChange(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="Pega aquí la URL del partido (Flashscore, Sofascore) para activar el modo en directo..."
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
              title="Abrir enlace en vivo en nueva pestaña"
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
              title="Limpiar URL y volver a modo pre-partido"
            >
              <X size={15} />
            </button>
          </div>
        )}
      </div>

      <div className="neural-url-hint">
        {isLive ? (
          <span>
            <strong>Modo en vivo activado por URL.</strong> Presiona <strong>Analizar</strong> arriba para procesar la telemetría en tiempo real (auto-sincronización cada 5 min).
          </span>
        ) : (
          <span>
            <strong>Modo pre-partido activo.</strong> Si ingresas la URL de un partido en disputa, el sistema activará automáticamente el modo en directo y el rastreo neuronal.
          </span>
        )}
      </div>
    </div>
  );
}
