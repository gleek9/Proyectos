import React from 'react';
import { Play, Loader2, User, LogOut } from 'lucide-react';

export default function HeaderBar({
  homeTeam,
  setHomeTeam,
  awayTeam,
  setAwayTeam,
  onRunAnalysis,
  loading,
  currentUser,
  onLogout,
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
      {/* Indicador Katakuri v3.3 con estado en vivo y pre-partido */}
      <div
        id="katakuri-brand-indicator"
        className={`ide-brand-clickable ${isLive ? 'is-live' : 'not-live'}`}
        style={{ cursor: 'default', userSelect: 'none' }}
        title={
          isLive
            ? 'Modo en vivo activo: rastreando URL online y auto-sincronizando cada 5 minutos'
            : 'Modo pre-partido estándar: agrega una URL para activar telemetría en vivo'
        }
      >
        <span className="brand-title">Katakuri v3.3</span>
        <span className="brand-sub"> · Analista Deportivo</span>
      </div>

      <div className="telemetry-status" style={{ display: 'flex', alignItems: 'center', gap: '0.65rem' }}>
        {/* Indicador de Auto-Sincronización Cada 5 Minutos */}
        <div
          className="sync-timer-compact"
          title="Sincronización automática cada 5 min (Búsqueda web con IA + Modelos predictivos locales Dixon-Coles, XGBoost y LSTM)"
        >
          <span className={`dot-status ${loading ? 'busy' : ''}`}></span>
          <span className="sync-compact-time">{formatCountdown(syncCountdown)}</span>
        </div>

        {/* Botón de Calibración / Backtest */}
        {onOpenBacktest && (
          <button
            type="button"
            className="btn-backtest-trigger"
            onClick={onOpenBacktest}
            title="Abrir panel de validación empírica y calibración de modelos (RPS, Brier, Log-Loss)"
          >
            <span style={{ display: 'inline-block', width: 6, height: 6, borderRadius: '50%', background: 'var(--emerald)' }}></span>
            <span>Calibración</span>
          </button>
        )}
      </div>

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
            style={{ width: '165px' }}
          />
        </div>

        <span style={{ color: 'var(--text-muted)', fontFamily: 'var(--font-mono)', fontSize: '0.8rem' }}>vs</span>

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
            style={{ width: '165px' }}
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

        {currentUser && (
          <div style={{
            display: 'flex',
            alignItems: 'center',
            gap: '0.45rem',
            marginLeft: '0.4rem',
            paddingLeft: '0.55rem',
            borderLeft: '1px solid var(--border-dim)'
          }}>
            <span style={{
              display: 'flex',
              alignItems: 'center',
              gap: '0.3rem',
              fontFamily: 'var(--font-mono)',
              fontSize: '0.75rem',
              color: 'var(--text-secondary)'
            }}>
              <User size={13} color="var(--cyan)" />
              {currentUser}
            </span>
            <button
              type="button"
              onClick={onLogout}
              title="Cerrar sesión"
              style={{
                background: 'transparent',
                border: 'none',
                color: 'var(--text-dim)',
                cursor: 'pointer',
                display: 'flex',
                alignItems: 'center',
                padding: '0.2rem'
              }}
            >
              <LogOut size={13} />
            </button>
          </div>
        )}
      </form>
    </header>
  );
}
