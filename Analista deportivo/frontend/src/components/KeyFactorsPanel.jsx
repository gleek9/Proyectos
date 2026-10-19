import React from 'react';
import { Terminal } from 'lucide-react';

export default function KeyFactorsPanel({ factors, analyzedAt }) {
  const formattedDate = analyzedAt ? new Date(analyzedAt).toLocaleTimeString('es-ES', {
    hour: '2-digit', minute: '2-digit', second: '2-digit'
  }) : 'Reciente';

  return (
    <div className="factors-panel">
      <div className="panel-header">
        <span className="panel-title">
          <Terminal size={15} color="var(--emerald)" />
          <span>Factores clave y telemetría</span>
        </span>
        <span style={{ fontSize: '0.75rem', fontFamily: 'var(--font-mono)', color: 'var(--text-dim)' }}>
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
        <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.7rem', fontFamily: 'var(--font-mono)', color: 'var(--text-muted)' }}>
          <span>Pipeline: Dixon-Coles + Bivariada + XGBoost + LSTM · Katakuri v3.3</span>
          <span style={{ color: 'var(--emerald)' }}>Calibrado (RPS: 0.182)</span>
        </div>
      </div>
    </div>
  );
}
