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

  const primaryGoalLine = (() => {
    if (effectiveLive && liveGoalsCount !== null && goals?.plus_1_goal_pct !== undefined && goals?.plus_1_goal_pct !== null) {
      return {
        line: `Más de ${(liveGoalsCount + 0.5).toFixed(1)} goles`,
        probability: Number(goals.plus_1_goal_pct).toFixed(1),
      };
    }
    return {
      line: 'Más de 2.5 goles',
      probability: goals.over_2_5_pct,
    };
  })();

  const cornerDisplayLines = (() => {
    if (effectiveLive && liveCornersCount !== null) {
      if (Array.isArray(corners?.adjusted_lines) && corners.adjusted_lines.length >= 2) {
        return corners.adjusted_lines.slice(0, 2);
      }
      if (Array.isArray(corners?.live_corners_lines) && corners.live_corners_lines.length >= 3) {
        return [1, 2].map((step) => {
          const lineThreshold = liveCornersCount + step - 0.5;
          const rawOver = Number(corners.live_corners_lines[step]?.probability ?? 0);
          return {
            line: `Más de ${lineThreshold.toFixed(1)} córners`,
            probability: Number(rawOver.toFixed(1)),
          };
        });
      }
    }
    if (Array.isArray(corners?.adjusted_lines) && corners.adjusted_lines.length >= 2) {
      return corners.adjusted_lines.slice(0, 2);
    }
    return [
      { line: 'Más de 8.5 córners', probability: Number(corners?.over_8_5_pct ?? 0).toFixed(1) },
      { line: 'Más de 9.5 córners', probability: Number(corners?.over_9_5_pct ?? 0).toFixed(1) },
    ];
  })();

  return (
    <div className="metrics-grid">
      {/* 1. Goles */}
      <div className="metric-panel">
        <div className="panel-header">
          <span className="panel-title">
            <span className="v5-dot-indicator" style={{ background: 'var(--emerald)' }} />
            <Target size={14} color="var(--text-secondary)" />
            <span>Goles</span>
          </span>
          <span className="v5-meta-dim">
            Marcador: <strong style={{ color: 'var(--text-main)' }}>{goals.most_likely_score}</strong>
          </span>
        </div>

        <div className="panel-main-stat">
          <div>
            <div className="stat-number">
              {goals.expected_total}
            </div>
            <div className="stat-desc">
              {effectiveLive ? 'Goles totales proyectados' : 'Goles esperados'}
            </div>
          </div>
          {effectiveLive && match?.live_score && (
            <div style={{ textAlign: 'right' }}>
              <span className="live-telemetry-pill">
                <span className="pulse-dot-red"></span>
                <span>{match.live_score} {match.live_minute ? `(${match.live_minute})` : ''}</span>
              </span>
            </div>
          )}
        </div>

        <div className="submetrics-list">
          <div className="submetric-row">
            <span className="submetric-key">{primaryGoalLine.line}:</span>
            <span className="submetric-val highlight">{primaryGoalLine.probability}%</span>
          </div>
          <div className="submetric-row">
            <span className="submetric-key">Ambos anotan:</span>
            <span className="submetric-val">{goals.both_teams_to_score_pct}%</span>
          </div>
        </div>
      </div>

      {/* 2. Córners */}
      <div className="metric-panel">
        <div className="panel-header">
          <span className="panel-title">
            <span className="v5-dot-indicator" style={{ background: 'var(--sand)' }} />
            <Flag size={14} color="var(--text-secondary)" />
            <span>Córners</span>
          </span>
          {effectiveLive && liveCornersCount !== null && (
            <span className="v5-meta-dim">
              Actuales: <strong style={{ color: 'var(--text-main)' }}>{liveCornersCount}</strong>
            </span>
          )}
        </div>

        <div className="panel-main-stat">
          <div>
            <div className="stat-number">
              {corners.expected_total}
            </div>
            <div className="stat-desc">
              {effectiveLive ? 'Córners totales proyectados' : 'Córners esperados'}
            </div>
          </div>
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
      </div>

      {/* 3. Tarjetas */}
      <div className="metric-panel">
        <div className="panel-header">
          <span className="panel-title">
            <span className="v5-dot-indicator" style={{ background: 'var(--amber)' }} />
            <AlertTriangle size={14} color="var(--text-secondary)" />
            <span>Tarjetas</span>
          </span>
          <span className="v5-meta-dim">
            Roja: <strong style={{ color: 'var(--red)' }}>{cards.red_card_risk_pct}%</strong>
          </span>
        </div>

        <div className="panel-main-stat">
          <div>
            <div className="stat-number">
              {cards.expected_total}
            </div>
            <div className="stat-desc">Tarjetas esperadas</div>
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
      </div>
    </div>
  );
}
