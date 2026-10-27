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

# Mapeo de ligas a códigos y temporadas
DATASET_SOURCES = {
    "premier_league": [("E0", "2324"), ("E0", "2425")],
    "laliga": [("SP1", "2324"), ("SP1", "2425")],
    "serie_a": [("I1", "2324"), ("I1", "2425")],
    "bundesliga": [("D1", "2324"), ("D1", "2425")],
    "ligue_1": [("F1", "2324"), ("F1", "2425")]
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
    "Le Havre": "Le Havre"
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

def load_all_real_matches() -> List[Dict]:
    """Carga y parsea todos los partidos oficiales de las fuentes reales."""
    all_matches = []

    for league_code, sources in DATASET_SOURCES.items():
        for code, season_code in sources:
            season_label = "2023-24" if season_code == "2324" else "2024-25"
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

        # 4. Asegurar catálogo de equipos (incorporando los nuevos de las 5 grandes ligas)
        existing_teams = {t.name: t for t in db.query(Team).all()}
        all_league_teams = set()
        for m in real_matches:
            all_league_teams.add((m["home"], m["league"]))
            all_league_teams.add((m["away"], m["league"]))

        for t_name, l_code in all_league_teams:
            if t_name not in existing_teams:
                # Buscar si hay alias en TEAMS_CONFIG
                base_cfg = next((tc for tc in TEAMS_CONFIG if tc["name"] == t_name), None)
                aliases = base_cfg["aliases"] if base_cfg else t_name.lower()
                elo_init = base_cfg["elo"] if base_cfg else 1600.0
                new_t = Team(
                    league_code=l_code,
                    name=t_name,
                    canonical_name=t_name,
                    aliases=aliases,
                    elo_rating=elo_init
                )
                db.add(new_t)
                existing_teams[t_name] = new_t
        db.commit()

        # 5. Inicializar ratings Elo
        elo_tracker = {}
        for t in db.query(Team).all():
            elo_tracker[t.name] = float(t.elo_rating or 1600.0)

        # Seguimiento móvil por equipo de partidos jugados
        team_match_history = {t_name: [] for t_name in elo_tracker}

        # 6. Insertar partidos y actualizar Elo cronológicamente
        db_match_objects = []
        for m in real_matches:
            h_name = m["home"]
            a_name = m["away"]

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

            # Guardar en historial móvil para reconstrucción de stats
            if h_name in team_match_history:
                team_match_history[h_name].append({
                    "opp": a_name, "was_home": True, "date": m["date"],
                    "gf": m["hg"], "ga": m["ag"], "res": m["res"],
                    "hst": m["hst"], "ast": m["ast"],
                    "cn": m["hc"], "cr": cards_h
                })
            if a_name in team_match_history:
                team_match_history[a_name].append({
                    "opp": h_name, "was_home": False, "date": m["date"],
                    "gf": m["ag"], "ga": m["hg"],
                    "res": "W" if m["res"] == "L" else ("L" if m["res"] == "W" else "D"),
                    "hst": m["ast"], "ast": m["hst"],
                    "cn": m["ac"], "cr": cards_a
                })

        db.bulk_save_objects(db_match_objects)
        db.commit()
        logger.info(f"Guardados {len(db_match_objects)} partidos reales oficiales en SQLite.")

        # 7. Actualizar Team.elo_rating y TeamStatsCache
        for t in db.query(Team).all():
            final_elo = round(elo_tracker.get(t.name, 1600.0), 1)
            t.elo_rating = final_elo

            hist = team_match_history.get(t.name, [])
            if not hist:
                continue

            last_15 = hist[-15:]
            last_10 = hist[-10:]
            last_5 = hist[-5:]

            gf_all = [x["gf"] for x in last_15]
            ga_all = [x["ga"] for x in last_15]
            cn_all = [x["cn"] for x in last_15]
            cr_all = [x["cr"] for x in last_15]
            sot_for_all = [x["hst"] for x in last_15]
            sot_against_all = [x["ast"] for x in last_15]

            # Splits de local y visitante
            home_matches = [x for x in hist if x["was_home"]][-10:]
            away_matches = [x for x in hist if not x["was_home"]][-10:]

            h_gf = round(sum(x["gf"] for x in home_matches) / max(1, len(home_matches)), 2) if home_matches else round(sum(gf_all) / len(gf_all), 2)
            h_ga = round(sum(x["ga"] for x in home_matches) / max(1, len(home_matches)), 2) if home_matches else round(sum(ga_all) / len(ga_all), 2)
            a_gf = round(sum(x["gf"] for x in away_matches) / max(1, len(away_matches)), 2) if away_matches else round(sum(gf_all) / len(gf_all), 2)
            a_ga = round(sum(x["ga"] for x in away_matches) / max(1, len(away_matches)), 2) if away_matches else round(sum(ga_all) / len(ga_all), 2)

            w5 = sum(1 for x in last_5 if x["res"] == "W")
            wr_5 = round(w5 / max(1, len(last_5)), 2)

            # JSON estructurado para el ensamble
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
                    "cards_total": x["cr"]
                })

            cache_obj = TeamStatsCache(
                team_name=t.name,
                league_code=t.league_code,
                elo_rating=final_elo,
                avg_goals_scored=round(sum(gf_all) / len(gf_all), 2),
                avg_goals_conceded=round(sum(ga_all) / len(ga_all), 2),
                home_goals_scored=h_gf,
                home_goals_conceded=h_ga,
                away_goals_scored=a_gf,
                away_goals_conceded=a_ga,
                avg_shots_target_for=round(sum(sot_for_all) / len(sot_for_all), 1),
                avg_shots_target_against=round(sum(sot_against_all) / len(sot_against_all), 1),
                avg_corners=round(sum(cn_all) / len(cn_all), 1),
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

if __name__ == "__main__":
    populate_real_database_and_compute_elo()
