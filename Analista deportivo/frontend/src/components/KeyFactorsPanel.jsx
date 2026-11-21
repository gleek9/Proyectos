import React from 'react';
import { Terminal } from 'lucide-react';

export default function KeyFactorsPanel({ factors, analyzedAt, healthInfo }) {
  const formattedDate = analyzedAt ? new Date(analyzedAt).toLocaleTimeString('es-ES', {
    hour: '2-digit', minute: '2-digit', second: '2-digit'
  }) : 'Reciente';

  const ver = healthInfo?.version ? `v${healthInfo.version.replace(/^v/, '')}` : 'v5.0.0';
  const pipelineStr = healthInfo?.models_local?.length
    ? healthInfo.models_local.join(' + ')
    : 'Dixon-Coles MLE + XGBoost/LightGBM 44F + RichLSTM 14F';
  const rpsLabel = healthInfo?.rps_oos != null ? `RPS OOS: ${healthInfo.rps_oos}` : 'Calibrado OOF';

  return (
    <div className="factors-panel">
      <div className="panel-header">
        <span className="panel-title">
          <Terminal size={15} color="var(--emerald)" />
          <span>Factores clave y telemetría</span>
        </span>
        <span className="v5-meta-dim">
          {formattedDate} UTC
        </span>
      </div>

      <div className="factors-list">
        {factors && factors.length > 0 ? (
          factors.map((factor, idx) => (
            <div key={idx} className="factor-item">
              <span className="factor-bullet">&gt;</span>
              <span>{factor}</span>
            </div>
          ))
        ) : (
          <div className="factor-item">
            <span className="factor-bullet">&gt;</span>
            <span>No se detectaron anomalías tácticas o ausencias críticas reportadas.</span>
          </div>
        )}
      </div>

      <div style={{ marginTop: 'auto', paddingTop: '0.75rem', borderTop: '1px solid var(--border-dim)' }}>
        <div
          style={{
            display: 'flex',
            justifyContent: 'space-between',
            flexWrap: 'wrap',
            gap: '0.4rem',
            fontSize: '0.7rem',
            fontFamily: 'var(--font-mono)',
            color: 'var(--text-muted)'
          }}
        >
          <span>Pipeline: {pipelineStr} · Katakuri {ver}</span>
          <span style={{ color: 'var(--emerald)' }}>{rpsLabel}</span>
        </div>
      </div>
    </div>
  );
}
