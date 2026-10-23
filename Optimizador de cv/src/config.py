import os
import sys
from pathlib import Path

# Determinar directorio base según ejecución en desarrollo o empaquetado (.exe)
if getattr(sys, 'frozen', False):
    BASE_DIR = Path(sys._MEIPASS)
    DATA_DIR = Path(os.getenv('APPDATA', str(Path.home()))) / 'Cuva'
    UI_DIR = BASE_DIR / 'src' / 'ui' if (BASE_DIR / 'src' / 'ui').exists() else BASE_DIR / 'ui'
else:
    BASE_DIR = Path(__file__).resolve().parent.parent
    DATA_DIR = BASE_DIR / 'data'
    UI_DIR = BASE_DIR / 'src' / 'ui'

# Asegurar que el directorio de datos persistente exista
DATA_DIR.mkdir(parents=True, exist_ok=True)

# Rutas de base de datos y UI
DB_PATH = DATA_DIR / 'cv_optimizer.db'
INDEX_HTML = UI_DIR / 'index.html'

# Constantes de la aplicación
APP_TITLE = "Cuva — Auditoría & Adaptación Profesional"
WINDOW_WIDTH = 1040
WINDOW_HEIGHT = 760
MIN_MATCH_THRESHOLD = 75.0  # Umbral de activación para adaptar CV (75% de afinidad mínima)
