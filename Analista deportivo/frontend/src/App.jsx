import React, { useState, useEffect, useRef, useCallback } from 'react';
import './styles/ide-theme.css';

import HeaderBar from './components/HeaderBar';
import WinnerCard from './components/WinnerCard';
import LiveNeuralSection from './components/LiveNeuralSection';
import NeuralUrlCard from './components/NeuralUrlCard';
import MetricCards from './components/MetricCards';
import DistributionChart from './components/DistributionChart';

import { Terminal, AlertCircle } from 'lucide-react';

const API_BASE = '';
const SYNC_INTERVAL_SECONDS = 300; // 5 minutos exactos

async function fetchJsonWithFallback(path, options) {
  let res;
  try {
    res = await fetch(`${API_BASE}${path}`, options);
  } catch {
    res = await fetch(`http://127.0.0.1:8000${path}`, options);
  }
  if (res && (res.status === 502 || res.status === 503 || res.status === 504)) {
    await new Promise((r) => setTimeout(r, 900));
    res = await fetch(`http://127.0.0.1:8000${path}`, options).catch(() => res);
  }
  return res;
}

export default function App() {
  const [homeTeam, setHomeTeam] = useState('');
  const [awayTeam, setAwayTeam] = useState('');

  // Modo En Vivo se activa ÚNICAMENTE mediante la presencia de matchUrl
  const [matchUrl, setMatchUrl] = useState(() => localStorage.getItem('katakuri_match_url') || '');
  const isLiveActive = Boolean(matchUrl && matchUrl.trim());

  const [loading, setLoading] = useState(false);
  const [syncingLive, setSyncingLive] = useState(false);
  const [error, setError] = useState(null);
  const [predictionData, setPredictionData] = useState(null);
  const [syncCountdown, setSyncCountdown] = useState(SYNC_INTERVAL_SECONDS);
  const [healthInfo, setHealthInfo] = useState(null);
  const [theme, setTheme] = useState(() => localStorage.getItem('katakuri_theme') || 'dark');

  useEffect(() => {
    document.documentElement.setAttribute('data-theme', theme);
    localStorage.setItem('katakuri_theme', theme);
  }, [theme]);

  const toggleTheme = useCallback(() => {
    setTheme((prev) => (prev === 'light' ? 'dark' : 'light'));
  }, []);

  const countdownIntervalRef = useRef(null);
  const nextSyncDeadlineRef = useRef(null);
  const isSyncingRef = useRef(false);

  useEffect(() => {
    let active = true;
    (async () => {
      try {
        const res = await fetchJsonWithFallback('/api/health');
        if (active && res.ok) {
          const data = await res.json();
          setHealthInfo(data);
        }
      } catch {
        // Silencioso en caso de arranque inicial
      }
    })();
    return () => {
      active = false;
    };
  }, []);

  const extractTeamsFromUrl = (url) => {
    if (!url) return null;
    try {
      const clean = url.trim().toLowerCase();
      const slugMatch = clean.match(/(?:partido|match|football|game|encuentro)\/([a-z0-9-]+?)(?:\/|$|\?)/i) ||
                        clean.match(/sofascore\.com\/(?:[a-z]{2}\/)?([a-z0-9-]+?)(?:\/[a-zA-Z0-9]+|\/|$)/i);
      const slug = slugMatch ? slugMatch[1] : '';
      if (slug && slug.includes('-')) {
        let parts = [];
        if (slug.includes('-vs-')) {
          parts = slug.split('-vs-');
        } else if (slug.includes('-v-')) {
          parts = slug.split('-v-');
        } else {
          let raw = slug.split('-');
          if (raw.length > 2 && /^\d+$/.test(raw[raw.length - 1])) {
            raw = raw.slice(0, -1);
          }
          if (raw.length === 2) {
            parts = raw;
          } else if (raw.length > 2) {
            const mid = Math.ceil(raw.length / 2);
            parts = [raw.slice(0, mid).join(' '), raw.slice(mid).join(' ')];
          }
        }
        if (parts.length >= 2) {
          const formatWord = (s) => s.replace(/[-_]+/g, ' ')
            .split(' ')
            .filter(Boolean)
            .map((w) => w.charAt(0).toUpperCase() + w.slice(1))
            .join(' ');
          const homeParsed = formatWord(parts[0]);
          const awayParsed = formatWord(parts[1]);
          if (homeParsed && awayParsed) {
            return { home: homeParsed, away: awayParsed };
          }
        }
      }
    } catch {
      // Ignorar si no se puede parsear
    }
    return null;
  };

  const handleUrlChange = (url) => {
    setMatchUrl(url);
    if (url && url.trim()) {
      localStorage.setItem('katakuri_match_url', url.trim());
      const extracted = extractTeamsFromUrl(url.trim());
      if (extracted) {
        setHomeTeam(extracted.home);
        setAwayTeam(extracted.away);
      }
    } else {
      localStorage.removeItem('katakuri_match_url');
    }
  };

  const handleClearUrl = useCallback(() => {
    setMatchUrl('');
    localStorage.removeItem('katakuri_match_url');
    setSyncCountdown(SYNC_INTERVAL_SECONDS);
    nextSyncDeadlineRef.current = null;
    if (countdownIntervalRef.current) {
      clearInterval(countdownIntervalRef.current);
      countdownIntervalRef.current = null;
    }
    setPredictionData((prev) => {
      if (!prev || !prev.match) return prev;
      return {
        ...prev,
        match: {
          ...prev.match,
          match_url: null,
          is_live: false,
          live_score: null,
          live_minute: null,
          live_corners: null
        }
      };
    });
  }, []);

  const handleSwapTeams = useCallback(() => {
    if (matchUrl) {
      handleClearUrl();
    }
    setHomeTeam((prevH) => {
      const prevA = awayTeam;
      setAwayTeam(prevH);
      return prevA;
    });
  }, [awayTeam, matchUrl, handleClearUrl]);

  const runAnalysis = useCallback(async (
    targetHome = homeTeam,
    targetAway = awayTeam,
    force = true,
    customMatchUrl = matchUrl,
    isBackgroundSync = false
  ) => {
    if (isSyncingRef.current && isBackgroundSync) return;

    const activeUrl = customMatchUrl !== undefined ? customMatchUrl : matchUrl;
    const trimmedUrl = activeUrl ? activeUrl.trim() : '';

    let cleanHome = (targetHome || '').trim();
    let cleanAway = (targetAway || '').trim();

    if (trimmedUrl && (!isBackgroundSync || !cleanHome || !cleanAway)) {
      const urlTeams = extractTeamsFromUrl(trimmedUrl);
      if (urlTeams) {
        cleanHome = urlTeams.home;
        cleanAway = urlTeams.away;
        setHomeTeam(urlTeams.home);
        setAwayTeam(urlTeams.away);
      }
    }

    if ((!cleanHome || !cleanAway) && !trimmedUrl) return;

    const isLive = Boolean(trimmedUrl);

    if (!isBackgroundSync && predictionData && (
      (trimmedUrl && predictionData.match?.match_url && trimmedUrl !== predictionData.match.match_url) ||
      (!trimmedUrl && (
        cleanHome.toLowerCase() !== (predictionData.match?.home_team || '').toLowerCase() ||
        cleanAway.toLowerCase() !== (predictionData.match?.away_team || '').toLowerCase()
      ))
    )) {
      setPredictionData(null);
    }

    isSyncingRef.current = true;
    if (isBackgroundSync) {
      setSyncingLive(true);
    } else {
      setLoading(true);
      setError(null);
    }

    const payload = {
      home_team: cleanHome || '',
      away_team: cleanAway || '',
      competition: predictionData?.match?.competition || 'General',
      force_refresh: force,
      is_live: isLive,
      match_url: trimmedUrl || '',
    };

    try {
      const res = await fetchJsonWithFallback('/api/predict', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Cache-Control': 'no-cache'
        },
        body: JSON.stringify(payload)
      });

      if (!res.ok) {
        const errJson = await res.json().catch(() => ({}));
        let errMsg = '';
        if (Array.isArray(errJson.detail)) {
          errMsg = errJson.detail.map((d) => (typeof d === 'object' ? (d.msg || JSON.stringify(d)) : String(d))).join('; ');
        } else if (errJson.detail && typeof errJson.detail === 'object') {
          errMsg = JSON.stringify(errJson.detail);
        } else if (errJson.detail) {
          errMsg = String(errJson.detail);
        } else if (res.status === 502 || res.status === 503 || res.status === 504) {
          errMsg = `Error de conexión con el backend (HTTP ${res.status}). El servidor FastAPI en http://127.0.0.1:8000 se está iniciando o no está disponible.`;
        } else {
          errMsg = `Error en el servidor: HTTP ${res.status}`;
        }
        throw new Error(errMsg);
      }

      const data = await res.json();
      setPredictionData(data);
      setError(null);

      if (data?.match?.home_team && data?.match?.away_team) {
        setHomeTeam(data.match.home_team);
        setAwayTeam(data.match.away_team);
      }

      if (isLive) {
        nextSyncDeadlineRef.current = Date.now() + SYNC_INTERVAL_SECONDS * 1000;
        setSyncCountdown(SYNC_INTERVAL_SECONDS);
      }
    } catch (err) {
      if (isBackgroundSync && predictionData) {
        nextSyncDeadlineRef.current = Date.now() + 30 * 1000;
        setSyncCountdown(30);
      } else if (err.message === 'Failed to fetch') {
        setError('No se pudo establecer conexión con el servidor backend (http://127.0.0.1:8000). Comprueba que el servidor esté activo.');
      } else {
        setError(err.message || 'Error conectando con el motor predictivo.');
      }
    } finally {
      isSyncingRef.current = false;
      setLoading(false);
      setSyncingLive(false);
    }
  }, [homeTeam, awayTeam, matchUrl, predictionData]);

  const hasPrediction = Boolean(predictionData);
  const homeCurrent = predictionData?.match?.home_team || homeTeam;
  const awayCurrent = predictionData?.match?.away_team || awayTeam;

  useEffect(() => {
    if (!isLiveActive || !hasPrediction) {
      if (countdownIntervalRef.current) {
        clearInterval(countdownIntervalRef.current);
        countdownIntervalRef.current = null;
      }
      nextSyncDeadlineRef.current = null;
      return undefined;
    }

    if (!nextSyncDeadlineRef.current) {
      nextSyncDeadlineRef.current = Date.now() + SYNC_INTERVAL_SECONDS * 1000;
    }

    const checkAndTick = () => {
      if (!nextSyncDeadlineRef.current) return;
      const remainingMs = nextSyncDeadlineRef.current - Date.now();
      const remainingSecs = Math.max(0, Math.ceil(remainingMs / 1000));
      setSyncCountdown(remainingSecs);

      if (remainingSecs === 0 && !isSyncingRef.current) {
        nextSyncDeadlineRef.current = Date.now() + SYNC_INTERVAL_SECONDS * 1000;
        setSyncCountdown(SYNC_INTERVAL_SECONDS);
        runAnalysis(homeCurrent, awayCurrent, true, matchUrl, true);
      }
    };

    countdownIntervalRef.current = setInterval(checkAndTick, 1000);

    const handleVisibilityOrFocus = () => {
      if (document.visibilityState === 'visible') {
        checkAndTick();
      }
    };
    document.addEventListener('visibilitychange', handleVisibilityOrFocus);
    window.addEventListener('focus', handleVisibilityOrFocus);

    return () => {
      if (countdownIntervalRef.current) {
        clearInterval(countdownIntervalRef.current);
        countdownIntervalRef.current = null;
      }
      document.removeEventListener('visibilitychange', handleVisibilityOrFocus);
      window.removeEventListener('focus', handleVisibilityOrFocus);
    };
  }, [isLiveActive, hasPrediction, homeCurrent, awayCurrent, matchUrl, runAnalysis]);

  const handleForceLiveSync = useCallback(() => {
    if (isLiveActive && hasPrediction && !loading && !syncingLive) {
      nextSyncDeadlineRef.current = Date.now() + SYNC_INTERVAL_SECONDS * 1000;
      setSyncCountdown(SYNC_INTERVAL_SECONDS);
      runAnalysis(homeCurrent, awayCurrent, true, matchUrl, true);
    }
  }, [isLiveActive, hasPrediction, loading, syncingLive, homeCurrent, awayCurrent, matchUrl, runAnalysis]);

  const versionTitle = healthInfo?.version ? `v${healthInfo.version.split('.').slice(0, 2).join('.')}` : 'v5.0';

  return (
    <div className="app-container" style={{ position: 'relative' }}>
      <HeaderBar
        homeTeam={homeTeam}
        setHomeTeam={setHomeTeam}
        awayTeam={awayTeam}
        setAwayTeam={setAwayTeam}
        onSwapTeams={handleSwapTeams}
        onRunAnalysis={() => runAnalysis(homeTeam, awayTeam, true, matchUrl, false)}
        onForceLiveSync={handleForceLiveSync}
        loading={loading}
        syncingLive={syncingLive}
        isLive={isLiveActive}
        syncCountdown={predictionData ? syncCountdown : null}
        matchUrl={matchUrl}
        onClearUrl={handleClearUrl}
        healthInfo={healthInfo}
        theme={theme}
        onToggleTheme={toggleTheme}
      />

      {error && (
        <div className="error-banner">
          <AlertCircle size={18} color="var(--red)" />
          <span>[Error de ejecución]: {error}</span>
        </div>
      )}

      {/* Carga */}
      {loading && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '0.85rem' }}>
          <div className="state-box" style={{ padding: '1.25rem' }}>
            <div className="terminal-spinner"></div>
            <div className="state-title">Calculando análisis Katakuri {versionTitle}</div>
            <div className="state-sub">
              {isLiveActive
                ? 'Sincronizando telemetría en vivo...'
                : 'Generando probabilidades 1X2, goles, córners y tarjetas...'}
            </div>
          </div>
          <div className="v5-skeleton-grid">
            <div className="v5-skeleton-box" style={{ gridColumn: 'span 12', height: '140px' }} />
            <div className="v5-skeleton-box" style={{ gridColumn: 'span 4', height: '170px' }} />
            <div className="v5-skeleton-box" style={{ gridColumn: 'span 4', height: '170px' }} />
            <div className="v5-skeleton-box" style={{ gridColumn: 'span 4', height: '170px' }} />
          </div>
        </div>
      )}

      {/* Resultados Esenciales */}
      {!loading && predictionData && (
        <>
          <WinnerCard
            match={predictionData.match}
            winner={predictionData.prediction.winner}
            isLive={isLiveActive}
          />

          {isLiveActive ? (
            <LiveNeuralSection
              prediction={predictionData.prediction}
              match={predictionData.match}
              isLive={true}
              matchUrl={matchUrl}
              onUrlChange={handleUrlChange}
              onClearUrl={handleClearUrl}
              onRunAnalysis={() => runAnalysis(homeTeam, awayTeam, true, matchUrl, false)}
              onForceLiveSync={handleForceLiveSync}
              syncingLive={syncingLive}
            />
          ) : (
            <NeuralUrlCard
              matchUrl={matchUrl}
              onUrlChange={handleUrlChange}
              onClearUrl={handleClearUrl}
              onRunAnalysis={() => runAnalysis(homeTeam, awayTeam, true, matchUrl, false)}
              isLive={false}
            />
          )}

          <MetricCards
            prediction={predictionData.prediction}
            match={predictionData.match}
            isLive={isLiveActive}
          />

          <DistributionChart chartData={predictionData.chart_data} theme={theme} />
        </>
      )}

      {/* Estado Vacío Inicial */}
      {!loading && !predictionData && !error && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '0.85rem' }}>
          <NeuralUrlCard
            matchUrl={matchUrl}
            onUrlChange={handleUrlChange}
            onClearUrl={handleClearUrl}
            onRunAnalysis={() => runAnalysis(homeTeam, awayTeam, true, matchUrl, false)}
            isLive={isLiveActive}
          />

          <div className="state-box">
            <Terminal size={30} color="var(--cyan)" />
            <div className="state-title">Katakuri {versionTitle} · Listo para analizar</div>
            <div className="state-sub">
              Selecciona Local y Visitante en la barra superior o pega la URL del partido para analizar en vivo.
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
