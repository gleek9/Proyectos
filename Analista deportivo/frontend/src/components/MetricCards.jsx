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
            <Target size={15} color="var(--emerald)" />
            <span>Proyección de goles</span>
          </span>
          <span style={{ fontSize: '0.75rem', fontFamily: 'var(--font-mono)', color: 'var(--text-dim)' }}>
            {effectiveLive ? 'En vivo dinámico' : 'Consenso bivariado'}
          </span>
        </div>

        <div className="panel-main-stat">
          <div>
            <div className="stat-number" style={{ color: 'var(--emerald)' }}>
              {goals.expected_total}
            </div>
            <div className="stat-desc">
              {effectiveLive ? 'Goles totales acumulados proyectados' : 'Goles totales esperados'}
            </div>
          </div>
          <div style={{ textAlign: 'right', display: 'flex', flexDirection: 'column', alignItems: 'flex-end', gap: '0.2rem' }}>
            {effectiveLive && match?.live_score && (
              <div>
                <span className="live-telemetry-pill">
                  <span className="pulse-dot-red"></span>
                  <span>Actual: {match.live_score} {match.live_minute ? `(${match.live_minute})` : ''}</span>
                </span>
              </div>
            )}
            <div>
              <span style={{ fontSize: '0.72rem', fontFamily: 'var(--font-mono)', color: 'var(--text-dim)' }}>
                {effectiveLive ? 'Proyección final' : 'Marcador probable'}
              </span>
              <div style={{ fontSize: '1.25rem', fontFamily: 'var(--font-mono)', fontWeight: 700, color: 'var(--text-main)' }}>
                {goals.most_likely_score}
              </div>
            </div>
          </div>
        </div>

        <div className="submetrics-list">
          <div className="submetric-row">
            <span className="submetric-key">Más de 1.5 goles:</span>
            <span className="submetric-val">{goals.over_1_5_pct}%</span>
          </div>
          <div className="submetric-row">
            <span className="submetric-key">Más de 2.5 goles:</span>
            <span className="submetric-val highlight">{goals.over_2_5_pct}%</span>
          </div>
          <div className="submetric-row">
            <span className="submetric-key">Más de 3.5 goles:</span>
            <span className="submetric-val">{goals.over_3_5_pct}%</span>
          </div>
          <div className="submetric-row">
            <span className="submetric-key">Ambos equipos anotan (Sí):</span>
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
            <Flag size={15} color="var(--azure)" />
            <span>Tiros de esquina</span>
          </span>
          <span style={{ fontSize: '0.75rem', fontFamily: 'var(--font-mono)', color: 'var(--text-dim)' }}>
            {effectiveLive ? 'Dinámica en vivo' : 'Binomial negativa'}
          </span>
        </div>

        <div className="panel-main-stat">
          <div>
            <div className="stat-number" style={{ color: 'var(--azure)' }}>
              {corners.expected_total}
            </div>
            <div className="stat-desc">
              {effectiveLive ? 'Córners totales proyectados' : 'Córners estimados'}
            </div>
          </div>
          {effectiveLive && (
            <div style={{ textAlign: 'right' }}>
              <span style={{ fontSize: '0.75rem', fontFamily: 'var(--font-mono)', color: 'var(--text-dim)' }}>
                Córners en directo
              </span>
              <div style={{ fontSize: '1.25rem', fontFamily: 'var(--font-mono)', fontWeight: 700, color: 'var(--azure)' }}>
                {corners.current_corners !== null && corners.current_corners !== undefined
                  ? corners.current_corners
                  : (match?.live_corners !== null && match?.live_corners !== undefined ? match.live_corners : '--')}
              </div>
            </div>
          )}
        </div>

        <div className="submetrics-list">
          <div className="submetric-row">
            <span className="submetric-key">Más de 8.5 córners:</span>
            <span className="submetric-val">{corners.over_8_5_pct}%</span>
          </div>
          <div className="submetric-row">
            <span className="submetric-key">Más de 9.5 córners:</span>
            <span className="submetric-val highlight">{corners.over_9_5_pct}%</span>
          </div>
          <div className="submetric-row">
            <span className="submetric-key">Más de 10.5 córners:</span>
            <span className="submetric-val">{corners.over_10_5_pct}%</span>
          </div>
        </div>

        <div className="metric-verdict" style={{ borderColor: 'var(--azure)' }}>
          {corners.human_verdict}
        </div>
      </div>

      {/* 3. Panel de Tarjetas */}
      <div className="metric-panel">
        <div className="panel-header">
          <span className="panel-title">
            <AlertTriangle size={15} color="var(--amber)" />
            <span>Disciplina y amonestaciones</span>
          </span>
          <span style={{ fontSize: '0.75rem', fontFamily: 'var(--font-mono)', color: 'var(--text-dim)' }}>
            Sobredispersión &alpha;=1.40
          </span>
        </div>

        <div className="panel-main-stat">
          <div>
            <div className="stat-number" style={{ color: 'var(--amber)' }}>
              {cards.expected_total}
            </div>
            <div className="stat-desc">Tarjetas esperadas</div>
          </div>
          <div style={{ textAlign: 'right' }}>
            <span style={{ fontSize: '0.75rem', fontFamily: 'var(--font-mono)', color: 'var(--text-dim)' }}>
              Riesgo de roja
            </span>
            <div style={{ fontSize: '1.25rem', fontFamily: 'var(--font-mono)', fontWeight: 700, color: 'var(--red)' }}>
              {cards.red_card_risk_pct}%
            </div>
          </div>
        </div>

        <div className="submetrics-list">
          <div className="submetric-row">
            <span className="submetric-key">Más de 3.5 tarjetas:</span>
            <span className="submetric-val highlight">{cards.over_3_5_pct}%</span>
          </div>
          <div className="submetric-row">
            <span className="submetric-key">Más de 4.5 tarjetas:</span>
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
