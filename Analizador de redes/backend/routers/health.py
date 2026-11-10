from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import text
from database import get_db
from config import settings
from schemas import HealthStatusResponse

router = APIRouter(prefix="/health", tags=["Monitoreo"])

@router.get("", response_model=HealthStatusResponse)
def health_check(db: Session = Depends(get_db)):
    """
    Monitor de estado del motor Social Analyzer: APIs y Base de Datos.
    """
    db_ok = False
    try:
        db.execute(text("SELECT 1"))
        db_ok = True
    except Exception:
        db_ok = False

    apify_ok = settings.is_apify_ready()
    gemini_ok = settings.is_gemini_ready()

    overall_status = "operational" if (db_ok and apify_ok and gemini_ok) else "degraded"

    return HealthStatusResponse(
        status=overall_status,
        apify_connected=apify_ok,
        gemini_connected=gemini_ok,
        gemini_model=settings.GEMINI_MODEL,
        database_connected=db_ok
    )
