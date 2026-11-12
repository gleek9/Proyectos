"""
Módulo de Carga, Normalización y Procesamiento de Datos Reales (Katakuri v4).
Descarga y procesa miles de partidos históricos oficiales de las grandes ligas europeas
(Premier League, LaLiga, Serie A, Bundesliga, Ligue 1) más datos de Liga MX y Champions League.
Calcula el rating Elo dinámico partido a partido cronológicamente y estadísticas móviles reales.
"""
import os
import csv
import io
import math
import logging
import urllib.request
from datetime import datetime
from typing import Dict, List, Optional, Tuple

from backend.app.db import SessionLocal, League, Team, HistoricalMatch, TeamStatsCache

logger = logging.getLogger(__name__)

DATA_DIR = os.path.join("backend", "data", "football_data")

# Mapeo de ligas a códigos y temporadas (incluye temporada 2022-23 de calentamiento para eliminar sesgo retrospectivo de Elo)
DATASET_SOURCES = {
    "premier_league": [("E0", "2223"), ("E0", "2324"), ("E0", "2425")],
    "laliga": [("SP1", "2223"), ("SP1", "2324"), ("SP1", "2425")],
    "serie_a": [("I1", "2223"), ("I1", "2324"), ("I1", "2425")],
    "bundesliga": [("D1", "2223"), ("D1", "2324"), ("D1", "2425")],
    "ligue_1": [("F1", "2223"), ("F1", "2324"), ("F1", "2425")],
    "eredivisie": [("N1", "2223"), ("N1", "2324"), ("N1", "2425")],
    "primeira_liga": [("P1", "2223"), ("P1", "2324"), ("P1", "2425")]
}

# Normalización de nombres de equipos de football-data a nombres canónicos limpios
TEAM_NAME_MAP = {
    # Premier League
    "Man City": "Manchester City",
    "Man United": "Manchester United",
    "Nott'm Forest": "Nottingham Forest",
    "Sheffield United": "Sheffield United",
    "Wolves": "Wolverhampton",
    
    # LaLiga
    "Ath Madrid": "Atletico Madrid",
    "Ath Bilbao": "Athletic Bilbao",
    "Sociedad": "Real Sociedad",
    "Betis": "Real Betis",
    "Celta": "Celta Vigo",
    "Espanol": "Espanyol",
    "Vallecano": "Rayo Vallecano",
    "Alaves": "Deportivo Alaves",
    "Leganes": "CD Leganes",
    "Valladolid": "Real Valladolid",

    # Serie A
    "Milan": "AC Milan",
    "Inter": "Inter",
    "Verona": "Hellas Verona",

    # Bundesliga
    "Dortmund": "Borussia Dortmund",
    "Leverkusen": "Bayer Leverkusen",
    "Ein Frankfurt": "Eintracht Frankfurt",
    "M'gladbach": "Borussia Monchengladbach",
    "FC Koln": "FC Cologne",
    "RB Leipzig": "RB Leipzig",
    "Union Berlin": "Union Berlin",
    "Werder Bremen": "Werder Bremen",
    "St Pauli": "St. Pauli",
    "Holstein Kiel": "Holstein Kiel",

    # Ligue 1
    "Paris SG": "PSG",
    "St Etienne": "Saint-Etienne",
    "Le Havre": "Le Havre",

    # Eredivisie & Primeira Liga
    "PSV": "PSV Eindhoven",
    "AZ": "AZ Alkmaar",
    "Sp Lisbon": "Sporting CP",
    "Sporting": "Sporting CP",
    "Porto": "FC Porto",
    "Sp Braga": "SC Braga",
    "Guimaraes": "Vitoria Guimaraes"
}

def parse_football_data_date(date_str: str) -> str:
    """Convierte fechas como '16/08/2024' o '16/08/24' a formato ISO 'YYYY-MM-DD'."""
    if not date_str:
        return "2024-01-01"
    parts = date_str.strip().split('/')
    if len(parts) == 3:
        day, month, year = parts
        if len(year) == 2:
            year = "20" + year
        return f"{year}-{int(month):02d}-{int(day):02d}"
    return date_str

def fetch_or_load_csv(code: str, season: str) -> List[Dict]:
    """Descarga el CSV desde football-data.co.uk o lo lee desde el caché local."""
    os.makedirs(DATA_DIR, exist_ok=True)
    local_path = os.path.join(DATA_DIR, f"{season}_{code}.csv")
    
    csv_text = None
    if os.path.exists(local_path) and os.path.getsize(local_path) > 1000:
        try:
            with open(local_path, "r", encoding="utf-8", errors="ignore") as f:
                csv_text = f.read()
        except Exception as e:
            logger.warning(f"Error leyendo caché local {local_path}: {e}")

    if not csv_text:
        url = f"https://www.football-data.co.uk/mmz4281/{season}/{code}.csv"
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=10) as r:
                raw_bytes = r.read()
                csv_text = raw_bytes.decode("utf-8", errors="ignore")
                with open(local_path, "w", encoding="utf-8") as f:
                    f.write(csv_text)
                logger.info(f"Descargado y guardado en caché: {local_path} ({len(csv_text)} bytes)")
        except Exception as e:
            logger.error(f"Error descargando {url}: {e}")
            return []

    rows = []
    reader = csv.DictReader(io.StringIO(csv_text))
    for r in reader:
        if r.get("HomeTeam") and r.get("AwayTeam") and r.get("FTHG") and r.get("FTAG"):
            try:
                int(r["FTHG"])
                int(r["FTAG"])
                rows.append(r)
            except ValueError:
                continue
    return rows

def canonicalize_team_name(raw_name: str) -> str:
    """Retorna el nombre canónico oficial para un equipo."""
    raw = raw_name.strip()
    return TEAM_NAME_MAP.get(raw, raw)

def calculate_elo_update(
    elo_home: float,
    elo_away: float,
    home_goals: int,
    away_goals: int,
    home_adv: float = 65.0,
    k_base: float = 30.0
) -> Tuple[float, float]:
    """
    Calcula la variación de Elo con K dinámico proporcional a la diferencia de goles.
    """
    delta_elo = (elo_home - elo_away) + home_adv
    expected_home = 1.0 / (1.0 + 10.0 ** (-delta_elo / 400.0))
    expected_away = 1.0 - expected_home

    if home_goals > away_goals:
        actual_home = 1.0
        actual_away = 0.0
    elif home_goals == away_goals:
        actual_home = 0.5
        actual_away = 0.5
    else:
        actual_home = 0.0
        actual_away = 1.0

    goal_diff = abs(home_goals - away_goals)
    k_mult = 1.0
    if goal_diff == 2:
        k_mult = 1.5
    elif goal_diff >= 3:
        k_mult = 1.75 + (goal_diff - 3) * 0.12

    k = k_base * k_mult
    new_elo_home = elo_home + k * (actual_home - expected_home)
    new_elo_away = elo_away + k * (actual_away - expected_away)

    return new_elo_home, new_elo_away

# Catálogo complementario curado para Liga MX y Champions League
CURATED_CHAMPIONS_MATCHES = [
    {"league": "champions_league", "season": "2024-25", "date": "2024-09-17", "home": "Real Madrid", "away": "Stuttgart", "hg": 3, "ag": 1, "hst": 8, "ast": 4, "hc": 6, "ac": 5, "hy": 2, "ay": 2, "hr": 0, "ar": 0, "b365h": 1.30, "b365d": 6.00, "b365a": 8.50},
    {"league": "champions_league", "season": "2024-25", "date": "2024-09-17", "home": "Bayern Munich", "away": "Dinamo Zagreb", "hg": 9, "ag": 2, "hst": 19, "ast": 3, "hc": 12, "ac": 2, "hy": 0, "ay": 1, "hr": 0, "ar": 0, "b365h": 1.15, "b365d": 9.00, "b365a": 15.00},
    {"league": "champions_league", "season": "2024-25", "date": "2024-09-17", "home": "AC Milan", "away": "Liverpool", "hg": 1, "ag": 3, "hst": 2, "ast": 11, "hc": 3, "ac": 9, "hy": 2, "ay": 2, "hr": 0, "ar": 0, "b365h": 3.80, "b365d": 3.75, "b365a": 1.95},
    {"league": "champions_league", "season": "2024-25", "date": "2024-09-18", "home": "Manchester City", "away": "Inter", "hg": 0, "ag": 0, "hst": 5, "ast": 4, "hc": 9, "ac": 3, "hy": 1, "ay": 0, "hr": 0, "ar": 0, "b365h": 1.55, "b365d": 4.33, "b365a": 5.75},
    {"league": "champions_league", "season": "2024-25", "date": "2024-09-18", "home": "PSG", "away": "Girona", "hg": 1, "ag": 0, "hst": 5, "ast": 1, "hc": 6, "ac": 1, "hy": 1, "ay": 2, "hr": 0, "ar": 0, "b365h": 1.40, "b365d": 5.00, "b365a": 7.50},
    {"league": "champions_league", "season": "2024-25", "date": "2024-09-19", "home": "Monaco", "away": "Barcelona", "hg": 2, "ag": 1, "hst": 8, "ast": 4, "hc": 5, "ac": 2, "hy": 3, "ay": 4, "hr": 0, "ar": 1, "b365h": 4.50, "b365d": 4.20, "b365a": 1.70},
    {"league": "champions_league", "season": "2024-25", "date": "2024-10-01", "home": "Arsenal", "away": "PSG", "hg": 2, "ag": 0, "hst": 6, "ast": 3, "hc": 4, "ac": 5, "hy": 1, "ay": 1, "hr": 0, "ar": 0, "b365h": 1.75, "b365d": 3.80, "b365a": 4.50},
    {"league": "champions_league", "season": "2024-25", "date": "2024-10-01", "home": "Bayer Leverkusen", "away": "AC Milan", "hg": 1, "ag": 0, "hst": 9, "ast": 5, "hc": 8, "ac": 3, "hy": 2, "ay": 2, "hr": 0, "ar": 0, "b365h": 1.65, "b365d": 4.20, "b365a": 4.75},
    {"league": "champions_league", "season": "2024-25", "date": "2024-10-02", "home": "Aston Villa", "away": "Bayern Munich", "hg": 1, "ag": 0, "hst": 3, "ast": 7, "hc": 3, "ac": 11, "hy": 2, "ay": 1, "hr": 0, "ar": 0, "b365h": 4.33, "b365d": 4.00, "b365a": 1.75},
    {"league": "champions_league", "season": "2024-25", "date": "2024-10-23", "home": "Barcelona", "away": "Bayern Munich", "hg": 4, "ag": 1, "hst": 4, "ast": 3, "hc": 4, "ac": 5, "hy": 0, "ay": 2, "hr": 0, "ar": 0, "b365h": 2.35, "b365d": 3.90, "b365a": 2.70},
    {"league": "champions_league", "season": "2024-25", "date": "2024-10-23", "home": "Real Madrid", "away": "Borussia Dortmund", "hg": 5, "ag": 2, "hst": 10, "ast": 7, "hc": 13, "ac": 4, "hy": 1, "ay": 0, "hr": 0, "ar": 0, "b365h": 1.50, "b365d": 4.75, "b365a": 5.75},
]

CURATED_LIGA_MX_MATCHES = [
    {"league": "liga_mx", "season": "2024-25", "date": "2024-07-13", "home": "América", "away": "Querétaro", "hg": 3, "ag": 1, "hst": 7, "ast": 2, "hc": 6, "ac": 3, "hy": 2, "ay": 3, "hr": 0, "ar": 0, "b365h": 1.45, "b365d": 4.33, "b365a": 6.50},
    {"league": "liga_mx", "season": "2024-25", "date": "2024-07-20", "home": "Monterrey", "away": "Cruz Azul", "hg": 0, "ag": 4, "hst": 3, "ast": 9, "hc": 5, "ac": 6, "hy": 3, "ay": 2, "hr": 0, "ar": 0, "b365h": 2.10, "b365d": 3.40, "b365a": 3.30},
    {"league": "liga_mx", "season": "2024-25", "date": "2024-08-24", "home": "Tigres UANL", "away": "Guadalajara", "hg": 1, "ag": 1, "hst": 5, "ast": 4, "hc": 7, "ac": 4, "hy": 2, "ay": 2, "hr": 0, "ar": 0, "b365h": 1.85, "b365d": 3.50, "b365a": 4.20},
    {"league": "liga_mx", "season": "2024-25", "date": "2024-08-31", "home": "Cruz Azul", "away": "América", "hg": 4, "ag": 1, "hst": 8, "ast": 3, "hc": 6, "ac": 5, "hy": 3, "ay": 4, "hr": 0, "ar": 0, "b365h": 2.25, "b365d": 3.30, "b365a": 3.10},
    {"league": "liga_mx", "season": "2024-25", "date": "2024-09-14", "home": "América", "away": "Guadalajara", "hg": 1, "ag": 0, "hst": 4, "ast": 3, "hc": 5, "ac": 6, "hy": 2, "ay": 3, "hr": 0, "ar": 0, "b365h": 1.95, "b365d": 3.40, "b365a": 3.80},
    {"league": "liga_mx", "season": "2024-25", "date": "2024-10-19", "home": "Monterrey", "away": "Tigres UANL", "hg": 4, "ag": 2, "hst": 7, "ast": 5, "hc": 4, "ac": 7, "hy": 3, "ay": 2, "hr": 0, "ar": 0, "b365h": 2.40, "b365d": 3.25, "b365a": 2.90},
    {"league": "liga_mx", "season": "2024-25", "date": "2024-10-26", "home": "Toluca", "away": "Puebla", "hg": 5, "ag": 0, "hst": 10, "ast": 2, "hc": 8, "ac": 2, "hy": 1, "ay": 2, "hr": 0, "ar": 0, "b365h": 1.35, "b365d": 5.00, "b365a": 8.00},
    {"league": "liga_mx", "season": "2024-25", "date": "2024-11-02", "home": "Cruz Azul", "away": "Santos Laguna", "hg": 2, "ag": 0, "hst": 6, "ast": 2, "hc": 7, "ac": 3, "hy": 1, "ay": 3, "hr": 0, "ar": 0, "b365h": 1.30, "b365d": 5.25, "b365a": 9.50},
    {"league": "liga_mx", "season": "2024-25", "date": "2024-11-06", "home": "América", "away": "Pachuca", "hg": 2, "ag": 1, "hst": 6, "ast": 4, "hc": 6, "ac": 5, "hy": 2, "ay": 1, "hr": 0, "ar": 0, "b365h": 1.70, "b365d": 3.80, "b365a": 4.60},
    {"league": "liga_mx", "season": "2024-25", "date": "2024-11-10", "home": "Toluca", "away": "América", "hg": 4, "ag": 0, "hst": 9, "ast": 4, "hc": 5, "ac": 6, "hy": 2, "ay": 3, "hr": 0, "ar": 0, "b365h": 2.30, "b365d": 3.40, "b365a": 2.95},
]

CURATED_WOMENS_MATCHES = [
    # Liga F Femenina (España)
    {"league": "liga_f", "season": "2023-24", "date": "2023-11-19", "home": "Barcelona F", "away": "Real Madrid F", "hg": 5, "ag": 0, "hst": 11, "ast": 1, "hc": 9, "ac": 2, "hy": 1, "ay": 2, "hr": 0, "ar": 0, "b365h": 1.14, "b365d": 7.50, "b365a": 13.00},
    {"league": "liga_f", "season": "2023-24", "date": "2024-01-21", "home": "Real Madrid F", "away": "Atletico Madrid F", "hg": 2, "ag": 1, "hst": 7, "ast": 4, "hc": 6, "ac": 5, "hy": 2, "ay": 2, "hr": 0, "ar": 0, "b365h": 1.75, "b365d": 3.60, "b365a": 4.20},
    {"league": "liga_f", "season": "2023-24", "date": "2024-02-14", "home": "Barcelona F", "away": "Levante F", "hg": 1, "ag": 1, "hst": 9, "ast": 3, "hc": 11, "ac": 2, "hy": 1, "ay": 3, "hr": 0, "ar": 0, "b365h": 1.08, "b365d": 9.50, "b365a": 19.00},
    {"league": "liga_f", "season": "2023-24", "date": "2024-03-10", "home": "Real Sociedad F", "away": "Barcelona F", "hg": 1, "ag": 7, "hst": 3, "ast": 14, "hc": 3, "ac": 9, "hy": 2, "ay": 0, "hr": 0, "ar": 0, "b365h": 15.00, "b365d": 8.00, "b365a": 1.12},
    {"league": "liga_f", "season": "2023-24", "date": "2024-03-24", "home": "Real Madrid F", "away": "Barcelona F", "hg": 0, "ag": 3, "hst": 2, "ast": 9, "hc": 3, "ac": 8, "hy": 2, "ay": 1, "hr": 0, "ar": 0, "b365h": 8.50, "b365d": 5.50, "b365a": 1.25},
    {"league": "liga_f", "season": "2023-24", "date": "2024-04-13", "home": "Atletico Madrid F", "away": "Athletic Bilbao F", "hg": 3, "ag": 0, "hst": 7, "ast": 3, "hc": 6, "ac": 4, "hy": 1, "ay": 2, "hr": 0, "ar": 0, "b365h": 1.55, "b365d": 3.90, "b365a": 5.40},
    {"league": "liga_f", "season": "2023-24", "date": "2024-04-28", "home": "Barcelona F", "away": "Madrid CFF", "hg": 8, "ag": 0, "hst": 16, "ast": 1, "hc": 12, "ac": 1, "hy": 0, "ay": 2, "hr": 0, "ar": 0, "b365h": 1.05, "b365d": 11.00, "b365a": 23.00},
    {"league": "liga_f", "season": "2023-24", "date": "2024-05-05", "home": "Sevilla F", "away": "Real Betis F", "hg": 2, "ag": 0, "hst": 6, "ast": 3, "hc": 6, "ac": 4, "hy": 2, "ay": 3, "hr": 0, "ar": 0, "b365h": 1.70, "b365d": 3.70, "b365a": 4.40},
    {"league": "liga_f", "season": "2023-24", "date": "2024-05-12", "home": "Athletic Bilbao F", "away": "Real Sociedad F", "hg": 2, "ag": 1, "hst": 6, "ast": 4, "hc": 5, "ac": 5, "hy": 2, "ay": 2, "hr": 0, "ar": 0, "b365h": 1.90, "b365d": 3.40, "b365a": 3.75},
    {"league": "liga_f", "season": "2023-24", "date": "2024-05-19", "home": "Valencia F", "away": "Levante F", "hg": 1, "ag": 2, "hst": 4, "ast": 6, "hc": 4, "ac": 7, "hy": 2, "ay": 2, "hr": 0, "ar": 0, "b365h": 3.40, "b365d": 3.50, "b365a": 1.95},
    {"league": "liga_f", "season": "2024-25", "date": "2024-09-13", "home": "Barcelona F", "away": "Real Sociedad F", "hg": 3, "ag": 1, "hst": 10, "ast": 2, "hc": 9, "ac": 2, "hy": 1, "ay": 1, "hr": 0, "ar": 0, "b365h": 1.07, "b365d": 10.00, "b365a": 21.00},
    {"league": "liga_f", "season": "2024-25", "date": "2024-09-22", "home": "Real Betis F", "away": "Real Madrid F", "hg": 0, "ag": 3, "hst": 2, "ast": 8, "hc": 3, "ac": 8, "hy": 2, "ay": 1, "hr": 0, "ar": 0, "b365h": 11.00, "b365d": 6.00, "b365a": 1.18},
    {"league": "liga_f", "season": "2024-25", "date": "2024-09-29", "home": "Barcelona F", "away": "Granada F", "hg": 10, "ag": 1, "hst": 18, "ast": 2, "hc": 11, "ac": 1, "hy": 0, "ay": 2, "hr": 0, "ar": 0, "b365h": 1.03, "b365d": 13.00, "b365a": 29.00},
    {"league": "liga_f", "season": "2024-25", "date": "2024-10-05", "home": "Madrid CFF", "away": "Athletic Bilbao F", "hg": 1, "ag": 2, "hst": 4, "ast": 5, "hc": 5, "ac": 6, "hy": 2, "ay": 2, "hr": 0, "ar": 0, "b365h": 2.40, "b365d": 3.30, "b365a": 2.70},
    {"league": "liga_f", "season": "2024-25", "date": "2024-10-13", "home": "Real Madrid F", "away": "Atletico Madrid F", "hg": 1, "ag": 1, "hst": 6, "ast": 4, "hc": 7, "ac": 4, "hy": 2, "ay": 3, "hr": 0, "ar": 0, "b365h": 1.80, "b365d": 3.50, "b365a": 4.10},
    {"league": "liga_f", "season": "2024-25", "date": "2024-10-20", "home": "Levante F", "away": "Barcelona F", "hg": 1, "ag": 4, "hst": 3, "ast": 11, "hc": 3, "ac": 9, "hy": 2, "ay": 1, "hr": 0, "ar": 0, "b365h": 13.00, "b365d": 7.00, "b365a": 1.14},
    {"league": "liga_f", "season": "2024-25", "date": "2024-11-02", "home": "Sevilla F", "away": "Valencia F", "hg": 3, "ag": 1, "hst": 6, "ast": 3, "hc": 6, "ac": 4, "hy": 2, "ay": 2, "hr": 0, "ar": 0, "b365h": 1.85, "b365d": 3.50, "b365a": 3.90},
    {"league": "liga_f", "season": "2024-25", "date": "2024-11-09", "home": "Atletico Madrid F", "away": "Barcelona F", "hg": 0, "ag": 3, "hst": 2, "ast": 9, "hc": 3, "ac": 8, "hy": 2, "ay": 1, "hr": 0, "ar": 0, "b365h": 7.50, "b365d": 4.80, "b365a": 1.33},
    {"league": "liga_f", "season": "2024-25", "date": "2024-11-16", "home": "Real Madrid F", "away": "Barcelona F", "hg": 0, "ag": 4, "hst": 3, "ast": 10, "hc": 4, "ac": 8, "hy": 2, "ay": 1, "hr": 0, "ar": 0, "b365h": 6.50, "b365d": 4.60, "b365a": 1.38},

    # Women's Super League (Inglaterra)
    {"league": "wsl", "season": "2023-24", "date": "2023-12-10", "home": "Arsenal F", "away": "Chelsea F", "hg": 4, "ag": 1, "hst": 8, "ast": 4, "hc": 6, "ac": 5, "hy": 2, "ay": 2, "hr": 0, "ar": 0, "b365h": 2.50, "b365d": 3.50, "b365a": 2.50},
    {"league": "wsl", "season": "2023-24", "date": "2024-01-21", "home": "Chelsea F", "away": "Manchester United F", "hg": 3, "ag": 1, "hst": 7, "ast": 4, "hc": 7, "ac": 4, "hy": 1, "ay": 2, "hr": 0, "ar": 0, "b365h": 1.55, "b365d": 4.00, "b365a": 5.25},
    {"league": "wsl", "season": "2023-24", "date": "2024-02-16", "home": "Chelsea F", "away": "Manchester City F", "hg": 0, "ag": 1, "hst": 5, "ast": 4, "hc": 7, "ac": 5, "hy": 2, "ay": 2, "hr": 0, "ar": 0, "b365h": 1.85, "b365d": 3.60, "b365a": 3.80},
    {"league": "wsl", "season": "2023-24", "date": "2024-03-15", "home": "Chelsea F", "away": "Arsenal F", "hg": 3, "ag": 1, "hst": 8, "ast": 4, "hc": 6, "ac": 5, "hy": 1, "ay": 2, "hr": 0, "ar": 0, "b365h": 1.95, "b365d": 3.50, "b365a": 3.50},
    {"league": "wsl", "season": "2023-24", "date": "2024-03-23", "home": "Manchester City F", "away": "Manchester United F", "hg": 3, "ag": 1, "hst": 8, "ast": 3, "hc": 8, "ac": 4, "hy": 1, "ay": 2, "hr": 0, "ar": 0, "b365h": 1.62, "b365d": 3.90, "b365a": 4.75},
    {"league": "wsl", "season": "2023-24", "date": "2024-04-21", "home": "Brighton F", "away": "Everton F", "hg": 1, "ag": 2, "hst": 4, "ast": 5, "hc": 5, "ac": 5, "hy": 2, "ay": 1, "hr": 0, "ar": 0, "b365h": 2.30, "b365d": 3.40, "b365a": 2.85},
    {"league": "wsl", "season": "2023-24", "date": "2024-05-01", "home": "Liverpool F", "away": "Chelsea F", "hg": 4, "ag": 3, "hst": 6, "ast": 7, "hc": 5, "ac": 8, "hy": 2, "ay": 1, "hr": 0, "ar": 0, "b365h": 6.50, "b365d": 4.50, "b365a": 1.40},
    {"league": "wsl", "season": "2023-24", "date": "2024-05-05", "home": "Manchester City F", "away": "Arsenal F", "hg": 1, "ag": 2, "hst": 5, "ast": 6, "hc": 6, "ac": 5, "hy": 2, "ay": 2, "hr": 0, "ar": 0, "b365h": 1.90, "b365d": 3.60, "b365a": 3.60},
    {"league": "wsl", "season": "2023-24", "date": "2024-05-18", "home": "Manchester United F", "away": "Chelsea F", "hg": 0, "ag": 6, "hst": 3, "ast": 11, "hc": 4, "ac": 7, "hy": 2, "ay": 1, "hr": 0, "ar": 0, "b365h": 4.20, "b365d": 3.90, "b365a": 1.72},
    {"league": "wsl", "season": "2023-24", "date": "2024-05-18", "home": "Aston Villa F", "away": "Manchester City F", "hg": 1, "ag": 2, "hst": 3, "ast": 9, "hc": 3, "ac": 8, "hy": 1, "ay": 1, "hr": 0, "ar": 0, "b365h": 8.00, "b365d": 5.25, "b365a": 1.30},
    {"league": "wsl", "season": "2024-25", "date": "2024-09-20", "home": "Chelsea F", "away": "Aston Villa F", "hg": 1, "ag": 0, "hst": 6, "ast": 3, "hc": 7, "ac": 4, "hy": 1, "ay": 2, "hr": 0, "ar": 0, "b365h": 1.22, "b365d": 6.00, "b365a": 10.00},
    {"league": "wsl", "season": "2024-25", "date": "2024-09-22", "home": "Arsenal F", "away": "Manchester City F", "hg": 2, "ag": 2, "hst": 6, "ast": 5, "hc": 6, "ac": 5, "hy": 2, "ay": 2, "hr": 0, "ar": 0, "b365h": 2.15, "b365d": 3.50, "b365a": 3.00},
    {"league": "wsl", "season": "2024-25", "date": "2024-09-29", "home": "Tottenham F", "away": "Aston Villa F", "hg": 2, "ag": 2, "hst": 5, "ast": 5, "hc": 6, "ac": 5, "hy": 2, "ay": 2, "hr": 0, "ar": 0, "b365h": 2.10, "b365d": 3.40, "b365a": 3.20},
    {"league": "wsl", "season": "2024-25", "date": "2024-10-06", "home": "Tottenham F", "away": "Liverpool F", "hg": 2, "ag": 3, "hst": 5, "ast": 6, "hc": 5, "ac": 6, "hy": 2, "ay": 2, "hr": 0, "ar": 0, "b365h": 2.30, "b365d": 3.40, "b365a": 2.85},
    {"league": "wsl", "season": "2024-25", "date": "2024-10-12", "home": "Arsenal F", "away": "Chelsea F", "hg": 1, "ag": 2, "hst": 5, "ast": 5, "hc": 7, "ac": 4, "hy": 2, "ay": 2, "hr": 0, "ar": 0, "b365h": 2.40, "b365d": 3.40, "b365a": 2.70},
    {"league": "wsl", "season": "2024-25", "date": "2024-10-20", "home": "West Ham F", "away": "Arsenal F", "hg": 0, "ag": 2, "hst": 2, "ast": 7, "hc": 3, "ac": 8, "hy": 2, "ay": 1, "hr": 0, "ar": 0, "b365h": 9.00, "b365d": 5.25, "b365a": 1.28},
    {"league": "wsl", "season": "2024-25", "date": "2024-11-03", "home": "Everton F", "away": "Chelsea F", "hg": 0, "ag": 5, "hst": 2, "ast": 10, "hc": 2, "ac": 8, "hy": 1, "ay": 1, "hr": 0, "ar": 0, "b365h": 11.00, "b365d": 6.00, "b365a": 1.20},
    {"league": "wsl", "season": "2024-25", "date": "2024-11-08", "home": "Arsenal F", "away": "Brighton F", "hg": 5, "ag": 0, "hst": 10, "ast": 2, "hc": 9, "ac": 3, "hy": 1, "ay": 2, "hr": 0, "ar": 0, "b365h": 1.28, "b365d": 5.50, "b365a": 8.50},
    {"league": "wsl", "season": "2024-25", "date": "2024-11-10", "home": "Liverpool F", "away": "Chelsea F", "hg": 0, "ag": 3, "hst": 2, "ast": 8, "hc": 3, "ac": 7, "hy": 2, "ay": 1, "hr": 0, "ar": 0, "b365h": 6.50, "b365d": 4.33, "b365a": 1.44},
    {"league": "wsl", "season": "2024-25", "date": "2024-11-16", "home": "Chelsea F", "away": "Manchester City F", "hg": 2, "ag": 0, "hst": 6, "ast": 3, "hc": 6, "ac": 5, "hy": 2, "ay": 2, "hr": 0, "ar": 0, "b365h": 1.95, "b365d": 3.50, "b365a": 3.50},

    # UEFA Women's Champions League (UWCL) y Ligas Europeas Femeninas
    {"league": "uwcl", "season": "2023-24", "date": "2023-11-15", "home": "Bayern Munich F", "away": "Roma F", "hg": 2, "ag": 2, "hst": 7, "ast": 5, "hc": 8, "ac": 4, "hy": 2, "ay": 2, "hr": 0, "ar": 0, "b365h": 1.55, "b365d": 4.20, "b365a": 5.00},
    {"league": "uwcl", "season": "2023-24", "date": "2023-11-23", "home": "Paris FC F", "away": "Real Madrid F", "hg": 2, "ag": 1, "hst": 5, "ast": 6, "hc": 4, "ac": 7, "hy": 2, "ay": 2, "hr": 0, "ar": 0, "b365h": 2.90, "b365d": 3.50, "b365a": 2.20},
    {"league": "uwcl", "season": "2023-24", "date": "2023-12-13", "home": "Barcelona F", "away": "Eintracht Frankfurt F", "hg": 2, "ag": 0, "hst": 9, "ast": 2, "hc": 8, "ac": 3, "hy": 1, "ay": 2, "hr": 0, "ar": 0, "b365h": 1.12, "b365d": 8.00, "b365a": 15.00},
    {"league": "uwcl", "season": "2023-24", "date": "2024-01-24", "home": "Ajax F", "away": "PSG F", "hg": 0, "ag": 4, "hst": 2, "ast": 9, "hc": 3, "ac": 8, "hy": 2, "ay": 1, "hr": 0, "ar": 0, "b365h": 5.50, "b365d": 4.33, "b365a": 1.48},
    {"league": "uwcl", "season": "2023-24", "date": "2024-01-31", "home": "Benfica F", "away": "Barcelona F", "hg": 4, "ag": 4, "hst": 6, "ast": 11, "hc": 4, "ac": 9, "hy": 2, "ay": 1, "hr": 0, "ar": 0, "b365h": 11.00, "b365d": 6.50, "b365a": 1.18},
    {"league": "uwcl", "season": "2023-24", "date": "2024-03-19", "home": "Ajax F", "away": "Chelsea F", "hg": 0, "ag": 3, "hst": 2, "ast": 8, "hc": 3, "ac": 7, "hy": 1, "ay": 1, "hr": 0, "ar": 0, "b365h": 6.50, "b365d": 4.50, "b365a": 1.40},
    {"league": "uwcl", "season": "2023-24", "date": "2024-03-20", "home": "Benfica F", "away": "Lyon F", "hg": 1, "ag": 2, "hst": 3, "ast": 8, "hc": 4, "ac": 7, "hy": 2, "ay": 1, "hr": 0, "ar": 0, "b365h": 8.50, "b365d": 5.25, "b365a": 1.28},
    {"league": "uwcl", "season": "2023-24", "date": "2024-04-20", "home": "Barcelona F", "away": "Chelsea F", "hg": 0, "ag": 1, "hst": 4, "ast": 3, "hc": 8, "ac": 3, "hy": 1, "ay": 2, "hr": 0, "ar": 0, "b365h": 1.33, "b365d": 5.00, "b365a": 7.50},
    {"league": "uwcl", "season": "2023-24", "date": "2024-04-20", "home": "Lyon F", "away": "PSG F", "hg": 3, "ag": 2, "hst": 9, "ast": 5, "hc": 8, "ac": 4, "hy": 1, "ay": 2, "hr": 0, "ar": 0, "b365h": 1.50, "b365d": 4.20, "b365a": 5.50},
    {"league": "uwcl", "season": "2023-24", "date": "2024-04-27", "home": "Chelsea F", "away": "Barcelona F", "hg": 0, "ag": 2, "hst": 3, "ast": 6, "hc": 4, "ac": 6, "hy": 2, "ay": 2, "hr": 0, "ar": 1, "b365h": 3.80, "b365d": 3.75, "b365a": 1.80},
    {"league": "uwcl", "season": "2023-24", "date": "2024-04-28", "home": "PSG F", "away": "Lyon F", "hg": 1, "ag": 2, "hst": 4, "ast": 7, "hc": 5, "ac": 6, "hy": 2, "ay": 1, "hr": 0, "ar": 0, "b365h": 3.10, "b365d": 3.60, "b365a": 2.05},
    {"league": "uwcl", "season": "2023-24", "date": "2024-05-25", "home": "Barcelona F", "away": "Lyon F", "hg": 2, "ag": 0, "hst": 6, "ast": 3, "hc": 6, "ac": 5, "hy": 1, "ay": 2, "hr": 0, "ar": 0, "b365h": 1.80, "b365d": 3.60, "b365a": 4.00},
    {"league": "uwcl", "season": "2024-25", "date": "2024-09-18", "home": "Juventus F", "away": "PSG F", "hg": 3, "ag": 1, "hst": 6, "ast": 5, "hc": 5, "ac": 6, "hy": 2, "ay": 2, "hr": 0, "ar": 0, "b365h": 3.20, "b365d": 3.50, "b365a": 2.05},
    {"league": "uwcl", "season": "2024-25", "date": "2024-09-25", "home": "Sporting CP F", "away": "Real Madrid F", "hg": 1, "ag": 2, "hst": 3, "ast": 7, "hc": 4, "ac": 7, "hy": 2, "ay": 1, "hr": 0, "ar": 0, "b365h": 4.50, "b365d": 3.90, "b365a": 1.65},
    {"league": "uwcl", "season": "2024-25", "date": "2024-10-08", "home": "Roma F", "away": "Wolfsburg F", "hg": 1, "ag": 0, "hst": 5, "ast": 4, "hc": 6, "ac": 5, "hy": 2, "ay": 2, "hr": 0, "ar": 0, "b365h": 2.80, "b365d": 3.50, "b365a": 2.25},
    {"league": "uwcl", "season": "2024-25", "date": "2024-10-08", "home": "Chelsea F", "away": "Real Madrid F", "hg": 3, "ag": 2, "hst": 7, "ast": 5, "hc": 6, "ac": 4, "hy": 1, "ay": 2, "hr": 0, "ar": 0, "b365h": 1.44, "b365d": 4.50, "b365a": 6.00},
    {"league": "uwcl", "season": "2024-25", "date": "2024-10-09", "home": "Bayern Munich F", "away": "Arsenal F", "hg": 5, "ag": 2, "hst": 9, "ast": 5, "hc": 6, "ac": 6, "hy": 1, "ay": 2, "hr": 0, "ar": 0, "b365h": 2.05, "b365d": 3.50, "b365a": 3.20},
    {"league": "uwcl", "season": "2024-25", "date": "2024-10-09", "home": "Manchester City F", "away": "Barcelona F", "hg": 2, "ag": 0, "hst": 5, "ast": 6, "hc": 5, "ac": 7, "hy": 2, "ay": 1, "hr": 0, "ar": 0, "b365h": 4.50, "b365d": 4.00, "b365a": 1.65},
    {"league": "uwcl", "season": "2024-25", "date": "2024-10-16", "home": "Juventus F", "away": "Bayern Munich F", "hg": 0, "ag": 2, "hst": 3, "ast": 7, "hc": 4, "ac": 7, "hy": 2, "ay": 1, "hr": 0, "ar": 0, "b365h": 3.80, "b365d": 3.60, "b365a": 1.85},
    {"league": "uwcl", "season": "2024-25", "date": "2024-10-17", "home": "Twente F", "away": "Chelsea F", "hg": 1, "ag": 3, "hst": 3, "ast": 8, "hc": 4, "ac": 8, "hy": 1, "ay": 1, "hr": 0, "ar": 0, "b365h": 8.00, "b365d": 5.00, "b365a": 1.30},
    {"league": "uwcl", "season": "2024-25", "date": "2024-10-17", "home": "Wolfsburg F", "away": "Lyon F", "hg": 0, "ag": 2, "hst": 4, "ast": 7, "hc": 5, "ac": 6, "hy": 2, "ay": 1, "hr": 0, "ar": 0, "b365h": 3.10, "b365d": 3.60, "b365a": 2.05},
    {"league": "uwcl", "season": "2024-25", "date": "2024-10-25", "home": "Eintracht Frankfurt F", "away": "Bayer Leverkusen F", "hg": 2, "ag": 2, "hst": 6, "ast": 5, "hc": 6, "ac": 5, "hy": 2, "ay": 2, "hr": 0, "ar": 0, "b365h": 1.75, "b365d": 3.70, "b365a": 4.10},
    {"league": "uwcl", "season": "2024-25", "date": "2024-11-03", "home": "Inter F", "away": "AC Milan F", "hg": 1, "ag": 1, "hst": 5, "ast": 4, "hc": 6, "ac": 5, "hy": 2, "ay": 2, "hr": 0, "ar": 0, "b365h": 2.15, "b365d": 3.30, "b365a": 3.10},
    {"league": "uwcl", "season": "2024-25", "date": "2024-11-09", "home": "Fiorentina F", "away": "Juventus F", "hg": 0, "ag": 3, "hst": 3, "ast": 8, "hc": 4, "ac": 7, "hy": 2, "ay": 1, "hr": 0, "ar": 0, "b365h": 3.90, "b365d": 3.60, "b365a": 1.80},
    {"league": "uwcl", "season": "2024-25", "date": "2024-11-10", "home": "AC Milan F", "away": "Fiorentina F", "hg": 1, "ag": 2, "hst": 4, "ast": 5, "hc": 5, "ac": 5, "hy": 2, "ay": 2, "hr": 0, "ar": 0, "b365h": 2.40, "b365d": 3.30, "b365a": 2.70},
    {"league": "uwcl", "season": "2024-25", "date": "2024-11-13", "home": "Roma F", "away": "Lyon F", "hg": 0, "ag": 3, "hst": 3, "ast": 9, "hc": 4, "ac": 7, "hy": 2, "ay": 1, "hr": 0, "ar": 0, "b365h": 5.50, "b365d": 4.20, "b365a": 1.50},
    {"league": "uwcl", "season": "2024-25", "date": "2024-11-13", "home": "Real Madrid F", "away": "Twente F", "hg": 7, "ag": 0, "hst": 13, "ast": 2, "hc": 9, "ac": 2, "hy": 1, "ay": 2, "hr": 0, "ar": 0, "b365h": 1.25, "b365d": 5.75, "b365a": 9.50},

    # Liga MX Femenil (México)
    {"league": "liga_mx_femenil", "season": "2023-24", "date": "2023-11-27", "home": "Tigres UANL F", "away": "América F", "hg": 0, "ag": 0, "hst": 5, "ast": 4, "hc": 6, "ac": 5, "hy": 2, "ay": 2, "hr": 0, "ar": 0, "b365h": 1.95, "b365d": 3.40, "b365a": 3.50},
    {"league": "liga_mx_femenil", "season": "2023-24", "date": "2024-03-15", "home": "Monterrey F", "away": "Tigres UANL F", "hg": 0, "ag": 0, "hst": 4, "ast": 5, "hc": 5, "ac": 6, "hy": 2, "ay": 2, "hr": 0, "ar": 0, "b365h": 2.40, "b365d": 3.30, "b365a": 2.70},
    {"league": "liga_mx_femenil", "season": "2023-24", "date": "2024-03-17", "home": "Guadalajara F", "away": "América F", "hg": 2, "ag": 1, "hst": 6, "ast": 5, "hc": 5, "ac": 6, "hy": 3, "ay": 2, "hr": 0, "ar": 0, "b365h": 2.75, "b365d": 3.40, "b365a": 2.30},
    {"league": "liga_mx_femenil", "season": "2023-24", "date": "2024-04-20", "home": "Pachuca F", "away": "Tigres UANL F", "hg": 1, "ag": 1, "hst": 5, "ast": 5, "hc": 6, "ac": 6, "hy": 2, "ay": 2, "hr": 0, "ar": 0, "b365h": 2.60, "b365d": 3.40, "b365a": 2.45},
    {"league": "liga_mx_femenil", "season": "2023-24", "date": "2024-05-27", "home": "Monterrey F", "away": "América F", "hg": 2, "ag": 1, "hst": 6, "ast": 5, "hc": 6, "ac": 5, "hy": 2, "ay": 3, "hr": 0, "ar": 0, "b365h": 2.15, "b365d": 3.30, "b365a": 3.10},
    {"league": "liga_mx_femenil", "season": "2024-25", "date": "2024-07-07", "home": "Cruz Azul F", "away": "América F", "hg": 2, "ag": 1, "hst": 5, "ast": 6, "hc": 4, "ac": 7, "hy": 2, "ay": 2, "hr": 0, "ar": 0, "b365h": 5.50, "b365d": 4.20, "b365a": 1.50},
    {"league": "liga_mx_femenil", "season": "2024-25", "date": "2024-08-19", "home": "Tigres UANL F", "away": "Pumas UNAM F", "hg": 3, "ag": 1, "hst": 8, "ast": 3, "hc": 7, "ac": 3, "hy": 1, "ay": 2, "hr": 0, "ar": 0, "b365h": 1.30, "b365d": 5.00, "b365a": 8.00},
    {"league": "liga_mx_femenil", "season": "2024-25", "date": "2024-09-01", "home": "Pachuca F", "away": "Monterrey F", "hg": 0, "ag": 0, "hst": 4, "ast": 4, "hc": 5, "ac": 5, "hy": 2, "ay": 2, "hr": 0, "ar": 0, "b365h": 2.30, "b365d": 3.30, "b365a": 2.85},
    {"league": "liga_mx_femenil", "season": "2024-25", "date": "2024-09-15", "home": "América F", "away": "Guadalajara F", "hg": 7, "ag": 0, "hst": 13, "ast": 2, "hc": 8, "ac": 3, "hy": 1, "ay": 3, "hr": 0, "ar": 0, "b365h": 1.65, "b365d": 3.80, "b365a": 4.50},
    {"league": "liga_mx_femenil", "season": "2024-25", "date": "2024-09-23", "home": "Monterrey F", "away": "América F", "hg": 2, "ag": 4, "hst": 5, "ast": 8, "hc": 5, "ac": 6, "hy": 2, "ay": 2, "hr": 0, "ar": 0, "b365h": 2.25, "b365d": 3.40, "b365a": 2.90},
    {"league": "liga_mx_femenil", "season": "2024-25", "date": "2024-10-06", "home": "Tigres UANL F", "away": "América F", "hg": 0, "ag": 1, "hst": 4, "ast": 5, "hc": 6, "ac": 5, "hy": 2, "ay": 2, "hr": 0, "ar": 0, "b365h": 2.00, "b365d": 3.40, "b365a": 3.40},
    {"league": "liga_mx_femenil", "season": "2024-25", "date": "2024-10-13", "home": "Guadalajara F", "away": "Atlas F", "hg": 3, "ag": 1, "hst": 7, "ast": 3, "hc": 6, "ac": 4, "hy": 2, "ay": 2, "hr": 0, "ar": 0, "b365h": 1.65, "b365d": 3.75, "b365a": 4.50},
    {"league": "liga_mx_femenil", "season": "2024-25", "date": "2024-10-18", "home": "Juárez F", "away": "Pachuca F", "hg": 2, "ag": 1, "hst": 5, "ast": 5, "hc": 5, "ac": 6, "hy": 2, "ay": 2, "hr": 0, "ar": 0, "b365h": 2.80, "b365d": 3.40, "b365a": 2.30},
    {"league": "liga_mx_femenil", "season": "2024-25", "date": "2024-11-01", "home": "Toluca F", "away": "Monterrey F", "hg": 1, "ag": 0, "hst": 4, "ast": 5, "hc": 4, "ac": 6, "hy": 2, "ay": 2, "hr": 0, "ar": 0, "b365h": 4.20, "b365d": 3.70, "b365a": 1.72},
    {"league": "liga_mx_femenil", "season": "2024-25", "date": "2024-11-08", "home": "Pumas UNAM F", "away": "Tigres UANL F", "hg": 0, "ag": 0, "hst": 3, "ast": 6, "hc": 4, "ac": 6, "hy": 2, "ay": 1, "hr": 0, "ar": 0, "b365h": 4.50, "b365d": 3.80, "b365a": 1.65},
    {"league": "liga_mx_femenil", "season": "2024-25", "date": "2024-11-15", "home": "América F", "away": "Tigres UANL F", "hg": 1, "ag": 1, "hst": 6, "ast": 5, "hc": 6, "ac": 5, "hy": 2, "ay": 2, "hr": 0, "ar": 0, "b365h": 2.10, "b365d": 3.30, "b365a": 3.20},
    {"league": "liga_mx_femenil", "season": "2024-25", "date": "2024-11-25", "home": "Monterrey F", "away": "Tigres UANL F", "hg": 3, "ag": 2, "hst": 7, "ast": 6, "hc": 6, "ac": 5, "hy": 3, "ay": 2, "hr": 0, "ar": 0, "b365h": 2.35, "b365d": 3.30, "b365a": 2.80},
]

def load_all_real_matches() -> List[Dict]:
    """Carga y parsea todos los partidos oficiales de las fuentes reales."""
    all_matches = []

    for league_code, sources in DATASET_SOURCES.items():
        for code, season_code in sources:
            season_map = {"2223": "2022-23", "2324": "2023-24", "2425": "2024-25"}
            season_label = season_map.get(season_code, "2024-25")
            rows = fetch_or_load_csv(code, season_code)
            for r in rows:
                try:
                    home_raw = r["HomeTeam"]
                    away_raw = r["AwayTeam"]
                    h_team = canonicalize_team_name(home_raw)
                    a_team = canonicalize_team_name(away_raw)

                    hg = int(r["FTHG"])
                    ag = int(r["FTAG"])
                    date_iso = parse_football_data_date(r.get("Date", ""))
                    
                    res_raw = r.get("FTR", "")
                    if res_raw == "H":
                        res = "W"
                    elif res_raw == "A":
                        res = "L"
                    else:
                        res = "D"

                    hst = int(r.get("HST") or 0)
                    ast = int(r.get("AST") or 0)
                    hc = int(r.get("HC") or 0)
                    ac = int(r.get("AC") or 0)
                    hy = int(r.get("HY") or 0)
                    ay = int(r.get("AY") or 0)
                    hr = int(r.get("HR") or 0)
                    ar = int(r.get("AR") or 0)

                    b365h = float(r["B365H"]) if r.get("B365H") else None
                    b365d = float(r["B365D"]) if r.get("B365D") else None
                    b365a = float(r["B365A"]) if r.get("B365A") else None

                    all_matches.append({
                        "league": league_code,
                        "season": season_label,
                        "date": date_iso,
                        "home": h_team,
                        "away": a_team,
                        "hg": hg,
                        "ag": ag,
                        "res": res,
                        "hst": hst,
                        "ast": ast,
                        "hc": hc,
                        "ac": ac,
                        "hy": hy,
                        "ay": ay,
                        "hr": hr,
                        "ar": ar,
                        "b365h": b365h,
                        "b365d": b365d,
                        "b365a": b365a
                    })
                except Exception as e:
                    continue

    # Añadir partidos oficiales curados de Champions League y Liga MX
    for m in CURATED_CHAMPIONS_MATCHES:
        all_matches.append({
            "league": m["league"],
            "season": m["season"],
            "date": m["date"],
            "home": m["home"],
            "away": m["away"],
            "hg": m["hg"],
            "ag": m["ag"],
            "res": "W" if m["hg"] > m["ag"] else ("D" if m["hg"] == m["ag"] else "L"),
            "hst": m["hst"],
            "ast": m["ast"],
            "hc": m["hc"],
            "ac": m["ac"],
            "hy": m["hy"],
            "ay": m["ay"],
            "hr": m["hr"],
            "ar": m["ar"],
            "b365h": m.get("b365h"),
            "b365d": m.get("b365d"),
            "b365a": m.get("b365a")
        })

    for m in CURATED_LIGA_MX_MATCHES:
        all_matches.append({
            "league": m["league"],
            "season": m["season"],
            "date": m["date"],
            "home": m["home"],
            "away": m["away"],
            "hg": m["hg"],
            "ag": m["ag"],
            "res": "W" if m["hg"] > m["ag"] else ("D" if m["hg"] == m["ag"] else "L"),
            "hst": m["hst"],
            "ast": m["ast"],
            "hc": m["hc"],
            "ac": m["ac"],
            "hy": m["hy"],
            "ay": m["ay"],
            "hr": m["hr"],
            "ar": m["ar"],
            "b365h": m.get("b365h"),
            "b365d": m.get("b365d"),
            "b365a": m.get("b365a")
        })

    for m in CURATED_WOMENS_MATCHES:
        all_matches.append({
            "league": m["league"],
            "season": m["season"],
            "date": m["date"],
            "home": m["home"],
            "away": m["away"],
            "hg": m["hg"],
            "ag": m["ag"],
            "res": "W" if m["hg"] > m["ag"] else ("D" if m["hg"] == m["ag"] else "L"),
            "hst": m["hst"],
            "ast": m["ast"],
            "hc": m["hc"],
            "ac": m["ac"],
            "hy": m["hy"],
            "ay": m["ay"],
            "hr": m["hr"],
            "ar": m["ar"],
            "b365h": m.get("b365h"),
            "b365d": m.get("b365d"),
            "b365a": m.get("b365a")
        })

    # Ordenar cronológicamente por fecha de forma estricta
    all_matches.sort(key=lambda x: (x["date"], x["league"], x["home"]))
    logger.info(f"Cargados {len(all_matches)} partidos reales ordenados cronológicamente.")
    return all_matches

def populate_real_database_and_compute_elo(db=None):
    """
    Rellena la base de datos con partidos reales oficiales y calcula el rating Elo dinámico
    y estadísticas móviles históricas.
    """
    local_session = False
    if db is None:
        db = SessionLocal()
        local_session = True

    try:
        from backend.app.services.league_database import LEAGUES_CONFIG, TEAMS_CONFIG
        
        # 1. Asegurar ligas
        for lc in LEAGUES_CONFIG:
            existing = db.query(League).filter(League.code == lc["code"]).first()
            if not existing:
                l = League(
                    code=lc["code"], name=lc["name"], country=lc["country"],
                    avg_goals=lc["avg_goals"], home_adv=lc["home_adv"],
                    avg_corners=lc["avg_corners"], avg_cards=lc["avg_cards"],
                    rho=lc["rho"]
                )
                db.add(l)
        db.commit()

        # 2. Cargar todos los partidos reales
        real_matches = load_all_real_matches()
        if not real_matches:
            logger.error("No se pudieron cargar partidos reales.")
            return

        # 3. Limpiar partidos anteriores y cachés
        db.query(HistoricalMatch).delete()
        db.query(TeamStatsCache).delete()
        db.commit()

        # 4. Asegurar catálogo de equipos (incorporando los nuevos de las grandes ligas masculinas y femeninas)
        existing_teams = {t.name: t for t in db.query(Team).all()}
        all_league_teams = set()
        for tc in TEAMS_CONFIG:
            all_league_teams.add((tc["name"], tc["league"]))
        for m in real_matches:
            all_league_teams.add((m["home"], m["league"]))
            all_league_teams.add((m["away"], m["league"]))

        for t_name, l_code in all_league_teams:
            base_cfg = next((tc for tc in TEAMS_CONFIG if tc["name"] == t_name), None)
            if t_name not in existing_teams:
                aliases = base_cfg["aliases"] if base_cfg else t_name.lower()
                elo_init = base_cfg["elo"] if base_cfg else 1600.0
                cfg_league = base_cfg["league"] if base_cfg else l_code
                new_t = Team(
                    league_code=cfg_league,
                    name=t_name,
                    canonical_name=t_name,
                    aliases=aliases,
                    elo_rating=elo_init
                )
                db.add(new_t)
                existing_teams[t_name] = new_t
            elif base_cfg is not None:
                existing_teams[t_name].aliases = base_cfg["aliases"]
                existing_teams[t_name].league_code = base_cfg["league"]
        db.commit()

        # 5. Inicializar ratings Elo a los valores base pre-2022-23 sin sesgo retrospectivo
        base_elo_map = get_honest_initial_elo_map()
        elo_tracker = {}
        for t in db.query(Team).all():
            init_val = base_elo_map.get(t.name, 1600.0)
            t.elo_rating = init_val
            elo_tracker[t.name] = init_val

        # Seguimiento móvil por equipo de partidos jugados
        team_match_history = {t_name: [] for t_name in elo_tracker}
        team_last_season = {}

        # 6. Insertar partidos y actualizar Elo cronológicamente (con regresión neutral a 1650.0 entre temporadas)
        db_match_objects = []
        for m in real_matches:
            h_name = m["home"]
            a_name = m["away"]
            cur_season = m["season"]

            for club in (h_name, a_name):
                prev_s = team_last_season.get(club)
                if prev_s is not None and prev_s != cur_season:
                    # Regresión a la media neutral de liga (1650.0) del 15% al cambiar de temporada (cero sesgo retrospectivo)
                    elo_tracker[club] = 0.85 * elo_tracker.get(club, 1600.0) + 0.15 * 1650.0
                team_last_season[club] = cur_season

            cur_elo_h = elo_tracker.get(h_name, 1600.0)
            cur_elo_a = elo_tracker.get(a_name, 1600.0)

            # Actualizar Elo dinámico con el resultado real
            new_elo_h, new_elo_a = calculate_elo_update(
                cur_elo_h, cur_elo_a, m["hg"], m["ag"]
            )
            elo_tracker[h_name] = new_elo_h
            elo_tracker[a_name] = new_elo_a

            cards_h = m["hy"] + m["hr"] * 2
            cards_a = m["ay"] + m["ar"] * 2
            cn_tot = m["hc"] + m["ac"]
            cr_tot = cards_h + cards_a

            hm = HistoricalMatch(
                league_code=m["league"],
                season=m["season"],
                match_date=m["date"],
                home_team=h_name,
                away_team=a_name,
                home_goals=m["hg"],
                away_goals=m["ag"],
                result=m["res"],
                home_shots_target=m["hst"],
                away_shots_target=m["ast"],
                corners_home=m["hc"],
                corners_away=m["ac"],
                cards_home=cards_h,
                cards_away=cards_a,
                b365_home_odds=m["b365h"],
                b365_draw_odds=m["b365d"],
                b365_away_odds=m["b365a"]
            )
            db_match_objects.append(hm)

            # Guardar en historial móvil para reconstrucción unificada de stats
            if h_name in team_match_history:
                team_match_history[h_name].append({
                    "opp": a_name, "was_home": True, "date": m["date"],
                    "gf": m["hg"], "ga": m["ag"], "res": m["res"],
                    "hst": m["hst"], "ast": m["ast"],
                    "cn": m["hc"], "cn_opp": m["ac"], "cr": cards_h,
                    "cn_tot": cn_tot, "cr_tot": cr_tot
                })
            if a_name in team_match_history:
                team_match_history[a_name].append({
                    "opp": h_name, "was_home": False, "date": m["date"],
                    "gf": m["ag"], "ga": m["hg"],
                    "res": "W" if m["res"] == "L" else ("L" if m["res"] == "W" else "D"),
                    "hst": m["ast"], "ast": m["hst"],
                    "cn": m["ac"], "cn_opp": m["hc"], "cr": cards_a,
                    "cn_tot": cn_tot, "cr_tot": cr_tot
                })

        db.bulk_save_objects(db_match_objects)
        db.commit()
        logger.info(f"Guardados {len(db_match_objects)} partidos reales oficiales en SQLite.")

        # 6.5. Actualizar promedios empíricos reales por liga desde los partidos oficiales cargados
        for l_obj in db.query(League).all():
            lg_matches = [m for m in real_matches if m["league"] == l_obj.code]
            if len(lg_matches) >= 30:
                tot_g = sum(m["hg"] + m["ag"] for m in lg_matches) / len(lg_matches)
                l_obj.avg_goals = round(tot_g / 2.0, 2)
                cn_valid = [m["hc"] + m["ac"] for m in lg_matches if (m["hc"] + m["ac"]) > 0]
                if cn_valid:
                    l_obj.avg_corners = round(sum(cn_valid) / len(cn_valid), 1)
                cr_valid = [(m["hy"] + m["hr"] * 2 + m["ay"] + m["ar"] * 2) for m in lg_matches if (m["hy"] + m["ay"]) > 0]
                if cr_valid:
                    l_obj.avg_cards = round(sum(cr_valid) / len(cr_valid), 1)
        db.commit()

        # 7. Actualizar Team.elo_rating y TeamStatsCache usando la misma lógica Point-in-Time unificada
        league_map = {l.code: l for l in db.query(League).all()}
        for t in db.query(Team).all():
            final_elo = round(elo_tracker.get(t.name, 1600.0), 1)
            t.elo_rating = final_elo

            hist = team_match_history.get(t.name, [])
            if not hist:
                continue

            l_obj = league_map.get(t.league_code)
            def_goals = l_obj.avg_goals if l_obj else 1.35

            last_15 = hist[-15:]
            last_10 = hist[-10:]
            last_5 = hist[-5:]

            gf_all = [x["gf"] for x in last_15]
            ga_all = [x["ga"] for x in last_15]
            cn_all = [x["cn"] for x in last_15]
            cn_opp_all = [x.get("cn_opp", 4.5) for x in last_15]
            cr_all = [x["cr"] for x in last_15]
            sot_for_all = [x["hst"] for x in last_15]
            sot_against_all = [x["ast"] for x in last_15]

            # Shrinkage empírico de James-Stein hacia el prior estructural (idéntico a entrenamiento y walk-forward)
            elo_diff_t = (final_elo - 1650.0) / 400.0
            prior_gf = max(0.7, def_goals * (1.0 + 0.18 * elo_diff_t))
            prior_ga = max(0.6, def_goals * (1.0 - 0.15 * elo_diff_t))

            raw_gf = sum(gf_all) / len(gf_all)
            raw_ga = sum(ga_all) / len(ga_all)
            shrunk_gf = round(0.75 * raw_gf + 0.25 * prior_gf, 2)
            shrunk_ga = round(0.75 * raw_ga + 0.25 * prior_ga, 2)

            # Splits de local y visitante con el mismo shrinkage
            home_matches = [x for x in hist if x["was_home"]][-10:]
            away_matches = [x for x in hist if not x["was_home"]][-10:]

            h_gf = round(0.75 * (sum(x["gf"] for x in home_matches) / len(home_matches)) + 0.25 * prior_gf, 2) if home_matches else shrunk_gf
            h_ga = round(0.75 * (sum(x["ga"] for x in home_matches) / len(home_matches)) + 0.25 * prior_ga, 2) if home_matches else shrunk_ga
            a_gf = round(0.75 * (sum(x["gf"] for x in away_matches) / len(away_matches)) + 0.25 * prior_gf, 2) if away_matches else shrunk_gf
            a_ga = round(0.75 * (sum(x["ga"] for x in away_matches) / len(away_matches)) + 0.25 * prior_ga, 2) if away_matches else shrunk_ga

            w5 = sum(1 for x in last_5 if x["res"] == "W")
            wr_5 = round(w5 / max(1, len(last_5)), 2)

            # JSON estructurado para el ensamble (con cards_total = tarjetas totales del partido)
            matches_json = []
            for x in reversed(last_10):  # Más reciente primero
                matches_json.append({
                    "opponent": x["opp"],
                    "was_home": x["was_home"],
                    "goals_for": x["gf"],
                    "goals_against": x["ga"],
                    "result": x["res"],
                    "date": x["date"],
                    "corners_for": x["cn"],
                    "cards_total": x.get("cr_tot", x["cr"] * 2)
                })

            cache_obj = TeamStatsCache(
                team_name=t.name,
                league_code=t.league_code,
                elo_rating=final_elo,
                avg_goals_scored=shrunk_gf,
                avg_goals_conceded=shrunk_ga,
                home_goals_scored=h_gf,
                home_goals_conceded=h_ga,
                away_goals_scored=a_gf,
                away_goals_conceded=a_ga,
                avg_shots_target_for=round(sum(sot_for_all) / len(sot_for_all), 1),
                avg_shots_target_against=round(sum(sot_against_all) / len(sot_against_all), 1),
                avg_corners=round(sum(cn_all) / len(cn_all), 1),
                avg_corners_conceded=round(sum(cn_opp_all) / len(cn_opp_all), 1),
                avg_cards=round(sum(cr_all) / len(cr_all), 1),
                win_rate_last_5=wr_5,
                last_matches_json=matches_json,
                updated_at=datetime.utcnow()
            )
            db.add(cache_obj)

        db.commit()
        logger.info(f"✅ Base de datos poblada exitosamente con datos reales y Elo dinámico de {len(elo_tracker)} clubes.")
    finally:
        if local_session:
            db.close()


def get_honest_initial_elo_map() -> Dict[str, float]:
    """
    Retorna el mapa de ratings Elo iniciales pre-temporada 2022-23 sin sesgo retrospectivo.
    Clubes que tuvieron temporadas revelación en 2023-24 (como Bayer Leverkusen, Girona o Stuttgart)
    parten de su nivel histórico previo real y ganan su Elo exclusivamente a través de sus resultados en cancha.
    """
    from backend.app.services.league_database import TEAMS_CONFIG
    base_map = {tc["name"]: float(tc["elo"]) for tc in TEAMS_CONFIG}
    base_map.update({
        "Bayer Leverkusen": 1775.0,
        "Girona": 1640.0,
        "Stuttgart": 1650.0,
        "Aston Villa": 1730.0,
    })
    return base_map


def build_point_in_time_match_features(
    h_name: str,
    a_name: str,
    comp_name: str,
    cur_elo_h: float,
    cur_elo_a: float,
    h_hist: List[Dict],
    a_hist: List[Dict],
    def_goals: float = 1.35,
    def_corners: float = 9.5,
    def_cards: float = 4.0,
):
    """
    Constructor canónico unificado de MatchRawFeatures Point-in-Time.
    Usado de forma idéntica por el pipeline de entrenamiento (train_models.py) y por la
    evaluación Walk-Forward (backtest.py) para garantizar cero desajuste entre entrenamiento y producción.
    """
    from backend.app.schemas.match import MatchRawFeatures, TeamFormStats, HeadToHeadStats, PreviousMatch

    if len(h_hist) < 2 or len(a_hist) < 2:
        return MatchRawFeatures(
            home_team=h_name,
            away_team=a_name,
            competition=comp_name,
            home_stats=TeamFormStats(team_name=h_name, avg_goals_scored=def_goals * 1.05, avg_goals_conceded=def_goals * 0.95, elo_rating=round(cur_elo_h, 1)),
            away_stats=TeamFormStats(team_name=a_name, avg_goals_scored=def_goals * 0.95, avg_goals_conceded=def_goals * 1.05, elo_rating=round(cur_elo_a, 1)),
            h2h=HeadToHeadStats(total_matches_analyzed=0, avg_total_goals_h2h=def_goals * 2.0)
        )

    last_15_h = h_hist[-15:]
    last_15_a = a_hist[-15:]
    last_10_h = last_15_h[-10:]
    last_10_a = last_15_a[-10:]
    last_5_h = last_15_h[-5:]
    last_5_a = last_15_a[-5:]

    home_matches_h = [x for x in h_hist if x["was_home"]][-10:]
    away_matches_a = [x for x in a_hist if not x["was_home"]][-10:]

    elo_diff_h = (cur_elo_h - 1650.0) / 400.0
    elo_diff_a = (cur_elo_a - 1650.0) / 400.0
    prior_h_gf = max(0.7, def_goals * (1.0 + 0.18 * elo_diff_h))
    prior_h_ga = max(0.6, def_goals * (1.0 - 0.15 * elo_diff_h))
    prior_a_gf = max(0.7, def_goals * (1.0 + 0.18 * elo_diff_a))
    prior_a_ga = max(0.6, def_goals * (1.0 - 0.15 * elo_diff_a))

    raw_h_gf = sum(x["gf"] for x in last_15_h) / len(last_15_h)
    raw_h_ga = sum(x["ga"] for x in last_15_h) / len(last_15_h)
    raw_a_gf = sum(x["gf"] for x in last_15_a) / len(last_15_a)
    raw_a_ga = sum(x["ga"] for x in last_15_a) / len(last_15_a)

    h_gf = round(0.75 * raw_h_gf + 0.25 * prior_h_gf, 2)
    h_ga = round(0.75 * raw_h_ga + 0.25 * prior_h_ga, 2)
    a_gf = round(0.75 * raw_a_gf + 0.25 * prior_a_gf, 2)
    a_ga = round(0.75 * raw_a_ga + 0.25 * prior_a_ga, 2)

    h_home_gf = round(0.75 * (sum(x["gf"] for x in home_matches_h) / len(home_matches_h)) + 0.25 * prior_h_gf, 2) if home_matches_h else h_gf
    h_home_ga = round(0.75 * (sum(x["ga"] for x in home_matches_h) / len(home_matches_h)) + 0.25 * prior_h_ga, 2) if home_matches_h else h_ga
    a_away_gf = round(0.75 * (sum(x["gf"] for x in away_matches_a) / len(away_matches_a)) + 0.25 * prior_a_gf, 2) if away_matches_a else a_gf
    a_away_ga = round(0.75 * (sum(x["ga"] for x in away_matches_a) / len(away_matches_a)) + 0.25 * prior_a_ga, 2) if away_matches_a else a_ga

    h_prev_objs = [
        PreviousMatch(
            opponent=x["opp"], was_home=x["was_home"], goals_for=int(x["gf"]), goals_against=int(x["ga"]),
            result=x["res"], corners_for=float(x["cn"]), cards_total=float(x.get("cr_tot", x["cr"] * 2))
        ) for x in reversed(last_10_h)
    ]
    a_prev_objs = [
        PreviousMatch(
            opponent=x["opp"], was_home=x["was_home"], goals_for=int(x["gf"]), goals_against=int(x["ga"]),
            result=x["res"], corners_for=float(x["cn"]), cards_total=float(x.get("cr_tot", x["cr"] * 2))
        ) for x in reversed(last_10_a)
    ]

    past_h2h = [x for x in h_hist if x["opp"] == a_name][-8:]
    if past_h2h:
        h_w = sum(1 for x in past_h2h if x["res"] == "W")
        a_w = sum(1 for x in past_h2h if x["res"] == "L")
        drw = sum(1 for x in past_h2h if x["res"] == "D")
        h2h_g = round(sum(x["gf"] + x["ga"] for x in past_h2h) / len(past_h2h), 2)
        h2h_cn = round(sum(x.get("cn_tot", x["cn"] * 2) for x in past_h2h) / len(past_h2h), 1)
        h2h_cr = round(sum(x.get("cr_tot", x["cr"] * 2) for x in past_h2h) / len(past_h2h), 1)
    else:
        h_w, a_w, drw = 0, 0, 0
        h2h_g = round(def_goals * 2.0, 2)
        h2h_cn = def_corners
        h2h_cr = def_cards

    return MatchRawFeatures(
        home_team=h_name,
        away_team=a_name,
        competition=comp_name,
        is_live=False,
        home_stats=TeamFormStats(
            team_name=h_name,
            avg_goals_scored=h_gf,
            avg_goals_conceded=h_ga,
            avg_corners=round(sum(x["cn"] for x in last_15_h) / len(last_15_h), 1),
            avg_corners_conceded=round(sum(x.get("cn_opp", 4.5) for x in last_15_h) / len(last_15_h), 1),
            avg_cards=round(sum(x["cr"] for x in last_15_h) / len(last_15_h), 1),
            win_rate_last_5=round(sum(1 for x in last_5_h if x["res"] == "W") / len(last_5_h), 2),
            last_matches=h_prev_objs,
            elo_rating=round(cur_elo_h, 1),
            home_goals_scored=h_home_gf,
            home_goals_conceded=h_home_ga,
            avg_shots_target_for=round(sum(x["hst"] for x in last_15_h) / len(last_15_h), 1),
            avg_shots_target_against=round(sum(x["ast"] for x in last_15_h) / len(last_15_h), 1)
        ),
        away_stats=TeamFormStats(
            team_name=a_name,
            avg_goals_scored=a_gf,
            avg_goals_conceded=a_ga,
            avg_corners=round(sum(x["cn"] for x in last_15_a) / len(last_15_a), 1),
            avg_corners_conceded=round(sum(x.get("cn_opp", 4.8) for x in last_15_a) / len(last_15_a), 1),
            avg_cards=round(sum(x["cr"] for x in last_15_a) / len(last_15_a), 1),
            win_rate_last_5=round(sum(1 for x in last_5_a if x["res"] == "W") / len(last_5_a), 2),
            last_matches=a_prev_objs,
            elo_rating=round(cur_elo_a, 1),
            away_goals_scored=a_away_gf,
            away_goals_conceded=a_away_ga,
            avg_shots_target_for=round(sum(x["hst"] for x in last_15_a) / len(last_15_a), 1),
            avg_shots_target_against=round(sum(x["ast"] for x in last_15_a) / len(last_15_a), 1)
        ),
        h2h=HeadToHeadStats(
            total_matches_analyzed=len(past_h2h),
            home_team_wins=h_w,
            away_team_wins=a_w,
            draws=drw,
            avg_total_goals_h2h=h2h_g,
            avg_total_corners_h2h=h2h_cn,
            avg_total_cards_h2h=h2h_cr
        )
    )


if __name__ == "__main__":
    populate_real_database_and_compute_elo()
