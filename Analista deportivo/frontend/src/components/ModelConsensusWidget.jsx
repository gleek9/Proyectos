import React from 'react';
import { Layers } from 'lucide-react';

function SubmodelRow({ title, weightPct, probs }) {
  if (!probs) return null;
  const h = Number(probs.home_win ?? 0);
  const d = Number(probs.draw ?? 0);
  const a = Number(probs.away_win ?? 0);
  const tot = h + d + a || 100;

  return (
    <div className="v5-submodel-row">
      <div className="v5-submodel-head">
        <span className="v5-submodel-name">
          <span>{title}</span>
          {weightPct != null && <span className="v5-weight-pill">Peso {weightPct}%</span>}
        </span>
        <span className="v5-submodel-probs">
          {h.toFixed(1)}% · {d.toFixed(1)}% · {a.toFixed(1)}%
        </span>
      </div>
      <div className="v5-submodel-bar">
        <div style={{ width: `${(h / tot) * 100}%`, background: 'var(--emerald)' }} />
        <div style={{ width: `${(d / tot) * 100}%`, background: 'var(--amber)' }} />
        <div style={{ width: `${(a / tot) * 100}%`, background: 'var(--purple)' }} />
      </div>
    </div>
  );
}

export default function ModelConsensusWidget({ subModels, match, comparison }) {
  if (!subModels) return null;

  const weights = subModels.weights || {};
  const models = [
    subModels.poisson_dixon_coles,
    subModels.tabular_ml,
    subModels.rich_lstm,
  ].filter(Boolean);

  // Medir dispersión de probabilidad Local entre modelos para indicar consenso vs volatilidad
  let spread = 0;
  if (models.length >= 2) {
    const hVals = models.map((m) => Number(m.home_win ?? 0));
    spread = Math.max(...hVals) - Math.min(...hVals);
  }
  const highAgreement = spread <= 8.0;
  const modelOnly = comparison?.model_only_probs;

  return (
    <div className="v5-consensus-panel">
      <div className="panel-header">
        <span className="panel-title">
          <Layers size={15} color="var(--purple)" />
          <span>Desglose de sub-modelos (1 / X / 2)</span>
        </span>
        <span
          className="badge"
          style={{
            borderColor: highAgreement ? 'rgba(16, 185, 129, 0.45)' : 'rgba(245, 158, 11, 0.45)',
            color: highAgreement ? 'var(--emerald)' : 'var(--amber)',
          }}
        >
          {highAgreement ? `Consenso sólido (Δ ${spread.toFixed(1)}%)` : `Divergencia (Δ ${spread.toFixed(1)}%)`}
        </span>
      </div>

      <div className="v5-consensus-list">
        <SubmodelRow
          title="Poisson Dixon-Coles MLE"
          weightPct={weights.poisson != null ? Math.round(weights.poisson * 100) : null}
          probs={subModels.poisson_dixon_coles}
        />
        <SubmodelRow
          title="XGBoost + LightGBM (44F)"
          weightPct={weights.tabular != null ? Math.round(weights.tabular * 100) : null}
          probs={subModels.tabular_ml}
        />
        <SubmodelRow
          title="RichLSTM Secuencial (14F)"
          weightPct={weights.lstm != null ? Math.round(weights.lstm * 100) : null}
          probs={subModels.rich_lstm}
        />
      </div>

      {modelOnly && (
        <div
          className="v5-meta-dim"
          style={{
            borderTop: '1px solid var(--border-subtle)',
            paddingTop: '0.45rem',
            display: 'flex',
            justifyContent: 'space-between',
            flexWrap: 'wrap',
            gap: '0.4rem',
          }}
        >
          <span>Modelo puro ({match?.home_team} / X / {match?.away_team}):</span>
          <strong style={{ color: 'var(--text-bright)' }}>
            {modelOnly.home_win_pct}% · {modelOnly.draw_pct}% · {modelOnly.away_win_pct}%
          </strong>
        </div>
      )}
    </div>
  );
}

