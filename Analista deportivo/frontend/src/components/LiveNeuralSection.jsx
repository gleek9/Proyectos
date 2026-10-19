import React from 'react';
import { Zap, TrendingUp, Globe, X, ExternalLink, Radio } from 'lucide-react';

export default function LiveNeuralSection({
  prediction,
  match,
  isLive,
  matchUrl,
  onUrlChange,
  onClearUrl,
  onRunAnalysis
}) {
  const effectiveLive = isLive !== undefined ? isLive : match?.is_live;
  if (!effectiveLive || !prediction) return null;

  const { goals, corners } = prediction;
  const currentGoals = goals?.current_goals !== null && goals?.current_goals !== undefined ? goals.current_goals : 0;
  const currentCorners = corners?.current_corners !== null && corners?.current_corners !== undefined
    ? corners.current_corners
    : (match?.live_corners !== null && match?.live_corners !== undefined ? match.live_corners : null);

  const handleKeyDown = (e) => {
    if (e.key === 'Enter') {
      e.preventDefault();
      if (onRunAnalysis) {
        onRunAnalysis();
      }
    }
  };

  return (
    <section className="live-neural-horizontal-panel" id="live-neural-section">
      {/* Encabezado con Telemetría en Vivo */}
      <div className="live-neural-header">
        <div className="live-neural-title-group">
          <Radio size={16} color="var(--red)" />
          <span>Red Neuronal LSTM y ensamble en vivo</span>
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
            {currentGoals} {currentGoals === 1 ? 'gol acumulado' : 'goles acumulados'}
          </span>
          <span className="neural-chip cyan">
            {currentCorners !== null && currentCorners !== undefined
              ? `${currentCorners} ${currentCorners === 1 ? 'córner actual' : 'córners actuales'}`
              : 'Tiros de esquina: En seguimiento'}
          </span>
        </div>
      </div>

      {/* Franja de URL Monitoreada en Vivo */}
      <div style={{
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        gap: '0.6rem',
        background: 'rgba(0, 0, 0, 0.35)',
        padding: '0.45rem 0.8rem',
        borderRadius: '6px',
        border: '1px solid rgba(244, 63, 94, 0.3)'
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', flex: 1, minWidth: 0 }}>
          <Globe size={13} color="var(--red)" style={{ flexShrink: 0 }} />
          <span style={{
            fontFamily: 'var(--font-mono)',
            fontSize: '0.72rem',
            color: 'var(--red)',
            fontWeight: 700,
            flexShrink: 0
          }}>
            URL activa:
          </span>
          <input
            id="live-neural-monitored-url"
            type="url"
            className="neural-url-input"
            value={matchUrl || ''}
            onChange={(e) => onUrlChange && onUrlChange(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Pegar URL del partido en vivo (ej: Flashscore, Sofascore)..."
            style={{ fontSize: '0.78rem' }}
          />
        </div>

        {matchUrl && matchUrl.trim() && (
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.35rem' }}>
            <a
              href={matchUrl.startsWith('http') ? matchUrl : `https://${matchUrl}`}
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
              onClick={onClearUrl}
              title="Quitar URL y volver a modo pre-partido"
            >
              <X size={14} />
            </button>
          </div>
        )}
      </div>

      {/* Grid Horizontal de 4 Paneles Clave */}
      <div className="live-neural-cards-grid">
        {/* 1. Sin Más Goles */}
        <div className="neural-card-item">
          <div className="neural-card-title">
            <span>Sin más goles (+0)</span>
            <span style={{ color: 'var(--amber)' }}>●</span>
          </div>
          <div className="neural-card-val amber">
            {goals?.no_more_goals_pct !== null && goals?.no_more_goals_pct !== undefined ? `${goals.no_more_goals_pct}%` : '42.0%'}
          </div>
          <div className="neural-card-sub">
            Marcador final sin cambios [{match?.live_score || '0 - 0'}]. El partido concluye con {currentGoals} goles.
          </div>
        </div>

        {/* 2. Más Goles */}
        <div className="neural-card-item">
          <div className="neural-card-title">
            <span>Más goles ({currentGoals + 1}+)</span>
            <span style={{ color: 'var(--lime)' }}>▲</span>
          </div>
          <div className="neural-card-val lime">
            {goals?.more_goals_pct !== null && goals?.more_goals_pct !== undefined ? `${goals.more_goals_pct}%` : '58.0%'}
          </div>
          <div className="neural-card-sub">
            Al menos +1 gol adicional en el tiempo restante. Supera el marcador actual.
          </div>
        </div>

        {/* 3. Desglose de Líneas de Goles */}
        <div className="neural-card-item">
          <div className="neural-card-title">
            <span>Líneas dinámicas de goles</span>
            <TrendingUp size={13} color="var(--text-dim)" />
          </div>
          <div className="neural-lines-list">
            {goals?.live_lines && goals.live_lines.length > 0 ? (
              goals.live_lines.map((lineItem, idx) => (
                <div key={idx} className="neural-line-row">
                  <span style={{ color: 'var(--text-secondary)' }}>{lineItem.line}:</span>
                  <span style={{ color: idx === 0 ? 'var(--amber)' : 'var(--lime)', fontWeight: 700 }}>
                    {lineItem.probability}%
                  </span>
                </div>
              ))
            ) : (
              <div style={{ fontSize: '0.72rem', color: 'var(--text-dim)' }}>
                Calculando líneas dinámicas...
              </div>
            )}
          </div>
        </div>

        {/* 4. Dinámica de Córners en Vivo */}
        <div className="neural-card-item">
          <div className="neural-card-title">
            <span>Córners en tiempo restante</span>
            <span style={{ color: 'var(--cyan)' }}>⚡</span>
          </div>
          <div className="neural-lines-list">
            {corners?.live_corners_lines && corners.live_corners_lines.length > 0 ? (
              corners.live_corners_lines.map((cl, cIdx) => (
                <div key={cIdx} className="neural-line-row">
                  <span style={{ color: 'var(--text-secondary)' }}>{cl.line}:</span>
                  <span style={{ color: 'var(--cyan)', fontWeight: 700 }}>{cl.probability}%</span>
                </div>
              ))
            ) : (
              <div style={{ fontSize: '0.72rem', color: 'var(--text-dim)' }}>
                {corners?.expected_total ? `Proyección total: ${corners.expected_total} córners` : 'Calculando córners...'}
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Veredicto de la Red Neuronal y Modelos Dinámicos */}
      <div className="live-neural-footer">
        <Zap size={15} color="var(--red)" style={{ flexShrink: 0 }} />
        <span>
          <strong>Inferencia Neuronal:</strong> {goals?.human_verdict || 'Análisis en tiempo real ajustado al flujo de tensión del encuentro.'}
        </span>
      </div>
    </section>
  );
}
