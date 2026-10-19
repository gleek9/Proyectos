import { Target, Flag, AlertTriangle } from 'lucide-react';

export default function MetricCards({ prediction, match, isLive }) {
  if (!prediction) return null;
  const { goals, corners, cards } = prediction;
  const effectiveLive = isLive !== undefined ? isLive : match?.is_live;

  return (
    <div className="metrics-grid">
      {/* 1. Panel de Goles */}
      <div className="metric-panel">
        <div className="panel-header">
          <span className="panel-title">
            <Target size={15} color="var(--lime)" />
            <span>Proyección de Goles</span>
          </span>
          <span style={{ fontSize: '0.75rem', fontFamily: 'var(--font-mono)', color: 'var(--text-dim)' }}>
            {effectiveLive ? 'MODELO EN VIVO DINÁMICO' : 'MODELO POISSON + ML'}
          </span>
        </div>

        <div className="panel-main-stat">
          <div>
            <div className="stat-number" style={{ color: 'var(--lime)' }}>
              {goals.expected_total}
            </div>
            <div className="stat-desc">
              {effectiveLive ? 'Goles Totales Acumulados Proyectados' : 'Goles Totales Esperados'}
            </div>
          </div>
          <div style={{ textAlign: 'right', display: 'flex', flexDirection: 'column', alignItems: 'flex-end', gap: '0.2rem' }}>
            {effectiveLive && match?.live_score && (
              <div>
                <span style={{ fontSize: '0.72rem', fontFamily: 'var(--font-mono)', color: 'var(--red)', fontWeight: 700, background: 'rgba(239, 68, 68, 0.12)', padding: '0.15rem 0.4rem', borderRadius: '4px', border: '1px solid rgba(239, 68, 68, 0.3)' }}>
                  🔴 ACTUAL: {match.live_score} {match.live_minute ? `(${match.live_minute})` : ''}
                </span>
              </div>
            )}
            <div>
              <span style={{ fontSize: '0.72rem', fontFamily: 'var(--font-mono)', color: 'var(--text-dim)' }}>
                {effectiveLive ? 'PROYECCIÓN FINAL' : 'MARCADOR PROBABLE'}
              </span>
              <div style={{ fontSize: '1.25rem', fontFamily: 'var(--font-mono)', fontWeight: 700, color: 'var(--text-main)' }}>
                {goals.most_likely_score}
              </div>
            </div>
          </div>
        </div>

        <div className="submetrics-list">
          <div className="submetric-row">
            <span className="submetric-key">Más de 1.5 Goles:</span>
            <span className="submetric-val">{goals.over_1_5_pct}%</span>
          </div>
          <div className="submetric-row">
            <span className="submetric-key">Más de 2.5 Goles:</span>
            <span className="submetric-val highlight">{goals.over_2_5_pct}%</span>
          </div>
          <div className="submetric-row">
            <span className="submetric-key">Más de 3.5 Goles:</span>
            <span className="submetric-val">{goals.over_3_5_pct}%</span>
          </div>
          <div className="submetric-row">
            <span className="submetric-key">Ambos Equipos Anotan (Sí):</span>
            <span className="submetric-val highlight">{goals.both_teams_to_score_pct}%</span>
          </div>
        </div>

        <div className="metric-verdict">
          {goals.human_verdict}
        </div>
      </div>

      {/* 2. Panel de Córners */}
      <div className="metric-panel">
        <div className="panel-header">
          <span className="panel-title">
            <Flag size={15} color="var(--cyan)" />
            <span>Tiros de Esquina</span>
          </span>
          <span style={{ fontSize: '0.75rem', fontFamily: 'var(--font-mono)', color: 'var(--text-dim)' }}>
            {effectiveLive ? 'DINÁMICA CÓRNERS EN VIVO' : 'PROYECCIÓN CÓRNERS'}
          </span>
        </div>

        <div className="panel-main-stat">
          <div>
            <div className="stat-number" style={{ color: 'var(--cyan)' }}>
              {corners.expected_total}
            </div>
            <div className="stat-desc">
              {effectiveLive ? 'Córners Totales Proyectados' : 'Córners Estimados'}
            </div>
          </div>
          {effectiveLive && (
            <div style={{ textAlign: 'right' }}>
              <span style={{ fontSize: '0.75rem', fontFamily: 'var(--font-mono)', color: 'var(--text-dim)' }}>
                CÓRNERS EN DIRECTO
              </span>
              <div style={{ fontSize: '1.25rem', fontFamily: 'var(--font-mono)', fontWeight: 700, color: 'var(--cyan)' }}>
                {corners.current_corners !== null && corners.current_corners !== undefined
                  ? corners.current_corners
                  : (match?.live_corners !== null && match?.live_corners !== undefined ? match.live_corners : '--')}
              </div>
            </div>
          )}
        </div>

        <div className="submetrics-list">
          <div className="submetric-row">
            <span className="submetric-key">Más de 8.5 Córners:</span>
            <span className="submetric-val">{corners.over_8_5_pct}%</span>
          </div>
          <div className="submetric-row">
            <span className="submetric-key">Más de 9.5 Córners:</span>
            <span className="submetric-val highlight">{corners.over_9_5_pct}%</span>
          </div>
          <div className="submetric-row">
            <span className="submetric-key">Más de 10.5 Córners:</span>
            <span className="submetric-val">{corners.over_10_5_pct}%</span>
          </div>
        </div>

        <div className="metric-verdict" style={{ borderColor: 'var(--cyan)' }}>
          {corners.human_verdict}
        </div>
      </div>

      {/* 3. Panel de Tarjetas */}
      <div className="metric-panel">
        <div className="panel-header">
          <span className="panel-title">
            <AlertTriangle size={15} color="var(--amber)" />
            <span>Disciplina y Tarjetas</span>
          </span>
          <span style={{ fontSize: '0.75rem', fontFamily: 'var(--font-mono)', color: 'var(--text-dim)' }}>
            ANÁLISIS DISCIPLINARIO
          </span>
        </div>

        <div className="panel-main-stat">
          <div>
            <div className="stat-number" style={{ color: 'var(--amber)' }}>
              {cards.expected_total}
            </div>
            <div className="stat-desc">Tarjetas Esperadas</div>
          </div>
          <div style={{ textAlign: 'right' }}>
            <span style={{ fontSize: '0.75rem', fontFamily: 'var(--font-mono)', color: 'var(--text-dim)' }}>
              RIESGO TARJETA ROJA
            </span>
            <div style={{ fontSize: '1.25rem', fontFamily: 'var(--font-mono)', fontWeight: 700, color: 'var(--red)' }}>
              {cards.red_card_risk_pct}%
            </div>
          </div>
        </div>

        <div className="submetrics-list">
          <div className="submetric-row">
            <span className="submetric-key">Más de 3.5 Tarjetas:</span>
            <span className="submetric-val highlight">{cards.over_3_5_pct}%</span>
          </div>
          <div className="submetric-row">
            <span className="submetric-key">Más de 4.5 Tarjetas:</span>
            <span className="submetric-val">{cards.over_4_5_pct}%</span>
          </div>
        </div>

        <div className="metric-verdict" style={{ borderColor: 'var(--amber)' }}>
          {cards.human_verdict}
        </div>
      </div>
    </div>
  );
}
