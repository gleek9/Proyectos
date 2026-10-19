# ⚽ Katakuri v3.5 — Plataforma Autónoma de Predicción Deportiva con IA

[![Python Version](https://img.shields.io/badge/Python-3.10%2B-blue?logo=python&logoColor=white)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115%2B-009688?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![React](https://img.shields.io/badge/React-19.2-61DAFB?logo=react&logoColor=black)](https://react.dev/)
[![Vite](https://img.shields.io/badge/Vite-8.3-646CFF?logo=vite&logoColor=white)](https://vitejs.dev/)
[![PyTorch](https://img.shields.io/badge/PyTorch-2.2%2B-EE4C2C?logo=pytorch&logoColor=white)](https://pytorch.org/)
[![XGBoost](https://img.shields.io/badge/XGBoost-2.1%2B-EB5424)](https://xgboost.readthedocs.io/)
[![Google Gemini](https://img.shields.io/badge/Google%20Gemini-3.5%20Flash%20Lite-8E75B2?logo=google&logoColor=white)](https://aistudio.google.com/)
[![License](https://img.shields.io/badge/License-Proprietary-red)](#licencia)

> **Katakuri v3.5** es una plataforma integral de analítica predictiva de fútbol que combina extracción web autónoma en tiempo real (mediante LLMs y feeds deportivos), un **meta-ensamble matemático cuantitativo 100% local** (Poisson Dixon-Coles, XGBoost y PyTorch LSTM) y una interfaz moderna estilo Dark IDE minimalista.

---

## 📑 Tabla de Contenidos

- [¿Qué hace la aplicación?](#-qué-hace-la-aplicación)
- [Arquitectura del Motor Predictivo](#-arquitectura-del-motor-predictivo)
- [Características Principales](#-características-principales)
- [Tecnologías Utilizadas](#-tecnologías-utilizadas)
- [Estructura del Proyecto](#-estructura-del-proyecto)
- [Requisitos Previos](#-requisitos-previos)
- [Instalación y Configuración](#-instalación-y-configuración)
- [Ejecución de la Plataforma](#-ejecución-de-la-plataforma)
- [Endpoints de la API](#-endpoints-de-la-api)
- [Suite de Pruebas y Backtesting](#-suite-de-pruebas-y-backtesting)

---

## 🎯 ¿Qué hace la aplicación?

A partir de **dos equipos** o una **URL directa de partido** (de plataformas como Sofascore, Flashscore, etc.), Katakuri realiza de manera autónoma y en segundos:

1. **Recolección en Vivo y Pre-Match**:
   - Extrae métricas históricas, últimos 10 partidos, goles esperados ($xG$), rachas, ausencias clave, tarjetas y córners.
   - En modo en vivo, captura en tiempo real el marcador, minuto de juego, tiros de esquina, posesión, tiros a puerta y expulsiones.
2. **Feature Engineering Avanzado**:
   - Normaliza métricas por torneo y liga.
   - Modela localía simétrica ($\sqrt{h}$), fatiga por días de descanso e impacto posicional de bajas.
3. **Inferencia Multi-Modelo Local**:
   - Ejecuta en paralelo modelos estadísticos bayesianos y de Machine Learning entrenados localmente (sin llamadas externas lentas para el cálculo numérico).
4. **Veredicto y Mercados Derivados**:
   - Traduce matrices probabilísticas a lenguaje 100% humano y gráficos interactivos:
     - **1X2 (Local / Empate / Visitante)** garantizando que sumen exactamente $100.0\%$.
     - **Doble Oportunidad (1X, X2, 12)** y **Empate No Válido (Draw No Bet / DNB)**.
     - **Líneas de Goles**: Over/Under 1.5, 2.5, 3.5 y marcador exacto más probable concordante.
     - **Córners**: Over/Under 8.5, 9.5, 10.5 y total proyectado.
     - **Tarjetas y Disciplina**: Total estimado y riesgo de tarjeta roja.
     - **Factores Clave y Telemetría**: Análisis narrativo contextual explicando el porqué de la predicción.

---

## 🧠 Arquitectura del Motor Predictivo

```
                  [ URL de Partido / Nombres de Equipos ]
                                     │
                                     ▼
        [ Agente Autónomo de Búsqueda (Gemini 3.5 Flash Lite + Feeds) ]
                                     │
                                     ▼
                   [ Feature Engineering Pipeline ]
            ├─ Series temporales (Racha de los últimos 10 partidos)
            ├─ Métricas territoriales (xG, posesión, tiros a puerta)
            └─ Factores contextuales (Localía, descanso, ausencias)
                                     │
         ┌───────────────────────────┼───────────────────────────┐
         ▼                           ▼                           ▼
  ┌──────────────┐            ┌──────────────┐            ┌──────────────┐
  │   Poisson    │            │   XGBoost    │            │ PyTorch LSTM │
  │ Dixon-Coles  │            │  (Tabular)   │            │ (Recurrente) │
  └──────┬───────┘            └──────┬───────┘            └──────┬───────┘
         │                           │                           │
         └───────────────────────────┼───────────────────────────┘
                                     │
                                     ▼
            [ Meta-Ensamble con Matriz Bivariada de Consenso ]
             ├─ Coalescencia estricta y calibración isotónica
             ├─ Modelado Binomial Negativo (Córners / Tarjetas)
             └─ Dinámica Game State & Ventaja Numérica In-Play
                                     │
                                     ▼
                  [ Frontend Dark IDE — React 19 + Vite ]
```

### Componentes Clave:
- **Poisson Bivariado con Dixon-Coles ($\tau$)**: Modela correlaciones de baja puntuación ($0-0, 1-0, 0-1, 1-1$) y aplica elasticidad amortiguada ($\gamma=0.52$).
- **Sobredispersión Binomial Negativa**: Corrige la varianza en córners y tarjetas evitando subestimar colas pesadas.
- **XGBoost / LightGBM**: Procesa 18 variables numéricas con calibración sigmoide para predecir probabilidades 1X2 y Over/Under.
- **PyTorch LSTM**: Red recurrente para capturar la inercia temporal y el momentum relativo de los equipos.
- **Efecto Game State (In-Play)**: Adapta las tasas de gol esperado por minuto según si el equipo va perdiendo, empatando o con inferioridad numérica por expulsión.

---

## ✨ Características Principales

- **Ingestión Jerárquica de URLs (v3.5)**: Introduce cualquier URL de Sofascore o Flashscore; el sistema extrae automáticamente la información y prioriza la URL sobre cualquier dato previo del formulario.
- **Acceso Directo Sin Fricción**: Interfaz lista para usar al instante, sin bloqueos de inicio de sesión obligatorios.
- **Diseño Dark IDE Minimalista**: Diseñado para alta legibilidad, con paleta oscura elegante, micro-animaciones, gráficos con Chart.js y tipografía de código moderno.
- **Resiliencia Operativa**: Servidor backend desacoplado con auto-recuperación de subprocesos y prevención de reinicios intempestivos.
- **Framework de Backtesting Integrado**: Suite matemática para validar la calibración de los modelos con métricas científicas: Ranked Probability Score (RPS), Brier Score, Log-Loss y MAE.

---

## 🛠 Tecnologías Utilizadas

### Backend
- **Python 3.10+**
- **FastAPI**: API REST asíncrona de alto rendimiento.
- **Uvicorn**: Servidor ASGI de producción.
- **LangChain & Google Gemini 3.5 Flash Lite**: Agente extractor inteligente de telemetría y datos web.
- **PyTorch**: Inferencia de red neuronal recurrente LSTM.
- **XGBoost & LightGBM**: Modelos tabulares basados en Gradient Boosting.
- **SciPy & NumPy**: Optimización matemática, distribuciones Poisson y Binomial Negativa.
- **SQLite & SQLAlchemy**: Almacenamiento local persistente y caché inteligente.

### Frontend
- **React 19**: Biblioteca reactiva para la interfaz de usuario.
- **Vite 8**: Herramienta de compilación ultrarrápida (HMR instantáneo).
- **Chart.js & react-chartjs-2**: Gráficos interactivos de distribución de probabilidades.
- **Lucide React**: Iconografía moderna y minimalista.
- **CSS3 Puro**: Sistema de diseño IDE Dark con variables CSS y diseño responsive.

---

## 📁 Estructura del Proyecto

```text
analista-deportivo/
├── .env.example              # Plantilla de variables de entorno
├── .gitignore                # Reglas de exclusión de Git (seguridad y temporales)
├── Agents.md                 # Especificación de roles y agentes de IA
├── PROJECT_STATUS.md         # Bitácora detallada de hitos y estado del proyecto
├── README.md                 # Este documento
├── run_app.py                # Script unificado de arranque supervisado
├── iniciar_app.bat           # Lanzador rápido para Windows (CMD/Batch)
├── iniciar_app.ps1           # Lanzador rápido para Windows (PowerShell)
├── detener_app.bat           # Detención limpia de servicios en Windows
│
├── backend/
│   ├── requirements.txt      # Dependencias de Python
│   ├── app/
│   │   ├── main.py           # Entrada FastAPI, rutas y middlewares
│   │   ├── agent/            # Módulo de extracción web autónoma
│   │   │   ├── collector.py  # Orquestador LangChain / Gemini / Feeds
│   │   │   └── search_tools.py
│   │   ├── engine/           # Motores predictivos cuantitativos
│   │   │   ├── poisson_model.py
│   │   │   ├── xgboost_model.py
│   │   │   ├── lstm_model.py
│   │   │   └── ensemble.py   # Meta-ensamble de consenso unificado
│   │   ├── database/         # Modelos SQLAlchemy y conexión SQLite
│   │   └── schemas/          # Modelos Pydantic de entrada y salida
│   └── tests/                # Suite de pruebas unitarias y backtesting
│
└── frontend/
    ├── package.json          # Dependencias y scripts de Node
    ├── vite.config.js        # Configuración de Vite y proxy local
    ├── index.html            # Entrypoint HTML
    └── src/
        ├── App.jsx           # Componente raíz y gestión de estado
        ├── components/       # Componentes modulares de interfaz
        │   ├── HeaderBar.jsx
        │   ├── LiveNeuralSection.jsx
        │   ├── MatchResultCard.jsx
        │   ├── KeyFactorsPanel.jsx
        │   └── MarketsGrid.jsx
        └── styles/
            └── ide-theme.css # Sistema de diseño Dark IDE
```

---

## 📦 Requisitos Previos

1. **Python 3.10 o superior**: [Descargar Python](https://www.python.org/downloads/)
2. **Node.js 18 o superior** y **npm**: [Descargar Node.js](https://nodejs.org/)
3. **Clave de API de Google Gemini**: Gratis en [Google AI Studio](https://aistudio.google.com/)

---

## 🚀 Instalación y Configuración

### 1. Clonar el Repositorio
```bash
git clone https://github.com/tu-usuario/katakuri.git
cd katakuri
```

### 2. Configurar Variables de Entorno
Copia la plantilla `.env.example` a `.env`:
```bash
cp .env.example .env
```
Edita `.env` e introduce tu clave de Google Gemini:
```env
GEMINI_API_KEY=tu_clave_de_gemini_aqui
```

### 3. Configurar el Backend (Python)
Crea y activa un entorno virtual:
```bash
# Windows
python -m venv .venv
.venv\Scripts\activate

# Linux / macOS
python3 -m venv .venv
source .venv/bin/activate
```
Instala las dependencias:
```bash
pip install -r backend/requirements.txt
```

### 4. Configurar el Frontend (React)
```bash
cd frontend
npm install
cd ..
```

---

## ⚡ Ejecución de la Plataforma

### Opción 1: Arranque Automático en 1 Clic (Recomendado)
Ejecuta el supervisor unificado que inicia Backend y Frontend coordinadamente:
```bash
python run_app.py
```
*O en Windows, haz doble clic en `iniciar_app.bat`.*

- **Frontend**: [http://localhost:5173](http://localhost:5173)
- **Backend API**: [http://127.0.0.1:8000](http://127.0.0.1:8000)
- **Documentación Interactiva Swagger**: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)

### Opción 2: Arranque Manual por Separado
- **Terminal 1 (Backend)**:
  ```bash
  .venv\Scripts\activate
  uvicorn backend.app.main:app --host 127.0.0.1 --port 8000
  ```
- **Terminal 2 (Frontend)**:
  ```bash
  cd frontend
  npm run dev
  ```

---

## 🔌 Endpoints de la API

| Método | Endpoint | Descripción |
|---|---|---|
| `POST` | `/api/predict` | Ejecuta la predicción integral pre-match o in-play para dos equipos o URL. |
| `GET` | `/api/health` | Estado del sistema, modelos cargados y conexión de base de datos. |
| `GET` | `/api/predictions/recent` | Consulta el historial de análisis almacenados localmente. |
| `GET` | `/api/backtest/benchmark` | Ejecuta el benchmark cuantitativo sobre el dataset histórico curado. |
| `POST` | `/api/backtest/run` | Ejecuta una sesión de backtesting sobre un lote personalizado. |
| `POST` | `/api/login` | Endpoint de autenticación JWT (opcional en v3.4+). |

---

## 🧪 Suite de Pruebas y Backtesting

Para verificar la integridad matemática y la calibración de los modelos, ejecuta:

```bash
# Validación del Consenso Bivariado, Sobredispersión y Game State
python backend/tests/test_v33_consensus_nbinom_gamestate.py

# Benchmark de Métricas de Calibración (RPS, Brier, Log-Loss)
python backend/tests/test_v33_backtest_framework.py

# Auditoría de Normalización por Torneo y Localía Simétrica
python backend/tests/test_v32_audit_fixes_points_1_and_2.py

# Verificación de Amortiguación de Goles y Córners
python backend/tests/test_v31_calibration_corners_and_goals.py
```

---

## 📄 Licencia

Este proyecto está bajo una licencia de uso personal y desarrollo privado. Todos los derechos reservados.
