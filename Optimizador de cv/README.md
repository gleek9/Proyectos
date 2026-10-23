# Cuva — Optimizador de CV & Auditor ATS con Inteligencia Artificial

<p align="center">
  <img src="assets/icon.png" alt="Cuva Logo" width="120" height="120" style="border-radius: 20px;"/>
</p>

<p align="center">
  <strong>Herramienta de escritorio nativa para Windows diseñada para adaptar currículums a ofertas de trabajo en segundos, auditar viabilidad laboral con precisión quirúrgica y generar PDFs listos para sistemas ATS.</strong>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Platform-Windows%20x64-0078D4?style=for-the-badge&logo=windows&logoColor=white" alt="Windows"/>
  <img src="https://img.shields.io/badge/AI%20Engine-Google%20Gemini%203.0%2B%20Flash-00F0FF?style=for-the-badge&logo=googlegemini&logoColor=white" alt="Gemini"/>
  <img src="https://img.shields.io/badge/Design-Cyber--Obsidian%202026-07080B?style=for-the-badge&logo=css3&logoColor=00F0FF" alt="Design 2026"/>
  <img src="https://img.shields.io/badge/Format-ATS%20Compliant%20PDF-00FF9D?style=for-the-badge&logo=adobeacrobatreader&logoColor=black" alt="ATS"/>
  <img src="https://img.shields.io/badge/Privacy-100%25%20SQLite%20Local-FFB800?style=for-the-badge&logo=sqlite&logoColor=white" alt="Local SQLite"/>
</p>

---

## 📑 Tabla de Contenidos

1. [¿Qué es Cuva?](#-qué-es-cuva)
2. [¿Cómo Funciona?](#-cómo-funciona)
3. [Características Principales](#-características-principales)
4. [Filosofía de Confianza y Privacidad (Career-Safe UX)](#-filosofía-de-confianza-y-privacidad-career-safe-ux)
5. [Estética Vanguardista: Cyber-Obsidian & Precision Neon 2026](#-estética-vanguardista-cyber-obsidian--precision-neon-2026)
6. [Arquitectura del Sistema](#-arquitectura-del-sistema)
7. [Requisitos e Instalación](#-requisitos-e-instalación)
8. [Uso Rápido](#-uso-rápido)
9. [Compilación del Ejecutable (.exe)](#-compilación-del-ejecutable-exe)
10. [Estructura del Proyecto](#-estructura-del-proyecto)
11. [Licencia y Ética](#-licencia-y-ética)

---

## 🎯 ¿Qué es Cuva?

**Cuva** es una aplicación de escritorio nativa para Windows (`.exe`), rápida, privada y libre de suscripciones mensuales, construida para resolver un problema crítico del mercado laboral actual: **más del 75% de los currículums son filtrados o descartados por sistemas ATS (Applicant Tracking Systems)** antes de que un reclutador humano llegue a leerlos, debido a discrepancias en palabras clave, redacción no alineada o formatos ilegibles.

Cuva analiza tu perfil profesional original, lo contrasta contra la oferta laboral real usando la inteligencia artificial de **Google Gemini 3.0+ Flash**, evalúa tu viabilidad porcentual de forma transparente y genera un currículum adaptado, ético y de alta conversión en formato **PDF estándar ATS**.

---

## ⚙️ ¿Cómo Funciona?

El flujo de trabajo en Cuva se divide en 3 pasos secuenciales y sin fricción:

```mermaid
graph TD
    A[📄 Ingesta de CV] -->|Drag & Drop PDF/DOCX| B[💾 Extracción y Almacenamiento Local]
    B --> C[🏢 Ingesta de Oferta Laboral]
    C -->|Opción 1: Pegado Directo| D[🧠 Motor de IA Gemini 3.0+ Flash]
    C -->|Opción 2: URL Pública| D
    D --> E[📊 Auditoría de Viabilidad ATS]
    E -->|Desglose en 3 Columnas| F{Match >= 75%?}
    F -->|No: < 75%| G[⚠️ Diagnóstico Educativo y Guía de Brechas]
    F -->|Sí: >= 75%| H[🚀 Desbloqueo de Botón Neón]
    H --> I[📥 Generador de PDF ATS con ReportLab]
    I --> J[✅ [Nombre_Apellido]_[Puesto].pdf]
```

1. **Paso 1: Perfil Profesional:** Arrastra tu CV actual en formato PDF o Word (`.docx`). Cuva extrae el texto, estructura tu experiencia y habilidades mediante IA, y lo almacena en tu base de datos local SQLite.
2. **Paso 2: Análisis de Vacante:** Pega la descripción de la vacante (desde LinkedIn, Indeed, portales corporativos o correos) con el botón de portapapeles en 1 clic, o ingresa un enlace web público.
3. **Paso 3: Diagnóstico y Descarga ATS:**
   - La IA audita la vacante en segundos frente a tu perfil.
   - Se muestra un porcentaje de viabilidad y un desglose transparente:
     - 🟢 **Requisitos Cubiertos:** Competencias clave que ya posees.
     - 🟡 **Habilidades Transferibles:** Experiencia adaptable al rol.
     - 🔴 **Brechas Detectadas:** Habilidades faltantes a reforzar.
   - Si alcanzas o superas el **75% de viabilidad**, se desbloquea el botón **"Generar CV Adaptado"** para descargar tu PDF optimizado.

---

## ⚡ Características Principales

* 🤖 **Exclusivo para Gemini 3.0+ Flash con Rotación de Cuota:** Utiliza la suite de última generación de Google Gemini (`gemini-3-flash-preview`, `gemini-3.8-flash`, etc.). Si un modelo agota su cuota de peticiones por minuto o diaria (error 429), Cuva salta automáticamente al siguiente modelo disponible de manera imperceptible.
* 📋 **Ingesta Dual de Vacantes:**
  * **Descripción Directa:** Editor de texto con pegado automático desde el portapapeles de Windows (`📋 Pegar Portapapeles`).
  * **Extractor Web Inteligente:** Descarga el cuerpo de la vacante mediante `Trafilatura` con fallback instantáneo a pegado manual ante portales con muros de login o captcha.
* 📍 **Residencia por Defecto como Requisito Cumplido:** La ubicación geográfica o país solicitados en la oferta se validan automáticamente como cumplidos, protegiendo al candidato de penalizaciones geográficas injustas.
* 🎯 **Umbral de Calificación del 75%:** Promueve candidaturas competitivas y realistas, evitando enviar postulaciones con baja probabilidad de éxito y enseñando qué habilidades aprender.
* 📄 **Motor de Generación PDF ATS Profesional (ReportLab):**
  * Estructura lineal y tipografía escalable legible por analizadores ATS (Workday, Taleo, Greenhouse, Lever).
  * Sin tablas complejas, iconos flotantes o gráficos que rompan el parser de RRHH.
  * Nomenclatura automática estandarizada: `[Nombre_Apellido]_[Puesto_Deseado].pdf`.
* 🖱️ **Soporte Drag & Drop:** Arrastra cualquier archivo PDF o DOCX directamente sobre la ventana para cargarlo al instante.

---

## 🔒 Filosofía de Confianza y Privacidad ("Career-Safe UX")

Tu trayectoria profesional es información sensible. Por ello, Cuva opera bajo el principio de **Zero-Leakage Assurance**:

1. **Base de Datos 100% Local:** Tu información se almacena exclusivamente en tu computadora en un archivo local `cuva.db` (SQLite3).
2. **Sin Servidores Intermedios:** Cuva no tiene servidores en la nube propios ni recolecta telemetría. La conexión es directa entre tu equipo y los endpoints oficiales de Google Gemini mediante tu propia API Key.
3. **Adaptación Ética:** La IA nunca inventa experiencia laboral falsa, cargos que no tuviste ni títulos académicos inexistentes. Su función es reorganizar la jerarquía de tus habilidades, destacar logros pertinentes y alinear la terminología con los requisitos exactos de la oferta.

---

## 💎 Estética Vanguardista: *Cyber-Obsidian & Precision Neon 2026*

Cuva implementa un lenguaje visual moderno y sofisticado:

* **Canvas Cósmico Obsidiana (`#07080B`):** Fondo ultraoscuro diseñado para descanso visual en pantallas OLED y máxima inmersión.
* **Dark Glassmorphism:** Tarjetas con fondo translúcido (`rgba(13, 17, 24, 0.75)`), desenfoque de fondo (`backdrop-filter: blur(16px)`) y bordes milimétricos luminosos.
* **Paleta Neón Calibrada:**
  * 🩵 *Electric Cyan (`#00F0FF`):* Marca Cuva, elementos activos, bordes en foco y badges interactivos.
  * 💚 *Cyber Mint (`#00FF9D`):* Porcentajes $\ge 75\%$, confirmaciones exitosas y requisitos cumplidos.
  * 💛 *Solar Flare Amber (`#FFB800`):* Habilidades transferibles y recomendaciones pedagógicas.
  * 🩷 *Laser Rose (`#FF385C`):* Brechas técnicas a reforzar.
* **Tipografías:** `Plus Jakarta Sans` para lectura ejecutiva y `JetBrains Mono` para porcentajes, métricas analíticas y badges.

---

## 🏗️ Arquitectura del Sistema

| Módulo | Componente Técnico | Descripción |
| :--- | :--- | :--- |
| **Ventana y Enlace Nativo** | `Python` + `PyWebView` | Interfaz web responsiva ejecutada en un runtime de escritorio nativo de Windows. |
| **Frontend** | `HTML5` + `Vanilla CSS` + `JS` | Cero dependencias pesadas, carga instantánea y microanimaciones ligeras de 60 FPS. |
| **Base de Datos** | `SQLite3` (`src/database.py`) | Almacenamiento transaccional de clave API, perfil original y vacantes analizadas. |
| **Cerebro de IA** | `google-genai` (`src/gemini_service.py`) | Extracción estructurada (JSON), comparación ATS y rotación inteligente de cuota Gemini Flash. |
| **Ingesta de Documentos** | `pypdf`, `pdfplumber`, `python-docx` (`src/cv_parser.py`) | Extracción limpia de texto estructurado de currículums. |
| **Scraping Web** | `trafilatura`, `BeautifulSoup4` (`src/web_scraper.py`) | Extracción limpia de ofertas laborales web con sanitización de texto. |
| **Generador de PDF** | `ReportLab` (`src/pdf_generator.py`) | Compilación de currículums ATS limpios, elegantes y escalables. |
| **Empaquetado** | `PyInstaller` (`main.spec`) | Compilación a un único archivo binario `.exe` autónomo sin consola. |

---

## 💻 Requisitos e Instalación

### Opción 1: Ejecutable para Windows (Recomendado para usuarios)
1. Descarga el ejecutable autónomo `Cuva.exe` desde la carpeta `dist/` o la sección de [Releases](https://github.com/):
   ```text
   dist/Cuva.exe
   ```
2. Ejecuta el archivo en cualquier sistema Windows de 64 bits. No requiere instalar Python ni librerías adicionales.

---

### Opción 2: Entorno de Desarrollo (Para desarrolladores)

#### Requisitos Previos:
* Python 3.10 o superior instalado en el sistema.
* Windows 10 u 11 (64-bit).
* Clave API gratuita de [Google AI Studio](https://aistudio.google.com/).

#### Pasos de Instalación:
1. Clonar el repositorio:
   ```bash
   git clone https://github.com/tu-usuario/cuva-optimizador-cv.git
   cd cuva-optimizador-cv
   ```

2. Crear y activar el entorno virtual:
   ```powershell
   python -m venv .venv
   .\.venv\Scripts\Activate.ps1
   ```

3. Instalar dependencias:
   ```powershell
   pip install -r requirements.txt
   ```

4. Iniciar la aplicación en modo desarrollo:
   ```powershell
   python main.py
   ```

---

## 🚀 Uso Rápido

1. **Configurar tu API Key:**
   - Abre Cuva y haz clic en el botón de **Configuración** (ícono de engranaje superior).
   - Pega tu clave de API de Google Gemini y presiona **Guardar**. Cuva validará la clave automáticamente y encenderá el indicador neón verde.
2. **Subir tu CV:**
   - En el Paso 1, arrastra tu CV (.pdf o .docx) a la zona señalada o haz clic para seleccionarlo.
3. **Analizar la Oferta:**
   - En el Paso 2, selecciona la pestaña **"Descripción Directa"**, copia la vacante en tu navegador y haz clic en **"📋 Pegar Portapapeles"**.
   - Presiona **"Analizar Compatibilidad"**.
4. **Auditoría y Generación:**
   - Examina el porcentaje de viabilidad y los requisitos cumplidos.
   - Si obtienes $\ge 75\%$, haz clic en **"Generar CV Adaptado"** y selecciona la carpeta de tu computadora donde deseas guardar el PDF generado.

---

## 📦 Compilación del Ejecutable (.exe)

Para generar el archivo ejecutable independiente empaquetado con todos sus recursos estáticos y dependencias:

```powershell
.\.venv\Scripts\pyinstaller --clean main.spec
```

El ejecutable resultante estará ubicado en:
```text
dist/Cuva.exe
```

---

## 📂 Estructura del Proyecto

```text
├── assets/                  # Recursos gráficos (icon.ico, icon.png)
├── dist/                    # Directorio de distribución con Cuva.exe
├── src/                     # Código fuente modular en Python
│   ├── api_bridge.py        # Puente JS-Python expuesto a PyWebView
│   ├── config.py            # Constantes, rutas y umbrales (75% match)
│   ├── cv_parser.py         # Extractor de texto de archivos PDF y DOCX
│   ├── database.py          # Gestor de base de datos SQLite local
│   ├── gemini_service.py    # Integración con Gemini 3.0+ Flash y rotación de cuota
│   ├── pdf_generator.py     # Generador de PDFs profesionales ATS con ReportLab
│   ├── web_scraper.py       # Extractor web de vacantes laborales
│   └── ui/                  # Frontend Web
│       ├── app.js           # Lógica interactiva de usuario y llamadas a la API
│       ├── index.html       # Estructura semántica con Google Fonts 2026
│       └── style.css        # Sistema de diseño Cyber-Obsidian & Precision Neon
├── AGENTS.md                # Reglas de gobierno, UX y arquitectura del sistema
├── PROJECT_STATUS.md        # Bitácora histórica de fases y versiones
├── README.md                # Documentación oficial del proyecto
├── main.py                  # Punto de entrada de la aplicación
├── main.spec                # Archivo de especificación de PyInstaller
└── requirements.txt         # Lista de dependencias del entorno
```

---

## 📜 Licencia y Ética Profesional

Este proyecto se distribuye bajo la licencia **MIT**.

> **Nota Ética:** Cuva está diseñada para ser una herramienta de empoderamiento laboral. No inventa credenciales falsas ni promueve la deshonestidad académica o profesional. Su propósito es ayudar a que el talento real sea valorado y no descartado por tecnicismos de formato en filtros automatizados de reclutamiento.
