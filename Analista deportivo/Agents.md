# AGENTS.md — Katakuri AI (Analista Deportivo)

Spec técnica de referencia. El estado vivo del proyecto (fases, versiones, credenciales operativas) está en `PROJECT_STATUS.md` — leerlo primero en cada sesión nueva. Versión actual: **v3.0**, idioma de toda la UI/telemetría: **español**.

## Comandos (Windows, PowerShell)

- Arrancar todo: `python run_app.py` (o `iniciar_app.bat`). Levanta uvicorn `--reload` y Vite, y abre el navegador tras healthcheck de `/api/health`.
- Detener: `detener_app.bat` o Ctrl+C en `run_app.py`.
- Backend manual: `.venv\Scripts\python -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000 --reload --reload-dir backend` (ejecutar desde la raíz; el paquete es `backend.app`, no `app`).
- Frontend: `cd frontend; npm run dev` (puerto 5173). Lint: `npm run lint` (**oxlint**, no ESLint). Build: `npm run build`.
- Tests: **no hay pytest instalado** — son scripts/unittest ejecutados directamente: `.venv\Scripts\python backend\tests\test_fase3_engine.py`. `test_gemini.py` y `test_parser.py` llaman a la API real de Gemini y requieren `GEMINI_API_KEY` y red; los demás usan mocks locales.

## Reglas operativas críticas (no romper)

- **Puerto 8000 fijo para el backend.** El proxy de Vite (`frontend/vite.config.js`) y `run_app.py` apuntan a `127.0.0.1:8000`; `.env` debe tener `PORT=8000`. Un puerto distinto produce HTTP 502.
- **Uvicorn siempre con `--reload-dir backend`.** Sin esto, los writes de SQLite (`analista.db` en la raíz) disparan reinicios del worker y cortan requests en curso.
- Frontend usa rutas relativas `/api/*` (proxy Vite, timeouts 180 s). Hay fallback directo a `http://127.0.0.1:8000` ante 502/503/504 en `App.jsx` y `LoginModal.jsx`. En Windows, `localhost` puede resolver a `::1` mientras uvicorn escucha en IPv4 — por eso se usa `127.0.0.1`.
- Config y secretos: `.env` en la raíz (ignorado por git). `backend/app/config.py` carga ese `.env` vía `ROOT_DIR`. Credenciales por defecto: usuario `Gleek` / `Contra123`, JWT HS256, tokens de 24 h.
- DB: SQLite vía SQLAlchemy (`backend/app/db.py`), archivo `analista.db` **en la raíz**. `init_db()` se ejecuta al importar el módulo y hace una migración manual de `match_url` con `PRAGMA table_info` — no hay Alembic.

## Arquitectura real (verificada contra el código, no contra la spec vieja)

- `backend/app/main.py`: endpoints `GET /api/health`, `POST /api/login`, `POST /api/predict`, `GET /api/predictions/recent`.
- `backend/app/agent/`: `scraper.py` (DuckDuckGo + Sofascore/Flashscore), `parser.py` (Gemini structured output), `collector.py`.
- `backend/app/models/`: `poisson.py` (Dixon-Coles, elasticidad γ=0.65, shrinkage bayesiano), `tabular_ml.py` (XGBoost/LightGBM, sigmoide calibrada), `lstm_net.py` (**PyTorch**, no TensorFlow — peso en `backend/weights/lstm_momentum.pt`), `ensemble.py` (meta-ensamble bayesiano). Peso tabular: `backend/weights/xgb_1x2.json`.
- LLM configurable por `GEMINI_MODEL` en `.env`; el default actual en `config.py` es `gemini-3.5-flash-lite`.
- Gemini solo busca/estructura datos; toda la inferencia es local. La localía (quién es local) la determina la IA, no el usuario. Si `is_live`, se priorizan datos in-play y refresco cada 5 min.
- Frontend: React 19 + Vite 8 + Chart.js, tema oscuro IDE (`#0e0e11`, `#16161a`, `#26262e`), números en monospace. Componentes en `frontend/src/components/`.

## Convenciones

- Al completar una tarea, actualizar `PROJECT_STATUS.md` (es el registro oficial; este archivo no se usa para tracking). Cada cambio de comportamiento incrementa la versión +0.1.
- No añadir texto de marketing a la UI: se comporta como panel de telemetría.
