import json
from typing import Dict, Any, Optional
from src.gemini_service import run_prompt_json
from src.database import save_job_analysis, get_user_profile

def evaluate_job_match(
    job_text: str, 
    job_url: str = "", 
    profile_data: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Compara el perfil profesional del usuario contra la vacante utilizando Google Gemini.
    Devuelve un diagnóstico estructurado con porcentaje, 3 columnas de habilidades y feedback de mentor.
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
2. Calcula un porcentaje de viabilidad real y objetivo (entero entre 0 y 100):
   - ≥ 90%: El candidato cubre prácticamente todos los requisitos críticos y tiene experiencia alineada en el rol.
   - 70% - 89%: Buen ajuste con sólida base transferible, pero le faltan algunas herramientas o tecnologías prioritarias.
   - < 70%: Brechas sustanciales de experiencia o requisitos no cubiertos.
3. Desglosa los requisitos en 3 listas claras:
   - "matched_skills": Requisitos clave y tecnologías de la oferta que el candidato CUMPLE demostrablemente con su experiencia.
   - "transferable_skills": Habilidades secundarias, metodologías o tecnologías afines que el candidato posee y puede transferir rápidamente.
   - "missing_skills": Requisitos clave o tecnologías obligatorias de la vacante que NO aparecen en el perfil del candidato y explican la puntuación.
4. Redacta un "mentor_feedback": 2 a 3 frases en tono constructivo de mentor ejecutivo. Si el porcentaje es < 90%, explica pedagógicamente qué habilidad necesita reforzar y resalta dónde tiene mayor fortaleza. Si es ≥ 90%, confirma su alta competitividad para postular.
5. Extrae una lista de 5 a 10 "key_ats_keywords" fundamentales de la oferta.

Genera ÚNICAMENTE este formato JSON:
{{
  "job_title": "Título del puesto",
  "company": "Nombre de la empresa",
  "match_percentage": 85,
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

    # Asegurar tipos y valores seguros
    match_pct = float(analysis_result.get("match_percentage", 50))
    match_pct = max(0.0, min(100.0, match_pct))
    analysis_result["match_percentage"] = int(match_pct)
    analysis_result["qualifies_for_adaptation"] = match_pct >= 90.0

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
