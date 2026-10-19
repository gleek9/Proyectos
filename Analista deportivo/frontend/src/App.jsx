import React, { useState, useEffect, useRef } from 'react';
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
  const [error, setError] = useState(null);
  const [predictionData, setPredictionData] = useState(null);
  const [syncCountdown, setSyncCountdown] = useState(SYNC_INTERVAL_SECONDS);
  const [liveScore, setLiveScore] = useState(null);
  const [liveMinute, setLiveMinute] = useState(null);
  const [liveCorners, setLiveCorners] = useState(null);
  const [isBacktestOpen, setIsBacktestOpen] = useState(false);

  const countdownIntervalRef = useRef(null);

  const extractTeamsFromUrl = (url) => {
    if (!url) return null;
    try {
      const clean = url.trim().toLowerCase();
      const slugMatch = clean.match(/(?:partido|match)\/([a-z0-9-]+?)(?:\/|$|\?)/i) ||
                        clean.match(/sofascore\.com\/(?:[a-z]{2}\/)?([a-z0-9-]+?)(?:\/[a-zA-Z0-9]+|\/|$)/i);
      const slug = slugMatch ? slugMatch[1] : '';
      if (slug && slug.includes('-')) {
        let parts = [];
        if (slug.includes('-vs-')) {
          parts = slug.split('-vs-');
        } else {
          const raw = slug.split('-');
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

  const handleClearUrl = () => {
    setMatchUrl('');
    localStorage.removeItem('katakuri_match_url');
    setLiveScore(null);
    setLiveMinute(null);
    setLiveCorners(null);
  };

  const runAnalysis = async (
    targetHome = homeTeam,
    targetAway = awayTeam,
    force = false,
    customMatchUrl = matchUrl
  ) => {
    const activeUrl = customMatchUrl !== undefined ? customMatchUrl : matchUrl;
    let trimmedUrl = activeUrl ? activeUrl.trim() : '';

    let cleanHome = (targetHome || '').trim();
    let cleanAway = (targetAway || '').trim();

    // Si hay una URL activa, la URL manda sobre cualquier equipo ingresado previamente
    if (trimmedUrl) {
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

    // Si la URL o los equipos cambiaron respecto al análisis actual, resetear telemetría previa
    if (predictionData && (
      (trimmedUrl && trimmedUrl !== predictionData.match?.match_url) ||
      (!trimmedUrl && (cleanHome !== predictionData.match?.home_team || cleanAway !== predictionData.match?.away_team))
    )) {
      setLiveScore(null);
      setLiveMinute(null);
      setLiveCorners(null);
      setPredictionData(null);
    }

    setLoading(true);
    setError(null);

    const payload = {
      home_team: cleanHome || '',
      away_team: cleanAway || '',
      competition: 'General',
      force_refresh: force || isLive,
      is_live: isLive,
      match_url: trimmedUrl || ''
    };

    if (isLive) {
      if (liveScore) payload.live_score = liveScore;
      if (liveMinute) payload.live_minute = liveMinute;
      if (liveCorners !== null && liveCorners !== undefined) {
        payload.live_corners = liveCorners;
      }
    }

    try {
      let res;
      try {
        res = await fetch(`${API_BASE}/api/predict`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(payload)
        });
      } catch {
        // Fallback a conexión directa si falla la petición proxy de red
        res = await fetch('http://127.0.0.1:8000/api/predict', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(payload)
        });
      }

      // Si el proxy de desarrollo devolvió 502/503/504 (servidor iniciando o desconexión del proxy), reintentar directo
      if (res && (res.status === 502 || res.status === 503 || res.status === 504)) {
        await new Promise(r => setTimeout(r, 1200));
        res = await fetch('http://127.0.0.1:8000/api/predict', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
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

      // Si la IA determinó el orden oficial de local y visitante, reflejarlo en los inputs
      if (data?.match?.home_team && data?.match?.away_team) {
        setHomeTeam(data.match.home_team);
        setAwayTeam(data.match.away_team);
      }

      // Sincronizar marcador y estado devuelto
      if (data?.match) {
        if (data.match.live_score) {
          setLiveScore(data.match.live_score);
        }
        if (data.match.live_minute) {
          setLiveMinute(data.match.live_minute);
        }
        if (data.match.live_corners !== undefined && data.match.live_corners !== null) {
          setLiveCorners(data.match.live_corners);
        } else if (data.prediction?.corners?.current_corners !== undefined) {
          setLiveCorners(data.prediction.corners.current_corners);
        }
      }
    } catch (err) {
      if (err.message === 'Failed to fetch') {
        setError('No se pudo establecer conexión con el servidor backend (http://127.0.0.1:8000). Comprueba que el servidor esté activo.');
      } else {
        setError(err.message || 'Error conectando con el motor predictivo.');
      }
    } finally {
      setLoading(false);
    }
  };

  // Sincronizar telemetría y nombres oficiales devueltos por el backend
  useEffect(() => {
    if (predictionData?.match) {
      if (predictionData.match.home_team) {
        setHomeTeam(predictionData.match.home_team);
      }
      if (predictionData.match.away_team) {
        setAwayTeam(predictionData.match.away_team);
      }
      if (predictionData.match.match_url && !matchUrl) {
        setMatchUrl(predictionData.match.match_url);
        localStorage.setItem('katakuri_match_url', predictionData.match.match_url);
      }
      if (predictionData.match.live_score) setLiveScore(predictionData.match.live_score);
      if (predictionData.match.live_minute) setLiveMinute(predictionData.match.live_minute);
      if (predictionData.match.live_corners !== undefined && predictionData.match.live_corners !== null) {
        setLiveCorners(predictionData.match.live_corners);
      } else if (predictionData.prediction?.corners?.current_corners !== undefined) {
        setLiveCorners(predictionData.prediction.corners.current_corners);
      }
    }
  }, [predictionData, matchUrl]);

  // Temporizador de cuenta regresiva para Auto-Sync (1 segundo por tick, solo en vivo)
  useEffect(() => {
    if (!isLiveActive || !predictionData) {
      if (countdownIntervalRef.current) clearInterval(countdownIntervalRef.current);
      setSyncCountdown(SYNC_INTERVAL_SECONDS);
      return;
    }

    if (countdownIntervalRef.current) clearInterval(countdownIntervalRef.current);

    countdownIntervalRef.current = setInterval(() => {
      setSyncCountdown((prev) => (prev <= 1 ? 0 : prev - 1));
    }, 1000);

    return () => {
      if (countdownIntervalRef.current) {
        clearInterval(countdownIntervalRef.current);
      }
    };
  }, [isLiveActive, predictionData]);

  // Disparar sincronización automática cuando el contador llega a 0 (solo en vivo)
  const homeCurrent = predictionData?.match?.home_team;
  const awayCurrent = predictionData?.match?.away_team;
  useEffect(() => {
    if (syncCountdown === 0 && isLiveActive && homeCurrent && awayCurrent && !loading) {
      console.log('⏰ Auto-Sync: 5 minutos cumplidos. Refrescando datos en vivo desde la URL online...');
      setSyncCountdown(SYNC_INTERVAL_SECONDS);
      runAnalysis(homeCurrent, awayCurrent, true, matchUrl);
    }
  }, [syncCountdown, isLiveActive, homeCurrent, awayCurrent, loading, matchUrl]);

  return (
    <div className="app-container" style={{ position: 'relative' }}>
      {/* 1. Header con Controles tipo IDE Limpio e Indicador Katakuri v3.5 */}
      <HeaderBar
        homeTeam={homeTeam}
        setHomeTeam={setHomeTeam}
        awayTeam={awayTeam}
        setAwayTeam={setAwayTeam}
        onRunAnalysis={() => runAnalysis(homeTeam, awayTeam, true)}
        loading={loading}
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

      {/* 4. Estado de Carga / Inferencia */}
      {loading && (
        <div className="state-box">
          <div className="terminal-spinner"></div>
          <div className="state-title">Pipeline predictivo Katakuri v3.5</div>
          <div className="state-sub">
            {isLiveActive
              ? 'Rastreando datos en vivo desde la URL online, extrayendo telemetría y ejecutando Red Neuronal LSTM...'
              : 'Analizando partido pre-match con modelos locales Poisson Dixon-Coles, XGBoost y Red Neuronal...'}
          </div>
        </div>
      )}

      {/* 5. Dashboard Completo de Resultados */}
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
              onRunAnalysis={() => runAnalysis(homeTeam, awayTeam, true)}
            />
          ) : (
            <NeuralUrlCard
              matchUrl={matchUrl}
              onUrlChange={handleUrlChange}
              onClearUrl={handleClearUrl}
              onRunAnalysis={() => runAnalysis(homeTeam, awayTeam, true)}
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
            onRunAnalysis={() => runAnalysis(homeTeam, awayTeam, true)}
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
