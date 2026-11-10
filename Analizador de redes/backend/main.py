from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from config import settings
from database import init_db
from routers import auth, profiles, health

from services.media_extractor import media_extractor

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Inicialización de la base de datos local SQLite
    print("[Social Analyzer v1.1] Inicializando base de datos local SQLite...")
    init_db()
    # Purgar cualquier archivo temporal residual previo
    media_extractor.purge_all_tmp()
    print("[Social Analyzer v1.1] Base de datos lista en ./data/citi_analyzer.db")
    print(f"[Social Analyzer v1.1] Modelo Gemini activo: {settings.GEMINI_MODEL}")
    print(f"[Social Analyzer v1.1] Apify Token configurado: {settings.is_apify_ready()}")
    yield
    # Limpieza final al detener el servidor
    media_extractor.purge_all_tmp()
    print("[Social Analyzer v1.1] Deteniendo servidor y purgando archivos temporales...")

app = FastAPI(
    title="Social Analyzer API",
    description="Motor de inteligencia de guiones virales y análisis de competidores (MVP Local-First)",
    version="1.1",
    lifespan=lifespan
)

# Configuración de CORS para permitir peticiones desde el frontend (puerto 3000 o cualquier origen local)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:5173",
        "*"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Registro de routers con prefijo /api
app.include_router(auth.router, prefix="/api")
app.include_router(profiles.router, prefix="/api")
app.include_router(health.router, prefix="/api")

@app.get("/")
def root():
    return {
        "app": "Social Analyzer API",
        "version": "1.1",
        "status": "online",
        "gemini_model": settings.GEMINI_MODEL,
        "docs_url": "/docs"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=settings.BACKEND_PORT, reload=True)
