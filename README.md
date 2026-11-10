# AI-Driven Problem Solving — Vibe Coding Monorepo

[![Philosophy](https://img.shields.io/badge/Philosophy-Vibe%20Coding-8A2BE2?style=flat-square)]() [![Architecture](https://img.shields.io/badge/Architecture-AI--Native-00A67E?style=flat-square)]() [![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB?style=flat-square&logo=python&logoColor=white)](https://www.python.org/) [![React](https://img.shields.io/badge/React-19%2B-61DAFB?style=flat-square&logo=react&logoColor=black)](https://react.dev/) [![FastAPI](https://img.shields.io/badge/FastAPI-Latest-009688?style=flat-square&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/) [![Maintainer](https://img.shields.io/badge/Maintainer-gleek9-181717?style=flat-square&logo=github)](https://github.com/gleek9)

> **Repositorio central de ingeniería de software asistida por Inteligencia Artificial.** Cada directorio dentro de este monorepo representa una aplicación completa diseñada para **resolver una problemática real**, combinando dirección arquitectónica humana, *Vibe Coding* de alta velocidad y modelos de IA (LLMs, Machine Learning y agentes autónomos).

---

## Tabla de Contenidos

- [Visión y Metodología](#visión-y-metodología)
- [Flujo de Trabajo (Del Problema al Sistema)](#flujo-de-trabajo-del-problema-al-sistema)
- [Catálogo de Proyectos](#catálogo-de-proyectos)
- [Proyecto Destacado: Katakuri v4.1](#proyecto-destacado-katakuri-v41)
- [Ecosistema Tecnológico](#ecosistema-tecnológico)
- [Estructura del Monorepo](#estructura-del-monorepo)
- [Guía de Inicio Rápido](#guía-de-inicio-rápido)

---

## Visión y Metodología

El desarrollo de software tradicional suele verse frenado por la fricción sintáctica y la configuración repetitiva (*boilerplate*). Este repositorio aplica la filosofía del **Vibe Coding** con enfoque en **Ingeniería de Producto**: utilizar el lenguaje natural, agentes de código y modelos fundacionales para iterar a la velocidad del pensamiento, concentrando el esfuerzo humano en entender el problema, diseñar la arquitectura matemática/lógica y validar los resultados.

Cada proyecto alojado aquí cumple con tres pilares:

1. **Problemática Real**: No son simples ejemplos básicos; atacan problemas complejos de datos, automatización, predicción o experiencia de usuario.
2. **IA como Motor y como Herramienta**: Se utiliza IA tanto para construir el software (orquestación agéntica y desarrollo asistido) como dentro del núcleo de las aplicaciones (Agentes LangChain, PyTorch, XGBoost, inferencia multimodal con Gemini 3.0+).
3. **Documentación y Trazabilidad**: Cada proyecto incluye su propia arquitectura documentada, especificación de agentes (`Agents.md` / `AGENTS.md`) y bitácora de estado (`PROJECT_STATUS.md`).

---

## Flujo de Trabajo (Del Problema al Sistema)

1. **Identificación de Problemática Real**: Análisis del dominio, detección de cuellos de botella o asimetrías de información y definición de métricas de éxito.
2. **Diseño de Arquitectura y Orquestación**: Definición de reglas de negocio, formulación de modelos matemáticos, especificación de roles en `AGENTS.md` e iteración rápida mediante *Vibe Coding*.
3. **Desarrollo Full-Stack y Motor de IA**: Implementación de backend asíncrono o puente nativo de escritorio, motores de inferencia local o vía API y construcción de interfaces modernas de alta usabilidad.
4. **Auditoría, Pruebas y Despliegue**: Validación rigurosa mediante suites de pruebas unitarias, *backtesting* cuantitativo, empaquetado de ejecutables y publicación documentada dentro del monorepo.

---

## Catálogo de Proyectos

### 01. [Katakuri v4.1 (Analista Deportivo)](./Analista%20deportivo)

- **Estado**: Activo — **v4.1** (100% Operativo · 81/81 pruebas pasando)
- **Directorio**: [`./Analista deportivo`](./Analista%20deportivo)
- **Problemática que Resuelve**: Asimetría de información, sesgo humano y fuga temporal (*look-ahead bias*) en el análisis deportivo. Calibrado con **4,749 partidos oficiales reales** (`football-data.co.uk`) en **9 competiciones** y **ratings Elo dinámicos para 164 clubes**, ejecuta inferencia probabilística multi-modelo (1X2, Goles, Córners adaptativos en vivo, Tarjetas) y **Backtesting Walk-Forward Point-in-Time con Value Betting (Stake Plano + 1/4 Kelly vs Bet365)**.
- **Stack Principal**: `Python 3.10+` · `FastAPI` · `React 19.2` · `Vite 8.3` · `PyTorch LSTM` · `XGBoost (23 features)` · `SQLite` · `Gemini 3.5 Flash Lite`

### 02. [Citi Analyzer v1.0.0 (Analizador de Redes)](./Analizador%20de%20redes)

- **Estado**: Activo — **v1.0.0** (100% Operativo)
- **Directorio**: [`./Analizador de redes`](./Analizador%20de%20redes)
- **Problemática que Resuelve**: Fricción en la investigación competitiva de contenido corto en Instagram. Automatiza la radiografía de voz de marca del cliente, detecta el **Top 3 de Reels más virales** de su competencia mediante **Apify**, extrae y transcribe el audio real con **`yt-dlp` + Gemini 3.0 Multimodal** y genera **3 guiones completos adaptados** con escaleta segundo a segundo en un tablero Kanban con estética *Swiss Grid Anti-IA* (`#58FF9C`).
- **Stack Principal**: `Python 3.11+` · `FastAPI` · `React` · `TypeScript` · `Tailwind CSS` · `SQLite` · `Apify API` · `yt-dlp` · `Gemini 3.0 Flash`

### 03. [Cuva v1.4 (Optimizador de CV & Auditor ATS)](./Optimizador%20de%20cv)

- **Estado**: Activo — **v1.4** (100% Operativo · Ejecutable `dist/Cuva.exe` compilado)
- **Directorio**: [`./Optimizador de cv`](./Optimizador%20de%20cv)
- **Problemática que Resuelve**: Más del 75% de los currículums son descartados por filtros ATS antes de ser leídos por un humano. **Cuva** es una aplicación de escritorio nativa para Windows (`.exe`) 100% privada que ingesta tu CV (PDF/DOCX vía Drag & Drop), audita su compatibilidad frente a una vacante (descripción directa o URL) con umbral del **75%**, valida la residencia por defecto y genera un **PDF estándar ATS con ReportLab** bajo una interfaz *Cyber-Obsidian & Precision Neon 2026*.
- **Stack Principal**: `Python 3.10+` · `PyWebView` · `HTML5 / CSS3 / JS` · `SQLite3` · `ReportLab` · `Trafilatura` · `PyInstaller` · `Gemini 3.0+ Flash (Rotación de Cuota)`

---

## Proyecto Destacado: Katakuri v4.1

Ubicado en [`./Analista deportivo`](./Analista%20deportivo), **Katakuri v4.1** es una plataforma autónoma de predicción deportiva de alta precisión con interfaz estilo *Dark IDE / Aurora UI*.

### ¿Cómo resuelve el problema en v4.1?

A partir de los nombres de dos equipos (resolución instantánea `<10ms` en SQLite para 164 clubes de Premier League, LaLiga, Serie A, Bundesliga, Ligue 1, Eredivisie, Primeira Liga, Champions League y Liga MX) o una URL directa en vivo (Sofascore / Flashscore con vía rápida `<0.5s` y Auto-Sync *Wall-Clock* cada 5 min), procesa *Feature Engineering* avanzado y alimenta un **meta-ensamble matemático 100% local**:

- **Poisson Bivariado con Dixon-Coles ($\tau$), Elo Dinámico y Splits (55/45)**: Expectativas de gol moduladas por diferencial Elo ($R_{elo} = 10^{\Delta Elo / 2100}$), parámetro $\rho$ específico por liga y decaimiento temporal ($\xi=0.12$).
- **XGBoost Supervisado Point-in-Time (23 Features)**: Clasificador multi-clase entrenado sin fuga temporal sobre 4,749 partidos reales con calibración de temperatura ($T=1.08$).
- **PyTorch LSTM Secuencial**: Red neuronal recurrente (`MatchSequenceLSTM`) para capturar la inercia y *momentum* de los últimos encuentros.
- **Modulador Bayesiano de Paridad & Dinámica In-Play**: Detección táctica de empates competitivos, sobredispersión Binomial Negativa en tarjetas/córners y **líneas de córners totales adaptativas** al volumen real en directo.
- **Backtesting Walk-Forward Point-in-Time & Value Betting (Flat + 1/4 Kelly)**: Simulación *out-of-sample* día por día contra cuotas reales de Bet365 con filtro multi-competición interactivo (**Flat ROI = +45.42%**, **Kelly 1/4 ROI = +29.74%**).

**[Explorar el código y documentación completa de Katakuri v4.1](./Analista%20deportivo)**

---

## Ecosistema Tecnológico

### Inteligencia Artificial & Data Science

- **LLMs & Multimodalidad**: Google Gemini 3.0+ Flash / 3.5 Flash Lite (rotación automática de cuota, transcripción de audio y extracción estructurada), LangChain.
- **Machine Learning & Deep Learning**: PyTorch (LSTM), XGBoost (23 features), LightGBM, Scikit-Learn.
- **Modelado Matemático & Cuantitativo**: SciPy, NumPy (Distribuciones de Poisson Dixon-Coles, Binomial Negativa, Rating Elo FIFA/Chess, Criterio de Kelly Fraccional, Calibración de Temperatura).

### Desarrollo Full-Stack & Desktop

- **Backend & Core**: Python 3.10+, FastAPI, Uvicorn, SQLAlchemy, Pydantic, SQLite (modo WAL), ReportLab, `yt-dlp`, `apify-client`, `trafilatura`.
- **Frontend Web**: React 19, Vite 8, TypeScript, Tailwind CSS, Chart.js, Lucide Icons, CSS3 Moderno (*Dark IDE*, *Swiss Grid Anti-IA*, *Cyber-Obsidian Neon*).
- **Desktop Nativo Windows**: PyWebView + PyInstaller (empaquetado en binario autónomo `.exe`).

---

## Estructura del Monorepo

```text
Proyectos/
├── README.md                          # Portada general del portafolio y catálogo central
│
├── Analista deportivo/                # 01. Katakuri v4.1 — Predicción Deportiva con IA
│   ├── README.md                      # Documentación técnica de Katakuri v4.1
│   ├── Agents.md                      # Especificación de arquitectura y reglas operativas
│   ├── PROJECT_STATUS.md              # Bitácora detallada de versiones (hasta v4.1)
│   ├── run_app.py                     # Supervisor unificado para arranque automático en 1 clic
│   ├── analista.db                    # SQLite con 4,749 partidos reales y 164 clubes (9 ligas)
│   ├── backend/                       # FastAPI + Motores Poisson, XGBoost (23 vars), LSTM y Walk-Forward
│   └── frontend/                      # Interfaz Dark IDE en React 19 + Vite 8 + Chart.js
│
├── Analizador de redes/               # 02. Citi Analyzer v1.0.0 — Inteligencia de Reels & Guiones
│   ├── README.md                      # Documentación técnica de Citi Analyzer v1.0.0
│   ├── AGENTS.md                      # Especificación de diseño Swiss Grid Anti-IA y pipeline
│   ├── PROJECT_STATUS.md              # Control de fases y guía de despliegue
│   ├── start_local.bat                # Lanzador automático en 1 clic para Windows
│   ├── backend/                       # FastAPI + Apify + yt-dlp + Gemini 3.0 Multimodal
│   └── frontend/                      # Tablero Kanban y Modal 6xl en React + TS + Tailwind
│
└── Optimizador de cv/                 # 03. Cuva v1.4 — Optimizador de CV & Auditor ATS
    ├── README.md                      # Documentación oficial de Cuva v1.4
    ├── AGENTS.md                      # Reglas de negocio y diseño Cyber-Obsidian 2026
    ├── PROJECT_STATUS.md              # Historial de versiones y mejoras (v1.0 a v1.4)
    ├── main.py                        # Punto de entrada de escritorio con PyWebView
    ├── dist/Cuva.exe                  # Ejecutable nativo autónomo para Windows x64
    └── src/                           # Módulos de parseo, evaluación ATS, Gemini 3.0+ y PDF ReportLab
```

---

## Guía de Inicio Rápido

Dado que este repositorio funciona como un **monorepo**, cada proyecto es autónomo y posee sus propias dependencias, variables de entorno y lanzadores de ejecución:

1. **Clonar el repositorio completo**:
   ```bash
   git clone https://github.com/gleek9/Proyectos.git
   cd Proyectos
   ```
2. **Iniciar Katakuri v4.1 (`Analista deportivo`)**:
   ```bash
   cd "Analista deportivo"
   python run_app.py
   ```
3. **Iniciar Citi Analyzer v1.0.0 (`Analizador de redes`)**:
   ```bat
   cd "Analizador de redes"
   .\start_local.bat
   ```
4. **Iniciar Cuva v1.4 (`Optimizador de cv`)**:
   - Ejecutar directamente `Optimizador de cv\dist\Cuva.exe`, o en modo desarrollo:
   ```powershell
   cd "Optimizador de cv"
   python main.py
   ```

---

## Licencia y Autoría

Desarrollado y mantenido por **[gleek9](https://github.com/gleek9)**. Los proyectos contenidos en este repositorio están destinados a demostrar capacidades de arquitectura de software, ciencia de datos e integración de Inteligencia Artificial aplicada a problemas reales.
