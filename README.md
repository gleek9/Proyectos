AI-Driven Problem Solving — Vibe Coding Monorepo
![Vibe Coding](https://img.shields.io/badge/Philosophy-Vibe%20Coding-8A2BE2?style=flat&logo=sparkles&logoColor=white)
![AI Native](https://img.shields.io/badge/Architecture-AI--Native-009688?style=flat&logo=google-gemini&logoColor=white)
![Python](https://img.shields.io/badge/Python-3.10%2B-blue?logo=python&logoColor=white)
![React](https://img.shields.io/badge/React-19%2B-61DAFB?logo=react&logoColor=black)
![FastAPI](https://img.shields.io/badge/FastAPI-Latest-009688?logo=fastapi&logoColor=white)
![Maintainer](https://img.shields.io/badge/Maintainer-gleek9-black?logo=github)
> **Repositorio central de ingeniería de software asistida por Inteligencia Artificial.**  
> Cada directorio dentro de este monorepo representa una aplicación completa diseñada para **resolver una problemática real**, combinando dirección arquitectónica humana, *Vibe Coding* de alta velocidad y modelos de IA (LLMs, Machine Learning y agentes autónomos).
---
Tabla de Contenidos
Visión y Metodología
Flujo de Trabajo (Del Problema al Sistema)
Catálogo de Proyectos
Proyecto Destacado: Katakuri v3.5
Ecosistema Tecnológico
Estructura del Monorepo
Guía de Inicio Rápido
---
Visión y Metodología
El desarrollo de software tradicional suele verse frenado por la fricción sintáctica y la configuración repetitiva (boilerplate). Este repositorio aplica la filosofía del Vibe Coding con enfoque en Ingeniería de Producto: utilizar el lenguaje natural, agentes de código y modelos fundacionales para iterar a la velocidad del pensamiento, concentrando el esfuerzo humano en entender el problema, diseñar la arquitectura matemática/lógica y validar los resultados.
Cada proyecto alojado aquí cumple con tres pilares:
Problemática Real: No son simples "Hola Mundo"; atacan problemas complejos de datos, automatización, predicción o experiencia de usuario.
IA como Motor y como Herramienta: Se utiliza IA tanto para construir el software (Cursor, Windsurf, Claude, Gemini) como dentro del núcleo de las aplicaciones (Agentes LangChain, PyTorch, XGBoost, inferencia LLM).
Documentación y Trazabilidad: Cada proyecto incluye su propia arquitectura documentada, especificación de agentes (`Agents.md`) y bitácora de estado (`PROJECT_STATUS.md`).
---
Flujo de Trabajo (Del Problema al Sistema)
```text
   [ 1. Identificación de Problemática Real ]
                       │
                       ▼
   [ 2. Diseño de Arquitectura y Orquestación (Prompts / Agents.md) ]
                       │
                       ▼
   [ 3. Desarrollo Iterativo con IA (Vibe Coding + Pair Programming) ]
     ├─ Backend & Motores Cuantitativos / Agentes
     ├─ Frontend Moderno & Visualización de Datos
     └─ Automatización de Arranque y Resiliencia
                       │
                       ▼
   [ 4. Auditoría, Testing Científico y Despliegue Local ]
```
---
Catálogo de Proyectos
A continuación se listan las soluciones desarrolladas en este repositorio. Haz clic en el nombre del proyecto para acceder a su código fuente y documentación detallada:
#	Proyecto	Problemática que Resuelve	IA & Modelos Integrados	Stack Principal	Estado
01	Katakuri v3.5 (Analista Deportivo)	Asimetría de información, sesgo humano y dispersión estadística en el análisis pre-partido y en vivo de fútbol.	Gemini 3.5 Flash Lite (Agente Web), Poisson Dixon-Coles, XGBoost, PyTorch LSTM	Python, FastAPI, React 19, Vite 8, SQLite	✅ v3.5 Activo
02	Próximo Proyecto...	En fase de definición de problemática y diseño arquitectónico.	TBD	TBD	🚧 En planeación
---
Proyecto Destacado: Katakuri v3.5
Ubicado en el directorio `./Analista deportivo`, Katakuri v3.5 es una plataforma autónoma de analítica predictiva de fútbol que ejemplifica el estándar de este repositorio:
El Problema: Analizar un partido de fútbol en tiempo real o pre-partido requiere cruzar docenas de fuentes (lesiones, fatiga, $xG$, rachas, estado del partido en vivo) y calcular probabilidades sin caer en sesgos emocionales ni depender de APIs lentas para el cálculo matemático.
La Solución con IA:
Extracción Autónoma: Un agente impulsado por Google Gemini 3.5 Flash Lite y feeds deportivos ingiere nombres de equipos o URLs directas (Sofascore/Flashscore) y extrae telemetría en segundos.
Meta-Ensamble Cuantitativo 100% Local: Procesa los datos mediante un consenso bivariado que une distribución Poisson con ajuste Dixon-Coles ($\tau$), Binomial Negativa (para sobredispersión en córners/tarjetas), XGBoost y redes recurrentes PyTorch LSTM, adaptándose dinámicamente al Game State en vivo.
Interfaz Dark IDE: Frontend en React 19 + Vite 8 sin fricción de acceso, con gráficas interactivas y suite de backtesting científico (RPS, Brier Score, Log-Loss).
Ir a la documentación completa y código de Katakuri v3.5
---
Ecosistema Tecnológico
Las soluciones de este repositorio se construyen combinando herramientas de desarrollo asistido por IA con tecnologías de producción robustas:
Desarrollo Asistido & Agentes (Vibe Coding Stack)
LLMs de Arquitectura y Código: Claude, Google Gemini, GPT-4o.
Orquestación de Agentes: Especificaciones estructuradas mediante archivos `Agents.md` y `PROJECT_STATUS.md`.
Frameworks de IA en Aplicaciones: LangChain, Google AI Studio (Gemini API), PyTorch, XGBoost, LightGBM, SciPy.
Stack de Ingeniería (Full-Stack & Data)
Backend: Python 3.10+, FastAPI, Uvicorn, SQLAlchemy, Pydantic, SQLite.
Frontend: React 19, Vite, Chart.js, Lucide Icons, CSS3 Moderno (Diseño tipo IDE).
Automatización: Scripts supervisados multi-proceso (`run_app.py`, `.bat`, `.ps1`).
---
Estructura del Monorepo
El repositorio está organizado de forma modular. Cada proyecto es completamente autónomo y contiene sus propios entornos, scripts de inicio y pruebas:
```text
Proyectos/
├── README.md                        # Portada general del Monorepo (Estás aquí)
│
├── Analista deportivo/              # [Proyecto 01] Katakuri v3.5
│   ├── Agents.md                    # Roles de agentes de IA utilizados en el proyecto
│   ├── PROJECT_STATUS.md            # Bitácora de evolución y auditorías técnicas
│   ├── README.md                    # Documentación técnica completa de Katakuri
│   ├── run_app.py                   # Supervisor de arranque en 1 clic
│   ├── backend/                     # API FastAPI + Agente Gemini + Motor ML/Estadístico
│   └── frontend/                    # Interfaz Dark IDE en React 19 + Vite 8
│
└── [Futuros Proyectos]/             # Nuevas soluciones basadas en IA
```
---
Guía de Inicio Rápido
Dado que cada carpeta es un proyecto independiente, puedes clonar este repositorio y ejecutar únicamente el proyecto que desees explorar:
1. Clonar el Monorepo
```bash
git clone https://github.com/gleek9/Proyectos.git
cd Proyectos
```
2. Entrar a un Proyecto (Ejemplo: Katakuri v3.5)
```bash
cd "Analista deportivo"
```
3. Seguir las instrucciones locales
Cada proyecto cuenta con su propio `README.md` detallado y scripts de automatización (como `run_app.py` o `iniciar_app.bat`) para levantar tanto el backend como el frontend de forma inmediata.
---
Contacto y Autor
Desarrollado y mantenido por gleek9.  
Explorando los límites de lo que se puede construir cuando la intuición de producto se une a la Inteligencia Artificial.
GitHub: @gleek9
---
Todos los proyectos contenidos en este repositorio cuentan con sus propias licencias y términos especificados en sus respectivos directorios.
