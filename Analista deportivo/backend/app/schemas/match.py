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
    date: Optional[str] = Field(None, description="Fecha del partido (YYYY-MM-DD)")
    shots_on_target_for: Optional[float] = Field(None, description="Tiros a puerta a favor en ese partido")
    shots_for: Optional[float] = Field(None, description="Tiros totales a favor en ese partido")
    fouls: Optional[float] = Field(None, description="Faltas cometidas en ese partido")
    ht_diff: Optional[float] = Field(None, description="Diferencia de goles al descanso (HT) a favor")
    xg_for: Optional[float] = Field(None, description="Expected Goals (xG) a favor en ese partido")
    opponent_elo: Optional[float] = Field(None, description="Rating Elo del rival en ese partido")

class TeamFormStats(BaseModel):
    team_name: str
    last_matches: List[PreviousMatch] = Field(default_factory=list, description="Últimos partidos recientes (hasta 10)")
    avg_goals_scored: float = Field(1.35, description="Promedio de goles anotados por partido")
    avg_goals_conceded: float = Field(1.25, description="Promedio de goles recibidos por partido")
    avg_corners: float = Field(4.8, description="Promedio de córners a favor por partido")
    avg_cards: float = Field(2.2, description="Promedio de tarjetas amarillas/rojas recibidas")
    win_rate_last_5: float = Field(0.5, description="Porcentaje de victorias en los últimos 5 partidos (0.0 a 1.0)")
    key_absences: List[str] = Field(default_factory=list, description="Jugadores clave lesionados o suspendidos")
    elo_rating: Optional[float] = Field(None, description="Rating Elo dinámico")
    home_goals_scored: Optional[float] = Field(None, description="Promedio de goles anotados jugando como local")
    home_goals_conceded: Optional[float] = Field(None, description="Promedio de goles concedidos jugando como local")
    away_goals_scored: Optional[float] = Field(None, description="Promedio de goles anotados jugando como visitante")
    away_goals_conceded: Optional[float] = Field(None, description="Promedio de goles concedidos jugando como visitante")
    avg_shots_target_for: Optional[float] = Field(None, description="Promedio de tiros a puerta a favor por partido")
    avg_shots_target_against: Optional[float] = Field(None, description="Promedio de tiros a puerta concedidos por partido")
    avg_shots_for: Optional[float] = Field(None, description="Promedio de tiros totales a favor por partido")
    avg_shots_against: Optional[float] = Field(None, description="Promedio de tiros totales concedidos por partido")
    avg_fouls_for: Optional[float] = Field(None, description="Promedio de faltas cometidas por partido")
    avg_fouls_against: Optional[float] = Field(None, description="Promedio de faltas recibidas por partido")
    ht_goal_diff_avg: Optional[float] = Field(None, description="Diferencia media de goles al descanso (HT)")
    avg_xg_for: Optional[float] = Field(None, description="Promedio histórico incremental de xG a favor")
    avg_xg_against: Optional[float] = Field(None, description="Promedio histórico incremental de xG en contra")
    avg_corners_conceded: Optional[float] = Field(None, description="Promedio de córners concedidos al rival por partido")
    rest_days: Optional[float] = Field(None, description="Días de descanso desde el último partido")

class HeadToHeadStats(BaseModel):
    total_matches_analyzed: int = Field(0, description="Número de enfrentamientos directos previos encontrados (0 si no hay datos)")
    home_team_wins: int = Field(0, description="Victorias del equipo local en H2H")
    draws: int = Field(0, description="Empates en H2H")
    away_team_wins: int = Field(0, description="Victorias del equipo visitante en H2H")
    avg_total_goals_h2h: float = Field(2.5, description="Promedio de goles totales por partido en H2H")
    avg_total_corners_h2h: float = Field(9.2, description="Promedio de córners totales en H2H")
    avg_total_cards_h2h: float = Field(4.2, description="Promedio de tarjetas totales en H2H")

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
    live_xg_home: Optional[float] = Field(None, description="Expected Goals (xG) del equipo local capturado de Sofascore")
    live_xg_away: Optional[float] = Field(None, description="Expected Goals (xG) del equipo visitante capturado de Sofascore")
    referee_name: Optional[str] = Field(None, description="Nombre del árbitro principal del encuentro")
    referee_avg_cards: Optional[float] = Field(None, description="Media histórica/carrera de tarjetas por partido del árbitro")
    market_home_odds: Optional[float] = Field(None, description="Cuota de mercado 1X2 para victoria local (si está disponible)")
    market_draw_odds: Optional[float] = Field(None, description="Cuota de mercado 1X2 para empate (si está disponible)")
    market_away_odds: Optional[float] = Field(None, description="Cuota de mercado 1X2 para victoria visitante (si está disponible)")
    b365_open_home_odds: Optional[float] = Field(None, description="Cuota de apertura Bet365 1X2 Local")
    b365_open_draw_odds: Optional[float] = Field(None, description="Cuota de apertura Bet365 1X2 Empate")
    b365_open_away_odds: Optional[float] = Field(None, description="Cuota de apertura Bet365 1X2 Visitante")
    ps_open_home_odds: Optional[float] = Field(None, description="Cuota de apertura Pinnacle 1X2 Local")
    ps_open_draw_odds: Optional[float] = Field(None, description="Cuota de apertura Pinnacle 1X2 Empate")
    ps_open_away_odds: Optional[float] = Field(None, description="Cuota de apertura Pinnacle 1X2 Visitante")
    ps_close_home_odds: Optional[float] = Field(None, description="Cuota de cierre Pinnacle 1X2 Local")
    ps_close_draw_odds: Optional[float] = Field(None, description="Cuota de cierre Pinnacle 1X2 Empate")
    ps_close_away_odds: Optional[float] = Field(None, description="Cuota de cierre Pinnacle 1X2 Visitante")
    b365_over_25_odds: Optional[float] = Field(None, description="Cuota Bet365 Over 2.5 goles")
    b365_under_25_odds: Optional[float] = Field(None, description="Cuota Bet365 Under 2.5 goles")
    p_over_25_odds: Optional[float] = Field(None, description="Cuota Pinnacle Over 2.5 goles")
    p_under_25_odds: Optional[float] = Field(None, description="Cuota Pinnacle Under 2.5 goles")
    home_stats: TeamFormStats
    away_stats: TeamFormStats
    h2h: HeadToHeadStats
    context_notes: List[str] = Field(
        default_factory=list,
        description="Factores contextuales clave (bajas importantes, racha de victorias, condiciones)"
    )

