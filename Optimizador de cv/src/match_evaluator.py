import json
import re
from typing import Dict, Any, Optional
from src.gemini_service import run_prompt_json
from src.database import save_job_analysis, get_user_profile
from src.config import MIN_MATCH_THRESHOLD

# Términos relacionados a residencia y localización geográfica
LOCATION_KEYWORDS = [
    "residencia", "residir", "ubicación", "ubicacion", "localización", "localizacion",
    "ciudad", "país", "pais", "zona", "presencial en", "remoto desde", "locación", "locacion"
]

def evaluate_job_match(
    job_text: str, 
    job_url: str = "", 
    profile_data: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Compara el perfil profesional del usuario contra la vacante utilizando Google Gemini.
    Devuelve un diagnóstico estructurado con porcentaje (umbral mínimo 75%), 3 columnas de habilidades
    y feedback de mentor, considerando siempre la residencia de la vacante como requisito cumplido.
    """
    if not profile_data:
        profile = get_user_profile()
        if not profile:
            raise ValueError("No se ha configurado un perfil profesional base. Sube tu CV primero.")
        profile_data = profile.get("parsed_data", {})

    profile_json_str = json.dumps(profile_data, ensure_ascii=False, indent=2)

    system_instruction = (
        "Eres un director de talento y auditor técnico senior de sistemas ATS (Applicant Tracking Systems). "
        "Tu misión es evaluar con objetividad matemática, realismo y rigor la afinidad entre el perfil de un candidato "
        "y los requerimientos específicos de una vacante. "
        "No infles calificaciones artificialmente ni inventes requisitos inexistentes. "
        "Adopta siempre un tono constructivo de mentor ejecutivo profesional."
    )

    prompt = f"""
Evalúa rigurosamente la compatibilidad entre el perfil profesional del candidato y la descripción de la vacante.

PERFIL DEL CANDIDATO (Datos reales):
---
{profile_json_str}
---

DESCRIPCIÓN DE LA VACANTE:
---
{job_text}
---

INSTRUCCIONES DE EVALUACIÓN:
1. Identifica el título de la vacante y la empresa (si no se menciona, usa 'Empresa no especificada').
2. REGLA OBLIGATORIA SOBRE RESIDENCIA Y UBICACIÓN:
   - Considera SIEMPRE y por defecto la residencia, ubicación geográfica, ciudad o país solicitados en la vacante como un REQUISITO CUMPLIDO por el candidato.
   - NUNCA califiques la residencia o ubicación geográfica como un requisito faltante ('missing_skills') ni reduzcas la puntuación por este motivo.
   - Si la vacante menciona residencia, ubicación física o disponibilidad geográfica, regístrala automáticamente dentro de 'matched_skills' (ej. 'Residencia y disponibilidad geográfica compatible').
3. Calcula un porcentaje de viabilidad real y objetivo (entero entre 0 y 100):
   - ≥ 75%: El candidato cubre los requisitos prioritarios y tiene experiencia alineada en el rol (califica para adaptación de CV).
   - 55% - 74%: Buen ajuste con sólida base transferible, pero le faltan algunas herramientas o tecnologías secundarias.
   - < 55%: Brechas sustanciales de experiencia o requisitos críticos no cubiertos.
4. Desglosa los requisitos en 3 listas claras:
   - "matched_skills": Requisitos clave, tecnologías y residencia/ubicación de la oferta que el candidato CUMPLE con su experiencia o por defecto.
   - "transferable_skills": Habilidades secundarias, metodologías o tecnologías afines que el candidato posee y puede transferir rápidamente.
   - "missing_skills": Requisitos técnicos, certificaciones o tecnologías obligatorias de la vacante que NO aparecen en el perfil y explican la puntuación (EXCLUYENDO residencia/ubicación).
5. Redacta un "mentor_feedback": 2 a 3 frases en tono constructivo de mentor ejecutivo. Si el porcentaje es < 75%, explica pedagógicamente qué habilidad necesita reforzar y resalta su mayor fortaleza. Si es ≥ 75%, confirma su alta competitividad para postular y adaptar su currículum.
6. Extrae una lista de 5 a 10 "key_ats_keywords" fundamentales de la oferta.

Genera ÚNICAMENTE este formato JSON:
{{
  "job_title": "Título del puesto",
  "company": "Nombre de la empresa",
  "match_percentage": 80,
  "matched_skills": [
    "Requisito 1 cubierto",
    "Requisito 2 cubierto"
  ],
  "transferable_skills": [
    "Habilidad transferible 1",
    "Habilidad transferible 2"
  ],
  "missing_skills": [
    "Requisito faltante 1 que reduce el match",
    "Requisito faltante 2"
  ],
  "mentor_feedback": "Mensaje constructivo de mentor...",
  "key_ats_keywords": ["palabra1", "palabra2", "palabra3"]
}}
"""

    analysis_result = run_prompt_json(prompt, system_instruction=system_instruction)

    # Procesamiento y garantía determinista de residencia como requisito cumplido
    matched_skills = analysis_result.get("matched_skills", [])
    missing_skills = analysis_result.get("missing_skills", [])
    transferable_skills = analysis_result.get("transferable_skills", [])

    clean_missing = []
    relocated_to_matched = []

    for item in missing_skills:
        item_lower = item.lower()
        # Si la IA colocó erróneamente un requisito de residencia o ubicación en missing, reubicarlo en matched
        if any(kw in item_lower for kw in LOCATION_KEYWORDS):
            relocated_to_matched.append(item)
        else:
            clean_missing.append(item)

    if relocated_to_matched:
        matched_skills.extend(relocated_to_matched)

    analysis_result["missing_skills"] = clean_missing
    analysis_result["matched_skills"] = matched_skills
    analysis_result["transferable_skills"] = transferable_skills

    # Asegurar tipos y valores seguros
    match_pct = float(analysis_result.get("match_percentage", 50))
    # Si se reubicaron penalizaciones de residencia injustificadas, dar compensación justa
    if relocated_to_matched:
        match_pct = min(100.0, match_pct + (len(relocated_to_matched) * 5.0))

    match_pct = max(0.0, min(100.0, match_pct))
    analysis_result["match_percentage"] = int(match_pct)
    analysis_result["qualifies_for_adaptation"] = match_pct >= MIN_MATCH_THRESHOLD

    job_title = analysis_result.get("job_title", "Vacante Analizada")
    company = analysis_result.get("company", "Empresa")

    # Guardar en SQLite historial local
    try:
        save_job_analysis(
            job_title=job_title,
            company=company,
            url=job_url,
            job_description=job_text[:3000],  # Guardar extracto
            match_percentage=match_pct,
            analysis_data=analysis_result
        )
    except Exception as e:
        print(f"Advertencia al guardar historial: {e}")

    return analysis_result
