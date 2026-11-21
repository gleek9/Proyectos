import React, { useState, useEffect, useRef } from 'react';
import { Play, Loader2, ArrowLeftRight, Sun, Moon } from 'lucide-react';

function TeamAutocompleteInput({
  id,
  label,
  tagClass,
  placeholder,
  value,
  onChangeValue,
  onClearUrl,
  matchUrl,
  disabled,
}) {
  const [suggestions, setSuggestions] = useState([]);
  const [open, setOpen] = useState(false);
  const wrapRef = useRef(null);

  useEffect(() => {
    const handleClickOutside = (ev) => {
      if (wrapRef.current && !wrapRef.current.contains(ev.target)) {
        setOpen(false);
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const trimmedQuery = (value || '').trim();

  useEffect(() => {
    if (!open || trimmedQuery.length < 2) {
      return undefined;
    }
    const timer = setTimeout(async () => {
      try {
        let res = await fetch(`/api/teams/search?q=${encodeURIComponent(trimmedQuery)}&limit=10`);
        if (res.status === 502 || res.status === 503 || res.status === 504) {
          res = await fetch(`http://127.0.0.1:8000/api/teams/search?q=${encodeURIComponent(trimmedQuery)}&limit=10`);
        }
        if (res.ok) {
          const data = await res.json();
          setSuggestions(data.teams || []);
        }
      } catch {
        setSuggestions([]);
      }
    }, 160);
    return () => clearTimeout(timer);
  }, [trimmedQuery, open]);

  const visibleSuggestions = open && trimmedQuery.length >= 2 ? suggestions : [];

  return (
    <div className="v5-team-input-wrap" ref={wrapRef}>
      <div className="input-group">
        <span className={`input-label-tag ${tagClass}`}>{label}</span>
        <input
          id={id}
          className="input-field"
          type="text"
          placeholder={placeholder}
          value={value}
          onFocus={() => setOpen(true)}
          onChange={(e) => {
            if (matchUrl && onClearUrl) onClearUrl();
            onChangeValue(e.target.value);
            setOpen(true);
          }}
          disabled={disabled}
          autoComplete="off"
        />
      </div>

      {visibleSuggestions.length > 0 && (
        <div className="v5-autocomplete-menu" role="listbox">
          {visibleSuggestions.map((team) => (
            <button
              key={`${team.league_code}-${team.name}`}
              type="button"
              className="v5-autocomplete-item"
              onMouseDown={(ev) => {
                ev.preventDefault();
                if (matchUrl && onClearUrl) onClearUrl();
                onChangeValue(team.name);
                setOpen(false);
              }}
            >
              <div className="v5-autocomplete-left">
                <span className="v5-autocomplete-name">{team.name}</span>
                <span className="v5-autocomplete-league">{team.league_name}</span>
              </div>
              <div className="v5-autocomplete-badges">
                {team.is_women && <span className="v5-women-badge">F</span>}
                <span className="v5-elo-badge">Elo {Math.round(team.elo_rating)}</span>
              </div>
            </button>
          ))}
        </div>
      )}
    </div>
  );
}

export default function HeaderBar({
  homeTeam,
  setHomeTeam,
  awayTeam,
  setAwayTeam,
  onSwapTeams,
  onRunAnalysis,
  onForceLiveSync,
  loading,
  syncingLive,
  isLive,
  syncCountdown,
  matchUrl,
  onClearUrl,
  healthInfo,
  theme,
  onToggleTheme,
}) {
  const hasTeams = Boolean(homeTeam && awayTeam && homeTeam.trim() && awayTeam.trim());
  const hasUrl = Boolean(matchUrl && matchUrl.trim());
  const canAnalyze = !loading && (hasTeams || hasUrl);
  const versionBadge = healthInfo?.version ? `v${healthInfo.version.split('.').slice(0, 2).join('.')}` : 'v5.0';

  const handleSubmit = (e) => {
    e.preventDefault();
    if (canAnalyze) {
      onRunAnalysis();
    }
  };

  const formatCountdown = (secs) => {
    if (secs === null || secs === undefined) return '5:00';
    const m = Math.floor(secs / 60);
    const s = secs % 60;
    return `${m}:${s < 10 ? '0' : ''}${s}`;
  };

  const handleHomeChange = (val) => {
    const separatorRegex = /\s+(?:vs\.?|v\.?|-|\/)\s+/i;
    if (separatorRegex.test(val)) {
      const parts = val.split(separatorRegex);
      if (parts.length >= 2) {
        setHomeTeam(parts[0].trim());
        setAwayTeam(parts[1].trim());
        return;
      }
    }
    setHomeTeam(val);
  };

  return (
    <header className="ide-navbar">
      <div className="navbar-brand-group">
        <div
          id="katakuri-brand-indicator"
          className={`ide-brand-clickable ${isLive ? 'is-live' : 'not-live'}`}
          title={
            isLive
              ? 'Modo en vivo activo: auto-sincronización cada 5 minutos'
              : 'Katakuri · Analista Deportivo'
          }
        >
          <span className="brand-title">Katakuri {versionBadge}</span>
          <span className="brand-sub"> · Analista</span>
        </div>

        <button
          type="button"
          className="v5-theme-btn"
          onClick={onToggleTheme}
          title={theme === 'light' ? 'Cambiar a tema oscuro (Warm Stealth)' : 'Cambiar a tema claro'}
          aria-label="Cambiar tema"
        >
          {theme === 'light' ? <Moon size={15} /> : <Sun size={15} />}
        </button>

        {isLive && (
          <>
            <div className="navbar-divider" />
            <div className="telemetry-status">
              <div
                className="sync-timer-compact"
                onClick={() => {
                  if (onForceLiveSync && !loading && !syncingLive) {
                    onForceLiveSync();
                  }
                }}
                style={{ cursor: !loading && !syncingLive ? 'pointer' : 'default' }}
                title="Sincronización automática cada 5 min (haz clic para refrescar ahora)"
              >
                <span className={`dot-status ${loading || syncingLive ? 'busy' : ''}`}></span>
                <span className="sync-compact-time">
                  {syncingLive ? 'Sync...' : formatCountdown(syncCountdown)}
                </span>
              </div>
            </div>
          </>
        )}
      </div>

      <form className="ide-inputs-form" onSubmit={handleSubmit}>
        <div className="v5-matchup-pill">
          <TeamAutocompleteInput
            id="home-team-input"
            label="Local"
            tagClass="home"
            placeholder="Ej: Real Madrid"
            value={homeTeam}
            onChangeValue={handleHomeChange}
            onClearUrl={onClearUrl}
            matchUrl={matchUrl}
            disabled={loading}
          />

          <button
            type="button"
            className="v5-swap-btn"
            onClick={() => onSwapTeams && onSwapTeams()}
            disabled={loading}
            title="Intercambiar Local y Visitante"
            aria-label="Intercambiar equipos"
          >
            <ArrowLeftRight size={13} />
          </button>

          <TeamAutocompleteInput
            id="away-team-input"
            label="Visita"
            tagClass="away"
            placeholder="Ej: Barcelona"
            value={awayTeam}
            onChangeValue={setAwayTeam}
            onClearUrl={onClearUrl}
            matchUrl={matchUrl}
            disabled={loading}
          />
        </div>

        <button
          id="run-analysis-btn"
          type="submit"
          className={`btn-run ${loading ? 'is-loading' : ''}`}
          disabled={!canAnalyze}
          title="Iniciar análisis y predicción"
        >
          {loading ? (
            <>
              <Loader2 className="spin-icon" size={14} />
              <span>Analizando...</span>
            </>
          ) : (
            <>
              <Play size={13} fill="currentColor" />
              <span>Analizar</span>
            </>
          )}
        </button>
      </form>
    </header>
  );
}
