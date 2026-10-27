"""
Módulo de Base de Datos SQLite (Local, sin Docker)
"""
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, Text, JSON
from sqlalchemy.orm import declarative_base, sessionmaker
from datetime import datetime
from backend.app.config import settings

# Engine para SQLite
engine = create_engine(
    settings.DATABASE_URL,
    connect_args={"check_same_thread": False}
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class MatchPrediction(Base):
    __tablename__ = "match_predictions"

    id = Column(Integer, primary_key=True, index=True)
    home_team = Column(String(100), index=True, nullable=False)
    away_team = Column(String(100), index=True, nullable=False)
    competition = Column(String(100), default="General")
    match_url = Column(String(500), nullable=True)
    analyzed_at = Column(DateTime, default=datetime.utcnow)

    # Resultados y probabilidades calculadas
    winner_home_pct = Column(Float)
    winner_draw_pct = Column(Float)
    winner_away_pct = Column(Float)
    human_verdict = Column(String(255))

    # Métricas clave
    expected_goals = Column(Float)
    over_2_5_pct = Column(Float)
    expected_corners = Column(Float)
    expected_cards = Column(Float)

    # Payload completo en JSON (para gráficas y desglose detallado)
    prediction_data = Column(JSON)
    raw_stats = Column(JSON)

class League(Base):
    __tablename__ = "leagues"

    id = Column(Integer, primary_key=True, index=True)
    code = Column(String(50), unique=True, index=True, nullable=False)
    name = Column(String(100), nullable=False)
    country = Column(String(50), default="")
    avg_goals = Column(Float, default=1.35)
    home_adv = Column(Float, default=1.14)
    avg_corners = Column(Float, default=9.5)
    avg_cards = Column(Float, default=3.8)
    rho = Column(Float, default=-0.10)

class Team(Base):
    __tablename__ = "teams"

    id = Column(Integer, primary_key=True, index=True)
    league_code = Column(String(50), index=True, nullable=False)
    name = Column(String(100), index=True, nullable=False)
    canonical_name = Column(String(100), nullable=False)
    aliases = Column(Text, default="")  # comma-separated lower-case alias names
    stadium = Column(String(100), nullable=True)
    elo_rating = Column(Float, default=1500.0)

class HistoricalMatch(Base):
    __tablename__ = "historical_matches"

    id = Column(Integer, primary_key=True, index=True)
    league_code = Column(String(50), index=True, nullable=False)
    season = Column(String(20), index=True, default="2024-25")
    match_date = Column(String(20), default="")
    home_team = Column(String(100), index=True, nullable=False)
    away_team = Column(String(100), index=True, nullable=False)
    home_goals = Column(Integer, nullable=False)
    away_goals = Column(Integer, nullable=False)
    result = Column(String(2), default="D")  # 'W', 'D', 'L'
    home_shots_target = Column(Integer, default=0)
    away_shots_target = Column(Integer, default=0)
    corners_home = Column(Integer, default=0)
    corners_away = Column(Integer, default=0)
    cards_home = Column(Integer, default=0)
    cards_away = Column(Integer, default=0)
    b365_home_odds = Column(Float, nullable=True)
    b365_draw_odds = Column(Float, nullable=True)
    b365_away_odds = Column(Float, nullable=True)

class TeamStatsCache(Base):
    __tablename__ = "team_stats_cache"

    id = Column(Integer, primary_key=True, index=True)
    team_name = Column(String(100), unique=True, index=True, nullable=False)
    league_code = Column(String(50), index=True, nullable=False)
    elo_rating = Column(Float, default=1500.0)
    avg_goals_scored = Column(Float, default=1.35)
    avg_goals_conceded = Column(Float, default=1.35)
    home_goals_scored = Column(Float, nullable=True)
    home_goals_conceded = Column(Float, nullable=True)
    away_goals_scored = Column(Float, nullable=True)
    away_goals_conceded = Column(Float, nullable=True)
    avg_shots_target_for = Column(Float, nullable=True)
    avg_shots_target_against = Column(Float, nullable=True)
    avg_corners = Column(Float, default=5.0)
    avg_cards = Column(Float, default=2.0)
    win_rate_last_5 = Column(Float, default=0.50)
    last_matches_json = Column(JSON, default=list)
    updated_at = Column(DateTime, default=datetime.utcnow)

def init_db():
    """Crea las tablas en el archivo SQLite analista.db si no existen y realiza migraciones"""
    Base.metadata.create_all(bind=engine)
    # Migraciones seguras para SQLite con PRAGMA
    try:
        with engine.connect() as conn:
            from sqlalchemy import text
            result = conn.execute(text("PRAGMA table_info(match_predictions)"))
            cols_preds = [row[1] for row in result.fetchall()]
            if "match_url" not in cols_preds:
                conn.execute(text("ALTER TABLE match_predictions ADD COLUMN match_url VARCHAR(500)"))
                conn.commit()

            result = conn.execute(text("PRAGMA table_info(historical_matches)"))
            cols_hm = [row[1] for row in result.fetchall()]
            for col in ["b365_home_odds", "b365_draw_odds", "b365_away_odds"]:
                if col not in cols_hm:
                    conn.execute(text(f"ALTER TABLE historical_matches ADD COLUMN {col} FLOAT"))
                    conn.commit()

            result = conn.execute(text("PRAGMA table_info(team_stats_cache)"))
            cols_tc = [row[1] for row in result.fetchall()]
            for col in ["home_goals_scored", "home_goals_conceded", "away_goals_scored", "away_goals_conceded", "avg_shots_target_for", "avg_shots_target_against"]:
                if col not in cols_tc:
                    conn.execute(text(f"ALTER TABLE team_stats_cache ADD COLUMN {col} FLOAT"))
                    conn.commit()
    except Exception:
        pass

# Auto-crear tablas si no existen
try:
    init_db()
except Exception:
    pass

def get_db():
    """Generador de sesión de base de datos"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
