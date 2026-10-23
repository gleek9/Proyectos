# AGENTS.md — Optimizador de CV

## 1. Visión y Misión

### Visión
Convertirse en la herramienta de escritorio de referencia, accesible, privada y sin fricción, para optimizar la postulación laboral, permitiendo que cualquier profesional adapte su currículum de manera inteligente y competitiva a ofertas de trabajo en segundos.

### Misión
Proporcionar una aplicación de escritorio nativa para Windows (`.exe`), rápida, estética y minimalista, que analice el perfil profesional del usuario, evalúe con precisión la viabilidad real frente a una oferta laboral mediante la IA de Google Gemini, y genere currículums altamente personalizados en formato ATS listos para descargar.

---

## 2. Principios de Diseño, UX/UI y Psicología de Confianza

El usuario está poniendo en manos del software una de las áreas más críticas de su vida: su carrera profesional. Por ello, la experiencia visual no debe parecer un juguete ni un experimento con "efectos mágicos de IA", sino un **instrumento de auditoría profesional de alta precisión, sobrio, transparente y seguro**.

### 2.1 Filosofía Estética: Dark Minimalist Neon 2026 (Cyber-Obsidian & Precision Neon)
- **Profundidad Cósmica y Fondos OLED:** Lienzo base ultraoscuro (`#07080B`) con una sutil malla atmosférica de resplandor cian y menta en los bordes que reduce la fatiga visual y confiere un aura de software de vanguardia (2026).
- **Superficies de Cristal Ahumado (Dark Glassmorphism):** Tarjetas con fondo translúcido (`rgba(13, 17, 24, 0.75)`), desenfoque de fondo (`backdrop-filter: blur(16px)`), bordes milimétricos (`1px solid rgba(255, 255, 255, 0.08)`) y sutiles relieves luminosos.
- **Luminiscencia y Acentos Neón de Alta Precisión:** Uso calibrado y elegante de luz neón:
  - *Cian Eléctrico (`#00F0FF`):* Identidad de marca, elementos interactivos, pestañas activas y focos.
  - *Cyber Mint (`#00FF9D`):* Éxito, calificaciones $\ge 75\%$ y requisitos cubiertos.
  - *Solar Flare (`#FFB800`):* Habilidades transferibles y advertencias pedagógicas.
  - *Laser Rose (`#FF385C`):* Brechas críticas o habilidades faltantes a reforzar.
- **Estructura Visible y Escaneabilidad Rápida:** Separadores translúcidos y espaciados generosos (`gap: 1.5rem`) que permiten auditar los resultados en menos de 5 segundos.

### 2.2 Sistema de Diseño y Tokens de Color (Cyber-Obsidian & Neon Palette)
Inspirado en los perfiles `dark-mode-oled` y `cyberpunk-ui` de `ui-ux-pro-max` adaptados al rigor profesional:

| Token | Valor Hex / CSS | Propósito Psicológico |
| :--- | :---: | :--- |
| **Canvas Cósmico Base** | `#07080B` (Deep Obsidian) | Lienzo ultraoscuro inmersivo; contraste máximo sin fatiga visual. |
| **Superficie de Tarjetas** | `rgba(13, 17, 24, 0.75)` | Cristal ahumado con desenfoque de 16px para superficies de trabajo. |
| **Bordes Luminosos** | `rgba(255, 255, 255, 0.08)` | Delimitaciones milimétricas elegantes con sutil halo luminoso. |
| **Texto de Alta Jerarquía** | `#F0F6FC` / `#FFFFFF` | Blanco puro y platino brillante de máxima legibilidad (WCAG AAA). |
| **Texto de Lectura** | `#C9D1D9` (Silver Slate) | Contraste óptimo y descanso para párrafos y descripciones. |
| **Texto Secundario** | `#8B949E` (Muted Grey) | Metadatos, etiquetas y contexto auxiliar. |
| **Cian Eléctrico (Primary)** | `#00F0FF` | Acento principal en marca, inputs activos y bordes con halo neón. |
| **Cyber Mint (Success)** | `#00FF9D` | Reservado para el porcentaje ≥ 75%, requisitos cumplidos y confirmación. |
| **Solar Flare (Warning)** | `#FFB800` | Destaca habilidades transferibles y alertas constructivas. |
| **Laser Rose (Danger)** | `#FF385C` | Brechas técnicas faltantes a reforzar. |

### 2.3 Pilares de Seguridad y Confianza del Usuario ("Career-Safe UX")
1. **Transparencia Local Visible (Zero-Leakage Assurance):**
   - La interfaz muestra de forma discreta pero permanente en el encabezado un sello de privacidad: *"SQLite Local · Privacidad Total"*.
   - Estado de la API Key validado con indicador luminoso de pulso activo.
2. **Diagnóstico Auditado y Justificado:**
   - El porcentaje de viabilidad nunca es una "caja negra". Se desglosa en tres columnas con marcadores neón dedicados:
     - *Requisitos cubiertos (Cyber Mint).*
     - *Habilidades transferibles (Solar Flare).*
     - *Brechas detectadas (Laser Rose).*
3. **Tono Constructivo (Feedback de Mentor Ejecutivo):**
   - Si el match es < 75%, muestra un diagnóstico formativo: *"Para postular con alta probabilidad a esta vacante, se requiere reforzar [Habilidad X]. Tu perfil tiene excelente alineación en [Habilidad Y]"*.
4. **Retroalimentación de Estado Determinista:**
   - Durante las llamadas a Gemini, se muestra una barra con trazo neón animado y pasos secuenciales deterministas.

### 2.4 Tipografía
- **Familia:** `Plus Jakarta Sans` para titulares e interfaz, `JetBrains Mono` para porcentajes, métricas y etiquetas de sistema.
- **Escala y Jerarquía:**
  - Títulos principales: Semibold (700-800), tamaño 22–26px, `letter-spacing: -0.03em`.
  - Subtítulos y secciones: Medium (600), tamaño 15–16px.
  - Cuerpo de texto: Regular (400), tamaño 14px, `line-height: 1.6`.
  - Métricas numéricas: Monospace (800), tamaño 28–36px con resplandor neón.

### 2.5 Microinteracciones y Respuesta Física
- **Transiciones:** Rápidas y fluidas: `160ms` con curva `cubic-bezier(0.16, 1, 0.3, 1)`.
- **Botón de Acción Principal (≥ 75%):** En reposo (< 75%) permanece bloqueado con borde tenue. Al alcanzar o superar el 75%, se transforma en un degradado vibrante de Cyber Mint a Cian Eléctrico con un resplandor neón profundo (`box-shadow: 0 0 25px rgba(0, 255, 157, 0.45)`).



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
- **Match < 75%:** La aplicación muestra el porcentaje, resalta los requisitos faltantes o áreas de oportunidad, pero mantiene deshabilitado el botón de creación de CV adaptado, explicando claramente al usuario qué habilidades le faltan para calificar.
- **Match ≥ 75%:** Se desbloquea con una animación suave el botón destacado **"Generar CV Adaptado"**.

### 4.3 Manejo de Errores y URLs Protegidas
- Cuando el usuario pegue un enlace de sitios con barreras antibot o muros de login (LinkedIn, Indeed, portales privados), el sistema conmuta automáticamente a la pestaña de descripción directa: *"El portal requiere autenticación o captcha. Pega la descripción de la vacante directamente aquí"*.

### 4.4 Residencia por Defecto como Requisito Cumplido
- La residencia, ubicación geográfica, ciudad o país solicitados en la vacante se validan por defecto como **requisito cumplido** (`matched_skills`). Nunca se penaliza el porcentaje de afinidad ni se clasifica como brecha faltante (`missing_skills`).

### 4.5 Ingesta Dual de Vacantes (Descripción Directa y Enlace Web)
- La aplicación ofrece como vía principal la inserción directa de texto con soporte de pegado rápido del portapapeles, además del análisis por URL pública.

### 4.6 Adaptación Ética y ATS
- La IA adaptará el perfil reorganizando el orden de las habilidades, resaltando logros afines y utilizando palabras clave de la oferta, **sin inventar** experiencia laboral inexistente o títulos académicos falsos.

---

## 5. Fases de Desarrollo

* **Fase 1:** Configuración del entorno, base de datos SQLite y puente PyWebView-Python.
* **Fase 2:** Integración con la API de Google Gemini (validación de key y prompts estructurados de extracción).
* **Fase 3:** Motor de lectura de CV original y persistencia del perfil profesional.
* **Fase 4:** Módulo de análisis de vacantes (Web Scraper + comparador ATS con cálculo porcentual).
* **Fase 5:** Motor generador de PDF profesional ATS con ReportLab y nomenclatura automática.
* **Fase 6:** Pulido estético de la interfaz de usuario (UI/UX), pruebas de flujo completo y empaquetado final a `.exe` con PyInstaller.
