from datetime import datetime
import json
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from database import get_db
from models import Profile, AnalysisReport, ScriptProposal
from schemas import (
    ProfileCreate,
    ProfileUpdate,
    ProfileListItemResponse,
    ProfileDetailResponse,
    AnalysisReportResponse,
    ScriptProposalResponse,
    TimelineBlock,
    AnalyzeProfileResponse
)

router = APIRouter(prefix="/profiles", tags=["Perfiles de Clientes"])

def calculate_time_elapsed(last_analyzed_at: datetime | None) -> str:
    """Calcula la leyenda dinámica de tiempo transcurrido desde el último análisis."""
    if not last_analyzed_at:
        return "Sin análisis previo"
    diff = datetime.utcnow() - last_analyzed_at
    seconds = int(diff.total_seconds())
    if seconds < 60:
        return "Último análisis: hace un momento"
    minutes = seconds // 60
    if minutes < 60:
        return f"Último análisis: hace {minutes}m"
    hours = minutes // 60
    if hours < 24:
        return f"Último análisis: hace {hours}h"
    days = hours // 24
    return f"Último análisis: hace {days}d"


def build_proposal_response(proposal: ScriptProposal) -> ScriptProposalResponse:
    """Convierte un modelo ScriptProposal a su esquema Pydantic."""
    raw_timeline = proposal.get_timeline_list()
    timeline_blocks = []
    for item in raw_timeline:
        if isinstance(item, dict):
            timeline_blocks.append(
                TimelineBlock(
                    time_range=item.get("time_range", "00:00 - 00:03"),
                    phase=item.get("phase", "Estructura"),
                    description=item.get("description", "")
                )
            )

    return ScriptProposalResponse(
        id=proposal.id,
        report_id=proposal.report_id,
        title=proposal.title,
        competitor_source_info=proposal.competitor_source_info,
        virality_badge=proposal.virality_badge,
        escalation_timeline=timeline_blocks,
        full_script=proposal.full_script,
        original_reel_url=proposal.original_reel_url,
        original_transcript=proposal.original_transcript,
        created_at=proposal.created_at
    )


def build_report_response(report: AnalysisReport) -> AnalysisReportResponse:
    """Convierte un modelo AnalysisReport con sus propuestas a esquema Pydantic."""
    proposals_response = [build_proposal_response(p) for p in report.proposals]
    return AnalysisReportResponse(
        id=report.id,
        profile_id=report.profile_id,
        summary=report.summary,
        created_at=report.created_at,
        proposals=proposals_response
    )


@router.get("", response_model=List[ProfileListItemResponse])
def get_all_profiles(db: Session = Depends(get_db)):
    """
    Obtiene la lista de todos los perfiles registrados para el grid Kanban.
    """
    profiles = db.query(Profile).order_by(Profile.created_at.desc()).all()
    results = []
    for p in profiles:
        comp_list = p.get_competitor_urls_list()
        results.append(
            ProfileListItemResponse(
                id=p.id,
                client_name=p.client_name,
                category=p.category,
                representative_color=p.representative_color,
                client_instagram_url=p.client_instagram_url,
                competitor_count=len(comp_list),
                created_at=p.created_at,
                last_analyzed_at=p.last_analyzed_at,
                time_elapsed_label=calculate_time_elapsed(p.last_analyzed_at)
            )
        )
    return results


@router.post("", response_model=ProfileDetailResponse, status_code=status.HTTP_201_CREATED)
def create_profile(payload: ProfileCreate, db: Session = Depends(get_db)):
    """
    Crea un nuevo perfil de cliente con sus competidores vinculados.
    """
    new_profile = Profile(
        client_name=payload.client_name.strip(),
        category=payload.category.strip(),
        representative_color=payload.representative_color or "#58FF9C",
        client_instagram_url=payload.client_instagram_url.strip()
    )
    # Limpiar y filtrar URLs vacías
    clean_competitors = [url.strip() for url in payload.competitor_urls if url.strip()]
    new_profile.set_competitor_urls_list(clean_competitors)

    db.add(new_profile)
    db.commit()
    db.refresh(new_profile)

    return ProfileDetailResponse(
        id=new_profile.id,
        client_name=new_profile.client_name,
        category=new_profile.category,
        representative_color=new_profile.representative_color,
        client_instagram_url=new_profile.client_instagram_url,
        competitor_urls=new_profile.get_competitor_urls_list(),
        brand_voice_summary=new_profile.brand_voice_summary,
        created_at=new_profile.created_at,
        last_analyzed_at=new_profile.last_analyzed_at,
        time_elapsed_label="Sin análisis previo",
        latest_report=None,
        proposals=[]
    )


@router.get("/{profile_id}", response_model=ProfileDetailResponse)
def get_profile_detail(profile_id: int, db: Session = Depends(get_db)):
    """
    Obtiene el detalle completo de un perfil y sus propuestas de guion más recientes.
    """
    profile = db.query(Profile).filter(Profile.id == profile_id).first()
    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No se encontró el perfil con ID {profile_id}"
        )

    # Buscar el reporte más reciente
    latest_report = (
        db.query(AnalysisReport)
        .filter(AnalysisReport.profile_id == profile.id)
        .order_by(AnalysisReport.created_at.desc())
        .first()
    )

    report_resp = build_report_response(latest_report) if latest_report else None
    proposals_resp = report_resp.proposals if report_resp else []

    return ProfileDetailResponse(
        id=profile.id,
        client_name=profile.client_name,
        category=profile.category,
        representative_color=profile.representative_color,
        client_instagram_url=profile.client_instagram_url,
        competitor_urls=profile.get_competitor_urls_list(),
        brand_voice_summary=profile.brand_voice_summary,
        created_at=profile.created_at,
        last_analyzed_at=profile.last_analyzed_at,
        time_elapsed_label=calculate_time_elapsed(profile.last_analyzed_at),
        latest_report=report_resp,
        proposals=proposals_resp
    )


@router.put("/{profile_id}", response_model=ProfileDetailResponse)
def update_profile(profile_id: int, payload: ProfileUpdate, db: Session = Depends(get_db)):
    """
    Actualiza la información y competidores de un perfil de cliente.
    """
    profile = db.query(Profile).filter(Profile.id == profile_id).first()
    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No se encontró el perfil con ID {profile_id}"
        )

    if payload.client_name is not None:
        profile.client_name = payload.client_name.strip()
    if payload.category is not None:
        profile.category = payload.category.strip()
    if payload.representative_color is not None:
        profile.representative_color = payload.representative_color
    if payload.client_instagram_url is not None:
        profile.client_instagram_url = payload.client_instagram_url.strip()
    if payload.competitor_urls is not None:
        clean_urls = [u.strip() for u in payload.competitor_urls if u.strip()]
        profile.set_competitor_urls_list(clean_urls)

    db.commit()
    db.refresh(profile)

    return get_profile_detail(profile_id=profile.id, db=db)


@router.delete("/{profile_id}")
def delete_profile(profile_id: int, db: Session = Depends(get_db)):
    """
    Elimina un perfil y todos sus reportes y guiones asociados en cascada.
    """
    profile = db.query(Profile).filter(Profile.id == profile_id).first()
    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No se encontró el perfil con ID {profile_id}"
        )

    client_name = profile.client_name
    db.delete(profile)
    db.commit()

    return {
        "status": "success",
        "message": f"Perfil '{client_name}' eliminado exitosamente.",
        "id": profile_id
    }


@router.post("/{profile_id}/analyze", response_model=AnalyzeProfileResponse)
def analyze_profile(profile_id: int, db: Session = Depends(get_db)):
    """
    Disparador del pipeline de análisis: extrae virales, transcribe y genera 3 propuestas de guiones.
    """
    profile = db.query(Profile).filter(Profile.id == profile_id).first()
    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No se encontró el perfil con ID {profile_id}"
        )

    from services.analyzer_service import run_analysis_pipeline
    report = run_analysis_pipeline(profile=profile, db=db)

    # Actualizar last_analyzed_at
    profile.last_analyzed_at = datetime.utcnow()
    db.commit()
    db.refresh(profile)

    return AnalyzeProfileResponse(
        status="success",
        message="Análisis de competencia completado y 3 guiones adaptados generados.",
        profile_id=profile.id,
        report=build_report_response(report)
    )
