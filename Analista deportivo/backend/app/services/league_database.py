"""
Módulo de Gestión de Base de Datos para Ligas Grandes (Katakuri v3.7).
Permite acceso instantáneo (<10ms) a estadísticas oficiales, clasificaciones,
historial H2H, rating Elo y partidos recientes sin necesidad de scraping web ni consumo de LLM.
"""
import logging
import re
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from sqlalchemy import or_, and_, desc
from backend.app.db import SessionLocal, League, Team, HistoricalMatch, TeamStatsCache
from backend.app.schemas.match import MatchRawFeatures, TeamFormStats, HeadToHeadStats, PreviousMatch

logger = logging.getLogger(__name__)

# Definición de competiciones oficiales con parámetros basales y correlación Dixon-Coles calibrada (rho)
LEAGUES_CONFIG = [
    {
        "code": "premier_league",
        "name": "Premier League",
        "country": "Inglaterra",
        "avg_goals": 1.41,
        "home_adv": 1.12,
        "avg_corners": 10.1,
        "avg_cards": 4.1,
        "rho": -0.10
    },
    {
        "code": "laliga",
        "name": "LaLiga",
        "country": "España",
        "avg_goals": 1.26,
        "home_adv": 1.14,
        "avg_corners": 9.2,
        "avg_cards": 4.5,
        "rho": -0.11
    },
    {
        "code": "serie_a",
        "name": "Serie A",
        "country": "Italia",
        "avg_goals": 1.29,
        "home_adv": 1.14,
        "avg_corners": 9.5,
        "avg_cards": 4.3,
        "rho": -0.13
    },
    {
        "code": "bundesliga",
        "name": "Bundesliga",
        "country": "Alemania",
        "avg_goals": 1.54,
        "home_adv": 1.11,
        "avg_corners": 9.7,
        "avg_cards": 3.8,
        "rho": -0.05
    },
    {
        "code": "ligue_1",
        "name": "Ligue 1",
        "country": "Francia",
        "avg_goals": 1.28,
        "home_adv": 1.13,
        "avg_corners": 9.3,
        "avg_cards": 3.9,
        "rho": -0.10
    },
    {
        "code": "champions_league",
        "name": "Champions League",
        "country": "Europa",
        "avg_goals": 1.48,
        "home_adv": 1.11,
        "avg_corners": 9.8,
        "avg_cards": 4.2,
        "rho": -0.08
    },
    {
        "code": "liga_mx",
        "name": "Liga MX",
        "country": "México",
        "avg_goals": 1.31,
        "home_adv": 1.18,
        "avg_corners": 9.4,
        "avg_cards": 4.6,
        "rho": -0.11
    },
    {
        "code": "eredivisie",
        "name": "Eredivisie",
        "country": "Países Bajos",
        "avg_goals": 1.52,
        "home_adv": 1.14,
        "avg_corners": 10.2,
        "avg_cards": 3.4,
        "rho": -0.04
    },
    {
        "code": "primeira_liga",
        "name": "Primeira Liga",
        "country": "Portugal",
        "avg_goals": 1.33,
        "home_adv": 1.15,
        "avg_corners": 9.9,
        "avg_cards": 4.8,
        "rho": -0.10
    },
    {
        "code": "liga_f",
        "name": "Liga F Femenina",
        "country": "España",
        "avg_goals": 1.58,
        "home_adv": 1.13,
        "avg_corners": 9.4,
        "avg_cards": 3.2,
        "rho": -0.07
    },
    {
        "code": "wsl",
        "name": "Women's Super League",
        "country": "Inglaterra",
        "avg_goals": 1.62,
        "home_adv": 1.12,
        "avg_corners": 9.8,
        "avg_cards": 3.1,
        "rho": -0.06
    },
    {
        "code": "uwcl",
        "name": "Champions Femenina",
        "country": "Europa",
        "avg_goals": 1.68,
        "home_adv": 1.12,
        "avg_corners": 9.7,
        "avg_cards": 3.3,
        "rho": -0.06
    },
    {
        "code": "liga_mx_femenil",
        "name": "Liga MX Femenil",
        "country": "México",
        "avg_goals": 1.64,
        "home_adv": 1.15,
        "avg_corners": 9.3,
        "avg_cards": 3.6,
        "rho": -0.07
    }
]

# Catálogo oficial de equipos con alias y elo inicial
TEAMS_CONFIG = [
    # Premier League
    {"name": "Manchester City", "league": "premier_league", "elo": 1960.0, "aliases": "man city,manchester city,mcfc,city"},
    {"name": "Arsenal", "league": "premier_league", "elo": 1920.0, "aliases": "arsenal,afc,gunners"},
    {"name": "Liverpool", "league": "premier_league", "elo": 1940.0, "aliases": "liverpool,lfc,reds"},
    {"name": "Aston Villa", "league": "premier_league", "elo": 1730.0, "aliases": "aston villa,villa,avfc"},
    {"name": "Tottenham", "league": "premier_league", "elo": 1770.0, "aliases": "tottenham,tottenham hotspur,spurs,thfc"},
    {"name": "Chelsea", "league": "premier_league", "elo": 1790.0, "aliases": "chelsea,cfc,blues"},
    {"name": "Newcastle", "league": "premier_league", "elo": 1760.0, "aliases": "newcastle,newcastle united,magpies"},
    {"name": "Manchester United", "league": "premier_league", "elo": 1750.0, "aliases": "man united,manchester united,mufc,man utd"},
    {"name": "Brighton", "league": "premier_league", "elo": 1710.0, "aliases": "brighton,brighton and hove albion,seagulls"},
    {"name": "West Ham", "league": "premier_league", "elo": 1690.0, "aliases": "west ham,west ham united,hammers"},

    # LaLiga
    {"name": "Real Madrid", "league": "laliga", "elo": 1970.0, "aliases": "real madrid,madrid,rm,real madrid cf,los blancos,merengues"},
    {"name": "Barcelona", "league": "laliga", "elo": 1930.0, "aliases": "barcelona,fc barcelona,barca,culés,blaugrana"},
    {"name": "Atletico Madrid", "league": "laliga", "elo": 1840.0, "aliases": "atletico madrid,atleti,atlético de madrid,colchoneros"},
    {"name": "Athletic Bilbao", "league": "laliga", "elo": 1780.0, "aliases": "athletic bilbao,athletic club,bilbao,leones"},
    {"name": "Real Sociedad", "league": "laliga", "elo": 1760.0, "aliases": "real sociedad,la real,txuri-urdin"},
    {"name": "Villarreal", "league": "laliga", "elo": 1750.0, "aliases": "villarreal,submarino amarillo"},
    {"name": "Real Betis", "league": "laliga", "elo": 1730.0, "aliases": "real betis,betis,béticos"},
    {"name": "Girona", "league": "laliga", "elo": 1640.0, "aliases": "girona,girona fc"},
    {"name": "Sevilla", "league": "laliga", "elo": 1690.0, "aliases": "sevilla,sevilla fc,palanganas"},
    {"name": "Valencia", "league": "laliga", "elo": 1660.0, "aliases": "valencia,valencia cf,che"},

    # Serie A
    {"name": "Inter", "league": "serie_a", "elo": 1910.0, "aliases": "inter,inter milan,internazionale,nerazzurri"},
    {"name": "Juventus", "league": "serie_a", "elo": 1830.0, "aliases": "juventus,juve,vecchia signora,bianconeri"},
    {"name": "AC Milan", "league": "serie_a", "elo": 1820.0, "aliases": "ac milan,milan,rossoneri"},
    {"name": "Napoli", "league": "serie_a", "elo": 1840.0, "aliases": "napoli,napoles,partenopei"},
    {"name": "Atalanta", "league": "serie_a", "elo": 1810.0, "aliases": "atalanta,dea"},
    {"name": "Roma", "league": "serie_a", "elo": 1750.0, "aliases": "roma,as roma,giallorossi"},
    {"name": "Lazio", "league": "serie_a", "elo": 1750.0, "aliases": "lazio,biancocelesti"},
    {"name": "Fiorentina", "league": "serie_a", "elo": 1720.0, "aliases": "fiorentina,viola"},

    # Bundesliga
    {"name": "Bayern Munich", "league": "bundesliga", "elo": 1930.0, "aliases": "bayern,bayern munich,bayern münchen,bavaria"},
    {"name": "Bayer Leverkusen", "league": "bundesliga", "elo": 1775.0, "aliases": "leverkusen,bayer leverkusen,werkself"},
    {"name": "Borussia Dortmund", "league": "bundesliga", "elo": 1820.0, "aliases": "dortmund,borussia dortmund,bvb"},
    {"name": "RB Leipzig", "league": "bundesliga", "elo": 1810.0, "aliases": "leipzig,rb leipzig,red bull leipzig"},
    {"name": "Stuttgart", "league": "bundesliga", "elo": 1650.0, "aliases": "stuttgart,vfb stuttgart"},
    {"name": "Eintracht Frankfurt", "league": "bundesliga", "elo": 1730.0, "aliases": "frankfurt,eintracht frankfurt,eintracht"},

    # Ligue 1
    {"name": "PSG", "league": "ligue_1", "elo": 1890.0, "aliases": "psg,paris saint-germain,paris sg,paris"},
    {"name": "Monaco", "league": "ligue_1", "elo": 1780.0, "aliases": "monaco,as monaco"},
    {"name": "Marseille", "league": "ligue_1", "elo": 1750.0, "aliases": "marseille,olympique de marseille,om"},
    {"name": "Lille", "league": "ligue_1", "elo": 1760.0, "aliases": "lille,losc lille"},
    {"name": "Lyon", "league": "ligue_1", "elo": 1720.0, "aliases": "lyon,olympique lyonnais,ol"},

    # Liga MX
    {"name": "América", "league": "liga_mx", "elo": 1640.0, "aliases": "américa,club américa,aguilas"},
    {"name": "Monterrey", "league": "liga_mx", "elo": 1610.0, "aliases": "monterrey,rayados"},
    {"name": "Tigres UANL", "league": "liga_mx", "elo": 1610.0, "aliases": "tigres,tigres uanl"},
    {"name": "Cruz Azul", "league": "liga_mx", "elo": 1600.0, "aliases": "cruz azul,la máquina,cementeros"},
    {"name": "Guadalajara", "league": "liga_mx", "elo": 1570.0, "aliases": "guadalajara,chivas,rebaño sagrado"},
    {"name": "Toluca", "league": "liga_mx", "elo": 1580.0, "aliases": "toluca,diablos rojos"},
    {"name": "Pachuca", "league": "liga_mx", "elo": 1560.0, "aliases": "pachuca,tuzos"},
    {"name": "Pumas UNAM", "league": "liga_mx", "elo": 1540.0, "aliases": "pumas,pumas unam,universidad"},

    # Eredivisie
    {"name": "PSV Eindhoven", "league": "eredivisie", "elo": 1850.0, "aliases": "psv,psv eindhoven,boeren"},
    {"name": "Feyenoord", "league": "eredivisie", "elo": 1810.0, "aliases": "feyenoord,feyenoord rotterdam"},
    {"name": "Ajax", "league": "eredivisie", "elo": 1760.0, "aliases": "ajax,afc ajax,ajax amsterdam"},
    {"name": "AZ Alkmaar", "league": "eredivisie", "elo": 1710.0, "aliases": "az,az alkmaar,alkmaar"},
    {"name": "Twente", "league": "eredivisie", "elo": 1720.0, "aliases": "twente,fc twente"},

    # Primeira Liga
    {"name": "Sporting CP", "league": "primeira_liga", "elo": 1860.0, "aliases": "sporting,sporting cp,sporting lisbon,sporting lisboa,sporting de lisboa,sp lisbon,leoes"},
    {"name": "Benfica", "league": "primeira_liga", "elo": 1840.0, "aliases": "benfica,sl benfica,aguias"},
    {"name": "FC Porto", "league": "primeira_liga", "elo": 1820.0, "aliases": "porto,fc porto,oporto,dragoes"},
    {"name": "SC Braga", "league": "primeira_liga", "elo": 1730.0, "aliases": "braga,sc braga,sp braga,sporting braga"},

    # Liga F Femenina (España)
    {"name": "Barcelona F", "league": "liga_f", "elo": 2030.0, "aliases": "barcelona f,barcelona w,fc barcelona f,fc barcelona w,barcelona fem,barcelona femenino,barcelona femenil,barcelona women,barca f,barca w,barça f,barça w"},
    {"name": "Real Madrid F", "league": "liga_f", "elo": 1840.0, "aliases": "real madrid f,real madrid w,madrid f,madrid w,real madrid fem,real madrid femenino,real madrid femenil,real madrid women"},
    {"name": "Atletico Madrid F", "league": "liga_f", "elo": 1800.0, "aliases": "atletico madrid f,atletico madrid w,atleti f,atleti w,atletico de madrid f,atletico de madrid w,atletico madrid femenino,atletico madrid femenil,atletico madrid women"},
    {"name": "Athletic Bilbao F", "league": "liga_f", "elo": 1740.0, "aliases": "athletic bilbao f,athletic bilbao w,athletic club f,athletic club w,bilbao f,bilbao w,athletic bilbao femenino,athletic femenino"},
    {"name": "Real Sociedad F", "league": "liga_f", "elo": 1720.0, "aliases": "real sociedad f,real sociedad w,la real f,la real w,real sociedad femenino,real sociedad femenil"},
    {"name": "Levante F", "league": "liga_f", "elo": 1730.0, "aliases": "levante f,levante w,levante ud f,levante ud w,levante femenino,levante women"},
    {"name": "Madrid CFF", "league": "liga_f", "elo": 1710.0, "aliases": "madrid cff,madrid cff f,madrid cff w,madrid club de futbol femenino"},
    {"name": "Sevilla F", "league": "liga_f", "elo": 1680.0, "aliases": "sevilla f,sevilla w,sevilla fc f,sevilla fc w,sevilla femenino,sevilla femenil"},
    {"name": "Valencia F", "league": "liga_f", "elo": 1650.0, "aliases": "valencia f,valencia w,valencia cf f,valencia cf w,valencia femenino"},
    {"name": "Real Betis F", "league": "liga_f", "elo": 1640.0, "aliases": "real betis f,real betis w,betis f,betis w,real betis feminas,betis femenino"},

    # Women's Super League (Inglaterra)
    {"name": "Chelsea F", "league": "wsl", "elo": 1960.0, "aliases": "chelsea f,chelsea w,chelsea women,chelsea fc women,chelsea ladies,chelsea femenino,chelsea femenil"},
    {"name": "Manchester City F", "league": "wsl", "elo": 1920.0, "aliases": "manchester city f,manchester city w,man city f,man city w,manchester city women,man city women,manchester city femenino,manchester city femenil"},
    {"name": "Arsenal F", "league": "wsl", "elo": 1910.0, "aliases": "arsenal f,arsenal w,arsenal women,arsenal fc women,arsenal ladies,arsenal femenino,arsenal femenil"},
    {"name": "Manchester United F", "league": "wsl", "elo": 1820.0, "aliases": "manchester united f,manchester united w,man united f,man united w,man utd f,man utd w,manchester united women,man united women,manchester united femenino"},
    {"name": "Liverpool F", "league": "wsl", "elo": 1760.0, "aliases": "liverpool f,liverpool w,liverpool women,liverpool fc women,liverpool ladies,liverpool femenino"},
    {"name": "Tottenham F", "league": "wsl", "elo": 1730.0, "aliases": "tottenham f,tottenham w,tottenham hotspur f,tottenham hotspur w,tottenham women,spurs f,spurs w,spurs women,tottenham femenino"},
    {"name": "Aston Villa F", "league": "wsl", "elo": 1710.0, "aliases": "aston villa f,aston villa w,villa f,villa w,aston villa women,aston villa femenino"},
    {"name": "Brighton F", "league": "wsl", "elo": 1690.0, "aliases": "brighton f,brighton w,brighton women,brighton and hove albion w,brighton femenino"},
    {"name": "Everton F", "league": "wsl", "elo": 1680.0, "aliases": "everton f,everton w,everton women,everton ladies,everton femenino"},
    {"name": "West Ham F", "league": "wsl", "elo": 1660.0, "aliases": "west ham f,west ham w,west ham united f,west ham united w,west ham women,west ham femenino"},

    # Champions Femenina / Grandes de Europa (Francia, Alemania, Italia, Portugal, Países Bajos)
    {"name": "Lyon F", "league": "uwcl", "elo": 1990.0, "aliases": "lyon f,lyon w,olympique lyonnais f,olympique lyonnais w,ol feminin,lyon feminin,lyon femenino,lyon femenil,lyon women"},
    {"name": "PSG F", "league": "uwcl", "elo": 1890.0, "aliases": "psg f,psg w,paris saint-germain f,paris saint-germain w,paris sg f,paris sg w,psg feminin,psg femenino,psg femenil,psg women"},
    {"name": "Paris FC F", "league": "uwcl", "elo": 1780.0, "aliases": "paris fc f,paris fc w,paris fc feminin,paris fc women,paris fc femenino"},
    {"name": "Bayern Munich F", "league": "uwcl", "elo": 1920.0, "aliases": "bayern munich f,bayern munich w,bayern f,bayern w,bayern munchen f,bayern munchen w,bayern frauen,bayern munich women,bayern femenino,bayern femenil"},
    {"name": "Wolfsburg F", "league": "uwcl", "elo": 1900.0, "aliases": "wolfsburg f,wolfsburg w,vfl wolfsburg f,vfl wolfsburg w,wolfsburg frauen,wolfsburg women,wolfsburgo f,wolfsburgo w,wolfsburg femenino"},
    {"name": "Eintracht Frankfurt F", "league": "uwcl", "elo": 1810.0, "aliases": "eintracht frankfurt f,eintracht frankfurt w,frankfurt f,frankfurt w,eintracht frankfurt frauen,frankfurt women,frankfurt femenino"},
    {"name": "Bayer Leverkusen F", "league": "uwcl", "elo": 1750.0, "aliases": "bayer leverkusen f,bayer leverkusen w,leverkusen f,leverkusen w,leverkusen frauen,leverkusen women,leverkusen femenino"},
    {"name": "Juventus F", "league": "uwcl", "elo": 1830.0, "aliases": "juventus f,juventus w,juve f,juve w,juventus women,juventus femminile,juventus femenino,juventus femenil"},
    {"name": "Roma F", "league": "uwcl", "elo": 1820.0, "aliases": "roma f,roma w,as roma f,as roma w,roma women,roma femminile,roma femenino,roma femenil"},
    {"name": "Inter F", "league": "uwcl", "elo": 1760.0, "aliases": "inter f,inter w,inter milan f,inter milan w,inter women,inter femminile,inter femenino"},
    {"name": "AC Milan F", "league": "uwcl", "elo": 1750.0, "aliases": "ac milan f,ac milan w,milan f,milan w,ac milan women,milan femminile,milan femenino"},
    {"name": "Fiorentina F", "league": "uwcl", "elo": 1740.0, "aliases": "fiorentina f,fiorentina w,fiorentina women,fiorentina femminile,fiorentina femenino"},
    {"name": "Benfica F", "league": "uwcl", "elo": 1800.0, "aliases": "benfica f,benfica w,sl benfica f,sl benfica w,benfica women,benfica femenino,benfica femenil"},
    {"name": "Sporting CP F", "league": "uwcl", "elo": 1740.0, "aliases": "sporting cp f,sporting cp w,sporting f,sporting w,sporting lisbon w,sporting femenino"},
    {"name": "Ajax F", "league": "uwcl", "elo": 1770.0, "aliases": "ajax f,ajax w,afc ajax f,afc ajax w,ajax women,ajax vrouwen,ajax femenino"},
    {"name": "Twente F", "league": "uwcl", "elo": 1750.0, "aliases": "twente f,twente w,fc twente f,fc twente w,twente women,twente vrouwen,twente femenino"},

    # Liga MX Femenil (México)
    {"name": "Tigres UANL F", "league": "liga_mx_femenil", "elo": 1820.0, "aliases": "tigres uanl f,tigres uanl w,tigres f,tigres w,tigres femenil,tigres uanl femenil,tigres femenino,las amazonas,amazonas"},
    {"name": "América F", "league": "liga_mx_femenil", "elo": 1800.0, "aliases": "america f,america w,américa f,américa w,club america f,club america w,america femenil,américa femenil,club america femenil,america femenino"},
    {"name": "Monterrey F", "league": "liga_mx_femenil", "elo": 1790.0, "aliases": "monterrey f,monterrey w,rayadas,rayadas de monterrey,monterrey femenil,cf monterrey f,cf monterrey w,monterrey femenino"},
    {"name": "Pachuca F", "league": "liga_mx_femenil", "elo": 1750.0, "aliases": "pachuca f,pachuca w,tuzas,pachuca femenil,cf pachuca f,cf pachuca w,pachuca femenino"},
    {"name": "Guadalajara F", "league": "liga_mx_femenil", "elo": 1740.0, "aliases": "guadalajara f,guadalajara w,chivas f,chivas w,chivas femenil,guadalajara femenil,cd guadalajara f,cd guadalajara w,guadalajara femenino"},
    {"name": "Pumas UNAM F", "league": "liga_mx_femenil", "elo": 1660.0, "aliases": "pumas unam f,pumas unam w,pumas f,pumas w,pumas femenil,pumas unam femenil,pumas femenino"},
    {"name": "Cruz Azul F", "league": "liga_mx_femenil", "elo": 1630.0, "aliases": "cruz azul f,cruz azul w,cruz azul femenil,cruz azul femenino"},
    {"name": "Toluca F", "league": "liga_mx_femenil", "elo": 1650.0, "aliases": "toluca f,toluca w,toluca femenil,deportivo toluca f,toluca femenino"},
    {"name": "Juárez F", "league": "liga_mx_femenil", "elo": 1670.0, "aliases": "juarez f,juarez w,juárez f,juárez w,fc juarez f,fc juarez w,juarez femenil,bravas,bravas de juarez"},
    {"name": "Atlas F", "league": "liga_mx_femenil", "elo": 1640.0, "aliases": "atlas f,atlas w,atlas femenil,atlas fc f,atlas femenino"}
]

class LeagueDatabaseService:
    def __init__(self):
        self._ensure_seeded()

    def _is_womens_query(self, text: str) -> bool:
        """
        Detecta si una consulta o nombre de equipo corresponde a fútbol femenino
        (sufijos 'F' o 'W' de Flashscore/Sofascore, 'Femenil', 'Femenino', 'Women', 'Frauen', 'Femminile', etc.).
        """
        if not text:
            return False
        t = text.lower().strip()
        replacements = [('á', 'a'), ('é', 'e'), ('í', 'i'), ('ó', 'o'), ('ú', 'u'), ('ü', 'u'), ('ñ', 'n')]
        for a, b in replacements:
            t = t.replace(a, b)
        # Sufijos explícitos en Flashscore/Sofascore: "Barcelona F", "Chelsea W", "Real Madrid (F)", "Arsenal (W)"
        if re.search(r"(?:\s+|[(\[/])(f|w)(?:[)\]]|\s*)$", t):
            return True
        # Palabras clave de categoría femenina o apodos exclusivos femeniles
        if re.search(r"\b(femenil|femenino|femenina|feminas|feminin|femminile|vrouwen|frauen|women|womens|ladies|fem|madrid cff|rayadas|amazonas|tuzas|bravas)\b", t):
            return True
        return False

    def _clean_club_base(self, text: str) -> str:
        """Limpia tanto prefijos de club como marcadores femeninos para comparar la raíz del club dentro de su categoría."""
        t = self._clean_str(text)
        t = re.sub(r"(?:\s+|[(\[/])(f|w)(?:[)\]]|\s*)$", "", t).strip()
        t = re.sub(r"\b(femenil|femenino|femenina|feminas|feminin|femminile|vrouwen|frauen|women|womens|ladies|fem)\b", "", t).strip()
        t = re.sub(r"\s+", " ", t)
        return t

    def _clean_str(self, text: str) -> str:
        if not text:
            return ""
        t = text.lower().strip()
        # Normalizar acentos
        replacements = [('á', 'a'), ('é', 'e'), ('í', 'i'), ('ó', 'o'), ('ú', 'u'), ('ü', 'u'), ('ñ', 'n')]
        for a, b in replacements:
            t = t.replace(a, b)
        # Quitar paréntesis/corchetes alrededor de sufijos F/W: "Barcelona (F)" -> "barcelona f"
        t = re.sub(r"[(\[]\s*(f|w|fem|femenil|femenino|women)\s*[)\]]", r" \1", t)
        # Quitar prefijos comunes
        t = re.sub(r"\b(fc|cf|club|deportivo|real|cd|ud|sc|sl|afc|vfl|as)\b", "", t).strip()
        t = re.sub(r"\s+", " ", t)
        return t

    def _ensure_seeded(self):
        """Inicializa las tablas de ligas, equipos y partidos si están vacías o incompletas."""
        db = SessionLocal()
        try:
            m_count = db.query(HistoricalMatch).count()
            womens_league = db.query(League).filter(League.code == "liga_f").first()
            if m_count < 500 or not womens_league:
                logger.info("Base de datos de ligas vacía o sin soporte femenil. Actualizando datos reales de ligas...")
                from backend.app.services.real_data_loader import populate_real_database_and_compute_elo
                populate_real_database_and_compute_elo(db)
        except Exception as e:
            logger.warning(f"Error verificando seed de base de datos deportiva: {e}")
        finally:
            db.close()

    def seed_database(self, db):
        """Puebla las ligas, equipos y partidos históricos reales/curados mediante real_data_loader."""
        from backend.app.services.real_data_loader import populate_real_database_and_compute_elo
        populate_real_database_and_compute_elo(db)
        # 1. Ligas
        for lc in LEAGUES_CONFIG:
            existing = db.query(League).filter(League.code == lc["code"]).first()
            if not existing:
                league = League(
                    code=lc["code"],
                    name=lc["name"],
                    country=lc["country"],
                    avg_goals=lc["avg_goals"],
                    home_adv=lc["home_adv"],
                    avg_corners=lc["avg_corners"],
                    avg_cards=lc["avg_cards"],
                    rho=lc["rho"]
                )
                db.add(league)
        db.commit()

        # 2. Equipos
        team_objs = {}
        for tc in TEAMS_CONFIG:
            existing = db.query(Team).filter(Team.name == tc["name"]).first()
            if not existing:
                t = Team(
                    league_code=tc["league"],
                    name=tc["name"],
                    canonical_name=tc["name"],
                    aliases=tc["aliases"],
                    elo_rating=tc["elo"]
                )
                db.add(t)
                db.flush()
                team_objs[tc["name"]] = t
            else:
                team_objs[tc["name"]] = existing
        db.commit()

        # 3. Partidos Históricos Realistas Calibrados (Últimas temporadas 2023-2025)
        # Generamos una red densa de encuentros históricos para cada liga
        matches_count = db.query(HistoricalMatch).count()
        if matches_count == 0:
            import random
            random.seed(42)
            match_list = []

            # Para cada liga, simular partidos round-robin entre los equipos de la liga
            for lc in LEAGUES_CONFIG:
                l_code = lc["code"]
                league_teams = [t for t in TEAMS_CONFIG if t["league"] == l_code]
                if len(league_teams) < 2:
                    continue

                for season in ["2023-24", "2024-25"]:
                    for i in range(len(league_teams)):
                        for j in range(len(league_teams)):
                            if i == j:
                                continue
                            home = league_teams[i]
                            away = league_teams[j]

                            # Simulación fiel al Elo y parámetros de liga
                            elo_diff = (home["elo"] - away["elo"]) + 65.0  # Ventaja de campo
                            home_base = lc["avg_goals"] * (1.0 + elo_diff / 800.0)
                            away_base = lc["avg_goals"] * (1.0 - elo_diff / 800.0)
                            home_base = max(0.4, min(3.5, home_base))
                            away_base = max(0.3, min(3.0, away_base))

                            hg = int(random.choices(range(6), weights=[
                                max(0.01, 2.718 ** (-home_base) * (home_base ** k) / max(1, k)) for k in range(6)
                            ])[0])
                            ag = int(random.choices(range(6), weights=[
                                max(0.01, 2.718 ** (-away_base) * (away_base ** k) / max(1, k)) for k in range(6)
                            ])[0])

                            res = "W" if hg > ag else ("D" if hg == ag else "L")
                            tot_corners = max(5, int(random.gauss(lc["avg_corners"], 2.1)))
                            cn_h = int(tot_corners * (0.52 + (elo_diff / 2500.0)))
                            cn_a = max(0, tot_corners - cn_h)
                            cr_h = int(random.choices([0, 1, 2, 3], weights=[0.2, 0.45, 0.25, 0.1])[0])
                            cr_a = int(random.choices([0, 1, 2, 3, 4], weights=[0.15, 0.4, 0.3, 0.1, 0.05])[0])

                            sot_h = max(1, int(hg + random.randint(2, 6)))
                            sot_a = max(1, int(ag + random.randint(1, 5)))

                            hm = HistoricalMatch(
                                league_code=l_code,
                                season=season,
                                match_date=f"2024-{random.randint(1, 12):02d}-{random.randint(1, 28):02d}",
                                home_team=home["name"],
                                away_team=away["name"],
                                home_goals=hg,
                                away_goals=ag,
                                result=res,
                                home_shots_target=sot_h,
                                away_shots_target=sot_a,
                                corners_home=cn_h,
                                corners_away=cn_a,
                                cards_home=cr_h,
                                cards_away=cr_a
                            )
                            match_list.append(hm)

            db.bulk_save_objects(match_list)
            db.commit()
            logger.info(f"Seeded {len(match_list)} historical matches in local SQLite database.")

        self.recalculate_team_cache(db)

    def recalculate_team_cache(self, db):
        """Calcula y almacena en caché las estadísticas móviles de los equipos."""
        teams = db.query(Team).all()
        for t in teams:
            # Buscar últimos partidos donde participó (como local o visitante)
            matches = db.query(HistoricalMatch).filter(
                or_(HistoricalMatch.home_team == t.name, HistoricalMatch.away_team == t.name)
            ).order_by(HistoricalMatch.id.desc()).limit(15).all()

            if not matches:
                continue

            goals_for_list = []
            goals_against_list = []
            corners_list = []
            cards_list = []
            wins = 0

            matches_json = []
            for m in matches[:10]:
                is_home = (m.home_team == t.name)
                gf = m.home_goals if is_home else m.away_goals
                ga = m.away_goals if is_home else m.home_goals
                opp = m.away_team if is_home else m.home_team
                res = "W" if gf > ga else ("D" if gf == ga else "L")
                if res == "W":
                    wins += 1

                cn = m.corners_home if is_home else m.corners_away
                cr = m.cards_home if is_home else m.cards_away

                goals_for_list.append(gf)
                goals_against_list.append(ga)
                corners_list.append(cn)
                cards_list.append(cr)

                matches_json.append({
                    "opponent": opp,
                    "was_home": is_home,
                    "goals_for": gf,
                    "goals_against": ga,
                    "result": res,
                    "date": m.match_date,
                    "corners_for": cn,
                    "cards_total": m.cards_home + m.cards_away
                })

            n = len(goals_for_list) or 1
            last_5 = matches[:5]
            w5 = sum(1 for m in last_5 if (m.home_goals > m.away_goals if m.home_team == t.name else m.away_goals > m.home_goals))
            wr_5 = round(w5 / max(1, len(last_5)), 2)

            existing_cache = db.query(TeamStatsCache).filter(TeamStatsCache.team_name == t.name).first()
            if not existing_cache:
                existing_cache = TeamStatsCache(team_name=t.name, league_code=t.league_code)
                db.add(existing_cache)

            existing_cache.elo_rating = t.elo_rating
            existing_cache.avg_goals_scored = round(sum(goals_for_list) / n, 2)
            existing_cache.avg_goals_conceded = round(sum(goals_against_list) / n, 2)
            existing_cache.avg_corners = round(sum(corners_list) / n, 1)
            existing_cache.avg_cards = round(sum(cards_list) / n, 1)
            existing_cache.win_rate_last_5 = wr_5
            existing_cache.last_matches_json = matches_json
            existing_cache.updated_at = datetime.utcnow()

        db.commit()
        logger.info("Caché analítica de equipos actualizada exitosamente.")

    def normalize_team(self, query: str, db=None) -> Optional[Team]:
        """Localiza un equipo por nombre o alias, separando estrictamente clubes masculinos y femeninos (F / W)."""
        if not query:
            return None
        q = query.strip()
        q_clean = self._clean_str(q)
        is_womens_q = self._is_womens_query(q)
        q_base = self._clean_club_base(q)

        local_session = False
        if db is None:
            db = SessionLocal()
            local_session = True

        try:
            all_teams = db.query(Team).all()
            # Particionar estrictamente entre equipos femeninos y masculinos para evitar colisiones (ej. "Barcelona F" vs "Barcelona")
            candidate_teams = [
                t for t in all_teams
                if (self._is_womens_query(t.name) or t.league_code in ("liga_f", "wsl", "uwcl", "liga_mx_femenil")) == is_womens_q
            ]

            # 1. Coincidencia exacta de nombre o alias limpio dentro de la categoría correspondiente
            for t in candidate_teams:
                if t.name.lower() == q.lower():
                    return t
                t_clean = self._clean_str(t.name)
                if q_clean == t_clean:
                    return t
                aliases = [self._clean_str(a) for a in (t.aliases or "").split(",") if a.strip()]
                if q_clean in aliases:
                    return t

            # 2. Si es consulta femenina (ej. "Barcelona W", "Chelsea (W)", "Arsenal Femenino"), comparar raíz limpia del club
            if is_womens_q and q_base:
                for t in candidate_teams:
                    t_base = self._clean_club_base(t.name)
                    if q_base == t_base:
                        return t
                    alias_bases = [self._clean_club_base(a) for a in (t.aliases or "").split(",") if a.strip()]
                    if q_base in alias_bases:
                        return t

            # 3. Coincidencia de palabra completa (longitud >= 3) dentro de la categoría (femenina o masculina)
            for t in candidate_teams:
                t_target = self._clean_club_base(t.name) if is_womens_q else self._clean_str(t.name)
                q_target = q_base if is_womens_q else q_clean
                if len(t_target) >= 3 and re.search(r'\b' + re.escape(t_target) + r'\b', q_target):
                    return t
                raw_aliases = (t.aliases or "").split(",")
                for raw_a in raw_aliases:
                    a = self._clean_club_base(raw_a) if is_womens_q else self._clean_str(raw_a)
                    if len(a) >= 3:
                        if re.search(r'\b' + re.escape(a) + r'\b', q_target) or re.search(r'\b' + re.escape(q_target) + r'\b', a):
                            return t

            return None
        finally:
            if local_session:
                db.close()

    def get_match_raw_features(
        self,
        home_query: str,
        away_query: str,
        competition_query: Optional[str] = None
    ) -> Optional[MatchRawFeatures]:
        """
        Devuelve el objeto MatchRawFeatures completo si ambos clubes están en la BD de ligas grandes.
        Tiempo de ejecución: < 10 ms.
        """
        db = SessionLocal()
        try:
            # Si la competición indica explícitamente liga femenina, propagar contexto a nombres sin sufijo
            is_comp_womens = bool(competition_query and self._is_womens_query(competition_query))
            h_q = f"{home_query} F" if (is_comp_womens and not self._is_womens_query(home_query)) else home_query
            a_q = f"{away_query} F" if (is_comp_womens and not self._is_womens_query(away_query)) else away_query

            home_team_obj = self.normalize_team(h_q, db=db)
            away_team_obj = self.normalize_team(a_q, db=db)

            if not home_team_obj or not away_team_obj:
                return None

            # Determinar competición oficial
            if home_team_obj.league_code != away_team_obj.league_code:
                if self._is_womens_query(home_team_obj.name) or self._is_womens_query(away_team_obj.name):
                    league_code = "uwcl"
                else:
                    league_code = "champions_league"
            else:
                league_code = home_team_obj.league_code
            league_obj = db.query(League).filter(League.code == league_code).first()
            comp_name = league_obj.name if league_obj else (competition_query or "General")

            # Obtener caché de ambos equipos
            h_cache = db.query(TeamStatsCache).filter(TeamStatsCache.team_name == home_team_obj.name).first()
            a_cache = db.query(TeamStatsCache).filter(TeamStatsCache.team_name == away_team_obj.name).first()

            if not h_cache or not a_cache:
                return None

            # Construir PreviousMatch para local
            h_matches = [
                PreviousMatch(
                    opponent=m["opponent"],
                    was_home=m["was_home"],
                    goals_for=m["goals_for"],
                    goals_against=m["goals_against"],
                    result=m["result"],
                    date=m.get("date"),
                    corners_for=m.get("corners_for"),
                    cards_total=m.get("cards_total")
                )
                for m in (h_cache.last_matches_json or [])
            ]

            # Construir PreviousMatch para visitante
            a_matches = [
                PreviousMatch(
                    opponent=m["opponent"],
                    was_home=m["was_home"],
                    goals_for=m["goals_for"],
                    goals_against=m["goals_against"],
                    result=m["result"],
                    date=m.get("date"),
                    corners_for=m.get("corners_for"),
                    cards_total=m.get("cards_total")
                )
                for m in (a_cache.last_matches_json or [])
            ]

            # Calcular historial H2H real entre ambos en la BD
            h2h_matches = db.query(HistoricalMatch).filter(
                or_(
                    and_(HistoricalMatch.home_team == home_team_obj.name, HistoricalMatch.away_team == away_team_obj.name),
                    and_(HistoricalMatch.home_team == away_team_obj.name, HistoricalMatch.away_team == home_team_obj.name)
                )
            ).order_by(HistoricalMatch.id.desc()).limit(8).all()

            h_wins = 0
            a_wins = 0
            draws = 0
            tot_goals_h2h = 0
            tot_corners_h2h = 0
            tot_cards_h2h = 0

            for hm in h2h_matches:
                tot_goals_h2h += (hm.home_goals + hm.away_goals)
                tot_corners_h2h += (hm.corners_home + hm.corners_away)
                tot_cards_h2h += (hm.cards_home + hm.cards_away)
                if hm.home_goals == hm.away_goals:
                    draws += 1
                elif hm.home_team == home_team_obj.name:
                    if hm.home_goals > hm.away_goals:
                        h_wins += 1
                    else:
                        a_wins += 1
                else:
                    if hm.away_goals > hm.home_goals:
                        h_wins += 1
                    else:
                        a_wins += 1

            n_h2h = len(h2h_matches)
            avg_g_h2h = round(tot_goals_h2h / n_h2h, 2) if n_h2h > 0 else (league_obj.avg_goals * 2.0 if league_obj else 2.7)
            avg_cn_h2h = round(tot_corners_h2h / n_h2h, 1) if n_h2h > 0 else (league_obj.avg_corners if league_obj else 9.5)
            avg_cr_h2h = round(tot_cards_h2h / n_h2h, 1) if n_h2h > 0 else (league_obj.avg_cards if league_obj else 4.0)

            h2h_obj = HeadToHeadStats(
                total_matches_analyzed=n_h2h,
                home_team_wins=h_wins,
                away_team_wins=a_wins,
                draws=draws,
                avg_total_goals_h2h=avg_g_h2h,
                avg_total_corners_h2h=avg_cn_h2h,
                avg_total_cards_h2h=avg_cr_h2h
            )

            home_stats = TeamFormStats(
                team_name=home_team_obj.name,
                avg_goals_scored=h_cache.avg_goals_scored,
                avg_goals_conceded=h_cache.avg_goals_conceded,
                avg_corners=h_cache.avg_corners,
                avg_corners_conceded=getattr(h_cache, "avg_corners_conceded", None),
                avg_cards=h_cache.avg_cards,
                win_rate_last_5=h_cache.win_rate_last_5,
                key_absences=[],
                last_matches=h_matches,
                elo_rating=h_cache.elo_rating or home_team_obj.elo_rating,
                home_goals_scored=h_cache.home_goals_scored,
                home_goals_conceded=h_cache.home_goals_conceded,
                avg_shots_target_for=h_cache.avg_shots_target_for,
                avg_shots_target_against=h_cache.avg_shots_target_against
            )

            away_stats = TeamFormStats(
                team_name=away_team_obj.name,
                avg_goals_scored=a_cache.avg_goals_scored,
                avg_goals_conceded=a_cache.avg_goals_conceded,
                avg_corners=a_cache.avg_corners,
                avg_corners_conceded=getattr(a_cache, "avg_corners_conceded", None),
                avg_cards=a_cache.avg_cards,
                win_rate_last_5=a_cache.win_rate_last_5,
                key_absences=[],
                last_matches=a_matches,
                elo_rating=a_cache.elo_rating or away_team_obj.elo_rating,
                away_goals_scored=a_cache.away_goals_scored,
                away_goals_conceded=a_cache.away_goals_conceded,
                avg_shots_target_for=a_cache.avg_shots_target_for,
                avg_shots_target_against=a_cache.avg_shots_target_against
            )

            raw = MatchRawFeatures(
                home_team=home_team_obj.name,
                away_team=away_team_obj.name,
                competition=comp_name,
                home_stats=home_stats,
                away_stats=away_stats,
                h2h=h2h_obj,
                is_live=False,
                live_score=None,
                live_minute=None,
                live_corners=None
            )

            logger.info(f"⚡ Partido cargado instantáneamente desde BD SQLite: {raw.home_team} vs {raw.away_team} ({comp_name})")
            return raw
        except Exception as e:
            logger.warning(f"Error recuperando partido de BD local: {e}")
            return None
        finally:
            db.close()

    def get_all_training_samples(self) -> List[Dict]:
        """Extrae todos los partidos históricos para entrenamiento de modelos de ML."""
        db = SessionLocal()
        try:
            matches = db.query(HistoricalMatch).all()
            samples = []
            for m in matches:
                samples.append({
                    "league": m.league_code,
                    "season": m.season,
                    "home_team": m.home_team,
                    "away_team": m.away_team,
                    "home_goals": m.home_goals,
                    "away_goals": m.away_goals,
                    "result": 0 if m.home_goals > m.away_goals else (1 if m.home_goals == m.away_goals else 2),
                    "total_goals": m.home_goals + m.away_goals,
                    "corners": m.corners_home + m.corners_away,
                    "cards": m.cards_home + m.cards_away
                })
            return samples
        finally:
            db.close()

league_db = LeagueDatabaseService()
