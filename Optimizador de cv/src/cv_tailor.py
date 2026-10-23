import json
import re
import unicodedata
from typing import Dict, Any, Optional
from src.gemini_service import run_prompt_json

def clean_filename_part(text: str) -> str:
    """Normaliza y limpia una cadena para usarla en nombres de archivos sin caracteres extraños."""
    # Remover tildes y diacríticos
    nfkd = unicodedata.normalize('NFKD', text)
    ascii_text = nfkd.encode('ASCII', 'ignore').decode('utf-8')
    # Reemplazar espacios y caracteres no alfanuméricos por guiones bajos
    cleaned = re.sub(r'[^a-zA-Z0-9]+', '_', ascii_text).strip('_')
    return cleaned or "Profesional"

def generate_ats_filename(full_name: str, target_title: str) -> str:
    """
    Genera el nombre estandarizado de archivo según AGENTS.md:
    [Nombre_Apellido]_[Puesto_Deseado].pdf
    """
    clean_name = clean_filename_part(full_name)
    clean_title = clean_filename_part(target_title)
    return f"{clean_name}_{clean_title}.pdf"

def tailor_cv_with_gemini(
    profile_data: Dict[str, Any], 
    job_analysis: Dict[str, Any],
    job_text: str = ""
) -> Dict[str, Any]:
    """
    Reescribe y adapta el perfil profesional del candidato para la vacante específica.
    Reorganiza habilidades, resalta logros relevantes e incorpora palabras clave de la oferta de forma ética.
    """
    profile_json = json.dumps(profile_data, ensure_ascii=False, indent=2)
    job_title = job_analysis.get("job_title", "Puesto Deseado")
    keywords = job_analysis.get("key_ats_keywords", [])
    keywords_str = ", ".join(keywords) if keywords else "Estándares del sector"

    system_instruction = (
        "Eres un redactor profesional senior de currículums ejecutivos y especialista en optimización para ATS. "
        "Tu misión es adaptar el currículum del candidato para maximizar su relevancia frente a la vacante objetivo. "
        "REGLA ÉTICA ESTRICTA: No inventes títulos universitarios, empresas ni tecnologías que el candidato no haya usado. "
        "Tu tarea consiste en reorganizar el orden de las habilidades, enfatizar los logros afines y refrasear la experiencia "
        "utilizando verbos de acción y las palabras clave de la oferta para superar los filtros ATS con el mayor puntaje."
    )

    prompt = f"""
Adapta el siguiente currículum profesional para la posición de: "{job_title}".

PALABRAS CLAVE ATS PRIORITARIAS:
{keywords_str}

DATOS DEL CANDIDATO (Base real):
---
{profile_json}
---

INSTRUCCIONES DE ADAPTACIÓN:
1. Adapta el "summary" (resumen ejecutivo) a 3 o 4 líneas directas y potentes orientadas al puesto de {job_title}.
2. En las "experiences", reordena y pule las viñetas de logros ("achievements") para resaltar proyectos afines a las necesidades del puesto. Emplea verbos de acción en pasado (Desarrollé, Diseñé, Lideré, Implementé, Automaticé) y métricas cuantitativas si existen.
3. En las "skills", coloca en primer lugar las habilidades técnicas que coincidan con la vacante.
4. Mantén las fechas, empresas, roles y educación 100% fieles a la realidad del candidato.

Devuelve ÚNICAMENTE un objeto JSON con esta estructura exacta:
{{
  "full_name": "{profile_data.get('full_name', 'Nombre Apellido')}",
  "target_title": "{job_title}",
  "email": "{profile_data.get('email', '')}",
  "phone": "{profile_data.get('phone', '')}",
  "location": "{profile_data.get('location', '')}",
  "linkedin": "{profile_data.get('linkedin', '')}",
  "portfolio": "{profile_data.get('portfolio', '')}",
  "summary": "Resumen ejecutivo profesional adaptado y persuasivo...",
  "experiences": [
    {{
      "role": "Cargo desempeñado",
      "company": "Empresa",
      "location": "Ubicación o Remoto",
      "period": "Mes Año - Mes Año o Actual",
      "achievements": [
        "Logro adaptado con verbo de acción y palabras clave...",
        "Otro logro relevante..."
      ]
    }}
  ],
  "skills": {{
    "technical": ["Habilidades técnicas prioritarias para la vacante"],
    "tools": ["Herramientas de software y plataformas"],
    "soft": ["Competencias interpersonales clave"]
  }},
  "education": [
    {{
      "degree": "Título académico",
      "institution": "Institución",
      "year": "Año"
    }}
  ],
  "certifications": [
    "Certificación relevante..."
  ],
  "languages": [
    "Idioma y nivel..."
  ]
}}
"""

    adapted_data = run_prompt_json(prompt, system_instruction=system_instruction)

    # Validaciones de seguridad
    if not adapted_data.get("full_name"):
        adapted_data["full_name"] = profile_data.get("full_name", "Profesional")
    if not adapted_data.get("target_title"):
        adapted_data["target_title"] = job_title

    return adapted_data
