import React from 'react';
import { Scale, Clock, UserCheck, AlertTriangle, Swords } from 'lucide-react';

function ComparisonBar({ label, homeVal, awayVal, homeDisplay, awayDisplay }) {
  const hNum = typeof homeVal === 'number' && !Number.isNaN(homeVal) ? Math.max(0, homeVal) : 0;
  const aNum = typeof awayVal === 'number' && !Number.isNaN(awayVal) ? Math.max(0, awayVal) : 0;
  const total = hNum + aNum;
  const hPct = total > 0 ? (hNum / total) * 100 : 50;
  const aPct = total > 0 ? 100 - hPct : 50;

  return (
    <div className="v5-comp-row">
      <div className="v5-comp-head">
        <span className="v5-comp-val-home">{homeDisplay}</span>
        <span className="v5-comp-label">{label}</span>
        <span className="v5-comp-val-away">{awayDisplay}</span>
      </div>
      <div className="v5-comp-bar-track">
        <div className="v5-comp-bar-home" style={{ width: `${hPct}%` }} />
        <div className="v5-comp-bar-away" style={{ width: `${aPct}%` }} />
      </div>
    </div>
  );
}

function FormPills({ teamName, results }) {
  if (!results || results.length === 0) return null;
  return (
    <div className="v5-form-group">
      <span style={{ color: 'var(--text-dim)', fontWeight: 500 }}>{teamName}:</span>
      {results.slice(0, 5).map((r, idx) => {
        const cls = r === 'W' ? 'w' : r === 'D' ? 'd' : 'l';
        const label = r === 'W' ? 'V' : r === 'D' ? 'E' : 'D';
        return (
          <span key={idx} className={`v5-form-dot ${cls}`} title={r}>
            {label}
          </span>
        );
      })}
    </div>
  );
}

export default function TeamComparisonStrip({ match, comparison }) {
  if (!comparison || !comparison.home || !comparison.away) return null;

  const { home, away, referee, h2h } = comparison;
  const hasXg = home.avg_xg_for != null && away.avg_xg_for != null;
  const absencesHome = home.key_absences || [];
  const absencesAway = away.key_absences || [];

  return (
    <section className="v5-comparison-panel" aria-label="Comparativa cara a cara">
      <div className="panel-header">
        <span className="panel-title">
          <Scale size={15} color="var(--cyan)" />
          <span>Comparativa pre-partido · {match?.home_team} vs {match?.away_team}</span>
        </span>
        <span className="v5-meta-dim">
          Local (verde) vs Visitante (violeta)
        </span>
      </div>

      <div className="v5-comp-rows">
        <ComparisonBar
          label="Rating Elo"
          homeVal={home.elo_rating ?? 1500}
          awayVal={away.elo_rating ?? 1500}
          homeDisplay={home.elo_rating != null ? home.elo_rating.toFixed(0) : '—'}
          awayDisplay={away.elo_rating != null ? away.elo_rating.toFixed(0) : '—'}
        />

        {hasXg ? (
          <ComparisonBar
            label="xG promedio"
            homeVal={home.avg_xg_for}
            awayVal={away.avg_xg_for}
            homeDisplay={home.avg_xg_for.toFixed(2)}
            awayDisplay={away.avg_xg_for.toFixed(2)}
          />
        ) : (
          <ComparisonBar
            label="Tiros a puerta p/p"
            homeVal={home.avg_shots_on_target ?? 0}
            awayVal={away.avg_shots_on_target ?? 0}
            homeDisplay={home.avg_shots_on_target != null ? home.avg_shots_on_target.toFixed(1) : '—'}
            awayDisplay={away.avg_shots_on_target != null ? away.avg_shots_on_target.toFixed(1) : '—'}
          />
        )}

        <ComparisonBar
          label="Goles F / C p/p"
          homeVal={home.avg_goals_for ?? 0}
          awayVal={away.avg_goals_for ?? 0}
          homeDisplay={`${(home.avg_goals_for ?? 0).toFixed(2)} / ${(home.avg_goals_against ?? 0).toFixed(2)}`}
          awayDisplay={`${(away.avg_goals_for ?? 0).toFixed(2)} / ${(away.avg_goals_against ?? 0).toFixed(2)}`}
        />

        <ComparisonBar
          label="Faltas · Tarjetas p/p"
          homeVal={home.avg_cards ?? 0}
          awayVal={away.avg_cards ?? 0}
          homeDisplay={`${home.avg_fouls != null ? home.avg_fouls.toFixed(1) : '—'} · ${(home.avg_cards ?? 0).toFixed(1)}`}
          awayDisplay={`${away.avg_fouls != null ? away.avg_fouls.toFixed(1) : '—'} · ${(away.avg_cards ?? 0).toFixed(1)}`}
        />
      </div>

      <div className="v5-comp-badges">
        <FormPills teamName={match?.home_team || 'Local'} results={home.form_last_5} />
        <FormPills teamName={match?.away_team || 'Visita'} results={away.form_last_5} />

        {(home.rest_days != null || away.rest_days != null) && (
          <span className="v5-meta-chip mono">
            <Clock size={12} color="var(--azure)" />
            <span>
              Descanso: {home.rest_days != null ? `${home.rest_days}d` : '—'} vs{' '}
              {away.rest_days != null ? `${away.rest_days}d` : '—'}
            </span>
          </span>
        )}

        {referee?.name && (
          <span className="v5-meta-chip">
            <UserCheck size={12} color="var(--amber)" />
            <span>
              Árbitro: <strong>{referee.name}</strong>
              {referee.avg_cards != null ? ` (${referee.avg_cards.toFixed(1)} tarj/p)` : ''}
            </span>
          </span>
        )}

        {h2h && h2h.total_matches > 0 && (
          <span className="v5-meta-chip mono">
            <Swords size={12} color="var(--cyan)" />
            <span>
              H2H ({h2h.total_matches}): {h2h.home_wins}V-{h2h.draws}E-{h2h.away_wins}D
              {h2h.avg_goals != null ? ` · ${h2h.avg_goals} goles` : ''}
            </span>
          </span>
        )}

        {(absencesHome.length > 0 || absencesAway.length > 0) && (
          <span className="v5-meta-chip" style={{ borderColor: 'rgba(244, 63, 94, 0.4)' }}>
            <AlertTriangle size={12} color="var(--red)" />
            <span>
              Bajas: {absencesHome.length} {match?.home_team} / {absencesAway.length} {match?.away_team}
            </span>
          </span>
        )}
      </div>
    </section>
  );
}

