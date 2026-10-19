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

def init_db():
    """Crea las tablas en el archivo SQLite analista.db si no existen y realiza migraciones"""
    Base.metadata.create_all(bind=engine)
    # Migración segura para SQLite si la columna match_url no existe
    try:
        with engine.connect() as conn:
            from sqlalchemy import text
            result = conn.execute(text("PRAGMA table_info(match_predictions)"))
            columns = [row[1] for row in result.fetchall()]
            if "match_url" not in columns:
                conn.execute(text("ALTER TABLE match_predictions ADD COLUMN match_url VARCHAR(500)"))
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
