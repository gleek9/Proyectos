import os
from pathlib import Path
from dotenv import load_dotenv

# Cargar variables desde .env en la raíz del proyecto
ROOT_DIR = Path(__file__).resolve().parent.parent.parent
load_dotenv(dotenv_path=ROOT_DIR / ".env")

class Settings:
    PORT: int = int(os.getenv("PORT", "8000"))
    NODE_ENV: str = os.getenv("NODE_ENV", "development")
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
    GEMINI_MODEL: str = os.getenv("GEMINI_MODEL", "gemini-3.5-flash-lite")
    
    # Base de datos SQLite
    DATABASE_URL: str = os.getenv("DATABASE_URL", f"sqlite:///{ROOT_DIR / 'analista.db'}")
    DB_PATH: Path = ROOT_DIR / "analista.db"
    
    # Seguridad y Autenticación
    JWT_SECRET: str = os.getenv("JWT_SECRET", "katakuri_ai_jwt_secret_token_secure_2026")
    JWT_ALGORITHM: str = os.getenv("JWT_ALGORITHM", "HS256")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "1440"))
    
    # Credenciales de Acceso
    APP_USERNAME: str = os.getenv("APP_USERNAME", "Gleek")
    APP_PASSWORD: str = os.getenv("APP_PASSWORD", "Contra123")

    # Directorio de pesos locales
    WEIGHTS_DIR: Path = ROOT_DIR / "backend" / "weights"

settings = Settings()
