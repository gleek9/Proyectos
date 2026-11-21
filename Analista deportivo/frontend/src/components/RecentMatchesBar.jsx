import React from 'react';
import { History } from 'lucide-react';

export default function RecentMatchesBar({
  matches = [],
  onSelectMatch,
  activeHome = '',
  activeAway = '',
}) {
  if (!matches || matches.length === 0) return null;

  return (
    <div className="v5-recent-bar" aria-label="Partidos analizados recientemente">
      <span className="v5-recent-label">
        <History size={13} color="var(--cyan)" />
        <span>Recientes</span>
      </span>

      <div className="v5-recent-chips">
        {matches.map((item) => {
          const isActive =
            activeHome &&
            activeAway &&
            item.home_team?.toLowerCase() === activeHome.trim().toLowerCase() &&
            item.away_team?.toLowerCase() === activeAway.trim().toLowerCase();

          return (
            <button
              key={item.id || `${item.home_team}-${item.away_team}`}
              type="button"
              className={`v5-recent-chip ${isActive ? 'is-active' : ''}`}
              onClick={() => onSelectMatch && onSelectMatch(item)}
              title={`Cargar análisis: ${item.home_team} vs ${item.away_team}`}
            >
              <span>
                {item.home_team} <strong>vs</strong> {item.away_team}
              </span>
              {item.competition && (
                <span className="v5-recent-chip-league">{item.competition}</span>
              )}
            </button>
          );
        })}
      </div>
    </div>
  );
}

