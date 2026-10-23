# PROJECT_STATUS.md — Estado del Proyecto: Cuva

> **Última actualización:** 2026-10-22  
> **Progreso Global:** 100% (Errores corregidos, Drag & Drop implementado, marca actualizada a Cuva y ejecutable generado con éxito)

---

## 📊 Tablero Resumen de Fases

| Fase | Descripción | Estado | Progreso |
| :---: | :--- | :---: | :---: |
| **0** | **Definición, Arquitectura y Skills** | ✅ Completada | 100% |
| **1** | **Estructura Base, Base de Datos y Ventana PyWebView** | ✅ Completada | 100% |
| **2** | **Conectividad con Google Gemini (BYOK)** | ✅ Completada | 100% |
| **3** | **Ingesta, Parseo y Persistencia del CV Base** | ✅ Completada | 100% |
| **4** | **Extracción de Ofertas y Comparador de Viabilidad (>90%)** | ✅ Completada | 100% |
| **5** | **Motor de Generación de PDF Adaptado (ATS)** | ✅ Completada | 100% |
| **6** | **Diseño UI/UX Final y Compilación a `.exe`** | ✅ Completada | 100% |

---

## 🛠️ Correcciones y Mantenimiento Post-Compilación (v1.1 — Cuva)

### Errores Reportados y Resueltos:
- [x] **Error de validación de API Key resuelto:**
  - *Causa raíz:* La validación llamaba al modelo `gemini-2.5-flash` (inexistente en la API pública de Gemini), provocando que Google rechazara las solicitudes con error 404/ClientError en cualquier clave válida de AI Studio. Además, existía una restricción estricta sobre el prefijo `AIza`.
  - *Solución:* Se adoptó `gemini-2.0-flash` como modelo principal con fallback dinámico a `gemini-1.5-flash`, `gemini-2.0-flash-lite` y `gemini-1.5-pro`. La validación ahora verifica credenciales usando la llamada oficial `client.models.list` sin consumo de cuota ni dependencia de nombres específicos, limpiando espacios y comillas accidentales.
- [x] **Soporte completo de Drag & Drop (Arrastrar y Soltar) para PDFs y DOCX:**
  - *Causa raíz:* No existían manejadores de eventos HTML5 `dragenter`, `dragover` ni `drop` en la interfaz web, impidiendo soltar archivos directamente desde el explorador de Windows.
  - *Solución:* Se configuró la captura global y específica de eventos Drag & Drop en el contenedor de carga, se agregaron estilos interactivos visuales (`.drag-over`) bajo el sistema Swiss White Minimalist y se implementó `ApiBridge.process_dropped_file` con decodificación Base64 y extracción multiformato (PDF y Word).
- [x] **Actualización de Identidad de Marca a "Cuva":**
  - Se actualizaron los títulos de la ventana, nombres de directores de datos (`%APPDATA%\Cuva`), encabezado institucional en `index.html` y archivo de especificación `main.spec` para compilar el binario `Cuva.exe`.

---

## 📝 Detalle por Fases

### Fase 0: Definición, Arquitectura y Configuración Inicial
- [x] Análisis de viabilidad técnica y operativa.
- [x] Selección del stack tecnológico (Python + PyWebView + SQLite + Gemini Flash + ReportLab + PyInstaller).
- [x] Instalación de Agent Skills (`frontend-design`, `ui-ux-pro-max`, `brainstorming`).
- [x] Creación de `AGENTS.md` con visión, misión, arquitectura y directrices.
- [x] Creación de `PROJECT_STATUS.md` para seguimiento granular.

---

### Fase 1: Estructura Base, Base de Datos y Ventana PyWebView
*Objetivo: Establecer el esqueleto de la aplicación de escritorio y la persistencia local.*
- [x] Definición del entorno virtual (`.venv`) y dependencias principales (`pywebview`, `pypdf`, `reportlab`, `beautifulsoup4`, `trafilatura`, `google-genai`).
- [x] Creación del esquema SQLite (`data/cv_optimizer.db`):
  - Tabla `config`: almacenamiento de la API Key de Google y preferencias.
  - Tabla `user_profile`: datos de contacto, resumen, experiencia, educación, habilidades.
  - Tabla `job_history`: historial de ofertas analizadas, porcentajes de match y CVs generados.
- [x] Inicialización de la ventana de escritorio con PyWebView con carga de vista HTML/CSS/JS moderna bajo el estándar Swiss White Minimalist y puente API bidireccional (`ApiBridge`: Python ⇄ JavaScript).
- [x] Diálogos nativos de Windows para selección de archivos (`create_file_dialog`) integrados en el puente.

---

### Fase 2: Conectividad con Google Gemini (BYOK)
*Objetivo: Permitir al usuario ingresar y validar su API Key de Google de forma segura.*
- [x] Pantalla/Modal de configuración con diseño minimalista para ingresar la API Key de Google Gemini con enlace directo a Google AI Studio.
- [x] Módulo `src/gemini_service.py` con validación en tiempo real conectando contra el modelo `gemini-2.0-flash` (con fallback automático a `gemini-1.5-flash` y `gemini-2.0-flash-lite`).
- [x] Guardado persistente y seguro de la clave verificada en la tabla `config` de SQLite local.
- [x] Manejo refinado de excepciones (`ClientError`, `APIError`, formato incorrecto, cuota agotada, problemas de red) con feedback pedagógico en la interfaz.

---

### Fase 3: Ingesta, Parseo y Persistencia del CV Base
*Objetivo: Permitir al usuario cargar su currículum una sola vez y estructurarlo.*
- [x] Componente visual selector de archivo PDF/DOCX conectado a la UI mediante cuadros de diálogo nativos de Windows y función de arrastrar y soltar (Drag & Drop).
- [x] Módulo extractor de texto multiformato (`src/document_parser.py`) con soporte completo para `.pdf` (`pypdf`) y `.docx` (`python-docx`).
- [x] Prompt estructurado ATS a Gemini para convertir el texto crudo del CV a un objeto JSON estandarizado:
  - Nombre completo, email, teléfono, ciudad/país, enlaces (LinkedIn/GitHub/Portfolio).
  - Experiencias laborales con viñetas de logros cuantitativos.
  - Habilidades técnicas, herramientas y habilidades blandas clasificadas.
  - Educación, certificaciones e idiomas.
- [x] Almacenamiento local del JSON resultante en la tabla `user_profile` de SQLite y sincronización instantánea en la interfaz de usuario.

---

### Fase 4: Extracción de Ofertas y Comparador de Viabilidad (>90%)
*Objetivo: Analizar la vacante desde una URL y calcular la afinidad objetiva.*
- [x] Campo de entrada de URL en la interfaz con botón "Auditar Viabilidad".
- [x] Módulo de web scraping (`src/job_scraper.py`) con headers realistas y extracción con Trafilatura y BeautifulSoup4:
  - Manejo automático de fallback: si la web bloquea el scraping (LinkedIn, Indeed, Cloudflare, authwalls), se despliega automáticamente el área de texto para pegar la descripción manualmente.
- [x] Prompt de evaluación y auditoría ATS en Gemini (`src/match_evaluator.py`):
  - Comparativa punto por punto: requisitos vs. experiencia real.
  - Cálculo de porcentaje objetivo de viabilidad (0 a 100%).
  - Desglose auditado en 3 columnas: requisitos cubiertos, habilidades transferibles y brechas formativas.
  - Generación de mensaje pedagógico en tono de mentor ejecutivo.
  - Persistencia de cada análisis en la tabla `job_history` de SQLite.
- [x] Lógica de activación condicional en la interfaz:
  - Si porcentaje < 90%: Feedback visual constructivo, explicación de brechas y botón bloqueado con mensaje explicativo.
  - Si porcentaje ≥ 90%: Desbloqueo suave del botón de acción pasando a Azul Autoridad (`#1E3A8A`) para proceder a la adaptación.

---

### Fase 5: Motor de Generación de PDF Adaptado (ATS)
*Objetivo: Crear el nuevo currículum optimizado listo para descarga directa.*
- [x] Prompt de reescritura ética a Gemini (`src/cv_tailor.py`):
  - Reorienta el perfil y los logros del candidato para destacar las coincidencias con la vacante sin inventar experiencia falsa.
  - Integra palabras clave de la oferta de trabajo de forma natural y ética.
- [x] Generador de PDF profesional en Python utilizando ReportLab Platypus (`src/pdf_generator.py`):
  - Diseño limpio en una sola columna, tipografía corporativa de alta legibilidad (`Helvetica`), márgenes de 36 pt (0.5"), divisores sutiles y estructura 100% parseable por sistemas ATS.
- [x] Convención de nombrado automática estricta:
  - Regla: `[Nombre_Apellido]_[Puesto_Deseado].pdf` (ej. `Uriel_Lopez_Senior_Frontend_Developer.pdf`) con sanitización de caracteres y acentos.
- [x] Diálogo nativo de Windows (`webview.SAVE_DIALOG`) para guardar directamente el archivo en la ubicación deseada por el usuario.
- [x] Componente visual de éxito en la interfaz con acciones directas para "Abrir PDF" y "Mostrar en Carpeta" (`os.startfile` / `explorer /select`).

---

### Fase 6: Pulido de UI/UX y Compilación a `.exe`
*Objetivo: Dejar el producto con acabados de alta calidad visual y empaquetar el ejecutable independiente.*
- [x] Aplicar directrices de diseño (`frontend-design` y `ui-ux-pro-max`):
  - Estética Swiss White Minimalist (lienzo en tonos blancos y Slate-50, tipografía Inter/Plus Jakarta Sans, sensación de confianza y precisión ejecutiva).
  - Microinteracciones deterministas, indicadores de privacidad local y feedback de mentor ejecutivo.
- [x] Pruebas integrales de flujo extremo a extremo (E2E) con validación de módulos y rutas `sys.frozen`.
- [x] Generación del icono nativo corporativo de alta resolución (`assets/icon.ico`) con dimensiones de 16px a 256px.
- [x] Configuración del archivo de especificación de **PyInstaller** (`main.spec`):
  - Empaquetado de recursos estáticos (`src/ui`, `assets`).
  - Inclusión de dependencias de datos de ReportLab (51 archivos) y Trafilatura (3 archivos).
  - Modo ventana sin consola (`console=False`) y asignación del icono de aplicación.
- [x] Generación exitosa del ejecutable independiente `dist/Cuva.exe` (~51 MB).

---

## 📌 Bitácora de Cambios (Changelog)

* **2026-10-22:**
  - Análisis inicial y validación de viabilidad del proyecto.
  - Definición de arquitectura (Python + PyWebView + SQLite + Gemini API + ReportLab + PyInstaller).
  - Instalación de las Agent Skills oficiales en `.agents/skills/`.
  - Creación de los documentos de gobierno del proyecto: `AGENTS.md` y `PROJECT_STATUS.md`.
  - **Fases 1 a 6:** Desarrollo de backend, integración con Gemini, ingesta de CV, comparador ATS, motor PDF ATS y compilación con PyInstaller.
  - **Mantenimiento y Corrección v1.1 (Cuva):**
    - Corrección en `src/gemini_service.py`: Reemplazo del modelo erróneo `gemini-2.5-flash` por los modelos estables `gemini-2.0-flash` y `gemini-1.5-flash`.
    - Validación ligera de clave API con `client.models.list` sin consumo de cuota ni fallos por prefijos restrictivos.
    - Implementación completa de Arrastrar y Soltar (Drag & Drop) en la interfaz con lectura Base64, soporte para PDF y Word (.docx), y estilos reactivos `.drag-over`.
    - Cambio de identidad corporativa y nomenclatura a **Cuva** en `config.py`, `index.html`, `app.js`, `main.spec` y compilación de `dist/Cuva.exe`.
  - **Mantenimiento y Corrección v1.2 (Soporte Gemini 3.0+ Flash con Rotación de Cuota):**
    - Despliegue exclusivo de la familia de modelos **Gemini 3.0 en adelante en modalidad Flash**:
      - `gemini-3-flash-preview`, `gemini-3.8-flash`, `gemini-3.7-flash`, `gemini-3.5-flash`, `gemini-3.5-flash-lite`, `gemini-3.1-flash-lite`, `gemini-3.1-flash`, `gemini-3.0-flash`, `gemini-3.0-flash-preview`, `gemini-3.0-flash-001`, `gemini-3-flash`, `gemini-3.0-flash-lite`.
    - Eliminación de modelos legacy/antiguos anteriores a 3.0 (1.5, 2.0).
    - Descubrimiento dinámico de modelos (`discover_flash_models`) con filtro estricto $\ge 3.0$ y ordenamiento de prioridad.
    - Rotación transparente de cuota (`RESOURCE_EXHAUSTED` / 429 / failover): si un modelo agota su cuota de peticiones por minuto o diarias en la cuenta del usuario, el sistema salta automáticamente al siguiente modelo Gemini 3.0+ Flash sin interrumpir el flujo.
    - Corrección en el clasificador de errores de `validate_api_key`: los errores de modelo no disponible o cuota no abortan la validación como "clave inválida", evaluando la lista completa con respaldo resiliente.
    - Limpieza de bloques de formato markdown (```json) en las respuestas de los modelos 3.0 Flash para evitar errores de parseo.

