import React, { useState, useEffect } from 'react';
import { X, Activity, ShieldCheck, RefreshCw, BarChart3, TrendingUp, Layers } from 'lucide-react';

export default function BacktestModal({ isOpen, onClose }) {
  const [mode, setMode] = useState('walk_forward'); // 'walk_forward' o 'benchmark'
  const [sampleSize, setSampleSize] = useState(100);
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const fetchBacktestData = async (targetMode = mode, targetSize = sampleSize) => {
    setLoading(true);
    setError(null);
    try {
      const endpoint = targetMode === 'walk_forward'
        ? `/api/backtest/walk-forward?n_matches=${targetSize}`
        : '/api/backtest/benchmark';

      const res = await fetch(endpoint);
      if (!res.ok) {
        throw new Error(`Error en el servidor: HTTP ${res.status}`);
      }
      const json = await res.json();
      setData(json);
    } catch (err) {
      // Fallback a conexión directa local si el proxy Vite tiene problemas
      try {
        const directUrl = targetMode === 'walk_forward'
          ? `http://127.0.0.1:8000/api/backtest/walk-forward?n_matches=${targetSize}`
          : 'http://127.0.0.1:8000/api/backtest/benchmark';
        const directRes = await fetch(directUrl);
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
    if (isOpen) {
      fetchBacktestData(mode, sampleSize);
    }
  }, [isOpen, mode, sampleSize]);

  if (!isOpen) return null;

  const valueBetting = data?.walk_forward_simulation?.value_betting;

  return (
    <div className="modal-backdrop" onClick={onClose} role="dialog" aria-modal="true" aria-labelledby="backtest-modal-title">
      <div className="modal-dialog backtest-dialog" onClick={(e) => e.stopPropagation()}>
        <div className="modal-header">
          <div className="modal-title-group">
            <Activity size={18} color="var(--emerald)" />
            <h2 id="backtest-modal-title" className="modal-title">Katakuri v4.0 · Validación empírica y simulación temporal</h2>
          </div>
          <button className="modal-close-btn" onClick={onClose} aria-label="Cerrar modal">
            <X size={18} />
          </button>
        </div>

        <div className="modal-body">
          <p className="modal-description">
            Evaluación matemática y backtesting sobre 3,525 partidos oficiales reales de ligas europeas (football-data.co.uk) con ratings Elo dinámicos y cuotas reales de Bet365.
          </p>

          {/* Selector de Pestañas / Modo */}
          <div className="backtest-tabs">
            <button
              type="button"
              className={`backtest-tab-btn ${mode === 'walk_forward' ? 'active' : ''}`}
              onClick={() => setMode('walk_forward')}
            >
              <TrendingUp size={14} />
              <span>Walk-Forward Temporal ({sampleSize} partidos reales)</span>
            </button>
            <button
              type="button"
              className={`backtest-tab-btn ${mode === 'benchmark' ? 'active' : ''}`}
              onClick={() => setMode('benchmark')}
            >
              <Layers size={14} />
              <span>Benchmark Curado (Control de Calibración)</span>
            </button>
          </div>

          {/* Selector de tamaño de muestra para Walk-Forward */}
          {mode === 'walk_forward' && (
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', fontSize: '0.78rem', color: 'var(--text-secondary)' }}>
              <span>Tamaño de muestra:</span>
              {[50, 100, 150, 200].map((size) => (
                <button
                  key={size}
                  type="button"
                  style={{
                    background: sampleSize === size ? 'var(--emerald)' : 'var(--bg-card)',
                    color: sampleSize === size ? '#000' : 'var(--text-main)',
                    border: '1px solid var(--border-dim)',
                    padding: '0.2rem 0.5rem',
                    borderRadius: '4px',
                    fontSize: '0.74rem',
                    cursor: 'pointer',
                    fontWeight: sampleSize === size ? 'bold' : 'normal'
                  }}
                  onClick={() => setSampleSize(size)}
                >
                  {size} partidos
                </button>
              ))}
            </div>
          )}

          {loading && (
            <div className="backtest-loading-state">
              <RefreshCw size={24} className="spin-icon" color="var(--emerald)" />
              <span>Ejecutando simulación temporal out-of-sample sobre partidos históricos...</span>
            </div>
          )}

          {error && (
            <div className="error-banner" style={{ margin: '1rem 0' }}>
              <span>{error}</span>
              <button className="btn-retry" onClick={() => fetchBacktestData(mode, sampleSize)}>Reintentar</button>
            </div>
          )}

          {!loading && data && data.metrics && (
            <div className="backtest-content">
              {/* Banner de Value Betting si está disponible */}
              {valueBetting && (
                <div className="value-betting-banner">
                  <div className="vb-header">
                    <span>Simulación de Apuestas con Valor (Edge &gt; {valueBetting.edge_threshold_pct}% vs Bet365)</span>
                    <span style={{ color: valueBetting.roi_pct >= 0 ? 'var(--emerald)' : '#ef4444' }}>
                      ROI: {valueBetting.roi_pct >= 0 ? `+${valueBetting.roi_pct}%` : `${valueBetting.roi_pct}%`}
                    </span>
                  </div>
                  <div className="vb-grid">
                    <div className="vb-stat">
                      <span className="vb-stat-label">Retorno Neto</span>
                      <span className="vb-stat-val" style={{ color: valueBetting.net_profit_units >= 0 ? 'var(--emerald)' : '#ef4444' }}>
                        {valueBetting.net_profit_units >= 0 ? `+${valueBetting.net_profit_units} u.` : `${valueBetting.net_profit_units} u.`}
                      </span>
                    </div>
                    <div className="vb-stat">
                      <span className="vb-stat-label">Acierto Apuestas</span>
                      <span className="vb-stat-val">{valueBetting.win_rate_pct}%</span>
                    </div>
                    <div className="vb-stat">
                      <span className="vb-stat-label">Apuestas Realizadas</span>
                      <span className="vb-stat-val">{valueBetting.bets_won} / {valueBetting.total_bets_placed}</span>
                    </div>
                    <div className="vb-stat">
                      <span className="vb-stat-label">Muestra Evaluada</span>
                      <span className="vb-stat-val">{data.total_matches_evaluated} encuentros</span>
                    </div>
                  </div>
                </div>
              )}

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
                  <div className="kpi-label" title="Precisión del desenlace 1X2 dominante predicho vs resultado final real.">
                    Precisión 1X2
                  </div>
                  <div className="kpi-value">{data.metrics.accuracy_1x2_pct}%</div>
                  <div className="kpi-sub">Log-Loss: {data.metrics.log_loss_mean}</div>
                </div>

                <div className="kpi-card">
                  <div className="kpi-label" title="Brier Score para Más de 2.5 Goles. Mide el error cuadrático medio de la probabilidad del mercado binario.">
                    Brier Score (Over 2.5)
                  </div>
                  <div className="kpi-value">{data.metrics.brier_score_over_2_5}</div>
                  <div className="kpi-sub">Precisión: {data.metrics.accuracy_over_2_5_pct}%</div>
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
                  <span>Desglose por partido ({data.total_matches_evaluated} encuentros oficiales)</span>
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
                    {data.matches.slice(0, 40).map((m) => (
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
          <button className="btn-secondary" onClick={() => fetchBacktestData(mode, sampleSize)} disabled={loading}>
            <RefreshCw size={14} className={loading ? 'spin-icon' : ''} />
            <span>Recalcular {mode === 'walk_forward' ? 'Walk-Forward' : 'Benchmark'}</span>
          </button>
          <button className="btn-primary" onClick={onClose}>
            Entendido
          </button>
        </div>
      </div>
    </div>
  );
}
