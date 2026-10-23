# AGENTS.md — Optimizador de CV

## 1. Visión y Misión

### Visión
Convertirse en la herramienta de escritorio de referencia, accesible, privada y sin fricción, para optimizar la postulación laboral, permitiendo que cualquier profesional adapte su currículum de manera inteligente y competitiva a ofertas de trabajo en segundos.

### Misión
Proporcionar una aplicación de escritorio nativa para Windows (`.exe`), rápida, estética y minimalista, que analice el perfil profesional del usuario, evalúe con precisión la viabilidad real frente a una oferta laboral mediante la IA de Google Gemini, y genere currículums altamente personalizados en formato ATS listos para descargar.

---

## 2. Principios de Diseño, UX/UI y Psicología de Confianza

El usuario está poniendo en manos del software una de las áreas más críticas de su vida: su carrera profesional. Por ello, la experiencia visual no debe parecer un juguete ni un experimento con "efectos mágicos de IA", sino un **instrumento de auditoría profesional de alta precisión, sobrio, transparente y seguro**.

### 2.1 Filosofía Estética: Minimalismo Suizo en Tonos Claros (Swiss White Minimalism)
- **Claridad Quirúrgica y Blancura Intencional:** Fondo amplio y limpio que transmita orden, rigor y serenidad. Se evitan las saturaciones visuales y los modos oscuros densos; predomina una estética de documento ejecutivo y papelería corporativa premium.
- **Zero AI Gimmicks:** Cero gradientes púrpuras/neón clichés, cero partículas brillantes o iconografía de "magia". El análisis se comunica como un cálculo analítico objetivo y determinista.
- **Estructura Visible como Información:** Líneas sutiles de separación, tarjetas bien delimitadas y espaciados generosos (`gap: 1.5rem` - `2rem`) que permiten al usuario escanear la información en menos de 5 segundos.

### 2.2 Sistema de Diseño y Tokens de Color (High-Trust Palette)
Inspirado en los perfiles de confianza y autoridad (*Swiss Minimal / Executive Authority* de `ui-ux-pro-max`):

| Token | Valor Hex | Propósito Psicológico |
| :--- | :---: | :--- |
| **Canvas de Fondo** | `#F8FAFC` (Slate-50) | Lienzo base neutro y limpio; descansa la vista frente al blanco absoluto. |
| **Superficie de Tarjetas** | `#FFFFFF` (Pure White) | Superficies de trabajo y foco, con sensación de documento físico pulcro. |
| **Bordes y Divisores** | `#E2E8F0` (Slate-200) | Delimitaciones milimétricas (1px solid), sin sombras pesadas. |
| **Texto Principal (Tinta)** | `#0F172A` (Slate-900) | Máximo contraste legible (WCAG AAA), tono tinta obsidiana para títulos. |
| **Texto de Lectura** | `#334155` (Slate-700) | Contraste óptimo y descanso para párrafos y descripciones. |
| **Texto Secundario** | `#64748B` (Slate-500) | Metadatos, etiquetas y contexto auxiliar. |
| **Azul Autoridad (Primary)** | `#1E3A8A` / `#2563EB` | Acento principal en botones interactivos; evoca rigor institucional y seguridad. |
| **Verde Calificación (Success)** | `#059669` (Emerald-600) | Reservado exclusivamente para el porcentaje ≥ 90% y confirmaciones de éxito. |
| **Ámbar Constructivo (Warning)** | `#D97706` (Amber-600) | Destaca brechas o requisitos faltantes de forma pedagógica, nunca alarmista. |

### 2.3 Pilares de Seguridad y Confianza del Usuario ("Career-Safe UX")
1. **Transparencia Local Visible (Zero-Leakage Assurance):**
   - La interfaz muestra de forma discreta pero permanente en el pie o encabezado un sello de privacidad: *"Tus datos y tu clave API se guardan exclusivamente en tu computadora (SQLite local). Nada pasa por servidores intermediarios"*.
   - Estado de la API Key validado con indicador verde sereno y opción inmediata de revocar o editar la clave.
2. **Diagnóstico Auditado y Justificado:**
   - El porcentaje de viabilidad nunca es una "caja negra". Debe desglosarse visualmente en tres columnas claras:
     - *Requisitos cubiertos con tu experiencia.*
     - *Habilidades transferibles o afines.*
     - *Brechas detectadas que motivan la puntuación.*
3. **Tono Constructivo (Feedback de Mentor Ejecutivo):**
   - Si el match es < 90%, el sistema no muestra un "error" en rojo que desanime al usuario. Muestra un diagnóstico formativo: *"Para postular con alta probabilidad a esta vacante, se requiere reforzar [Habilidad X]. Tu perfil tiene excelente alineación en [Habilidad Y]"*.
4. **Retroalimentación de Estado Determinista:**
   - Durante las llamadas a Gemini, no se utilizan spinners infinitos genéricos. Se muestra un indicador de pasos progresivos con transiciones suaves:
     1. *Extrayendo requisitos clave de la vacante...*
     2. *Cruzando perfil con estándares de sistemas ATS...*
     3. *Calculando porcentaje de viabilidad...*

### 2.4 Tipografía
- **Familia:** `Inter` o `Plus Jakarta Sans` (Sans-serif geométrica de alta legibilidad en pantallas desktop).
- **Escala y Jerarquía:**
  - Títulos principales: Semibold (600), tamaño 22–26px, `letter-spacing: -0.02em`.
  - Subtítulos y secciones: Medium (500), tamaño 15–16px.
  - Cuerpo de texto: Regular (400), tamaño 14px, `line-height: 1.55`.
  - Etiquetas y micro-copys: Regular o Medium (500), tamaño 12px, sin uso indiscriminado de mayúsculas sostenidas.

### 2.5 Microinteracciones y Respuesta Física
- **Transiciones:** Rápidas y naturales: `150ms` a `200ms` con curva `cubic-bezier(0.16, 1, 0.3, 1)`.
- **Botón de Acción Principal (≥ 90%):** En reposo permanece inactivo con mensaje claro (*"Requiere ≥ 90% de afinidad"*). Al alcanzar o superar el 90%, se activa con una transición sutil de color y elevación hacia el Azul Autoridad (`#1E3A8A`), invitando al usuario a descargar con total certeza su nuevo documento.


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
