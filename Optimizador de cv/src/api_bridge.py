import json
import webview
from typing import Dict, Any, Optional
from src.database import (
    get_config, set_config, delete_config,
    get_user_profile, get_job_history
)
from src.config import MIN_MATCH_THRESHOLD

class ApiBridge:
    """Puente bidireccional entre la interfaz web (JavaScript) y el backend en Python."""

    def __init__(self):
        self._window: Optional[webview.Window] = None

    def set_window(self, window: webview.Window):
        self._window = window

    # --- Estado Global de la Aplicación ---

    def get_app_state(self) -> Dict[str, Any]:
        """Devuelve el estado actual de la aplicación (configuración, perfil, etc.)."""
        api_key = get_config("gemini_api_key", "")
        profile = get_user_profile()
        has_api_key = bool(api_key and len(api_key.strip()) > 10)
        
        return {
            "has_api_key": has_api_key,
            "has_profile": profile is not None,
            "user_name": profile.get("full_name", "") if profile else "",
            "profile_summary": profile.get("summary", "") if profile else "",
            "original_cv_file": profile.get("original_filename", "") if profile else "",
            "min_match_threshold": MIN_MATCH_THRESHOLD,
            "recent_history": get_job_history(limit=5)
        }

    # --- Gestión de API Key ---

    def save_api_key(self, api_key: str) -> Dict[str, Any]:
        """Valida contra los servidores de Google Gemini y guarda en SQLite si es válida."""
        from src.gemini_service import validate_api_key
        
        clean_key = api_key.strip().strip('"').strip("'").strip()
        is_valid, message = validate_api_key(clean_key)
        if not is_valid:
            return {"success": False, "error": message}
        
        set_config("gemini_api_key", clean_key)
        return {"success": True, "message": message}

    def test_current_api_key(self) -> Dict[str, Any]:
        """Comprueba el estado de la clave almacenada actualmente."""
        from src.gemini_service import validate_api_key
        
        key = get_config("gemini_api_key")
        if not key:
            return {"success": False, "error": "No hay ninguna clave API configurada."}
        
        is_valid, message = validate_api_key(key)
        return {"success": is_valid, "message": message}

    def remove_api_key(self) -> Dict[str, Any]:
        """Elimina la clave API guardada de la base de datos local."""
        delete_config("gemini_api_key")
        return {"success": True, "message": "Clave eliminada exitosamente."}

    def get_clipboard_text(self) -> Dict[str, Any]:
        """Obtiene el texto almacenado en el portapapeles de Windows de forma segura."""
        try:
            import tkinter as tk
            root = tk.Tk()
            root.withdraw()
            text = root.clipboard_get()
            root.destroy()
            return {"success": True, "text": text}
        except Exception:
            return {"success": False, "text": ""}

    # --- Ingesta y Procesamiento de Currículum ---

    def select_and_process_cv(self) -> Dict[str, Any]:
        """Abre el diálogo nativo de Windows, extrae el texto y estructura el CV con Gemini."""
        from pathlib import Path
        from src.document_parser import extract_text_from_file, parse_cv_with_gemini
        from src.database import save_user_profile

        api_key = get_config("gemini_api_key")
        if not api_key:
            return {
                "success": False, 
                "error": "Primero debes configurar tu API Key de Google en el botón 'Clave API' (arriba a la derecha)."
            }

        if not self._window:
            return {"success": False, "error": "Ventana no inicializada."}

        file_types = ('Archivos de Currículum (*.pdf;*.docx)', '*.pdf;*.docx')
        result = self._window.create_file_dialog(
            webview.OPEN_DIALOG,
            allow_multiple=False,
            file_types=[file_types[0]]
        )

        if not result or len(result) == 0:
            return {"success": False, "cancelled": True}

        file_path = result[0]
        filename = Path(file_path).name

        try:
            # 1. Extracción de texto
            raw_text = extract_text_from_file(file_path)

            # 2. Estructuración con IA
            structured = parse_cv_with_gemini(raw_text)

            # 3. Guardado en SQLite
            save_user_profile(structured, original_filename=filename)

            return {
                "success": True,
                "message": f"Currículum '{filename}' procesado y guardado exitosamente.",
                "profile": structured,
                "filename": filename
            }

        except Exception as e:
            return {"success": False, "error": f"Error al procesar el archivo: {str(e)}"}

    def process_dropped_file(self, filename: str, base64_data: str = "", local_path: Optional[str] = None) -> Dict[str, Any]:
        """Procesa un archivo de currículum (.pdf o .docx) arrastrado directamente a la aplicación."""
        import base64
        import tempfile
        import os
        from pathlib import Path
        from src.document_parser import extract_text_from_file, parse_cv_with_gemini
        from src.database import save_user_profile

        api_key = get_config("gemini_api_key")
        if not api_key:
            return {
                "success": False,
                "error": "Primero debes configurar tu API Key de Google en el botón superior derecho 'Clave API'."
            }

        # Validar extensión permitida
        clean_name = filename.strip()
        lower_name = clean_name.lower()
        if not (lower_name.endswith('.pdf') or lower_name.endswith('.docx')):
            return {
                "success": False,
                "error": "Formato de archivo no compatible. Por favor arrastra un archivo en formato PDF o Word (.docx)."
            }

        temp_path = None
        try:
            # Si se proporcionó una ruta local válida y existe en el sistema de archivos
            if local_path and os.path.exists(local_path):
                file_to_parse = local_path
            else:
                # Decodificar el contenido base64 recibido desde el navegador
                if not base64_data:
                    return {"success": False, "error": "No se recibieron datos legibles del archivo arrastrado."}
                
                # Remover posible prefijo data:...;base64,
                raw_b64 = base64_data.split(",", 1)[1] if "," in base64_data else base64_data
                file_bytes = base64.b64decode(raw_b64)
                
                ext = Path(clean_name).suffix or ".pdf"
                with tempfile.NamedTemporaryFile(delete=False, suffix=ext) as tmp:
                    tmp.write(file_bytes)
                    temp_path = tmp.name
                file_to_parse = temp_path

            # 1. Extracción de texto
            raw_text = extract_text_from_file(file_to_parse)

            # 2. Estructuración con IA
            structured = parse_cv_with_gemini(raw_text)

            # 3. Guardado en SQLite
            save_user_profile(structured, original_filename=clean_name)

            return {
                "success": True,
                "message": f"Currículum '{clean_name}' procesado y guardado exitosamente.",
                "profile": structured,
                "filename": clean_name
            }

        except Exception as e:
            return {"success": False, "error": f"Error al procesar el archivo arrastrado: {str(e)}"}
        finally:
            if temp_path and os.path.exists(temp_path):
                try:
                    os.remove(temp_path)
                except Exception:
                    pass

    def reset_profile(self) -> Dict[str, Any]:
        """Elimina el perfil guardado para permitir subir uno nuevo."""
        from src.database import delete_user_profile
        delete_user_profile()
        return {"success": True, "message": "Perfil eliminado."}

    # --- Auditoría y Análisis de Vacantes ---

    def analyze_job_offer(self, url: str = "", manual_text: str = "") -> Dict[str, Any]:
        """Extrae el contenido de la vacante y ejecuta la auditoría de viabilidad ATS con Gemini."""
        from src.job_scraper import extract_job_content, JobScraperError
        from src.match_evaluator import evaluate_job_match

        # 1. Validaciones previas
        api_key = get_config("gemini_api_key")
        if not api_key:
            return {
                "success": False,
                "error": "Debes configurar tu API Key de Google antes de analizar vacantes."
            }

        profile = get_user_profile()
        if not profile:
            return {
                "success": False,
                "error": "Por favor sube tu currículum base en el Paso 1 antes de analizar una oferta."
            }

        job_text = manual_text.strip()
        used_url = url.strip()

        # 2. Si no hay texto manual, intentar scraping de la URL
        if not job_text:
            if not used_url:
                return {
                    "success": False,
                    "error": "Ingresa una URL de la vacante o pega su descripción manualmente."
                }
            try:
                job_text = extract_job_content(used_url)
            except JobScraperError as e:
                return {
                    "success": False,
                    "requires_manual": e.requires_manual,
                    "error": str(e)
                }
            except Exception as e:
                return {
                    "success": False,
                    "requires_manual": True,
                    "error": f"Error al acceder a la URL: {str(e)[:100]}. Intenta pegando la descripción manualmente."
                }

        # 3. Evaluar viabilidad con Gemini
        try:
            analysis = evaluate_job_match(
                job_text=job_text,
                job_url=used_url,
                profile_data=profile.get("parsed_data", {})
            )
            return {"success": True, "analysis": analysis}
        except Exception as e:
            return {
                "success": False,
                "error": f"Error durante la auditoría con IA: {str(e)}"
            }

    # --- Generación de CV Adaptado (Fase 5) ---

    def generate_adapted_cv(self, job_analysis: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Adapta el currículum con Gemini y genera el documento PDF ATS profesional con ReportLab.
        Abre el diálogo nativo para guardar con el nombre estandarizado [Nombre_Apellido]_[Puesto_Deseado].pdf.
        """
        from pathlib import Path
        from src.cv_tailor import tailor_cv_with_gemini, generate_ats_filename
        from src.pdf_generator import build_ats_pdf
        from src.database import update_job_history_cv, get_job_history

        # 1. Comprobaciones de seguridad
        api_key = get_config("gemini_api_key")
        if not api_key:
            return {
                "success": False, 
                "error": "Debes configurar tu API Key de Google antes de generar un currículum optimizado."
            }

        profile = get_user_profile()
        if not profile or not profile.get("parsed_data"):
            return {
                "success": False, 
                "error": "No se encontró ningún perfil profesional base cargado en el sistema."
            }

        profile_data = profile.get("parsed_data", {})

        # Si no se pasó análisis explícito, buscar el más reciente en base de datos
        history_id = None
        if not job_analysis:
            recent = get_job_history(limit=1)
            if recent and recent[0].get("analysis"):
                job_analysis = recent[0]["analysis"]
                history_id = recent[0]["id"]
            else:
                return {
                    "success": False, 
                    "error": "No hay ningún análisis de vacante disponible para realizar la adaptación."
                }
        else:
            history_id = job_analysis.get("id")

        # 2. Criterio de activación: requiere afinidad >= 75% (configurable en config.py)
        score = job_analysis.get("match_percentage", 0)
        if score < MIN_MATCH_THRESHOLD:
            return {
                "success": False,
                "error": f"La afinidad actual es del {score}%. Para garantizar altos estándares de éxito, se requiere ≥ {int(MIN_MATCH_THRESHOLD)}% de compatibilidad para adaptar el currículum."
            }

        # 3. Nomenclatura del archivo generado según AGENTS.md regla 4.1: [Nombre_Apellido]_[Puesto_Deseado].pdf
        full_name = profile_data.get("full_name") or profile.get("full_name") or "Profesional"
        target_title = job_analysis.get("job_title") or "Puesto_Deseado"
        default_filename = generate_ats_filename(full_name, target_title)

        if not self._window:
            return {"success": False, "error": "Ventana de escritorio no inicializada."}

        # 4. Diálogo nativo para guardar archivo en Windows
        file_types = ('Documentos PDF (*.pdf)', '*.pdf')
        save_result = self._window.create_file_dialog(
            webview.SAVE_DIALOG,
            save_filename=default_filename,
            file_types=[file_types[0]]
        )

        if not save_result:
            return {"success": False, "cancelled": True}

        dest_file = save_result[0] if isinstance(save_result, (list, tuple)) else str(save_result)
        if not dest_file.lower().endswith(".pdf"):
            dest_file += ".pdf"

        try:
            # 5. Adaptación ética con Gemini (reordenamiento de habilidades y logros clave)
            adapted_cv = tailor_cv_with_gemini(profile_data, job_analysis)

            # 6. Construcción del PDF ATS con ReportLab
            final_path = build_ats_pdf(adapted_cv, dest_file)

            # 7. Actualización en SQLite del historial
            if history_id:
                try:
                    update_job_history_cv(history_id, final_path)
                except Exception:
                    pass

            return {
                "success": True,
                "file_path": final_path,
                "filename": Path(final_path).name,
                "message": "Currículum adaptado y optimizado para ATS generado con éxito."
            }

        except Exception as e:
            return {
                "success": False,
                "error": f"Error al generar el currículum adaptado: {str(e)}"
            }

    # --- Apertura de Archivos y Carpetas en el Sistema ---

    def open_file(self, file_path: str) -> Dict[str, Any]:
        """Abre el archivo PDF generado con el visor predeterminado de Windows."""
        import os
        from pathlib import Path
        path = Path(file_path).resolve()
        if not path.exists():
            return {"success": False, "error": "El archivo especificado no existe."}
        try:
            os.startfile(str(path))
            return {"success": True}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def open_containing_folder(self, file_path: str) -> Dict[str, Any]:
        """Abre el explorador de archivos de Windows y resalta el archivo generado."""
        import os
        import subprocess
        from pathlib import Path
        path = Path(file_path).resolve()
        try:
            if os.name == 'nt' and path.exists():
                subprocess.Popen(['explorer', '/select,', str(path)])
            else:
                os.startfile(str(path.parent))
            return {"success": True}
        except Exception as e:
            return {"success": False, "error": str(e)}

    # --- Métodos de Historial ---

    def get_history(self) -> Dict[str, Any]:
        """Obtiene el historial de ofertas analizadas."""
        return {"success": True, "history": get_job_history(limit=15)}
