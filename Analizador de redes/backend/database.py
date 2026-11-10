import os
from pathlib import Path
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
from config import settings

# Asegurar que el directorio /data existe
settings.DATA_DIR.mkdir(parents=True, exist_ok=True)

# Normalizar URL de SQLite para que siempre use ruta absoluta a /data
db_url = settings.DATABASE_URL
if db_url.startswith("sqlite:///./data/"):
    db_file = settings.DATA_DIR / "citi_analyzer.db"
    db_url = f"sqlite:///{db_file.as_posix()}"
elif db_url.startswith("sqlite:///"):
    # Si es ruta relativa simple
    if not os.path.isabs(db_url.replace("sqlite:///", "")):
        db_file = settings.DATA_DIR / "citi_analyzer.db"
        db_url = f"sqlite:///{db_file.as_posix()}"

connect_args = {"check_same_thread": False} if db_url.startswith("sqlite") else {}

engine = create_engine(
    db_url,
    connect_args=connect_args,
    echo=False
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def init_db():
    # Importar modelos para que Base.metadata los reconozca
    import models  # noqa: F401
    Base.metadata.create_all(bind=engine)
