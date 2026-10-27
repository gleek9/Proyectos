# AGENTS.md — Katakuri v4.0 (Analista Deportivo de Alta Precisión)

Spec técnica de referencia. El estado vivo del proyecto (fases, versiones, credenciales operativas) está en `PROJECT_STATUS.md` — leerlo primero en cada sesión nueva. Versión actual: **v4.0**, idioma de toda la UI/telemetría: **español**.

## Comandos (Windows, PowerShell)

- Arrancar todo: `python run_app.py` (o `iniciar_app.bat` / `iniciar_app.ps1`). Levanta uvicorn `--reload` y Vite, y abre el navegador tras healthcheck de `/api/health`.
- Detener: `detener_app.bat` o Ctrl+C en `run_app.py`.
- Backend manual: `.venv\Scripts\python -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000 --reload --reload-dir backend` (ejecutar desde la raíz; el paquete es `backend.app`, no `app`).
- Frontend: `cd frontend; npm run dev` (puerto 5173). Lint: `npm run lint` (**oxlint**, no ESLint). Build: `npm run build`.
- Tests: Ejecutar con unittest de Python: `.venv\Scripts\python -m unittest discover -s backend/tests` (75/75 pruebas pasando al 100%).

## Reglas operativas críticas (no romper)

- **Puerto 8000 fijo para el backend.** El proxy de Vite (`frontend/vite.config.js`) y `run_app.py` apuntan a `127.0.0.1:8000`; `.env` debe tener `PORT=8000`. Un puerto distinto produce HTTP 502.
- **Uvicorn siempre con `--reload-dir backend`.** Sin esto, los writes de SQLite (`analista.db` en la raíz) disparan reinicios del worker y cortan requests en curso.
- Frontend usa rutas relativas `/api/*` (proxy Vite, timeouts 180 s). Hay fallback directo a `http://127.0.0.1:8000` ante 502/503/504 en `App.jsx` y `LoginModal.jsx`. En Windows, `localhost` puede resolver a `::1` mientras uvicorn escucha en IPv4 — por eso se usa `127.0.0.1`.
- Config y secretos: `.env` en la raíz (ignorado por git). `backend/app/config.py` carga ese `.env` vía `ROOT_DIR`. Credenciales por defecto: usuario `Gleek` / `Contra123`, JWT HS256, tokens de 24 h.
- DB: SQLite vía SQLAlchemy (`backend/app/db.py`), archivo `analista.db` **en la raíz** poblado con **3,525 partidos oficiales reales** (`HistoricalMatch`) de `football-data.co.uk` y caché de 122 clubes con Elo dinámico (`TeamStatsCache`).

## Arquitectura real v4.0 (verificada contra el código)

- `backend/app/main.py`: endpoints `GET /api/health`, `POST /api/login`, `POST /api/predict`, `GET /api/predictions/recent`, `GET /api/backtest/benchmark`, `POST /api/backtest/run`, `GET /api/backtest/walk-forward`.
- `backend/app/services/`: `real_data_loader.py` (ingesta de 3,525 partidos oficiales y cálculo de Elo dinámico FIFA/Chess), `league_database.py` (resolución de partidos en <10ms y normalización de alias).
- `backend/app/agent/`: `scraper.py` (DuckDuckGo + Sofascore/Flashscore), `parser.py` (Gemini structured output), `collector.py`.
- `backend/app/models/`:
  - `poisson.py`: Dixon-Coles calibrado, modulación por Rating Elo Dinámico ($R_{elo} = 10^{\Delta Elo / 2400}$), splits ponderados Home/Away (55/45), decaimiento temporal ($\xi=0.12$), sobredispersión binomial negativa en córners/tarjetas y dinámica game state.
  - `tabular_ml.py`: XGBoost Supervisado con 23 features predictivas calibrado multi-clase (peso en `backend/weights/xgb_1x2.json`).
  - `lstm_net.py`: Red neuronal recurrente LSTM en PyTorch entrenada cronológicamente (peso en `backend/weights/lstm_momentum.pt`).
  - `ensemble.py`: Meta-ensamble bayesiano con matriz bivariada de consenso, coalescencia estricta y traductor a lenguaje humano.
- `backend/app/analytics/`: `backtest.py` (RPS, Brier Score, Log-Loss, MAE/RMSE, dataset benchmark y simulación temporal walk-forward con Value Betting vs Bet365).
- Frontend: React 19 + Vite 8 + Chart.js, tema oscuro IDE (`#090a0f`, `#11131a`, `#151821`), números en monospace. Componente `BacktestModal.jsx` con telemetría interactiva de Walk-Forward y Value Betting (ROI % y ganancia en unidades).

## Convenciones

- Al completar una tarea, actualizar `PROJECT_STATUS.md` (es el registro oficial; este archivo no se usa para tracking). Cada cambio de versión se refleja en `PROJECT_STATUS.md`.
- No añadir texto de marketing a la UI: se comporta como panel de telemetría de alta precisión.
