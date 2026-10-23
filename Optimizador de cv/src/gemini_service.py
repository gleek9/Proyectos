import json
from typing import Tuple, Optional, Dict, Any
from google import genai
from google.genai import errors
from src.database import get_config, set_config

# Modelos preferidos Gemini 3.0 en adelante en modalidad Flash con múltiples respaldos por cuota
PREFERRED_FLASH_MODELS_V3 = [
    "gemini-3-flash-preview",
    "gemini-3.8-flash",
    "gemini-3.7-flash",
    "gemini-3.5-flash",
    "gemini-3.5-flash-lite",
    "gemini-3.1-flash-lite",
    "gemini-3.1-flash",
    "gemini-3.0-flash",
    "gemini-3.0-flash-preview",
    "gemini-3.0-flash-001",
    "gemini-3-flash",
    "gemini-3.0-flash-lite",
]

def is_gemini_v3_flash(model_id: str) -> bool:
    """Verifica si el identificador corresponde a un modelo Flash de generación 3.0 o superior."""
    clean = model_id.lower().replace("models/", "").strip()
    if "flash" not in clean:
        return False
    # Excluir explícitamente versiones antiguas anteriores a 3.0
    if any(clean.startswith(f"gemini-{v}") for v in ["1.", "1-", "1.5", "2.0", "2.5", "2-", "2."]):
        return False
    # Aceptar cualquier modelo Flash versión 3.0+ o futuras versiones (3.x, 4.x)
    return any(prefix in clean for prefix in ["gemini-3", "gemini-3.", "gemini-4"])

def get_gemini_client(api_key: Optional[str] = None) -> Optional[genai.Client]:
    """Crea una instancia del cliente de Google Gemini usando la clave provista o la almacenada en SQLite."""
    key = api_key or get_config("gemini_api_key")
    if not key:
        return None
    return genai.Client(api_key=key.strip().strip('"').strip("'"))

def discover_flash_models(client: genai.Client) -> list:
    """
    Descubre dinámicamente los modelos Flash Gemini 3.0 en adelante disponibles para la cuenta.
    Prioriza modelos 3.0+ y prepara una lista con múltiples respaldos para rotación automática de cuota.
    """
    discovered_v3 = []

    try:
        # Consultar la lista de modelos activos en Google AI Studio para este usuario
        for model in client.models.list():
            raw_name = getattr(model, "name", "") or ""
            model_id = raw_name.replace("models/", "").strip()
            
            # Verificar si tiene acciones soportadas que restrinjan generación
            supported = getattr(model, "supported_actions", None)
            if supported:
                supported_lower = [str(a).lower() for a in supported]
                if not any("generate" in a or "predict" in a for a in supported_lower):
                    continue

            if is_gemini_v3_flash(model_id):
                if model_id not in discovered_v3:
                    discovered_v3.append(model_id)
    except Exception:
        # Fallback a la lista curada de modelos 3.0+ si models.list() no está disponible o tiene restricciones
        pass

    # Combinar modelos descubiertos en tiempo real con la lista de modelos 3.0+ Flash
    combined = []
    for m in discovered_v3:
        clean = m.replace("models/", "").strip()
        if clean and clean not in combined:
            combined.append(clean)

    for m in PREFERRED_FLASH_MODELS_V3:
        clean = m.replace("models/", "").strip()
        if clean and clean not in combined:
            combined.append(clean)

    return combined

def validate_api_key(api_key: str) -> Tuple[bool, str]:
    """
    Valida en tiempo real la clave API de Google Gemini utilizando modelos Flash 3.0 en adelante.
    Verifica conectividad y comprueba la disponibilidad de múltiples modelos de respaldo para rotación de cuota.
    """
    clean_key = api_key.strip().strip('"').strip("'").strip()
    if not clean_key:
        return False, "La clave de API no puede estar vacía."
    
    if len(clean_key) < 10:
        return False, "La clave ingresada es demasiado corta para ser una clave válida de Google AI Studio."

    try:
        client = genai.Client(api_key=clean_key)
        
        # 1. Obtener lista de modelos Flash 3.0+
        flash_models = discover_flash_models(client)

        # 2. Probar conectividad con los modelos Flash 3.0+ ordenados por prioridad
        success = False
        connected_model = ""

        for model_name in flash_models:
            try:
                response = client.models.generate_content(
                    model=model_name,
                    contents="OK"
                )
                if response and response.text:
                    success = True
                    connected_model = model_name
                    break
            except errors.APIError as api_err:
                err_text = str(api_err).lower()
                
                # Rechazo inequívoco de credenciales por parte de Google
                if "api_key_invalid" in err_text or "api key not valid" in err_text or "key expired" in err_text:
                    return False, "La clave de API ingresada es inválida o ha sido revocada en Google AI Studio."
                if "permission_denied" in err_text or "403" in err_text:
                    if "billing" in err_text:
                        return False, "La cuenta asociada a la clave requiere verificar facturación o permisos adicionales."
                    return False, "Permiso denegado. Revisa que tu clave API tenga permisos habilitados en Google AI Studio."
                
                # Si es cuota agotada (429/ResourceExhausted) o modelo no disponible en la cuenta (404/400),
                # se continúa con el siguiente modelo Flash 3.0+ de la lista de respaldo
                continue
            except Exception:
                continue

        if success:
            backup_count = max(0, len(flash_models) - 1)
            return True, f"Clave verificada exitosamente. Motor activo: {connected_model} (con {backup_count} modelos Flash 3.0+ configurados para rotación por cuota)."

        # 3. Verificación de respaldo si todos los modelos Flash 3.0+ estuvieron saturados de cuota
        try:
            pager = client.models.list(config={"page_size": 1})
            if next(iter(pager), None) is not None:
                return True, "Clave verificada correctamente con Google AI Studio. Modelos Flash 3.0+ configurados con rotación activa."
        except Exception:
            pass

        return False, "No se pudo obtener respuesta de los modelos Gemini Flash 3.0+. Comprueba tu cuota en Google AI Studio o tu conexión."

    except errors.APIError as e:
        error_str = str(e).lower()
        if "api_key_invalid" in error_str or "api key not valid" in error_str:
            return False, "La clave de API ingresada es inválida o ha sido revocada en Google AI Studio."
        elif "quota" in error_str or "resource_exhausted" in error_str or "429" in error_str:
            return False, "Tu clave de API ha alcanzado temporalmente el límite de cuota en Google AI Studio."
        elif "permission_denied" in error_str or "403" in error_str:
            return False, "Permiso denegado. Revisa las restricciones de tu clave en Google AI Studio."
        else:
            return False, f"Error devuelto por Google: {e.message if hasattr(e, 'message') else str(e)[:120]}"

    except errors.ServerError:
        return False, "Los servidores de Google Gemini están experimentando saturación temporal. Intenta en un momento."

    except Exception as e:
        err_msg = str(e)
        if "connection" in err_msg.lower() or "timeout" in err_msg.lower():
            return False, "No se pudo conectar a los servidores de Google. Comprueba tu conexión a internet."
        return False, f"Error al verificar la clave: {err_msg[:100]}"

def run_prompt_json(prompt: str, system_instruction: Optional[str] = None) -> Dict[str, Any]:
    """
    Ejecuta un prompt estructurado solicitando una respuesta exclusivamente en JSON.
    Implementa rotación automática entre modelos Flash 3.0+ si un modelo agota su cuota (429/ResourceExhausted).
    """
    client = get_gemini_client()
    if not client:
        raise ValueError("No hay una clave API configurada. Configúrala primero en Ajustes.")

    flash_models = discover_flash_models(client)
    last_error = None
    tested_models = []

    for model in flash_models:
        try:
            tested_models.append(model)
            config = {
                "response_mime_type": "application/json"
            }
            if system_instruction:
                config["system_instruction"] = system_instruction

            response = client.models.generate_content(
                model=model,
                contents=prompt,
                config=config
            )

            if response and response.text:
                clean_text = response.text.strip()
                # Limpiar posibles delimitadores de código markdown
                if clean_text.startswith("```"):
                    lines = clean_text.splitlines()
                    if lines and lines[0].startswith("```"):
                        lines = lines[1:]
                    if lines and lines[-1].startswith("```"):
                        lines = lines[:-1]
                    clean_text = "\n".join(lines).strip()

                return json.loads(clean_text)
        except Exception as e:
            last_error = e
            # Ante error de cuota agotada (429/RESOURCE_EXHAUSTED) o modelo no disponible,
            # rota de inmediato al siguiente modelo Flash 3.0+ en la lista
            continue

    raise RuntimeError(
        f"Fallo al procesar con los modelos Gemini Flash 3.0+ (probados: {', '.join(tested_models[:5])}). Último error: {last_error}"
    )
