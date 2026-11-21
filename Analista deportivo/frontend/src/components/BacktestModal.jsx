import React, { useState, useEffect, useCallback } from 'react';
import { X, Activity, ShieldCheck, RefreshCw, BarChart3, TrendingUp, Layers } from 'lucide-react';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Tooltip,
  Legend,
  Filler,
} from 'chart.js';
import { Line } from 'react-chartjs-2';

ChartJS.register(CategoryScale, LinearScale, PointElement, LineElement, Tooltip, Legend, Filler);

const LEAGUES_OPTIONS = [
  { code: '', label: 'Todas las ligas (13)' },
  { code: 'premier_league', label: 'Premier League' },
  { code: 'laliga', label: 'LaLiga' },
  { code: 'serie_a', label: 'Serie A' },
  { code: 'bundesliga', label: 'Bundesliga' },
  { code: 'ligue_1', label: 'Ligue 1' },
  { code: 'eredivisie', label: 'Eredivisie' },
  { code: 'primeira_liga', label: 'Primeira Liga' },
  { code: 'champions_league', label: 'Champions League' },
  { code: 'liga_mx', label: 'Liga MX' },
  { code: 'liga_f', label: 'Liga F Femenina' },
  { code: 'wsl', label: 'WSL Femenina' },
  { code: 'uwcl', label: 'UWCL Femenina' },
  { code: 'liga_mx_femenil', label: 'Liga MX Femenil' },
];

const ODDS_SOURCES = [
  { id: 'closing', label: 'Cierre Bet365' },
  { id: 'opening', label: 'Apertura Bet365' },
  { id: 'pinnacle_opening', label: 'Apertura Pinnacle' },
  { id: 'pinnacle_closing', label: 'Cierre Pinnacle' },
];

export default function BacktestModal({ isOpen, onClose, healthInfo }) {
  const [mode, setMode] = useState('walk_forward');
  const [sampleSize, setSampleSize] = useState(250);
  const [competition, setCompetition] = useState('');
  const [oddsSource, setOddsSource] = useState('opening');
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const fetchBacktestData = useCallback(async (
    targetMode = mode,
    targetSize = sampleSize,
    targetComp = competition,
    targetSource = oddsSource
  ) => {
    setLoading(true);
    setError(null);
    const compQuery = targetComp ? `&competition=${encodeURIComponent(targetComp)}` : '';
    const sourceQuery = targetSource ? `&odds_source=${encodeURIComponent(targetSource)}` : '';
    const relPath = targetMode === 'walk_forward'
      ? `/api/backtest/walk-forward?n_matches=${targetSize}${compQuery}${sourceQuery}`
      : '/api/backtest/benchmark';

    try {
      let res = await fetch(relPath);
      if (!res.ok && (res.status === 502 || res.status === 503 || res.status === 504)) {
        res = await fetch(`http://127.0.0.1:8000${relPath}`);
      }
      if (!res.ok) {
        throw new Error(`Error en el servidor: HTTP ${res.status}`);
      }
      const json = await res.json();
      setData(json);
    } catch (err) {
      try {
        const directRes = await fetch(`http://127.0.0.1:8000${relPath}`);
        if (!directRes.ok) throw new Error(`HTTP ${directRes.status}`);
        const json = await directRes.json();
        setData(json);
      } catch {
        setError(err.message || 'No se pudo conectar con el endpoint de backtesting.');
      }
    } finally {
      setLoading(false);
    }
  }, [mode, sampleSize, competition, oddsSource]);

  useEffect(() => {
    if (isOpen) {
      fetchBacktestData(mode, sampleSize, competition, oddsSource);
    }
  }, [isOpen, mode, sampleSize, competition, oddsSource, fetchBacktestData]);

  if (!isOpen) return null;

  const wf = data?.walk_forward_simulation;
  const valueBetting = wf?.value_betting;
  const marketBench = wf?.market_benchmark;
  const pinnacleBench = wf?.pinnacle_closing_benchmark;
  const equityCurve = valueBetting?.equity_curve || [];

  const verBadge = healthInfo?.version ? `v${healthInfo.version.split('.').slice(0, 2).join('.')}` : 'v5.0';
  const datasetSummary = healthInfo?.dataset_summary || '7,270 partidos oficiales en 13 competiciones';

  const chartData = equityCurve.length > 0 ? {
    labels: equityCurve.map((pt) => `#${pt.bet}`),
    datasets: [
      {
        label: 'Flat Betting (1u)',
        data: equityCurve.map((pt) => pt.flat_profit),
        borderColor: '#10b981',
        backgroundColor: 'rgba(16, 185, 129, 0.12)',
        borderWidth: 2,
        pointRadius: 1.5,
        tension: 0.25,
        fill: true,
      },
      {
        label: '1/4 Kelly Dinámico (u)',
        data: equityCurve.map((pt) => pt.kelly_profit),
        borderColor: '#38bdf8',
        backgroundColor: 'rgba(56, 189, 248, 0.08)',
        borderWidth: 2,
        pointRadius: 1.5,
        tension: 0.25,
        fill: false,
      },
    ],
  } : null;

  const chartOptions = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        labels: {
          color: '#cbd5e1',
          font: { family: "'JetBrains Mono', monospace", size: 11 },
        },
      },
    },
    scales: {
      x: {
        grid: { color: 'rgba(255, 255, 255, 0.04)' },
        ticks: { color: '#64748b', font: { family: "'JetBrains Mono', monospace", size: 10 }, maxTicksLimit: 8 },
      },
      y: {
        grid: { color: 'rgba(255, 255, 255, 0.05)' },
        ticks: { color: '#94a3b8', font: { family: "'JetBrains Mono', monospace", size: 10 } },
      },
    },
  };

  return (
    <div className="modal-backdrop" onClick={onClose} role="dialog" aria-modal="true" aria-labelledby="backtest-modal-title">
      <div className="modal-dialog backtest-dialog" onClick={(e) => e.stopPropagation()}>
        <div className="modal-header">
          <div className="modal-title-group">
            <Activity size={18} color="var(--emerald)" />
            <h2 id="backtest-modal-title" className="modal-title">
              Katakuri {verBadge} · Validación Out-of-Sample y Opening vs Closing CLV
            </h2>
          </div>
          <button type="button" className="modal-close-btn" onClick={onClose} aria-label="Cerrar modal">
            <X size={18} />
          </button>
        </div>

        <div className="modal-body">
          <p className="modal-description">
            Evaluación estricta Point-in-Time (cero fuga temporal desde 2025-01-01) sobre {datasetSummary}, comparando Dixon-Coles MLE + XGBoost/LightGBM 44F + RichLSTM 14F frente a Bet365 y Pinnacle.
          </p>

          {/* Selector de Pestañas / Modo */}
          <div className="backtest-tabs">
            <button
              type="button"
              className={`backtest-tab-btn ${mode === 'walk_forward' ? 'active' : ''}`}
              onClick={() => setMode('walk_forward')}
            >
              <TrendingUp size={14} />
              <span>Walk-Forward OOS ({sampleSize} partidos)</span>
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

          {/* Controles Walk-Forward: Muestra, Cuotas y 13 Competiciones */}
          {mode === 'walk_forward' && (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '0.6rem', fontSize: '0.78rem', color: 'var(--text-secondary)' }}>
              <div style={{ display: 'flex', flexWrap: 'wrap', alignItems: 'center', justifyContent: 'space-between', gap: '0.65rem' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem', flexWrap: 'wrap' }}>
                  <span>Muestra:</span>
                  {[100, 250, 600, 1250].map((size) => (
                    <button
                      key={size}
                      type="button"
                      className={`v5-bt-source-btn ${sampleSize === size ? 'active' : ''}`}
                      style={{ border: '1px solid var(--border-subtle)', borderRadius: '5px' }}
                      onClick={() => setSampleSize(size)}
                    >
                      {size}
                    </button>
                  ))}
                </div>

                <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem' }}>
                  <span>Liga:</span>
                  <select
                    value={competition}
                    onChange={(e) => setCompetition(e.target.value)}
                    style={{
                      background: 'var(--bg-surface)',
                      color: 'var(--text-main)',
                      border: '1px solid var(--border-subtle)',
                      padding: '0.26rem 0.5rem',
                      borderRadius: '5px',
                      fontSize: '0.75rem'
                    }}
                  >
                    {LEAGUES_OPTIONS.map((lg) => (
                      <option key={lg.code || 'all'} value={lg.code}>{lg.label}</option>
                    ))}
                  </select>
                </div>
              </div>

              <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', flexWrap: 'wrap' }}>
                <span>Referencia de cuotas:</span>
                <div className="v5-bt-source-pill">
                  {ODDS_SOURCES.map((src) => (
                    <button
                      key={src.id}
                      type="button"
                      className={`v5-bt-source-btn ${oddsSource === src.id ? 'active' : ''}`}
                      onClick={() => setOddsSource(src.id)}
                    >
                      {src.label}
                    </button>
                  ))}
                </div>
              </div>
            </div>
          )}

          {loading && (
            <div className="backtest-loading-state">
              <RefreshCw size={24} className="spin-icon" color="var(--emerald)" />
              <span>Ejecutando simulación temporal Out-of-Sample ({oddsSource})...</span>
            </div>
          )}

          {error && (
            <div className="error-banner" style={{ margin: '1rem 0' }}>
              <span>{error}</span>
              <button
                type="button"
                className="btn-retry"
                onClick={() => fetchBacktestData(mode, sampleSize, competition, oddsSource)}
              >
                Reintentar
              </button>
            </div>
          )}

          {!loading && data && data.metrics && (
            <div className="backtest-content">
              {/* Banner Value Betting + Kelly + CLV */}
              {valueBetting && (
                <div className="value-betting-banner">
                  <div className="vb-header">
                    <span>Value Betting (Edge &ge; {valueBetting.edge_threshold_pct}% · {marketBench?.bookmaker || oddsSource})</span>
                    <span className="v5-tabular-num" style={{ color: valueBetting.roi_pct >= 0 ? 'var(--emerald)' : '#ef4444' }}>
                      Flat ROI: {valueBetting.roi_pct >= 0 ? `+${valueBetting.roi_pct}%` : `${valueBetting.roi_pct}%`}
                    </span>
                  </div>
                  <div className="vb-grid">
                    <div className="vb-stat">
                      <span className="vb-stat-label">ROI 1/4 Kelly</span>
                      <span
                        className="vb-stat-val v5-tabular-num"
                        style={{ color: (valueBetting.kelly_roi_pct ?? 0) >= 0 ? 'var(--emerald)' : '#ef4444' }}
                      >
                        {valueBetting.kelly_roi_pct != null
                          ? `${valueBetting.kelly_roi_pct >= 0 ? '+' : ''}${valueBetting.kelly_roi_pct}%`
                          : '—'}
                      </span>
                    </div>
                    <div className="vb-stat">
                      <span className="vb-stat-label">CLV Medio / Beat</span>
                      <span className="vb-stat-val v5-tabular-num">
                        {valueBetting.avg_clv_pct != null
                          ? `${valueBetting.avg_clv_pct >= 0 ? '+' : ''}${valueBetting.avg_clv_pct}% (${valueBetting.clv_beat_rate_pct ?? 0}%)`
                          : 'N/A'}
                      </span>
                    </div>
                    <div className="vb-stat">
                      <span className="vb-stat-label">Aciertos / Apuestas</span>
                      <span className="vb-stat-val v5-tabular-num">
                        {valueBetting.bets_won} / {valueBetting.total_bets_placed} ({valueBetting.win_rate_pct}%)
                      </span>
                    </div>
                    <div className="vb-stat">
                      <span className="vb-stat-label">Retorno Neto Flat</span>
                      <span
                        className="vb-stat-val v5-tabular-num"
                        style={{ color: valueBetting.net_profit_units >= 0 ? 'var(--emerald)' : '#ef4444' }}
                      >
                        {valueBetting.net_profit_units >= 0 ? `+${valueBetting.net_profit_units} u.` : `${valueBetting.net_profit_units} u.`}
                      </span>
                    </div>
                  </div>
                </div>
              )}

              {/* Curva de Capital Acumulado Flat vs 1/4 Kelly */}
              {chartData && (
                <div className="v5-bt-chart-box">
                  <div className="panel-header" style={{ marginBottom: '0.5rem' }}>
                    <span className="panel-title">
                      <TrendingUp size={14} color="var(--emerald)" />
                      <span>Curva de capital acumulada (unidades)</span>
                    </span>
                    <span className="v5-meta-dim">{equityCurve.length} puntos muestreados</span>
                  </div>
                  <div className="v5-bt-chart-canvas">
                    <Line data={chartData} options={chartOptions} />
                  </div>
                </div>
              )}

              {/* Benchmark vs Casa / Pinnacle Closing */}
              {(marketBench || pinnacleBench) && (
                <div className="backtest-kpi-grid" style={{ marginBottom: '0.85rem' }}>
                  {marketBench && (
                    <div className="kpi-card">
                      <div className="kpi-label">RPS Mercado ({marketBench.bookmaker})</div>
                      <div className="kpi-value">{marketBench.market_rps_mean ?? '—'}</div>
                      <div className="kpi-sub">
                        Delta Katakuri: {marketBench.rps_delta_vs_market != null ? `${marketBench.rps_delta_vs_market > 0 ? '+' : ''}${marketBench.rps_delta_vs_market}` : '—'} · Acc {marketBench.market_accuracy_pct ?? '—'}%
                      </div>
                    </div>
                  )}
                  {pinnacleBench && (
                    <div className="kpi-card">
                      <div className="kpi-label">Pinnacle Cierre (Estándar Oro)</div>
                      <div className="kpi-value">{pinnacleBench.market_rps_mean ?? '—'}</div>
                      <div className="kpi-sub">
                        Delta Katakuri: {pinnacleBench.rps_delta_vs_market != null ? `${pinnacleBench.rps_delta_vs_market > 0 ? '+' : ''}${pinnacleBench.rps_delta_vs_market}` : '—'} · Acc {pinnacleBench.market_accuracy_pct ?? '—'}%
                      </div>
                    </div>
                  )}
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
                  <div className="kpi-label">RPS Medio (1X2)</div>
                  <div className="kpi-value emerald">{data.metrics.rps_mean}</div>
                  <div className="kpi-sub">Estándar óptimo: &le; 0.215</div>
                </div>

                <div className="kpi-card">
                  <div className="kpi-label">Precisión 1X2</div>
                  <div className="kpi-value">{data.metrics.accuracy_1x2_pct}%</div>
                  <div className="kpi-sub">Log-Loss: {data.metrics.log_loss_mean}</div>
                </div>

                <div className="kpi-card">
                  <div className="kpi-label">Brier Score (Over 2.5)</div>
                  <div className="kpi-value">{data.metrics.brier_score_over_2_5}</div>
                  <div className="kpi-sub">Precisión: {data.metrics.accuracy_over_2_5_pct}%</div>
                </div>

                <div className="kpi-card">
                  <div className="kpi-label">MAE Goles</div>
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
          <button
            type="button"
            className="btn-secondary"
            onClick={() => fetchBacktestData(mode, sampleSize, competition, oddsSource)}
            disabled={loading}
          >
            <RefreshCw size={14} className={loading ? 'spin-icon' : ''} />
            <span>Recalcular {mode === 'walk_forward' ? 'Walk-Forward' : 'Benchmark'}</span>
          </button>
          <button type="button" className="btn-primary" onClick={onClose}>
            Entendido
          </button>
        </div>
      </div>
    </div>
  );
}
