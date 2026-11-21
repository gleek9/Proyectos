import React from 'react';
import { Percent, Calculator } from 'lucide-react';

export default function OddsValuePanel({
  match,
  comparison,
  marketOdds,
  useMarketPrior,
  onOddsChange,
  onTogglePrior,
  onApplyOdds,
  loading,
}) {
  const outcomes = comparison?.market_odds_eval?.outcomes;
  const bestSide = comparison?.market_odds_eval?.best_value_side;
  const isLive = Boolean(match?.is_live);

  const cards = [
    { key: 'home', title: `1 · ${match?.home_team || 'Local'}`, data: outcomes?.home },
    { key: 'draw', title: 'X · Empate', data: outcomes?.draw },
    { key: 'away', title: `2 · ${match?.away_team || 'Visitante'}`, data: outcomes?.away },
  ];

  return (
    <section className="v5-odds-panel" aria-label="Calculadora de Value Betting y Cuotas">
      <div className="v5-odds-top">
        <span className="panel-title">
          <Calculator size={15} color="var(--emerald)" />
          <span>Calculadora Fair Odds, Edge y 1/4 Kelly</span>
        </span>

        <div className="v5-odds-inputs">
          <div className="v5-odds-field">
            <label htmlFor="v5-odd-1">1:</label>
            <input
              id="v5-odd-1"
              type="number"
              step="0.01"
              min="1.01"
              placeholder="Ej. 2.10"
              value={marketOdds.home}
              onChange={(e) => onOddsChange('home', e.target.value)}
            />
          </div>
          <div className="v5-odds-field">
            <label htmlFor="v5-odd-x">X:</label>
            <input
              id="v5-odd-x"
              type="number"
              step="0.01"
              min="1.01"
              placeholder="3.40"
              value={marketOdds.draw}
              onChange={(e) => onOddsChange('draw', e.target.value)}
            />
          </div>
          <div className="v5-odds-field">
            <label htmlFor="v5-odd-2">2:</label>
            <input
              id="v5-odd-2"
              type="number"
              step="0.01"
              min="1.01"
              placeholder="3.50"
              value={marketOdds.away}
              onChange={(e) => onOddsChange('away', e.target.value)}
            />
          </div>

          {!isLive && (
            <label className="v5-prior-toggle" title="Desactivar para ver proyección Katakuri sin anclaje al mercado">
              <input
                type="checkbox"
                checked={useMarketPrior}
                onChange={(e) => onTogglePrior(e.target.checked)}
              />
              <span>Prior mercado (85%)</span>
            </label>
          )}

          <button
            type="button"
            className="calibration-btn"
            onClick={onApplyOdds}
            disabled={loading}
          >
            <Percent size={13} />
            <span>{loading ? 'Recalculando...' : 'Evaluar Value'}</span>
          </button>
        </div>
      </div>

      {outcomes && (
        <div className="v5-odds-grid">
          {cards.map(({ key, title, data }) => {
            const edge = data?.edge_pct;
            const hasValue = edge != null && edge > 0;
            const isBest = bestSide === key;
            return (
              <div key={key} className={`v5-odds-card ${hasValue ? 'has-value' : ''}`}>
                <div className="v5-odds-card-head">
                  <span>{title}</span>
                  {isBest && (
                    <span className="badge" style={{ color: 'var(--emerald)', borderColor: 'var(--emerald)' }}>
                      Mejor Valor
                    </span>
                  )}
                </div>
                <div className="v5-odds-metrics">
                  <span style={{ color: 'var(--text-dim)' }}>
                    Cuota justa: <strong style={{ color: 'var(--text-bright)' }}>{data?.fair_odds ?? '—'}</strong>
                  </span>
                  <span style={{ color: hasValue ? 'var(--emerald)' : 'var(--text-muted)' }}>
                    Edge: {edge != null ? `${edge > 0 ? '+' : ''}${edge}%` : '—'}
                  </span>
                </div>
                <div className="v5-meta-dim" style={{ display: 'flex', justifyContent: 'space-between' }}>
                  <span>Prob: {data?.prob_pct ?? '—'}%</span>
                  <span>1/4 Kelly: {data?.kelly_quarter_pct != null ? `${data.kelly_quarter_pct}%` : '—'}</span>
                </div>
              </div>
            );
          })}
        </div>
      )}
    </section>
  );
}

