"""
Schemas Pydantic para el Motor Predictivo y la Respuesta de la API de Katakuri AI.
Cumple estrictamente con el contrato estipulado en AGENTS.md.
"""
from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel, Field

class PredictRequest(BaseModel):
    home_team: Optional[str] = Field(None, description="Nombre del equipo local (opcional si se provee match_url)")
    away_team: Optional[str] = Field(None, description="Nombre del equipo visitante (opcional si se provee match_url)")
    competition: Optional[str] = Field("General", description="Nombre de la liga o torneo")
    force_refresh: Optional[bool] = Field(False, description="Forzar nueva búsqueda y análisis omitiendo la caché")
    match_url: Optional[str] = Field(None, description="URL directa del partido en vivo (ej. Flashscore / Sofascore)")
    is_live: Optional[bool] = Field(None, description="Forzar o indicar estado de partido en vivo")
    live_minute: Optional[str] = Field(None, description="Minuto en vivo personalizado o detectado (ej: '45'')")
    live_score: Optional[str] = Field(None, description="Marcador en vivo personalizado o detectado (ej: '1 - 0')")
    live_corners: Optional[int] = Field(None, description="Córners en vivo personalizados o detectados (ej: 5)")
    live_red_cards_home: Optional[int] = Field(0, description="Tarjetas rojas activas del local en vivo")
    live_red_cards_away: Optional[int] = Field(0, description="Tarjetas rojas activas del visitante en vivo")
    live_shots_on_target_home: Optional[int] = Field(None, description="Tiros a puerta del local en vivo")
    live_shots_on_target_away: Optional[int] = Field(None, description="Tiros a puerta del visitante en vivo")

class DoubleChancePrediction(BaseModel):
    home_or_draw_pct: float = Field(..., description="1X: Victoria local o Empate (%)")
    draw_or_away_pct: float = Field(..., description="X2: Empate o Victoria visitante (%)")
    home_or_away_pct: float = Field(..., description="12: Victoria local o Victoria visitante (%)")

class DrawNoBetPrediction(BaseModel):
    home_dnb_pct: float = Field(..., description="Victoria local (Empate no válido / DNB) (%)")
    away_dnb_pct: float = Field(..., description="Victoria visitante (Empate no válido / DNB) (%)")

class WinnerPrediction(BaseModel):
    home_win_pct: float = Field(..., description="Probabilidad de victoria local (0 a 100)")
    draw_pct: float = Field(..., description="Probabilidad de empate (0 a 100)")
    away_win_pct: float = Field(..., description="Probabilidad de victoria visitante (0 a 100)")
    human_verdict: str = Field(..., description="Veredicto claro en lenguaje humano")
    double_chance: Optional[DoubleChancePrediction] = Field(None, description="Probabilidades de Doble Oportunidad (1X, X2, 12)")
    draw_no_bet: Optional[DrawNoBetPrediction] = Field(None, description="Probabilidades de Empate Apuesta No Válida (DNB)")

class LiveGoalLine(BaseModel):
    line: str = Field(..., description="Descripción de la línea (ej: 'Sin más goles (+0)', '+1 gol o más')")
    over_threshold: float = Field(..., description="Umbral de goles totales (ej: 3.5)")
    probability: float = Field(..., description="Probabilidad en porcentaje (%)")

class LiveCornerLine(BaseModel):
    line: str = Field(..., description="Descripción de la línea de córners en vivo")
    probability: float = Field(..., description="Probabilidad en porcentaje (%)")

class GoalsPrediction(BaseModel):
    expected_total: float = Field(..., description="Goles totales esperados en el encuentro")
    most_likely_score: str = Field(..., description="Marcador exacto más probable (ej: '2 - 1')")
    over_1_5_pct: float = Field(..., description="Probabilidad de más de 1.5 goles (%)")
    over_2_5_pct: float = Field(..., description="Probabilidad de más de 2.5 goles (%)")
    over_3_5_pct: float = Field(..., description="Probabilidad de más de 3.5 goles (%)")
    both_teams_to_score_pct: float = Field(..., description="Probabilidad de ambos anotan (%)")
    human_verdict: str = Field(..., description="Explicación clara del pronóstico de goles")
    # Campos dinámicos en vivo analizados con Red Neuronal LSTM + Poisson + XGBoost
    is_live: Optional[bool] = Field(False, description="Indica si la predicción corresponde a partido en vivo")
    current_goals: Optional[int] = Field(None, description="Goles acumulados actuales en el encuentro")
    no_more_goals_pct: Optional[float] = Field(None, description="Probabilidad de no meter más goles (+0 goles adicionales)")
    more_goals_pct: Optional[float] = Field(None, description="Probabilidad de meter más goles de los que hay (al menos +1 gol adicional)")
    plus_1_goal_pct: Optional[float] = Field(None, description="Probabilidad de +1 gol adicional o más")
    plus_2_goals_pct: Optional[float] = Field(None, description="Probabilidad de +2 goles adicionales o más")
    plus_3_goals_pct: Optional[float] = Field(None, description="Probabilidad de +3 goles adicionales o más")
    live_lines: Optional[List[LiveGoalLine]] = Field(default_factory=list, description="Líneas dinámicas de goles en vivo")

class CornersPrediction(BaseModel):
    expected_total: float = Field(..., description="Total esperado de córners en el partido")
    over_8_5_pct: float = Field(..., description="Probabilidad de más de 8.5 córners (%)")
    over_9_5_pct: float = Field(..., description="Probabilidad de más de 9.5 córners (%)")
    over_10_5_pct: float = Field(..., description="Probabilidad de más de 10.5 córners (%)")
    human_verdict: str = Field(..., description="Veredicto humano sobre tiros de esquina")
    # Campos dinámicos en vivo
    is_live: Optional[bool] = Field(False, description="Indica si corresponde a partido en vivo")
    current_corners: Optional[int] = Field(None, description="Córners acumulados en el partido hasta el momento")
    expected_remaining_corners: Optional[float] = Field(None, description="Córners adicionales esperados en el tiempo restante")
    no_more_corners_pct: Optional[float] = Field(None, description="Probabilidad de no haber más córners en el tiempo restante")
    more_corners_pct: Optional[float] = Field(None, description="Probabilidad de nuevos córners en el tiempo restante")
    live_corners_lines: Optional[List[LiveCornerLine]] = Field(default_factory=list, description="Líneas dinámicas de córners en vivo")

class CardsPrediction(BaseModel):
    expected_total: float = Field(..., description="Total esperado de tarjetas en el encuentro")
    over_3_5_pct: float = Field(..., description="Probabilidad de más de 3.5 tarjetas (%)")
    over_4_5_pct: float = Field(..., description="Probabilidad de más de 4.5 tarjetas (%)")
    red_card_risk_pct: float = Field(..., description="Probabilidad o riesgo de tarjeta roja (%)")
    human_verdict: str = Field(..., description="Veredicto humano de intensidad y tarjetas")
    # Campos dinámicos en vivo
    is_live: Optional[bool] = Field(False, description="Indica si corresponde a partido en vivo")
    expected_remaining_cards: Optional[float] = Field(None, description="Tarjetas adicionales esperadas en el tiempo restante")

class MatchPredictionDetails(BaseModel):
    winner: WinnerPrediction
    goals: GoalsPrediction
    corners: CornersPrediction
    cards: CardsPrediction

class GoalDistributionItem(BaseModel):
    goals: str = Field(..., description="Etiqueta del total de goles (ej: '2 Goles')")
    probability: float = Field(..., description="Probabilidad en porcentaje (%)")

class TopScoreItem(BaseModel):
    score: str = Field(..., description="Marcador (ej: '2 - 1')")
    probability: float = Field(..., description="Probabilidad en porcentaje (%)")

class ChartData(BaseModel):
    goals_distribution: List[GoalDistributionItem]
    top_scores: List[TopScoreItem]

class MatchMeta(BaseModel):
    home_team: str
    away_team: str
    competition: Optional[str] = "General"
    is_live: bool = False
    match_url: Optional[str] = None
    live_minute: Optional[str] = None
    live_score: Optional[str] = None
    live_corners: Optional[int] = None
    live_red_cards_home: Optional[int] = 0
    live_red_cards_away: Optional[int] = 0
    live_shots_on_target_home: Optional[int] = None
    live_shots_on_target_away: Optional[int] = None
    live_possession_home: Optional[float] = None
    live_possession_away: Optional[float] = None
    analyzed_at: datetime = Field(default_factory=datetime.utcnow)

class PredictionResponse(BaseModel):
    match: MatchMeta
    prediction: MatchPredictionDetails
    chart_data: ChartData
    key_factors: List[str] = Field(default_factory=list)

