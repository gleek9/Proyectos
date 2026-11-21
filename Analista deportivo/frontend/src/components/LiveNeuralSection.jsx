import React from 'react';
import { Globe, X, ExternalLink, Radio, RefreshCw } from 'lucide-react';

function parseLiveProgressPct(minuteStr) {
  if (!minuteStr) return 0;
  const clean = String(minuteStr).trim().toUpperCase();
  if (clean === 'HT' || clean === 'DESCANSO') return 50;
  if (clean === 'FT' || clean === 'AP' || clean === 'FINAL') return 100;
  const numMatch = clean.match(/(\d+)/);
  if (!numMatch) return 15;
  const mins = Number(numMatch[1]);
  return Math.max(2, Math.min(100, Math.round((mins / 90) * 100)));
}

export default function LiveNeuralSection({
  prediction,
  match,
  isLive,
  matchUrl,
  onUrlChange,
  onClearUrl,
  onRunAnalysis,
  onForceLiveSync,
  syncingLive,
}) {
  const effectiveLive = isLive !== undefined ? isLive : match?.is_live;
  if (!effectiveLive || !prediction) return null;

  const { goals } = prediction;
  const currentGoals = goals?.current_goals !== null && goals?.current_goals !== undefined ? goals.current_goals : 0;
  const progressPct = parseLiveProgressPct(match?.live_minute);

  const handleKeyDown = (e) => {
    if (e.key === 'Enter') {
      e.preventDefault();
      if (onRunAnalysis) {
        onRunAnalysis();
      }
    }
  };

  return (
    <section className="live-neural-horizontal-panel" id="live-neural-section" style={{ gap: '0.65rem', padding: '0.85rem 1rem' }}>
      <div className="live-neural-header">
        <div className="live-neural-title-group">
          <Radio size={15} color="var(--red)" />
          <span>Seguimiento en vivo</span>
        </div>

        <div className="live-neural-chips">
          {match?.live_minute && (
            <span className="neural-chip">
              Minuto: <strong>{match.live_minute}</strong>
            </span>
          )}
          <span className="neural-chip">
            Marcador: <strong>{match?.live_score || '0 - 0'}</strong>
          </span>
          <span className="neural-chip lime">
            +1 gol ({currentGoals + 1}+): <strong>{goals?.more_goals_pct ?? 0}%</strong>
          </span>
        </div>
      </div>

      <div className="v5-live-progress-wrap">
        <span className="v5-meta-dim">0&apos;</span>
        <div className="v5-live-track" title={`Avance del partido: ${progressPct}%`}>
          <div className="v5-live-fill" style={{ width: `${progressPct}%` }} />
        </div>
        <span className="v5-meta-dim">90&apos;</span>

        {onForceLiveSync && (
          <button
            type="button"
            className="v5-live-sync-btn"
            onClick={onForceLiveSync}
            disabled={syncingLive}
          >
            <RefreshCw size={12} className={syncingLive ? 'spin-icon' : ''} />
            <span>{syncingLive ? 'Sincronizando...' : 'Sync ahora'}</span>
          </button>
        )}
      </div>

      <div className="v5-live-url-row">
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', flex: 1, minWidth: 0 }}>
          <Globe size={13} color="var(--red)" style={{ flexShrink: 0 }} />
          <input
            id="live-neural-monitored-url"
            type="text"
            className="neural-url-input"
            value={matchUrl || ''}
            onChange={(e) => onUrlChange && onUrlChange(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Pegar URL del partido en vivo (Flashscore, Sofascore)..."
            autoComplete="off"
            spellCheck="false"
            style={{ fontSize: '0.78rem' }}
          />
        </div>

        {Boolean(matchUrl && matchUrl.trim()) && (
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.35rem', flexShrink: 0, position: 'relative', zIndex: 5 }}>
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
              title="Quitar URL y volver a modo pre-partido"
            >
              <X size={15} />
            </button>
          </div>
        )}
      </div>
    </section>
  );
}
