# PROJECT_STATUS.md — Estado del Proyecto: Optimizador de CV

> **Última actualización:** 2026-10-22  
> **Progreso Global:** 5% (Fase de Definición y Arquitectura completada)

---

## 📊 Tablero Resumen de Fases

| Fase | Descripción | Estado | Progreso |
| :---: | :--- | :---: | :---: |
| **0** | **Definición, Arquitectura y Skills** | ✅ Completada | 100% |
| **1** | **Estructura Base, Base de Datos y Ventana PyWebView** | ⏳ Pendiente | 0% |
| **2** | **Conectividad con Google Gemini (BYOK)** | ⏳ Pendiente | 0% |
| **3** | **Ingesta, Parseo y Persistencia del CV Base** | ⏳ Pendiente | 0% |
| **4** | **Extracción de Ofertas y Comparador de Viabilidad (>90%)** | ⏳ Pendiente | 0% |
| **5** | **Motor de Generación de PDF Adaptado (ATS)** | ⏳ Pendiente | 0% |
| **6** | **Diseño UI/UX Final y Compilación a `.exe`** | ⏳ Pendiente | 0% |

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
- [ ] Definición del entorno virtual y dependencias principales (`pywebview`, `pypdf`, `reportlab`, `beautifulsoup4`, `trafilatura`, `google-genai`).
- [ ] Creación del esquema SQLite (`cv_optimizer.db`):
  - Tabla `config`: almacenamiento de la API Key de Google.
  - Tabla `user_profile`: datos de contacto, resumen, experiencia, educación, habilidades.
  - Tabla `job_history`: historial de ofertas analizadas, porcentajes de match y CVs generados.
- [ ] Inicialización de la ventana de escritorio con PyWebView con carga de vista HTML/CSS básica y puente API bidireccional (Python ⇄ JavaScript).

---

### Fase 2: Conectividad con Google Gemini (BYOK)
*Objetivo: Permitir al usuario ingresar y validar su API Key de Google de forma segura.*
- [ ] Pantalla/Modal de configuración inicial para ingresar la API Key de Google Gemini.
- [ ] Endpoint en Python para validar la clave contra el modelo `gemini-1.5-flash` o `gemini-2.0-flash`.
- [ ] Guardado persistente de la API Key en SQLite una vez verificada.
- [ ] Manejo de errores de cuota, clave inválida o problemas de red con mensajes claros al usuario.

---

### Fase 3: Ingesta, Parseo y Persistencia del CV Base
*Objetivo: Permitir al usuario cargar su currículum una sola vez y estructurarlo.*
- [ ] Componente visual de "Drag & Drop" o selector de archivo PDF/DOCX.
- [ ] Módulo extractor de texto en Python (`pypdf` / `pdfplumber`).
- [ ] Prompt estructurado a Gemini para convertir el texto crudo del CV a un objeto JSON estandarizado:
  - Nombre completo, email, teléfono, ciudad/país, enlaces (LinkedIn/GitHub/Portfolio).
  - Experiencias laborales con viñetas de logros cuantificables.
  - Habilidades técnicas y blandas clasificadas.
  - Educación y certificaciones.
- [ ] Almacenamiento del JSON resultante en la tabla `user_profile`.

---

### Fase 4: Extracción de Ofertas y Comparador de Viabilidad (>90%)
*Objetivo: Analizar la vacante desde una URL y calcular la afinidad objetiva.*
- [ ] Campo de entrada de URL en la interfaz con botón "Analizar Oferta".
- [ ] Módulo de web scraping para extraer título, requisitos y descripción del trabajo:
  - Soporte para fallback: si la web bloquea el scraping (LinkedIn/Indeed), se despliega un área de texto para pegar la descripción manualmente.
- [ ] Prompt de evaluación ATS a Gemini:
  - Comparativa punto por punto: requisitos vs. experiencia del perfil.
  - Cálculo de porcentaje de viabilidad (0 a 100%).
  - Lista de fortalezas detectadas y lista de brechas/habilidades ausentes.
- [ ] Lógica de activación condicional en la UI:
  - Si porcentaje < 90%: Feedback visual claro, recomendaciones y botón de creación deshabilitado.
  - Si porcentaje ≥ 90%: Desbloqueo del botón de creación con animación visual destacada.

---

### Fase 5: Motor de Generación de PDF Adaptado (ATS)
*Objetivo: Crear el nuevo currículum optimizado listo para descarga directa.*
- [ ] Prompt de reescritura a Gemini:
  - Reorienta el perfil y los logros del candidato para destacar las coincidencias con la vacante.
  - Integra palabras clave de la oferta de trabajo de forma natural y ética.
- [ ] Generador de PDF en Python utilizando `ReportLab`:
  - Diseño limpio, tipografía legible, márgenes estándar y estructura parseable por sistemas ATS.
- [ ] Convención de nombrado automática:
  - Regla: `[Nombre_Apellido]_[Puesto_Deseado].pdf` (ej. `Uriel_Lopez_Senior_Frontend_Developer.pdf`).
- [ ] Diálogo nativo para guardar/descargar el archivo PDF directamente en la computadora.

---

### Fase 6: Pulido de UI/UX y Compilación a `.exe`
*Objetivo: Dejar el producto con acabados de alta calidad visual y empaquetar el ejecutable independiente.*
- [ ] Aplicar directrices de diseño (`frontend-design` y `ui-ux-pro-max`):
  - Modo oscuro refinado, espaciado armónico, tipografía moderna.
  - Microinteracciones, loaders animados durante las llamadas a la IA.
- [ ] Pruebas integrales de flujo extremo a extremo (E2E).
- [ ] Configuración del archivo de especificación de **PyInstaller** (`main.spec`):
  - Empaquetado de recursos estáticos (HTML, CSS, JS, plantillas).
  - Inclusión de dependencias binarias necesarias.
  - Configuración de icono de aplicación y modo ventana sin consola.
- [ ] Generación y validación del archivo final `OptimizadorCV.exe`.

---

## 📌 Bitácora de Cambios (Changelog)

* **2026-10-22:**
  - Análisis inicial y validación de viabilidad del proyecto.
  - Definición de arquitectura (Python + PyWebView + SQLite + Gemini API + ReportLab + PyInstaller).
  - Instalación de las Agent Skills oficiales en `.agents/skills/`.
  - Creación de los documentos de gobierno del proyecto: `AGENTS.md` y `PROJECT_STATUS.md`.
