"""
Katakuri AI — Servidor API Principal (FastAPI).
Puntos de entrada REST para predicción deportiva, orquestación de modelos locales y caché en SQLite.
"""
import logging
from datetime import datetime, timedelta
from typing import List, Optional
from fastapi import FastAPI, HTTPException, Depends, Query
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from sqlalchemy import or_, and_
from contextlib import asynccontextmanager

from backend.app.config import settings
from backend.app.db import init_db, get_db, MatchPrediction
from backend.app.schemas.prediction import PredictRequest, PredictionResponse
from backend.app.schemas.match import MatchRawFeatures
from backend.app.agent.collector import collector
from backend.app.models.ensemble import ensemble_engine

# Configuración de logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("katakuri.api")

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Inicialización de la base de datos SQLite y carga de modelos locales."""
    logger.info("Iniciando Katakuri AI API Server...")
    init_db()
    logger.info("Base de datos SQLite verificada y lista.")
    yield
    logger.info("Apagando Katakuri AI API Server...")

app = FastAPI(
    title="Katakuri AI - Plataforma de Predicción Deportiva",
    description="Motor autónomo de predicción deportiva impulsado por Gemini 2.5 Flash, XGBoost, PyTorch LSTM y Poisson Dixon-Coles.",
    version="1.8.0",
    lifespan=lifespan
)

# Configuración de CORS amplia para desarrollo y producción de React/Vite
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/api/health")
async def health_check():
    """Endpoint de comprobación de salud del sistema."""
    return {
        "status": "online",
        "app_name": "Katakuri AI",
        "gemini_model": settings.GEMINI_MODEL,
        "models_local": ["Poisson Dixon-Coles", "XGBoost Tabular", "PyTorch LSTM", "Meta-Ensemble"],
        "database": "SQLite (Local)",
        "timestamp": datetime.utcnow().isoformat()
    }

from pydantic import BaseModel

class LoginRequest(BaseModel):
    username: str
    password: str

@app.post("/api/login")
async def login(credentials: LoginRequest):
    """
    Endpoint de autenticación para acceso a la plataforma Katakuri.
    Valida las credenciales configuradas en el archivo .env (APP_USERNAME y APP_PASSWORD).
    """
    expected_user = settings.APP_USERNAME.strip()
    expected_pass = settings.APP_PASSWORD.strip()

    if credentials.username.strip() == expected_user and credentials.password.strip() == expected_pass:
        import hashlib, hmac
        token_payload = f"{expected_user}:{datetime.utcnow().strftime('%Y-%m-%d')}"
        sig = hmac.new(settings.JWT_SECRET.encode(), token_payload.encode(), hashlib.sha256).hexdigest()
        token = f"{token_payload}:{sig}"

        logger.info(f"Usuario '{expected_user}' autenticado exitosamente.")
        return {
            "success": True,
            "access_token": token,
            "token_type": "bearer",
            "username": expected_user
        }

    logger.warning(f"Intento fallido de login para usuario: '{credentials.username}'")
    raise HTTPException(
        status_code=401,
        detail="Credenciales de acceso inválidas. Verifica tu usuario y contraseña."
    )


@app.post("/api/predict", response_model=PredictionResponse)
async def predict_match(
    request: PredictRequest,
    db: Session = Depends(get_db)
):
    """
    Endpoint principal de predicción deportiva.
    1. Verifica si existe un análisis reciente en caché en SQLite (< 12 horas).
    2. Si no existe o se solicita force_refresh:
       - Recopila datos de la web y genera JSON estructurado con Gemini 2.5 Flash.
       - Ejecuta el ensamble local de modelos (Poisson, XGBoost, LSTM).
       - Persiste el resultado en SQLite para acelerar futuras consultas.
    3. Retorna el objeto PredictionResponse 100% entendible para humanos.
    """
    home_clean = request.home_team.strip() if request.home_team else ""
    away_clean = request.away_team.strip() if request.away_team else ""
    comp_clean = request.competition.strip() if request.competition else "General"
    clean_url = request.match_url.strip() if request.match_url else None

    if not clean_url and (not home_clean or not away_clean):
        raise HTTPException(
            status_code=400,
            detail="Debes ingresar el equipo local y el equipo visitante, o bien proporcionar una URL de partido."
        )

    if home_clean and away_clean and home_clean.lower() == away_clean.lower():
        raise HTTPException(
            status_code=400,
            detail="El equipo local y el equipo visitante no pueden ser idénticos."
        )

    # 1. Comprobar caché en SQLite (solo si se conocen los equipos y no se pasó una URL directa)
    if not request.force_refresh and not clean_url and home_clean and away_clean:
        # Búsqueda bidireccional en caso de que el usuario haya ingresado los equipos en orden invertido
        cached_record = db.query(MatchPrediction).filter(
            or_(
                and_(MatchPrediction.home_team.ilike(home_clean), MatchPrediction.away_team.ilike(away_clean)),
                and_(MatchPrediction.home_team.ilike(away_clean), MatchPrediction.away_team.ilike(home_clean))
            )
        ).order_by(MatchPrediction.analyzed_at.desc()).first()

        if cached_record and cached_record.prediction_data:
            try:
                cached_dict = cached_record.prediction_data
                match_meta = cached_dict.get("match", {})
                is_live_match = match_meta.get("is_live", False)
                age_minutes = (datetime.utcnow() - cached_record.analyzed_at).total_seconds() / 60.0

                # Si el usuario solicitó explícitamente activar o desactivar el modo en vivo y difiere de la caché, recalcular
                if request.is_live is not None and request.is_live != is_live_match:
                    logger.info(f"Caché omitida por alternancia manual de modo en vivo (solicitado: {request.is_live} vs caché: {is_live_match}).")
                # Si el registro no tiene el campo is_live, expirar inmediatamente
                elif "is_live" not in match_meta:
                    logger.info(f"Registro en caché sin campos live para {home_clean} vs {away_clean}. Procediendo con nuevo cálculo.")
                # Si el partido está en vivo y ya pasaron más de 5 minutos, expirar
                elif is_live_match and age_minutes > 5:
                    logger.info(f"Caché de partido en vivo expirada ({round(age_minutes, 1)} min) para {home_clean} vs {away_clean}. Procediendo con actualización.")
                # Si el partido no está en vivo pero tiene más de 12 horas, expirar
                elif not is_live_match and age_minutes > 720:
                    logger.info(f"Caché estándar expirada ({round(age_minutes/60, 1)} horas). Procediendo con actualización.")
                else:
                    logger.info(f"Caché HIT para {home_clean} vs {away_clean} (analizado hace {round(age_minutes, 1)} min, en vivo: {is_live_match})")
                    return PredictionResponse.model_validate(cached_dict)
            except Exception as e:
                logger.warning(f"Error parseando datos en caché: {e}. Procediendo con nuevo cálculo.")

    # 2. Recopilar datos web mediante Gemini 2.5 Flash + LangChain
    logger.info(f"Iniciando recolección de datos y predicción para {home_clean} vs {away_clean} (match_url: {request.match_url})...")
    try:
        effective_live = bool(clean_url) or bool(request.is_live)
        raw_features: MatchRawFeatures = collector.collect(
            home_team=home_clean,
            away_team=away_clean,
            competition=comp_clean,
            force_refresh=request.force_refresh,
            is_live=effective_live,
            live_score=request.live_score,
            live_minute=request.live_minute,
            live_corners=getattr(request, "live_corners", None),
            live_red_cards_home=getattr(request, "live_red_cards_home", 0),
            live_red_cards_away=getattr(request, "live_red_cards_away", 0),
            live_shots_on_target_home=getattr(request, "live_shots_on_target_home", None),
            live_shots_on_target_away=getattr(request, "live_shots_on_target_away", None),
            match_url=clean_url
        )
    except Exception as e:
        logger.error(f"Fallo en recolección web para {home_clean} vs {away_clean}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Error recopilando estadísticas del encuentro: {str(e)}"
        )

    # 3. Ejecutar Ensamble Predictivo Local
    try:
        prediction_result: PredictionResponse = ensemble_engine.predict(raw_features)
    except Exception as e:
        logger.error(f"Error ejecutando modelos predictivos: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Error en el motor predictivo local: {str(e)}"
        )

    # 4. Persistir en Base de Datos SQLite
    try:
        p_details = prediction_result.prediction
        new_record = MatchPrediction(
            home_team=prediction_result.match.home_team,
            away_team=prediction_result.match.away_team,
            competition=prediction_result.match.competition,
            match_url=prediction_result.match.match_url or request.match_url,
            analyzed_at=prediction_result.match.analyzed_at,
            winner_home_pct=p_details.winner.home_win_pct,
            winner_draw_pct=p_details.winner.draw_pct,
            winner_away_pct=p_details.winner.away_win_pct,
            human_verdict=p_details.winner.human_verdict,
            expected_goals=p_details.goals.expected_total,
            over_2_5_pct=p_details.goals.over_2_5_pct,
            expected_corners=p_details.corners.expected_total,
            expected_cards=p_details.cards.expected_total,
            prediction_data=prediction_result.model_dump(mode="json"),
            raw_stats=raw_features.model_dump(mode="json")
        )
        db.add(new_record)
        db.commit()
        db.refresh(new_record)
        logger.info(f"Predicción guardada en SQLite con ID: {new_record.id}")
    except Exception as e:
        logger.warning(f"No se pudo guardar la predicción en SQLite: {e}")
        db.rollback()

    return prediction_result

@app.get("/api/predictions/recent")
async def get_recent_predictions(
    limit: int = Query(10, ge=1, le=50),
    db: Session = Depends(get_db)
):
    """
    Retorna la lista de los últimos partidos analizados guardados en SQLite.
    Permite al frontend mostrar un historial de consultas y accesos rápidos.
    """
    records = db.query(MatchPrediction).order_by(
        MatchPrediction.analyzed_at.desc()
    ).limit(limit).all()

    results = []
    for r in records:
        pred_meta = (r.prediction_data or {}).get("match", {})
        results.append({
            "id": r.id,
            "home_team": r.home_team,
            "away_team": r.away_team,
            "competition": r.competition,
            "analyzed_at": r.analyzed_at.isoformat() if r.analyzed_at else None,
            "is_live": pred_meta.get("is_live", False),
            "match_url": r.match_url or pred_meta.get("match_url"),
            "live_minute": pred_meta.get("live_minute"),
            "live_score": pred_meta.get("live_score"),
            "live_corners": pred_meta.get("live_corners"),
            "winner_home_pct": r.winner_home_pct,
            "winner_draw_pct": r.winner_draw_pct,
            "winner_away_pct": r.winner_away_pct,
            "human_verdict": r.human_verdict,
            "expected_goals": r.expected_goals,
            "over_2_5_pct": r.over_2_5_pct
        })
    return {"total": len(results), "predictions": results}

@app.get("/api/backtest/benchmark")
async def run_benchmark_backtest():
    """
    Ejecuta el ciclo de backtesting automatizado sobre el dataset histórico benchmark
    calculando RPS (Ranked Probability Score), Brier Score, Log-Loss, MAE y precisión.
    """
    from backend.app.analytics.backtest import run_backtest, get_benchmark_dataset
    dataset = get_benchmark_dataset()
    results = run_backtest(dataset)
    return results

@app.post("/api/backtest/run")
async def run_custom_backtest(items: List[dict]):
    """
    Permite evaluar un lote personalizado de partidos con resultados verificados.
    """
    from backend.app.analytics.backtest import run_backtest, HistoricalEvaluationItem
    try:
        parsed_items = [HistoricalEvaluationItem(**item) for item in items]
        results = run_backtest(parsed_items)
        return results
    except Exception as e:
        logger.error(f"Error procesando backtest personalizado: {e}")
        raise HTTPException(status_code=400, detail=f"Error en formato de datos de evaluación: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.app.main:app", host="0.0.0.0", port=settings.PORT, reload=True, reload_dirs=["backend"])

