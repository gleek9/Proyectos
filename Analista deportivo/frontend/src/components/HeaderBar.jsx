import React from 'react';
import { Play, Loader2 } from 'lucide-react';

export default function HeaderBar({
  homeTeam,
  setHomeTeam,
  awayTeam,
  setAwayTeam,
  onRunAnalysis,
  onForceLiveSync,
  loading,
  syncingLive,
  isLive,
  syncCountdown,
  matchUrl,
  onClearUrl,
  onOpenBacktest
}) {
  const hasTeams = Boolean(homeTeam && awayTeam && homeTeam.trim() && awayTeam.trim());
  const hasUrl = Boolean(matchUrl && matchUrl.trim());
  const canAnalyze = !loading && (hasTeams || hasUrl);

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

  // Detección automática si el usuario pega o escribe "EquipoA vs EquipoB" o "EquipoA - EquipoB"
  const handleTeamChange = (e) => {
    if (matchUrl && onClearUrl) {
      onClearUrl();
    }
    const val = e.target.value;
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
      {/* Grupo izquierdo: Identidad de Marca y Telemetría de Modelo */}
      <div className="navbar-brand-group">
        <div
          id="katakuri-brand-indicator"
          className={`ide-brand-clickable ${isLive ? 'is-live' : 'not-live'}`}
          title={
            isLive
              ? 'Modo en vivo activo: rastreando URL online y auto-sincronizando cada 5 minutos'
              : 'Modo pre-partido estándar: agrega una URL para activar telemetría en vivo'
          }
        >
          <span className="brand-title">Katakuri v4.1</span>
          <span className="brand-sub"> · Analista Deportivo</span>
        </div>

        <div className="navbar-divider" />

        <div className="telemetry-status">
          {/* Indicador de Auto-Sincronización Cada 5 Minutos */}
          <div
            className="sync-timer-compact"
            onClick={() => {
              if (onForceLiveSync && isLive && !loading && !syncingLive) {
                onForceLiveSync();
              }
            }}
            style={{ cursor: isLive && !loading && !syncingLive ? 'pointer' : 'default' }}
            title={
              isLive
                ? 'Sincronización automática cada 5 min activa (Haz clic para refrescar telemetría en vivo ahora)'
                : 'Sincronización automática cada 5 min (activa al ingresar URL de partido en directo)'
            }
          >
            <span className={`dot-status ${loading || syncingLive ? 'busy' : ''}`}></span>
            <span className="sync-compact-time">
              {syncingLive ? 'Sync...' : formatCountdown(syncCountdown)}
            </span>
          </div>

          {/* Botón de Calibración / Backtest */}
          {onOpenBacktest && (
            <button
              type="button"
              className="btn-backtest-trigger"
              onClick={onOpenBacktest}
              title="Abrir panel de validación empírica y calibración de modelos (RPS, Brier, Log-Loss)"
            >
              <span className="dot-backtest-pill"></span>
              <span>Calibración</span>
            </button>
          )}
        </div>
      </div>

      {/* Grupo derecho: Formulario de comandos y análisis */}
      <form className="ide-inputs-form" onSubmit={handleSubmit}>
        <div className="input-group">
          <span className="input-label-tag home">Local</span>
          <input
            id="home-team-input"
            className="input-field"
            type="text"
            placeholder="Ej: Real Madrid"
            value={homeTeam}
            onChange={handleTeamChange}
            disabled={loading}
          />
        </div>

        <span className="vs-badge">vs</span>

        <div className="input-group">
          <span className="input-label-tag away">Visitante</span>
          <input
            id="away-team-input"
            className="input-field"
            type="text"
            placeholder="Ej: Barcelona"
            value={awayTeam}
            onChange={(e) => {
              if (matchUrl && onClearUrl) onClearUrl();
              setAwayTeam(e.target.value);
            }}
            disabled={loading}
          />
        </div>

        <button
          id="run-analysis-btn"
          type="submit"
          className={`btn-run ${loading ? 'is-loading' : ''}`}
          disabled={!canAnalyze}
          title="Iniciar pipeline de análisis y predicción"
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
