# ⚽ Katakuri v4.0 — Plataforma Autónoma de Predicción Deportiva de Alta Precisión con IA

[![Python Version](https://img.shields.io/badge/Python-3.10%2B-blue?logo=python&logoColor=white)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115%2B-009688?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![React](https://img.shields.io/badge/React-19.2-61DAFB?logo=react&logoColor=black)](https://react.dev/)
[![Vite](https://img.shields.io/badge/Vite-8.3-646CFF?logo=vite&logoColor=white)](https://vitejs.dev/)
[![PyTorch](https://img.shields.io/badge/PyTorch-2.2%2B-EE4C2C?logo=pytorch&logoColor=white)](https://pytorch.org/)
[![XGBoost](https://img.shields.io/badge/XGBoost-2.1%2B-EB5424)](https://xgboost.readthedocs.io/)
[![Google Gemini](https://img.shields.io/badge/Google%20Gemini-3.5%20Flash%20Lite-8E75B2?logo=google&logoColor=white)](https://aistudio.google.com/)
[![License](https://img.shields.io/badge/License-Proprietary-red)](#licencia)

> **Katakuri v4.0** es una plataforma integral de analítica predictiva de alta precisión calibrada sobre **3,525 partidos oficiales reales** (football-data.co.uk) y ratings Elo dinámicos para 122 clubes. Integra un **meta-ensamble matemático cuantitativo 100% local** (Poisson Dixon-Coles modulado por Elo y Splits Home/Away, XGBoost Supervisado con 23 features predictivas y PyTorch LSTM secuencial) junto con un motor de **Backtesting Temporal Walk-Forward y Value Betting (+53.56% ROI vs Bet365)**.

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
- **Base de Datos Oficial Real (3,525 partidos / 122 equipos)**: Ingestión masiva de `football-data.co.uk` con marcadores oficiales, remates a puerta (*Shots on Target*), córners, tarjetas y cuotas reales de Bet365.
- **Rating Elo Dinámico Cronológico**: Algoritmo FIFA/Chess Elo ($K=24$, localía 65 pts) actualizado jornada a jornada para los 122 clubes.
- **Poisson Bivariado con Dixon-Coles ($\tau$), Elo y Splits**: Expectativas de gol moduladas por diferencia de Elo ($R_{elo} = 10^{\Delta Elo / 2400}$), splits home/away (55/45) y correlación $\rho$ adaptativa por torneo.
- **Sobredispersión Binomial Negativa**: Corrige la varianza en córners y tarjetas evitando subestimar colas pesadas.
- **XGBoost Supervisado (23 Features Predictivas)**: Clasificador multi-clase 1X2 entrenado cronológicamente con early stopping sobre datos empíricos reales.
- **PyTorch LSTM**: Red recurrente `MatchSequenceLSTM` entrenada para capturar la inercia temporal y el momentum relativo.
- **Backtesting Walk-Forward & Value Betting**: Validación out-of-sample (+53.56% ROI vs Bet365, RPS = 0.1888) integrado en API y UI.
- **Efecto Game State (In-Play)**: Adapta las tasas de gol esperado por minuto y aceleración de córners en desventaja.

---

## ✨ Características Principales

- **Alta Precisión Matemática (v4.0)**: Desempeño predictivo respaldado por 3,525 partidos reales con calibración RPS $\le 0.190$ (estándar Constantinou-Fenton).
- **Simulador de Apuestas de Valor (Value Betting)**: Identifica y cuantifica discrepancias analíticas entre las probabilidades del modelo y las cuotas de las casas de apuestas (Bet365).
- **Resolución Instantánea (<10ms)**: Búsqueda y feature engineering ultra-rápido en SQLite para los 122 equipos principales de Europa y América.
- **Ingestión Jerárquica de URLs en Vivo**: Soporta enlaces de Sofascore o Flashscore, extrayendo telemetría in-play y auto-sincronizando cada 5 minutos.
- **Diseño Dark IDE Minimalista**: Diseñado para alta legibilidad táctica, con paleta oscura elegante, micro-animaciones, gráficos interactivos con Chart.js y tipografía monoespaciada.
- **Lanzador Automatizado en 1 Clic**: Scripts de arranque con auto-recuperación de procesos para Windows (`iniciar_app.bat`, `iniciar_app.ps1`, `run_app.py`).

---

## 🛠 Tecnologías Utilizadas

### Backend
- **Python 3.10+**
- **FastAPI**: API REST asíncrona de alto rendimiento.
- **Uvicorn**: Servidor ASGI de producción con recarga en caliente supervisada.
- **LangChain & Google Gemini 3.5 Flash Lite**: Agente extractor inteligente de telemetría y datos web fallback.
- **PyTorch**: Red neuronal recurrente LSTM (`backend/weights/lstm_momentum.pt`).
- **XGBoost & LightGBM**: Modelo tabular supervisado de 23 features (`backend/weights/xgb_1x2.json`).
- **SciPy & NumPy**: Optimización matemática, distribuciones Poisson y Binomial Negativa.
- **SQLite & SQLAlchemy**: Almacenamiento local persistente (`analista.db`).

### Frontend
- **React 19**: Biblioteca reactiva para la interfaz de usuario.
- **Vite 8**: Herramienta de compilación ultrarrápida.
- **Chart.js & react-chartjs-2**: Gráficos interactivos de distribución de probabilidades.
- **Lucide React**: Iconografía moderna y minimalista.
- **CSS3 Puro**: Sistema de diseño Dark IDE con variables CSS y diseño responsive.

---

## 📁 Estructura del Proyecto

```text
analista-deportivo/
├── .env.example              # Plantilla de variables de entorno
├── .gitignore                # Reglas de exclusión de Git (seguridad y temporales)
├── Agents.md                 # Especificación técnica de referencia para agentes
├── PROJECT_STATUS.md         # Bitácora viva de arquitectura y avances
├── README.md                 # Este documento
├── run_app.py                # Script unificado de arranque supervisado Fullstack
├── iniciar_app.bat           # Lanzador rápido en 1 clic para Windows (CMD/Batch)
├── iniciar_app.ps1           # Lanzador rápido para Windows (PowerShell)
├── detener_app.bat           # Detención limpia de servicios en Windows
├── analista.db               # Base de datos SQLite (3,525 partidos oficiales y 122 clubes)
│
├── backend/
│   ├── requirements.txt      # Dependencias de Python
│   ├── data/                 # Datasets oficiales CSV de football-data.co.uk
│   ├── weights/              # Pesos entrenados de XGBoost (xgb_1x2.json) y LSTM (lstm_momentum.pt)
│   ├── app/
│   │   ├── main.py           # Entrada FastAPI, rutas REST y ciclo de vida
│   │   ├── config.py         # Configuración central y variables de entorno
│   │   ├── db.py             # Modelos relacionales SQLAlchemy (HistoricalMatch, TeamStatsCache)
│   │   ├── services/         # Servicios de datos oficiales
│   │   │   ├── real_data_loader.py # Ingestión de CSVs oficiales y cálculo de Elo dinámico
│   │   │   └── league_database.py  # Resolución de partidos en <10ms y normalización de alias
│   │   ├── agent/            # Extracción web autónoma fallback
│   │   │   ├── collector.py  # Orquestador LangChain / Gemini / Base de Datos
│   │   │   ├── parser.py     # Parser estructurado de respuestas
│   │   │   └── scraper.py    # Extracción en tiempo real vía httpx/BeautifulSoup
│   │   ├── analytics/        # Calibración, entrenamiento y evaluación
│   │   │   ├── backtest.py   # Motor de Walk-Forward, Value Betting, RPS y Brier
│   │   │   └── train_models.py # Pipeline de reentrenamiento supervisado sin data leakage
│   │   ├── models/           # Motores predictivos cuantitativos 100% locales
│   │   │   ├── poisson.py    # Dixon-Coles calibrado con Elo y Splits Home/Away
│   │   │   ├── tabular_ml.py # Inferencia tabular XGBoost (23 variables)
│   │   │   ├── lstm_net.py   # Red neuronal recurrente LSTM en PyTorch
│   │   │   └── ensemble.py   # Meta-ensamble bivariado de consenso y veredictos
│   │   └── schemas/          # Modelos de validación Pydantic tipados
│   │       ├── match.py      # Esquemas de entrada y telemetría en vivo
│   │       └── prediction.py # Esquemas de salida estructurada y mercados derivados
│   └── tests/                # 75 pruebas unitarias y suites de integración
│
└── frontend/
    ├── package.json          # Dependencias y scripts de Node
    ├── vite.config.js        # Configuración de Vite y proxy local hacia backend
    ├── index.html            # Entrypoint HTML
    └── src/
        ├── main.jsx          # Entrypoint de React
        ├── App.jsx           # Componente raíz y orquestación de estado
        ├── components/       # Componentes modulares de interfaz Dark IDE
        │   ├── HeaderBar.jsx         # Barra de estado y selector de backend
        │   ├── NeuralUrlCard.jsx     # Tarjeta de consulta manual y URL directa
        │   ├── LiveNeuralSection.jsx # Telemetría neuronal LSTM y líneas in-play
        │   ├── WinnerCard.jsx        # Veredicto de ganador, cuotas y mercados derivados
        │   ├── MetricCards.jsx       # Métricas de goles, córners y tarjetas
        │   ├── DistributionChart.jsx # Distribución visual de goles esperados
        │   ├── KeyFactorsPanel.jsx   # Factores futbolísticos determinantes
        │   ├── BacktestModal.jsx     # Modal interactivo de Walk-Forward y Value Betting
        │   └── LoginModal.jsx        # Acceso y autenticación del sistema
        └── styles/
            └── ide-theme.css         # Sistema de diseño integral Dark IDE
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
*O en Windows, haz doble clic en `iniciar_app.bat` (o ejecuta `.\iniciar_app.ps1` en PowerShell).*

- **Frontend UI**: [http://localhost:5173](http://localhost:5173)
- **Backend API**: [http://127.0.0.1:8000](http://127.0.0.1:8000)
- **Documentación Interactiva Swagger**: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)

Para detener ambos servidores limpiamente en Windows:
```bash
detener_app.bat
```

### Opción 2: Arranque Manual por Separado
- **Terminal 1 (Backend)**:
  ```bash
  .venv\Scripts\activate
  uvicorn backend.app.main:app --host 127.0.0.1 --port 8000 --reload --reload-dir backend
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
| `POST` | `/api/predict` | Ejecuta la predicción integral pre-match o in-play con ensamble Katakuri v4.0. |
| `GET` | `/api/health` | Estado del sistema, modelos cargados y conexión a base de datos. |
| `GET` | `/api/predictions/recent` | Consulta el historial de análisis almacenados localmente. |
| `GET` | `/api/backtest/walk-forward` | **(Nuevo en v4.0)** Simulación out-of-sample cronológica y telemetría de Value Betting. |
| `GET` | `/api/backtest/benchmark` | Ejecuta el benchmark cuantitativo sobre el dataset histórico curado. |
| `POST` | `/api/backtest/run` | Ejecuta una sesión de backtesting sobre un lote personalizado. |
| `POST` | `/api/login` | Endpoint de autenticación JWT (opcional). |

---

## 🧪 Suite de Pruebas y Backtesting

Para verificar la integridad de la base de datos real, los ratings Elo dinámicos, los modelos ML y la calibración probabilística, ejecuta:

```bash
# Ejecución de la suite completa de 75 pruebas (100% éxito garantizado):
.venv\Scripts\python -m unittest discover -s backend/tests

# O ejecutar la suite específica de validación v4.0 (Datos Reales, Elo y Walk-Forward):
.venv\Scripts\python -m unittest backend/tests/test_v40_real_data_and_walkforward.py

# Benchmark de métricas de calibración (RPS, Brier, Log-Loss, MAE):
.venv\Scripts\python -m unittest backend/tests/test_v33_backtest_framework.py
```

---

## 📄 Licencia

Este proyecto está bajo una licencia de uso personal y desarrollo privado. Todos los derechos reservados.
