import os
from pathlib import Path
from dotenv import load_dotenv

# Localizar la raíz del proyecto y cargar .env
BASE_DIR = Path(__file__).resolve().parent.parent
env_path = BASE_DIR / ".env"
if not env_path.exists():
    env_path = Path(__file__).resolve().parent / ".env"

load_dotenv(dotenv_path=env_path, override=True)

class Settings:
    # Credenciales de Acceso
    ADMIN_USER: str = os.getenv("ADMIN_USER", "Admin")
    ADMIN_PASS: str = os.getenv("ADMIN_PASS", "Admin")
    APP_SECRET_KEY: str = os.getenv("APP_SECRET_KEY", "citi_analyzer_secret_key_dev")

    # APIs de Extracción e Inteligencia Artificial
    APIFY_API_TOKEN: str = os.getenv("APIFY_API_TOKEN", "")
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
    GEMINI_MODEL: str = os.getenv("GEMINI_MODEL", "gemini-3-flash-preview")

    # Base de Datos y Servidor
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./data/citi_analyzer.db")
    BACKEND_PORT: int = int(os.getenv("BACKEND_PORT", 8000))
    FRONTEND_PORT: int = int(os.getenv("FRONTEND_PORT", 3000))
    NEXT_PUBLIC_API_URL: str = os.getenv("NEXT_PUBLIC_API_URL", "http://localhost:8000")

    # Rutas del Sistema
    BASE_DIR: Path = BASE_DIR
    DATA_DIR: Path = BASE_DIR / "data"
    TMP_MEDIA_DIR: Path = BASE_DIR / "tmp_media"

    @classmethod
    def is_apify_ready(cls) -> bool:
        return bool(cls.APIFY_API_TOKEN and not cls.APIFY_API_TOKEN.startswith("tu_token"))

    @classmethod
    def is_gemini_ready(cls) -> bool:
        return bool(cls.GEMINI_API_KEY and not cls.GEMINI_API_KEY.startswith("tu_api_key"))

settings = Settings()
