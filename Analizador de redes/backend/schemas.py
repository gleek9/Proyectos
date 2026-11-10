from datetime import datetime
from typing import List, Optional, Any
from pydantic import BaseModel, Field

# Esquemas de Autenticación
class AuthLoginRequest(BaseModel):
    username: str
    password: str

class AuthLoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    username: str

# Bloque de Escaleta por Tiempo
class TimelineBlock(BaseModel):
    time_range: str = Field(..., example="00:00 - 00:03")
    phase: str = Field(..., example="Gancho Visual y Auditivo")
    description: str = Field(..., example="Muestra un titular en pantalla y lanza una pregunta incómoda.")

# Propuesta de Guion
class ScriptProposalBase(BaseModel):
    title: str
    competitor_source_info: Optional[str] = None
    virality_badge: Optional[str] = None
    escalation_timeline: List[TimelineBlock]
    full_script: str
    original_reel_url: Optional[str] = None
    original_transcript: Optional[str] = None

class ScriptProposalResponse(ScriptProposalBase):
    id: int
    report_id: int
    created_at: datetime

    class Config:
        from_attributes = True

# Reporte de Análisis
class AnalysisReportResponse(BaseModel):
    id: int
    profile_id: int
    summary: Optional[str] = None
    created_at: datetime
    proposals: List[ScriptProposalResponse] = []

    class Config:
        from_attributes = True

# Esquemas de Creación y Edición de Perfil
class ProfileCreate(BaseModel):
    client_name: str = Field(..., min_length=1, max_length=255)
    category: str = Field(..., min_length=1, max_length=100)
    representative_color: str = Field(default="#58FF9C", max_length=20)
    client_instagram_url: str = Field(..., min_length=5, max_length=500)
    competitor_urls: List[str] = Field(default_factory=list)

class ProfileUpdate(BaseModel):
    client_name: Optional[str] = None
    category: Optional[str] = None
    representative_color: Optional[str] = None
    client_instagram_url: Optional[str] = None
    competitor_urls: Optional[List[str]] = None

# Elemento para el Tablero Kanban (Resumen rápido)
class ProfileListItemResponse(BaseModel):
    id: int
    client_name: str
    category: str
    representative_color: str
    client_instagram_url: str
    competitor_count: int
    created_at: datetime
    last_analyzed_at: Optional[datetime] = None
    time_elapsed_label: str

    class Config:
        from_attributes = True

# Detalle Completo de Perfil para la Mini-Ventana Modal
class ProfileDetailResponse(BaseModel):
    id: int
    client_name: str
    category: str
    representative_color: str
    client_instagram_url: str
    competitor_urls: List[str]
    brand_voice_summary: Optional[str] = None
    created_at: datetime
    last_analyzed_at: Optional[datetime] = None
    time_elapsed_label: str
    latest_report: Optional[AnalysisReportResponse] = None
    proposals: List[ScriptProposalResponse] = []

    class Config:
        from_attributes = True

# Respuesta del disparador de análisis
class AnalyzeProfileResponse(BaseModel):
    status: str
    message: str
    profile_id: int
    report: AnalysisReportResponse

# Estado de Salud y Monitoreo del Motor
class HealthStatusResponse(BaseModel):
    status: str
    apify_connected: bool
    gemini_connected: bool
    gemini_model: str
    database_connected: bool
