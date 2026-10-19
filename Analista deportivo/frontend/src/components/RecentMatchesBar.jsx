import React from 'react';
import { History } from 'lucide-react';

export default function RecentMatchesBar({ recentList, onSelectMatch, currentMatch }) {
  const defaultPresets = [
    { home: 'Real Madrid', away: 'FC Barcelona', comp: 'LaLiga' },
    { home: 'Manchester City', away: 'Liverpool', comp: 'Premier League' },
    { home: 'Arsenal', away: 'Chelsea', comp: 'Premier League' },
    { home: 'Bayern München', away: 'Borussia Dortmund', comp: 'Bundesliga' },
  ];

  // Si hay registros en SQLite, mostrarlos primero
  const items = recentList && recentList.length > 0
    ? recentList.map(r => ({
        home: r.home_team,
        away: r.away_team,
        comp: r.competition,
        is_live: r.is_live,
        live_score: r.live_score,
        match_url: r.match_url
      }))
    : defaultPresets;

  return (
    <div className="recent-bar">
      <span className="recent-label">
        <History size={13} color="var(--azure)" />
        <span>Historial y sugeridos:</span>
      </span>

      {items.map((m, idx) => {
        const isActive = currentMatch &&
          currentMatch.home_team?.toLowerCase() === m.home?.toLowerCase() &&
          currentMatch.away_team?.toLowerCase() === m.away?.toLowerCase();

        return (
          <button
            key={idx}
            type="button"
            className={`recent-chip ${isActive ? 'active' : ''}`}
            onClick={() => onSelectMatch(m.home, m.away, m.comp, m.is_live, m.live_score, m.match_url)}
          >
            {m.is_live && <span className="pulse-dot-red" style={{ marginRight: '6px' }}></span>}
            {m.home} <span style={{ color: 'var(--text-muted)' }}>vs</span> {m.away}
            {m.live_score && <span style={{ color: 'var(--crimson)', marginLeft: '6px', fontWeight: 700 }}>[{m.live_score}]</span>}
          </button>
        );
      })}
    </div>
  );
}
