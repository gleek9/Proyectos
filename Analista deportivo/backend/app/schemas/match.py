"""
Schemas Pydantic para la ingestión y estructuración de datos de partidos.
"""
from typing import List, Optional
from pydantic import BaseModel, Field

class MatchSearchQuery(BaseModel):
    home_team: str = Field(..., description="Nombre del equipo local")
    away_team: str = Field(..., description="Nombre del equipo visitante")
    competition: Optional[str] = Field("General", description="Nombre de la liga o torneo")

class PreviousMatch(BaseModel):
    opponent: str = Field(..., description="Equipo rival")
    was_home: bool = Field(..., description="Si jugó como local (True) o visitante (False)")
    goals_for: int = Field(0, description="Goles anotados")
    goals_against: int = Field(0, description="Goles recibidos")
    corners_for: Optional[float] = Field(None, description="Tiros de esquina a favor (si está disponible)")
    cards_total: Optional[float] = Field(None, description="Tarjetas totales del partido (si está disponible)")
    result: str = Field("D", description="Resultado: 'W' (Victoria), 'D' (Empate), 'L' (Derrota)")

class TeamFormStats(BaseModel):
    team_name: str
    last_matches: List[PreviousMatch] = Field(default_factory=list, description="Últimos partidos recientes (hasta 10)")
    avg_goals_scored: float = Field(1.5, description="Promedio de goles anotados por partido")
    avg_goals_conceded: float = Field(1.2, description="Promedio de goles recibidos por partido")
    avg_corners: float = Field(5.0, description="Promedio de córners a favor por partido")
    avg_cards: float = Field(2.2, description="Promedio de tarjetas amarillas/rojas recibidas")
    win_rate_last_5: float = Field(0.5, description="Porcentaje de victorias en los últimos 5 partidos (0.0 a 1.0)")
    key_absences: List[str] = Field(default_factory=list, description="Jugadores clave lesionados o suspendidos")

class HeadToHeadStats(BaseModel):
    total_matches_analyzed: int = Field(5, description="Número de enfrentamientos directos previos encontrados")
    home_team_wins: int = Field(2, description="Victorias del equipo local en H2H")
    draws: int = Field(1, description="Empates en H2H")
    away_team_wins: int = Field(2, description="Victorias del equipo visitante en H2H")
    avg_total_goals_h2h: float = Field(2.8, description="Promedio de goles totales por partido en H2H")
    avg_total_corners_h2h: float = Field(9.5, description="Promedio de córners totales en H2H")
    avg_total_cards_h2h: float = Field(4.5, description="Promedio de tarjetas totales en H2H")

class MatchRawFeatures(BaseModel):
    """
    Schema estricto estructurado que Gemini 2.5 Flash debe extraer de las búsquedas web.
    Alimenta de forma limpia y tipada a los modelos locales (XGBoost, LSTM, Poisson).
    """
    home_team: str = Field(..., description="Nombre del equipo anfitrión local oficial determinado por la IA")
    away_team: str = Field(..., description="Nombre del equipo visitante oficial determinado por la IA")
    competition: str = Field("General", description="Competición o torneo")
    is_live: bool = Field(False, description="Si el partido se encuentra actualmente en curso/en vivo")
    match_url: Optional[str] = Field(None, description="URL del partido en vivo en Flashscore/Sofascore")
    live_minute: Optional[str] = Field(None, description="Minuto de juego si está en vivo (ej: '34'' o '2T 68'')")
    live_score: Optional[str] = Field(None, description="Marcador parcial actual si está en vivo (ej: '1 - 0')")
    live_corners: Optional[int] = Field(None, description="Tiros de esquina acumulados en vivo si el partido está en juego (ej: 6)")
    live_red_cards_home: Optional[int] = Field(0, description="Tarjetas rojas del equipo local en directo")
    live_red_cards_away: Optional[int] = Field(0, description="Tarjetas rojas del equipo visitante en directo")
    live_shots_on_target_home: Optional[int] = Field(None, description="Tiros a puerta del equipo local en directo")
    live_shots_on_target_away: Optional[int] = Field(None, description="Tiros a puerta del equipo visitante en directo")
    live_possession_home: Optional[float] = Field(None, description="Porcentaje de posesión local en directo (ej: 58.0)")
    live_possession_away: Optional[float] = Field(None, description="Porcentaje de posesión visitante en directo (ej: 42.0)")
    home_stats: TeamFormStats
    away_stats: TeamFormStats
    h2h: HeadToHeadStats
    context_notes: List[str] = Field(
        default_factory=list,
        description="Factores contextuales clave (bajas importantes, racha de victorias, condiciones)"
    )

