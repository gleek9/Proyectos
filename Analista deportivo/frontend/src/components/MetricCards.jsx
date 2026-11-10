import { Target, Flag, AlertTriangle } from 'lucide-react';

export default function MetricCards({ prediction, match, isLive }) {
  if (!prediction) return null;
  const { goals, corners, cards } = prediction;
  const effectiveLive = isLive !== undefined ? isLive : match?.is_live;

  const liveCornersCount =
    corners?.current_corners !== null && corners?.current_corners !== undefined
      ? Number(corners.current_corners)
      : (match?.live_corners !== null && match?.live_corners !== undefined ? Number(match.live_corners) : null);

  const liveGoalsCount =
    goals?.current_goals !== null && goals?.current_goals !== undefined
      ? Number(goals.current_goals)
      : null;

  // Líneas de goles en vivo: parten siempre de +1 gol adicional respecto a los goles actuales del partido
  const goalDisplayLines = (() => {
    if (effectiveLive && liveGoalsCount !== null && goals?.plus_1_goal_pct !== undefined && goals?.plus_1_goal_pct !== null) {
      return [
        { line: `Más de ${(liveGoalsCount + 0.5).toFixed(1)} goles`, probability: Number(goals.plus_1_goal_pct).toFixed(1) },
        { line: `Más de ${(liveGoalsCount + 1.5).toFixed(1)} goles`, probability: Number(goals.plus_2_goals_pct ?? 0).toFixed(1) },
        { line: `Más de ${(liveGoalsCount + 2.5).toFixed(1)} goles`, probability: Number(goals.plus_3_goals_pct ?? 0).toFixed(1) },
      ];
    }
    return [
      { line: 'Más de 1.5 goles', probability: goals.over_1_5_pct },
      { line: 'Más de 2.5 goles', probability: goals.over_2_5_pct },
      { line: 'Más de 3.5 goles', probability: goals.over_3_5_pct },
    ];
  })();

  // Líneas de córners en vivo: parten SIEMPRE de +1 córner más de los que hay actualmente en el partido
  // Ejemplo: si hay 3 córners -> Más de 3.5 córners (+1), Más de 4.5 córners (+2), Más de 5.5 córners (+3)
  const cornerDisplayLines = (() => {
    if (effectiveLive && liveCornersCount !== null) {
      if (Array.isArray(corners?.adjusted_lines) && corners.adjusted_lines.length >= 3) {
        return corners.adjusted_lines.slice(0, 3);
      }
      if (Array.isArray(corners?.live_corners_lines) && corners.live_corners_lines.length >= 4) {
        return [1, 2, 3].map((step) => {
          const lineThreshold = liveCornersCount + step - 0.5;
          const rawOver = Number(corners.live_corners_lines[step]?.probability ?? 0);
          return {
            line: `Más de ${lineThreshold.toFixed(1)} córners`,
            probability: Number(rawOver.toFixed(1)),
          };
        });
      }
    }
    if (Array.isArray(corners?.adjusted_lines) && corners.adjusted_lines.length >= 3) {
      return corners.adjusted_lines.slice(0, 3);
    }
    return [
      { line: 'Más de 8.5 córners', probability: Number(corners?.over_8_5_pct ?? 0).toFixed(1) },
      { line: 'Más de 9.5 córners', probability: Number(corners?.over_9_5_pct ?? 0).toFixed(1) },
      { line: 'Más de 10.5 córners', probability: Number(corners?.over_10_5_pct ?? 0).toFixed(1) },
    ];
  })();

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
          {goalDisplayLines.map((item, idx) => (
            <div key={idx} className="submetric-row">
              <span className="submetric-key">{item.line}:</span>
              <span className={`submetric-val${idx === 1 ? ' highlight' : ''}`}>{item.probability}%</span>
            </div>
          ))}
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
          {cornerDisplayLines.map((item, idx) => (
            <div key={idx} className="submetric-row">
              <span className="submetric-key">
                {String(item.line).endsWith(':') ? item.line : `${item.line}:`}
              </span>
              <span className={`submetric-val${idx === 1 ? ' highlight' : ''}`}>
                {item.probability}%
              </span>
            </div>
          ))}
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
