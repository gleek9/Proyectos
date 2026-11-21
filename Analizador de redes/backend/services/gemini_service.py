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
                "temperature": 0.72,
                "topP": 0.95,
                "maxOutputTokens": 8192
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
        Recibe el perfil del cliente y los Reels virales de referencia (hasta 10 referencias analizadas).
        Aplica frameworks de retención y hooks virales (60-90 segundos) unificando cada sección de la escaleta con su guion exacto.
        """
        prompt = f"""
Actúa como un Director Creativo Senior y Estratega de Contenido Vertical de Alta Retención (TikTok / Instagram Reels / Shorts).

INFORMACIÓN DEL CLIENTE:
- Nombre de la Marca: {client_name}
- Categoría / Industria: {category}
- Perfil de Voz y Audiencia (Brand Voice): {brand_voice}

REELS VIRALES DE REFERENCIA EXTRAÍDOS DE LA COMPETENCIA:
{json.dumps(competitor_reels, indent=2, ensure_ascii=False)}

REGLAS OBLIGATORIAS DE VIRALIDAD, RETENCIÓN Y FORMATO (60 A 90 SEGUNDOS):
1. USO PROFUNDO DE LA REFERENCIA:
   - Analiza a fondo la transcripción, el caption y las métricas de cada Reel de referencia.
   - Identifica exactamente POR QUÉ retuvo a la audiencia (el mecanismo psicológico de su hook, el conflicto que plantea, el ritmo de revelación y su cierre) y trasládalo al contexto real de {client_name} sin copiar genéricamente.
   - Si una referencia habla de un tema o ángulo específico, usa ese ángulo real y supéralo en claridad y gancho.

2. HOOKS DE ALTA RETENCIÓN (00:00 - 00:04):
   - PROHIBIDO empezar con saludos ("Hola a todos", "En este video...", "¿Sabías qué..." tibio) o presentando la marca primero.
   - Cada una de las 3 propuestas DEBE usar un arquetipo de hook distinto entre estos:
     * Curiosity Gap (abre un bucle concreto sin regalar la respuesta aún)
     * Contrarian Claim (desmiente una creencia popular del sector con "pero")
     * Stakes / Consequence (enmarca un costo o pérdida real si siguen igual)
     * Mistake / Cost Confession (cifra o error específico que cuesta dinero/tiempo)
     * Direct Call-Out (nombra exactamente a la audiencia y su situación)
     * Withhold / Result-First (muestra el resultado primero y retiene el método un instante)
   - Incluye texto en pantalla de 3 a 5 palabras de alto contraste para que funcione incluso en silencio.

3. DURACIÓN ESTRICTA DE 60 A 90 SEGUNDOS Y RITMO DE LECTURA NATURAL:
   - Cada guion completo DEBE durar entre **65 y 85 segundos** (rango obligatorio **60–90 segundos**, equivalente a **160 a 225 palabras habladas** a ritmo natural).
   - Frases cortas y naturales de 8 a 16 palabras para leer fluido en voz alta frente a cámara o teleprompter, usando conectores de quiebre ("Pero espera", "Por eso", "El problema es que", "Y aquí viene lo clave").
   - Estructura obligatoria de 5 secciones con relación causal ("pero / por eso", nunca "y luego"):
     1) `[00:00 - 00:04]` Hook (Visual + Auditivo + Texto en pantalla) — ~12-18 palabras
     2) `[00:04 - 00:20]` Contexto y Tensión (escenario cotidiano y problema real) — ~35-45 palabras
     3) `[00:20 - 00:36]` Re-Hook / Quiebre (reinicia la atención con un giro, mito desmontado o cuello de botella) — ~30-40 palabras
     4) `[00:36 - 01:08]` Desarrollo y Payoff Paso a Paso (cierra el bucle abierto con pasos claros, ejemplos reales y cortes cada 3-4s) — ~65-90 palabras
     5) `[01:08 - 01:22]` Remate + CTA Limpio (cierre contundente o loop al inicio + una sola acción de baja fricción) — ~20-30 palabras

4. CADA SECCIÓN DE LA ESCALETA UNIDA CON SU GUION:
   - Cada objeto en `escalation_timeline` DEBE incluir tanto la dirección visual (`description` + `on_screen_text`) como el texto exacto palabra por palabra que el usuario debe decir en esa sección (`spoken_text`).
   - `full_script` debe reunir el guion completo unificado con marcas de tiempo, indicaciones visuales y locución completa.

FORMATO DE SALIDA ESTRICTO:
Responde ÚNICAMENTE con un JSON válido (sin markdown ```json) con una lista de 3 objetos:

[
  {{
    "title": "Título magnético adaptado al cliente",
    "competitor_source_info": "Ref: @competidor (185K vistas) • Hook: Contrarian Claim",
    "virality_badge": "185K vistas • ~75s",
    "original_reel_url": "https://instagram.com/reel/...",
    "original_transcript": "Mecanismo extraído de la referencia: qué gancho/estructura usó el competidor y por qué se adaptó así para el cliente.",
    "escalation_timeline": [
      {{
        "time_range": "00:00 - 00:04",
        "phase": "Hook · Contrarian Claim",
        "on_screen_text": "Esto te cuesta clientes",
        "description": "Plano medio cercano con movimiento rápido de cámara al frente y corte seco.",
        "spoken_text": "Frase de impacto inicial palabra por palabra..."
      }},
      {{
        "time_range": "00:04 - 00:20",
        "phase": "Contexto y Tensión",
        "on_screen_text": "El error común",
        "description": "Cambio de ángulo o B-roll mostrando el problema cotidiano del cliente.",
        "spoken_text": "Desarrollo de la tensión y escenario de 35-45 palabras..."
      }},
      {{
        "time_range": "00:20 - 00:36",
        "phase": "Re-Hook y Quiebre",
        "on_screen_text": "Pero hay un problema",
        "description": "Zoom-in ligero y cambio de ritmo visual para reiniciar la retención.",
        "spoken_text": "Frase de quiebre que abre un nuevo bucle de 30-40 palabras..."
      }},
      {{
        "time_range": "00:36 - 01:08",
        "phase": "Payoff y Solución",
        "on_screen_text": "3 pasos reales",
        "description": "Cortes dinámicos cada 3-4s mostrando cada punto clave o resultado.",
        "spoken_text": "Explicación concreta paso a paso de 65-90 palabras que cumple la promesa del hook..."
      }},
      {{
        "time_range": "01:08 - 01:22",
        "phase": "Remate y CTA",
        "on_screen_text": "Guarda esto",
        "description": "Plano limpio a cámara con cierre directo.",
        "spoken_text": "Conclusión redonda y llamado único a la acción de 20-30 palabras..."
      }}
    ],
    "full_script": "[00:00 - 00:04 | Hook]\\n(Visual: ...)\\nTexto hablado...\\n\\n[00:04 - 00:20 | Contexto]\\n..."
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
