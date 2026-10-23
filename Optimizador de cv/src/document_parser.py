import os
from pathlib import Path
from typing import Dict, Any, Optional
import pypdf
import docx
from src.gemini_service import run_prompt_json

def extract_text_from_file(file_path: str) -> str:
    """
    Extrae el texto sin formato de un archivo PDF o Word (.docx).
    Lanza ValueError si el archivo está vacío, no existe o no es soportado.
    """
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"El archivo no existe: {file_path}")

    ext = path.suffix.lower()
    extracted_text = ""

    if ext == ".pdf":
        try:
            reader = pypdf.PdfReader(str(path))
            pages_text = []
            for i, page in enumerate(reader.pages):
                text = page.extract_text()
                if text:
                    pages_text.append(text.strip())
            extracted_text = "\n\n".join(pages_text)
        except Exception as e:
            raise ValueError(f"No se pudo leer el archivo PDF: {str(e)}")

    elif ext == ".docx":
        try:
            doc = docx.Document(str(path))
            paras = [p.text.strip() for p in doc.paragraphs if p.text.strip()]
            
            # También extraer texto de tablas si las hay
            for table in doc.tables:
                for row in table.rows:
                    row_text = [cell.text.strip() for cell in row.cells if cell.text.strip()]
                    if row_text:
                        paras.append(" | ".join(row_text))
            
            extracted_text = "\n".join(paras)
        except Exception as e:
            raise ValueError(f"No se pudo leer el documento Word: {str(e)}")

    else:
        raise ValueError(f"Formato no soportado ({ext}). Utiliza un archivo .pdf o .docx.")

    cleaned_text = extracted_text.strip()
    if not cleaned_text or len(cleaned_text) < 30:
        raise ValueError("El archivo no contiene suficiente texto legible (posible documento escaneado como imagen).")

    return cleaned_text

def parse_cv_with_gemini(raw_text: str) -> Dict[str, Any]:
    """
    Utiliza Google Gemini para estructurar el texto crudo del currículum en un esquema JSON estándar ATS.
    """
    system_instruction = (
        "Eres un auditor y especialista senior en reclutamiento y sistemas ATS (Applicant Tracking Systems). "
        "Tu tarea es analizar el texto extraído de un currículum vitae y devolver un JSON estandarizado, "
        "sin inventar información y preservando nombres, fechas, logros cuantitativos y habilidades reales del candidato."
    )

    prompt = f"""
Analiza detalladamente el siguiente texto extraído de un currículum vitae y conviértelo en el siguiente formato JSON estandarizado:

{{
  "full_name": "Nombre completo del candidato",
  "email": "correo electrónico detectado o vacío",
  "phone": "número de teléfono detectado o vacío",
  "location": "Ciudad, País o vacío",
  "linkedin": "enlace o usuario de LinkedIn detectado o vacío",
  "portfolio": "enlace a GitHub, web o portafolio si existe o vacío",
  "summary": "Resumen profesional u objetivo del candidato sintetizado",
  "experiences": [
    {{
      "role": "Puesto o cargo desempeñado",
      "company": "Empresa u organización",
      "location": "Ubicación o Remoto",
      "start_date": "Fecha o año de inicio",
      "end_date": "Fecha o año de fin (o 'Actual')",
      "achievements": [
        "Logro o responsabilidad destacada",
        "Otro logro con métrica o impacto"
      ]
    }}
  ],
  "education": [
    {{
      "degree": "Título obtenido o carrera",
      "institution": "Universidad, instituto o escuela",
      "year": "Año de graduación o período"
    }}
  ],
  "skills": {{
    "technical": ["Habilidades duras / lenguajes / frameworks"],
    "tools": ["Herramientas de software / plataformas"],
    "soft": ["Habilidades interpersonales / de liderazgo"]
  }},
  "certifications": [
    "Certificación o curso relevante con fecha o emisor si existe"
  ],
  "languages": [
    "Idiomas y nivel de dominio si están indicados"
  ]
}}

TEXTO DEL CURRÍCULUM:
---
{raw_text}
---

Devuelve ÚNICAMENTE el objeto JSON válido.
"""

    structured_data = run_prompt_json(prompt, system_instruction=system_instruction)

    # Validaciones mínimas de integridad
    if not structured_data.get("full_name"):
        structured_data["full_name"] = "Profesional"

    if not structured_data.get("experiences"):
        structured_data["experiences"] = []

    if not structured_data.get("skills"):
        structured_data["skills"] = {"technical": [], "tools": [], "soft": []}

    return structured_data
