import React, { useState, useEffect } from 'react';
import { X, Activity, ShieldCheck, RefreshCw, BarChart3 } from 'lucide-react';

export default function BacktestModal({ isOpen, onClose }) {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const fetchBenchmark = async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await fetch('/api/backtest/benchmark');
      if (!res.ok) {
        throw new Error(`Error en el servidor: HTTP ${res.status}`);
      }
      const json = await res.json();
      setData(json);
    } catch (err) {
      // Fallback a conexión directa local si el proxy Vite tiene problemas
      try {
        const directRes = await fetch('http://127.0.0.1:8000/api/backtest/benchmark');
        if (!directRes.ok) throw new Error(`HTTP ${directRes.status}`);
        const json = await directRes.json();
        setData(json);
      } catch {
        setError(err.message || 'No se pudo conectar con el endpoint de backtesting.');
      }
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (isOpen && !data && !loading) {
      fetchBenchmark();
    }
  }, [isOpen, data, loading]);

  if (!isOpen) return null;

  return (
    <div className="modal-backdrop" onClick={onClose} role="dialog" aria-modal="true" aria-labelledby="backtest-modal-title">
      <div className="modal-dialog backtest-dialog" onClick={(e) => e.stopPropagation()}>
        <div className="modal-header">
          <div className="modal-title-group">
            <Activity size={18} color="var(--emerald)" />
            <h2 id="backtest-modal-title" className="modal-title">Validación empírica y calibración de modelos</h2>
          </div>
          <button className="modal-close-btn" onClick={onClose} aria-label="Cerrar modal">
            <X size={18} />
          </button>
        </div>

        <div className="modal-body">
          <p className="modal-description">
            Evaluación automatizada contra dataset histórico de control con resultados reales confirmados (Premier League, LaLiga, Serie A, Bundesliga).
          </p>

          {loading && (
            <div className="backtest-loading-state">
              <RefreshCw size={24} className="spin-icon" color="var(--emerald)" />
              <span>Ejecutando ciclo de backtesting sobre partidos históricos...</span>
            </div>
          )}

          {error && (
            <div className="error-banner" style={{ margin: '1rem 0' }}>
              <span>{error}</span>
              <button className="btn-retry" onClick={fetchBenchmark}>Reintentar</button>
            </div>
          )}

          {!loading && data && data.metrics && (
            <div className="backtest-content">
              {/* Veredicto de Calibración */}
              <div className="backtest-verdict-card">
                <div className="verdict-icon">
                  <ShieldCheck size={20} color="var(--emerald)" />
                </div>
                <div className="verdict-text">
                  <div className="verdict-headline">Estado de calibración</div>
                  <div className="verdict-body">{data.verdict}</div>
                </div>
              </div>

              {/* Grid de Métricas Principales */}
              <div className="backtest-kpi-grid">
                <div className="kpi-card">
                  <div className="kpi-label" title="Ranked Probability Score (Constantinou & Fenton). Evalúa la distancia ordinal de las probabilidades 1X2. Menor a 0.20 indica calibración óptima.">
                    RPS Medio (1X2)
                  </div>
                  <div className="kpi-value emerald">{data.metrics.rps_mean}</div>
                  <div className="kpi-sub">Estándar óptimo: &le; 0.215</div>
                </div>

                <div className="kpi-card">
                  <div className="kpi-label" title="Brier Score para Más de 2.5 Goles. Mide el error cuadrático medio de la probabilidad del mercado binario.">
                    Brier Score (Over 2.5)
                  </div>
                  <div className="kpi-value">{data.metrics.brier_score_over_2_5}</div>
                  <div className="kpi-sub">Precisión: {data.metrics.accuracy_over_2_5_pct}%</div>
                </div>

                <div className="kpi-card">
                  <div className="kpi-label" title="Brier Score para Ambos Equipos Anotan (BTTS).">
                    Brier Score (BTTS)
                  </div>
                  <div className="kpi-value">{data.metrics.brier_score_btts}</div>
                  <div className="kpi-sub">Precisión: {data.metrics.accuracy_btts_pct}%</div>
                </div>

                <div className="kpi-card">
                  <div className="kpi-label" title="Error absoluto medio entre los goles proyectados por el ensamble y los goles reales anotados.">
                    MAE Goles
                  </div>
                  <div className="kpi-value">{data.metrics.goals_mae}</div>
                  <div className="kpi-sub">RMSE: {data.metrics.goals_rmse}</div>
                </div>
              </div>

              {/* Tabla de Partidos Evaluados */}
              <div className="backtest-table-container">
                <div className="table-header-title">
                  <BarChart3 size={15} color="var(--text-secondary)" />
                  <span>Desglose por partido del benchmark ({data.total_matches_evaluated} encuentros)</span>
                </div>
                <table className="backtest-table">
                  <thead>
                    <tr>
                      <th>Partido</th>
                      <th>Marcador</th>
                      <th>1X2 Real</th>
                      <th>1X2 Predicho</th>
                      <th>RPS</th>
                      <th>Goles Proy.</th>
                    </tr>
                  </thead>
                  <tbody>
                    {data.matches.map((m) => (
                      <tr key={m.match_id}>
                        <td className="team-cell">{m.match}</td>
                        <td className="score-cell">{m.actual_score}</td>
                        <td className="outcome-cell">
                          <span className={`outcome-pill outcome-${m.actual_outcome}`}>
                            {m.actual_outcome === '1' ? 'Local' : m.actual_outcome === 'X' ? 'Empate' : 'Visitante'}
                          </span>
                        </td>
                        <td className="pred-cell">
                          <span className={`pred-pill ${m.dominant_pred === m.actual_outcome ? 'hit' : 'miss'}`}>
                            {m.dominant_pred === '1' ? 'Local' : m.dominant_pred === 'X' ? 'Empate' : 'Visitante'}
                          </span>
                        </td>
                        <td className="mono-cell">{m.rps}</td>
                        <td className="mono-cell">{m.expected_goals}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}
        </div>

        <div className="modal-footer">
          <button className="btn-secondary" onClick={fetchBenchmark} disabled={loading}>
            <RefreshCw size={14} className={loading ? 'spin-icon' : ''} />
            <span>Recalcular benchmark</span>
          </button>
          <button className="btn-primary" onClick={onClose}>
            Entendido
          </button>
        </div>
      </div>
    </div>
  );
}
