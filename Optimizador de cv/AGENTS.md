# AGENTS.md — Optimizador de CV

## 1. Visión y Misión

### Visión
Convertirse en la herramienta de escritorio de referencia, accesible, privada y sin fricción, para optimizar la postulación laboral, permitiendo que cualquier profesional adapte su currículum de manera inteligente y competitiva a ofertas de trabajo en segundos.

### Misión
Proporcionar una aplicación de escritorio nativa para Windows (`.exe`), rápida, estética y minimalista, que analice el perfil profesional del usuario, evalúe con precisión la viabilidad real frente a una oferta laboral mediante la IA de Google Gemini, y genere currículums altamente personalizados en formato ATS listos para descargar.

---

## 2. Principios de Diseño y Experiencia de Usuario (UX/UI)

1. **Simplicidad Radical (Zero Clutter):** La interfaz debe mostrar únicamente los elementos necesarios en cada momento. Sin menús ocultos, opciones confusas ni configuraciones complejas.
2. **Flujo Paso a Paso:**
   - **Paso 0 (Configuración Inicial):** Introducción de la API Key de Google (se valida al instante y se guarda cifrada/localmente).
   - **Paso 1 (Perfil Base):** Carga del CV en PDF/Word una sola vez; la IA estructura la información y la almacena en la base de datos local.
   - **Paso 2 (Análisis de Oferta):** El usuario ingresa la URL de la vacante (con opción de pegar texto si la página tiene bloqueo o captcha).
   - **Paso 3 (Diagnóstico y Match):** Diagnóstico visual inmediato del porcentaje de compatibilidad, puntos fuertes y brechas.
   - **Paso 4 (Generación Condicional):** Si el porcentaje es ≥ 90%, se activa el botón para generar y descargar el nuevo CV adaptado.
3. **Estética Premium y Sofisticada:**
   - Paleta sobria (modo oscuro elegante con toques de acento en tonos neutros o índigo tecnológico).
   - Tipografía moderna (Inter / Outfit / SF Pro display).
   - Microinteracciones y transiciones suaves durante el análisis (spinners o barras de progreso elegantes, sin pantallas congeladas).
4. **Respeto a la Privacidad (Local-First):** Todos los datos personales y la clave API residen exclusivamente en la base de datos local del usuario (`SQLite`). No existen servidores externos intermediarios.

---

## 3. Arquitectura y Stack Tecnológico

| Capa | Tecnología | Justificación |
| :--- | :--- | :--- |
| **Empaquetado y Ventana** | **Python + PyWebView** | Permite construir una interfaz web fluida y moderna compilada en un único archivo ejecutable `.exe` nativo de Windows mediante **PyInstaller**. |
| **Frontend** | **HTML5 + Vanilla CSS + JS** | Cero dependencias pesadas de frameworks, carga instantánea, animaciones ligeras y control total del diseño. |
| **Base de Datos Local** | **SQLite3** | Cero configuración, liviano, transaccional y embebido directamente en el ejecutable. |
| **Motor de IA** | **Google Gemini API** (`google-genai` / REST) | Utiliza modelos Gemini Flash (rápido, económico, alta precisión de análisis y salida estructurada en JSON). |
| **Procesamiento de Documentos** | **pypdf / pdfplumber** | Lectura y extracción limpia de texto estructurado de los currículums de entrada. |
| **Generación de CV (PDF)** | **ReportLab** | Generación programática de PDFs con formato profesional, limpio, tipografía escalable y 100% compatible con lectores ATS. |
| **Extracción Web (Scraping)** | **Trafilatura / BeautifulSoup4** | Extracción del texto principal de la vacante con fallback automático a pegado manual si la web requiere login o captcha. |

---

## 4. Reglas de Negocio y Pautas Operativas

### 4.1 Nomenclatura del Archivo Generado
El currículum optimizado generado para descarga **debe** seguir estrictamente la convención de nombres:
```text
[Nombre_Apellido]_[Puesto_Deseado].pdf
```
*Ejemplo:* `Uriel_Lopez_Senior_Frontend_Developer.pdf`

### 4.2 Criterio de Activación de Optimización
- **Match < 90%:** La aplicación muestra el porcentaje, resalta los requisitos faltantes o áreas de oportunidad, pero mantiene deshabilitado el botón de creación de CV adaptado, explicando claramente al usuario qué habilidades le faltan para calificar.
- **Match ≥ 90%:** Se desbloquea con una animación suave el botón destacado **"Generar CV Adaptado"**.

### 4.3 Manejo de Errores y URLs Protegidas
- Cuando el usuario pegue un enlace de sitios con barreras antibot o muros de login (LinkedIn, Indeed, portales privados), el sistema no debe fallar; mostrará un diálogo intuitivo: *"El portal requiere autenticación. Pega la descripción de la vacante aquí"*.

### 4.4 Adaptación Ética y ATS
- La IA adaptará el perfil reorganizando el orden de las habilidades, resaltando logros afines y utilizando palabras clave de la oferta, **sin inventar** experiencia laboral inexistente o títulos académicos falsos.

---

## 5. Fases de Desarrollo

* **Fase 1:** Configuración del entorno, base de datos SQLite y puente PyWebView-Python.
* **Fase 2:** Integración con la API de Google Gemini (validación de key y prompts estructurados de extracción).
* **Fase 3:** Motor de lectura de CV original y persistencia del perfil profesional.
* **Fase 4:** Módulo de análisis de vacantes (Web Scraper + comparador ATS con cálculo porcentual).
* **Fase 5:** Motor generador de PDF profesional ATS con ReportLab y nomenclatura automática.
* **Fase 6:** Pulido estético de la interfaz de usuario (UI/UX), pruebas de flujo completo y empaquetado final a `.exe` con PyInstaller.
