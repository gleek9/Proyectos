import React from 'react';
import { Trophy } from 'lucide-react';

export default function WinnerCard({ match, winner, isLive }) {
  if (!match || !winner) return null;

  const { home_win_pct, draw_pct, away_win_pct, human_verdict } = winner;
  const showLive = isLive !== undefined ? isLive : match.is_live;

  return (
    <section className="winner-section">
      <div className="winner-header">
        <div className="match-title">
          <span className="team-name home">{match.home_team}</span>
          {showLive && match.live_score ? (
            <div className="live-score-pill" title={`Marcador oficial en directo: ${match.live_score}`}>
              <span className="live-score-num">{match.live_score.split('-')[0]?.trim()}</span>
              <span className="live-score-sep">-</span>
              <span className="live-score-num">{match.live_score.split('-')[1]?.trim()}</span>
              {match.live_minute && (
                <span className="live-score-min">{match.live_minute}</span>
              )}
            </div>
          ) : (
            <span className="vs-badge">VS</span>
          )}
          <span className="team-name away">{match.away_team}</span>
          <span style={{ fontSize: '0.8rem', color: 'var(--text-dim)', fontWeight: 400 }}>
            [{match.competition || 'General'}]
          </span>
          {showLive && (
            <span className="live-badge-tag" style={{ display: 'inline-flex', alignItems: 'center', gap: '0.35rem' }}>
              <span className="pulse-dot-red"></span>
              <span>En vivo {match.live_score ? `[${match.live_score}]` : ''}</span>
              <span style={{ fontSize: '0.65rem', background: 'rgba(244, 63, 94, 0.22)', padding: '0.1rem 0.35rem', borderRadius: '3px', marginLeft: '0.2rem' }}>
                Prioridad activa
              </span>
            </span>
          )}
        </div>

        <div className="human-verdict-box">
          <Trophy size={16} color="var(--emerald)" />
          <span>Veredicto: <strong>{human_verdict}</strong></span>
        </div>
      </div>

      <div className="probs-bar-container">
        <div className="probs-segmented-bar">
          <div
            className="seg-home"
            style={{ width: `${home_win_pct}%` }}
            title={`Victoria ${match.home_team}: ${home_win_pct}%`}
          />
          <div
            className="seg-draw"
            style={{ width: `${draw_pct}%` }}
            title={`Empate: ${draw_pct}%`}
          />
          <div
            className="seg-away"
            style={{ width: `${away_win_pct}%` }}
            title={`Victoria ${match.away_team}: ${away_win_pct}%`}
          />
        </div>

        <div className="probs-labels-grid">
          <div className="prob-item">
            <span className="prob-title" title={`Victoria de ${match.home_team}`}>
              1. {match.home_team || 'Local'}
            </span>
            <span className="prob-value home">{home_win_pct}%</span>
          </div>

          <div className="prob-item" style={{ textAlign: 'center' }}>
            <span className="prob-title" title="Empate">
              X. Empate
            </span>
            <span className="prob-value draw">{draw_pct}%</span>
          </div>

          <div className="prob-item" style={{ textAlign: 'right' }}>
            <span className="prob-title" title={`Victoria de ${match.away_team}`}>
              2. {match.away_team || 'Visitante'}
            </span>
            <span className="prob-value away">{away_win_pct}%</span>
          </div>
        </div>
      </div>

      {(winner.double_chance || winner.draw_no_bet) && (
        <div className="derived-markets-container">
          {winner.double_chance && (
            <div className="derived-market-card">
              <div className="derived-market-title">
                Doble oportunidad (1X / X2 / 12)
              </div>
              <div className="derived-market-row">
                <span className="derived-stat-pill">1X: <strong style={{ color: 'var(--cyan)' }}>{winner.double_chance.home_or_draw_pct}%</strong></span>
                <span className="derived-stat-pill">X2: <strong style={{ color: 'var(--purple)' }}>{winner.double_chance.draw_or_away_pct}%</strong></span>
                <span className="derived-stat-pill">12: <strong style={{ color: 'var(--lime)' }}>{winner.double_chance.home_or_away_pct}%</strong></span>
              </div>
            </div>
          )}

          {winner.draw_no_bet && (
            <div className="derived-market-card">
              <div className="derived-market-title">
                Empate apuesta no válida (DNB)
              </div>
              <div className="derived-market-row">
                <span className="derived-stat-pill">Local DNB: <strong style={{ color: 'var(--cyan)' }}>{winner.draw_no_bet.home_dnb_pct}%</strong></span>
                <span className="derived-stat-pill">Visitante DNB: <strong style={{ color: 'var(--purple)' }}>{winner.draw_no_bet.away_dnb_pct}%</strong></span>
              </div>
            </div>
          )}
        </div>
      )}
    </section>
  );
}
