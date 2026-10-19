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
              <span>RED NEURONAL LSTM // MODO EN VIVO ACTIVO</span>
            </>
          ) : (
            <>
              <Activity size={15} color="var(--cyan)" />
              <span>RED NEURONAL // CASILLA PARA MODO EN VIVO</span>
            </>
          )}
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '0.45rem' }}>
          {isLive ? (
            <span className="neural-chip accent">
              🔴 RASTREO ONLINE (5 MIN)
            </span>
          ) : (
            <span className="neural-chip">
              🔵 MODO PRE-MATCH
            </span>
          )}
        </div>
      </div>

      <div className="neural-url-input-container">
        <Globe size={15} color={isLive ? 'var(--red)' : 'var(--cyan)'} style={{ flexShrink: 0 }} />
        <input
          id="neural-match-url-input"
          type="url"
          className="neural-url-input"
          value={matchUrl}
          onChange={(e) => onUrlChange(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="Pega aquí la URL del partido en vivo (ej: Flashscore, Sofascore) para entrar a Modo En Vivo..."
          autoComplete="off"
          spellCheck="false"
        />

        {matchUrl && matchUrl.trim() && (
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.3rem' }}>
            <a
              href={matchUrl.startsWith('http') ? matchUrl : `https://${matchUrl}`}
              target="_blank"
              rel="noopener noreferrer"
              className="neural-url-clear-btn"
              title="Abrir enlace en nueva pestaña"
            >
              <ExternalLink size={13} />
            </a>
            <button
              type="button"
              className="neural-url-clear-btn"
              onClick={onClearUrl}
              title="Limpiar URL y volver a Modo Pre-Match (recuadro azul)"
            >
              <X size={14} />
            </button>
          </div>
        )}
      </div>

      <div className="neural-url-hint">
        {isLive ? (
          <span>
            ⚡ <strong>Modo En Vivo activado por URL.</strong> El recuadro Katakuri está en <strong>ROJO</strong>. Presiona <strong>ANALIZAR</strong> arriba para procesar el partido en vivo. Se auto-sincronizará cada 5 minutos.
          </span>
        ) : (
          <span>
            ℹ️ El recuadro Katakuri está en <strong>AZUL</strong> (Pre-Match). Al pegar una URL, Katakuri pasará a <strong>MODO EN VIVO</strong> automáticamente y el recuadro cambiará a <strong>ROJO</strong>.
          </span>
        )}
      </div>
    </div>
  );
}
