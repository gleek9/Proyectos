import json
import base64
import urllib.request
import urllib.error
from typing import Optional, Dict, Any, List
from config import settings

class GeminiService:
    def __init__(self):
        self.api_key = settings.GEMINI_API_KEY
        self.model = settings.GEMINI_MODEL or "gemini-3-flash-preview"
        self.fallback_model = "gemini-2.5-flash"

    def _call_api(self, model_name: str, payload: dict) -> dict:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent?key={self.api_key}"
        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(
            url,
            data=data,
            headers={"Content-Type": "application/json"}
        )
        with urllib.request.urlopen(req, timeout=30) as resp:
            return json.loads(resp.read().decode("utf-8"))

    def generate_content(self, prompt: str, system_instruction: Optional[str] = None) -> str:
        """
        Genera contenido de texto con Gemini 3.0 gratuito (con fallback a 2.5-flash).
        """
        payload: Dict[str, Any] = {
            "contents": [
                {
                    "parts": [{"text": prompt}]
                }
            ],
            "generationConfig": {
                "temperature": 0.7,
                "topP": 0.95,
                "maxOutputTokens": 4096
            }
        }

        if system_instruction:
            payload["systemInstruction"] = {
                "parts": [{"text": system_instruction}]
            }

        # Intentar con modelo principal (Gemini 3.0)
        try:
            res = self._call_api(self.model, payload)
            candidates = res.get("candidates", [])
            if candidates:
                return candidates[0]["content"]["parts"][0]["text"]
        except Exception as e:
            # Fallback a gemini-2.5-flash
            try:
                res = self._call_api(self.fallback_model, payload)
                candidates = res.get("candidates", [])
                if candidates:
                    return candidates[0]["content"]["parts"][0]["text"]
            except Exception as e_fallback:
                raise RuntimeError(f"Error generando con Gemini ({self.model} y {self.fallback_model}): {e_fallback}")

        return ""

    def transcribe_and_analyze_audio(self, audio_bytes: bytes, mime_type: str = "audio/mp3") -> str:
        """
        Transcribe audio directamente usando Gemini Multimodal sin necesidad de Groq.
        """
        audio_b64 = base64.b64encode(audio_bytes).decode("utf-8")
        prompt = (
            "Transcribe palabra por palabra y con total exactitud todo lo que se dice en este audio en español. "
            "Incluye marcas de tiempo [00:00 - 00:03] al inicio de cada cambio de idea o bloque. "
            "Identifica claramente el gancho inicial (primeros 3 segundos), el cuerpo/retención y la llamada a la acción (CTA)."
        )

        payload = {
            "contents": [
                {
                    "parts": [
                        {
                            "inlineData": {
                                "mimeType": mime_type,
                                "data": audio_b64
                            }
                        },
                        {"text": prompt}
                    ]
                }
            ],
            "generationConfig": {
                "temperature": 0.2
            }
        }

        try:
            res = self._call_api(self.model, payload)
            return res["candidates"][0]["content"]["parts"][0]["text"]
        except Exception:
            res = self._call_api(self.fallback_model, payload)
            return res["candidates"][0]["content"]["parts"][0]["text"]

    def generate_script_proposals(
        self,
        client_name: str,
        category: str,
        brand_voice: str,
        competitor_reels: List[dict]
    ) -> List[dict]:
        """
        Recibe el perfil del cliente y los 3 Reels virales de competidores.
        Devuelve un JSON estructurado con las 3 propuestas adaptadas (Título, Escaleta por tiempos y Guion completo).
        """
        prompt = f"""
Actúa como un Director Creativo Senior y Guionista Experto en Contenido Vertical de Alta Conversión (Método ACE: Analizar, Crear, Escalar).

INFORMACIÓN DEL CLIENTE:
- Nombre de la Marca: {client_name}
- Categoría / Industria: {category}
- Perfil de Voz y Audiencia (Brand Voice): {brand_voice}

REELS VIRALES DE LA COMPETENCIA A ADAPTAR:
{json.dumps(competitor_reels, indent=2, ensure_ascii=False)}

INSTRUCCIÓN:
Para cada uno de los Reels virales (máximo 3), realiza ingeniería inversa:
1. Extrae el principio psicológico del gancho original y el formato narrativo que lo hizo viral.
2. Adapta completamente la idea para {client_name}, usando su tono, su jerga y sus servicios.
3. Genera una ESCALETA TÉCNICA detallada desglosada en bloques de tiempo exactos:
   - [00:00 - 00:03] Gancho Visual y Auditivo (impacto, patrón disruptivo)
   - [00:03 - 00:15] Retención / Desarrollo (conflicto, dato revelador, prueba)
   - [00:15 - 00:30+] Resolución y Llamada a la Acción (CTA específico)
4. Redacta el GUION COMPLETO palabra por palabra, listo para leer en teleprompter o memorizar y grabar.

FORMATO DE SALIDA ESTRICTO:
Debes responder ÚNICAMENTE con un JSON válido (sin bloques de código markdown tipo ```json, solo el JSON puro) con la siguiente estructura de lista:

[
  {{
    "title": "Título magnético para el cliente",
    "competitor_source_info": "Inspirado en Reel de @competidor con 185K vistas",
    "virality_badge": "185K vistas • 14K likes",
    "original_reel_url": "https://instagram.com/reel/...",
    "original_transcript": "Transcripción o resumen de lo que decía el video original",
    "escalation_timeline": [
      {{
        "time_range": "00:00 - 00:03",
        "phase": "Gancho Visual y Auditivo",
        "description": "Qué hace la persona ante cámara, plano, texto en pantalla y primera frase de choque."
      }},
      {{
        "time_range": "00:03 - 00:15",
        "phase": "Retención y Problema Real",
        "description": "Desarrollo del concepto central, desmontando un mito común."
      }},
      {{
        "time_range": "00:15 - 00:30",
        "phase": "Resolución y Llamada a la Acción",
        "description": "Conclusión de alto valor y llamado a comentar una palabra clave."
      }}
    ],
    "full_script": "Texto exacto palabra por palabra que el creador debe decir ante cámara."
  }}
]
"""
        response_text = self.generate_content(
            prompt=prompt,
            system_instruction="Eres un motor de inteligencia artificial especializado en ingeniería inversa de videos virales y redacción de guiones de alto impacto. Devuelves exclusivamente JSON puro estructurado."
        )

        clean_text = response_text.strip()
        if clean_text.startswith("```json"):
            clean_text = clean_text[7:]
        if clean_text.startswith("```"):
            clean_text = clean_text[3:]
        if clean_text.endswith("```"):
            clean_text = clean_text[:-3]
        clean_text = clean_text.strip()

        try:
            proposals = json.loads(clean_text)
            if isinstance(proposals, list):
                return proposals
        except Exception:
            pass

        return []

gemini_service = GeminiService()
