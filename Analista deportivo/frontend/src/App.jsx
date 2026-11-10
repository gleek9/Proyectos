import React, { useState, useEffect, useRef, useCallback } from 'react';
import './styles/ide-theme.css';

import HeaderBar from './components/HeaderBar';
import WinnerCard from './components/WinnerCard';
import LiveNeuralSection from './components/LiveNeuralSection';
import NeuralUrlCard from './components/NeuralUrlCard';
import MetricCards from './components/MetricCards';
import DistributionChart from './components/DistributionChart';
import KeyFactorsPanel from './components/KeyFactorsPanel';
import BacktestModal from './components/BacktestModal';

import { Terminal, AlertCircle } from 'lucide-react';

// Si existe proxy en Vite, las rutas relativas eliminan conflictos de IPv6 / CORS.
// Fallback a 127.0.0.1:8000 explícito para evitar problemas de resolución localhost en Windows.
const API_BASE = '';
const SYNC_INTERVAL_SECONDS = 300; // 5 minutos exactos

export default function App() {
  const [homeTeam, setHomeTeam] = useState('');
  const [awayTeam, setAwayTeam] = useState('');

  // La URL del partido en vivo guardada en localStorage.
  // Regla absoluta: Modo En Vivo se activa ÚNICAMENTE mediante la presencia de matchUrl.
  const [matchUrl, setMatchUrl] = useState(() => localStorage.getItem('katakuri_match_url') || '');
  const isLiveActive = Boolean(matchUrl && matchUrl.trim());

  const [loading, setLoading] = useState(false);
  const [syncingLive, setSyncingLive] = useState(false);
  const [error, setError] = useState(null);
  const [predictionData, setPredictionData] = useState(null);
  const [syncCountdown, setSyncCountdown] = useState(SYNC_INTERVAL_SECONDS);
  const [isBacktestOpen, setIsBacktestOpen] = useState(false);

  const countdownIntervalRef = useRef(null);
  const nextSyncDeadlineRef = useRef(null);
  const isSyncingRef = useRef(false);

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
            .map(w => w.charAt(0).toUpperCase() + w.slice(1))
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
    // Limpiar match_url del estado de predicción actual para que no re-active el modo en vivo ni restaure la URL
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

  const runAnalysis = useCallback(async (
    targetHome = homeTeam,
    targetAway = awayTeam,
    force = false,
    customMatchUrl = matchUrl,
    isBackgroundSync = false
  ) => {
    if (isSyncingRef.current && isBackgroundSync) return;

    const activeUrl = customMatchUrl !== undefined ? customMatchUrl : matchUrl;
    const trimmedUrl = activeUrl ? activeUrl.trim() : '';

    let cleanHome = (targetHome || '').trim();
    let cleanAway = (targetAway || '').trim();

    // Si hay una URL activa y no es un refresco de fondo con equipos oficiales ya resueltos, extraer equipos de la URL
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

    // Solo limpiar el dashboard si el usuario cambió manualmente a otro partido distinto (nunca en auto-sync de fondo)
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

    // Importante: Cuando hay URL en vivo (trimmedUrl), NO enviar live_score/live_minute/live_corners viejos
    // para obligar al backend a extraer el minuto, marcador y córners frescos de la URL en tiempo real.
    const payload = {
      home_team: cleanHome || '',
      away_team: cleanAway || '',
      competition: predictionData?.match?.competition || 'General',
      force_refresh: true,
      is_live: isLive,
      match_url: trimmedUrl || ''
    };

    try {
      let res;
      try {
        res = await fetch(`${API_BASE}/api/predict`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'Cache-Control': 'no-cache'
          },
          body: JSON.stringify(payload)
        });
      } catch {
        // Fallback a conexión directa si falla la petición proxy de red
        res = await fetch('http://127.0.0.1:8000/api/predict', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'Cache-Control': 'no-cache'
          },
          body: JSON.stringify(payload)
        });
      }

      // Si el proxy de desarrollo devolvió 502/503/504 (servidor iniciando o desconexión del proxy), reintentar directo
      if (res && (res.status === 502 || res.status === 503 || res.status === 504)) {
        await new Promise(r => setTimeout(r, 1200));
        res = await fetch('http://127.0.0.1:8000/api/predict', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'Cache-Control': 'no-cache'
          },
          body: JSON.stringify(payload)
        }).catch(() => res);
      }

      if (!res.ok) {
        const errJson = await res.json().catch(() => ({}));
        let errMsg = '';
        if (Array.isArray(errJson.detail)) {
          errMsg = errJson.detail.map(d => (typeof d === 'object' ? (d.msg || JSON.stringify(d)) : String(d))).join('; ');
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

      // Si la IA determinó el orden oficial de local y visitante, reflejarlo en los inputs
      if (data?.match?.home_team && data?.match?.away_team) {
        setHomeTeam(data.match.home_team);
        setAwayTeam(data.match.away_team);
      }

      // Reiniciar el reloj de 5 minutos exactos tras cada sincronización exitosa en vivo
      if (isLive) {
        nextSyncDeadlineRef.current = Date.now() + SYNC_INTERVAL_SECONDS * 1000;
        setSyncCountdown(SYNC_INTERVAL_SECONDS);
      }
    } catch (err) {
      // Si es una sincronización automática de fondo, NO cerrar ni borrar la sesión activa en pantalla;
      // programar reintento automático en 30 segundos y mantener los datos visibles.
      if (isBackgroundSync && predictionData) {
        console.warn('⚠️ Auto-Sync: Fallo temporal de red al refrescar, reintentando en 30s sin cerrar sesión:', err.message);
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

  // Temporizador de cuenta regresiva basado en reloj real (Wall-Clock Time) inmune al throttling de pestañas en segundo plano
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
      setSyncCountdown(SYNC_INTERVAL_SECONDS);
      return;
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
        // Reprogramar inmediatamente el siguiente ciclo de 5 minutos y lanzar refresco en segundo plano
        nextSyncDeadlineRef.current = Date.now() + SYNC_INTERVAL_SECONDS * 1000;
        setSyncCountdown(SYNC_INTERVAL_SECONDS);
        runAnalysis(homeCurrent, awayCurrent, true, matchUrl, true);
      }
    };

    countdownIntervalRef.current = setInterval(checkAndTick, 1000);

    // Si el usuario vuelve a la pestaña después de varios minutos, sincronizar al instante si ya venció el plazo
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

  return (
    <div className="app-container" style={{ position: 'relative' }}>
      {/* 1. Header con Controles tipo IDE Limpio e Indicador Katakuri v4.1 */}
      <HeaderBar
        homeTeam={homeTeam}
        setHomeTeam={setHomeTeam}
        awayTeam={awayTeam}
        setAwayTeam={setAwayTeam}
        onRunAnalysis={() => runAnalysis(homeTeam, awayTeam, true, matchUrl, false)}
        onForceLiveSync={() => {
          if (isLiveActive && hasPrediction && !loading && !syncingLive) {
            nextSyncDeadlineRef.current = Date.now() + SYNC_INTERVAL_SECONDS * 1000;
            setSyncCountdown(SYNC_INTERVAL_SECONDS);
            runAnalysis(homeCurrent, awayCurrent, true, matchUrl, true);
          }
        }}
        loading={loading}
        syncingLive={syncingLive}
        isLive={isLiveActive}
        syncCountdown={predictionData ? syncCountdown : null}
        matchUrl={matchUrl}
        onClearUrl={handleClearUrl}
        onOpenBacktest={() => setIsBacktestOpen(true)}
      />

      {/* 2. Banner de Error si ocurre */}
      {error && (
        <div className="error-banner">
          <AlertCircle size={18} color="var(--red)" />
          <span>[Error de ejecución]: {error}</span>
        </div>
      )}

      {/* 4. Estado de Carga Inicial */}
      {loading && (
        <div className="state-box">
          <div className="terminal-spinner"></div>
          <div className="state-title">Pipeline predictivo Katakuri v4.1</div>
          <div className="state-sub">
            {isLiveActive
              ? 'Rastreando datos en vivo desde la URL online, extrayendo telemetría y ejecutando Red Neuronal LSTM...'
              : 'Analizando partido pre-match con modelos locales Poisson Dixon-Coles, XGBoost y Red Neuronal...'}
          </div>
        </div>
      )}

      {/* 5. Dashboard Completo de Resultados (permanece montado durante auto-sync cada 5 min) */}
      {!loading && predictionData && (
        <>
          {/* Tarjeta Principal de Ganador (1X2) */}
          <WinnerCard
            match={predictionData.match}
            winner={predictionData.prediction.winner}
            isLive={isLiveActive}
          />

          {/* Sección de Red Neuronal: Si hay URL activa muestra telemetría live, si es pre-match muestra casilla para ingresar URL */}
          {isLiveActive ? (
            <LiveNeuralSection
              prediction={predictionData.prediction}
              match={predictionData.match}
              isLive={true}
              matchUrl={matchUrl}
              onUrlChange={handleUrlChange}
              onClearUrl={handleClearUrl}
              onRunAnalysis={() => runAnalysis(homeTeam, awayTeam, true, matchUrl, false)}
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

          {/* Grid de Métricas Clave (Goles, Córners, Tarjetas) */}
          <MetricCards
            prediction={predictionData.prediction}
            match={predictionData.match}
            isLive={isLiveActive}
          />

          {/* Sección Inferior: Gráficas de Distribución + Factores Clave */}
          <div className="analysis-bottom-grid">
            <DistributionChart
              chartData={predictionData.chart_data}
            />
            <KeyFactorsPanel
              factors={predictionData.key_factors}
              analyzedAt={predictionData.match.analyzed_at}
            />
          </div>
        </>
      )}

      {/* Estado Vacío Inicial si aún no hay partido analizado: Casilla de URL donde está la sección de red neuronal */}
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
            <Terminal size={32} color="var(--cyan)" />
            <div className="state-title">Katakuri · Analista Deportivo en espera</div>
            <div className="state-sub">
              Ingresa dos equipos en la barra superior para iniciar el análisis. Para activar el <strong>modo en vivo</strong>, pega la URL del partido en la casilla de arriba y presiona <strong>Analizar</strong>.
            </div>
          </div>
        </div>
      )}

      {/* 6. Modal de Validación Empírica y Calibración de Modelos */}
      <BacktestModal
        isOpen={isBacktestOpen}
        onClose={() => setIsBacktestOpen(false)}
      />
    </div>
  );
}
