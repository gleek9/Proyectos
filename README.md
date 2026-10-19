# AI-Driven Problem Solving — Vibe Coding Monorepo



[![Philosophy](https://img.shields.io/badge/Philosophy-Vibe%20Coding-8A2BE2?style=flat-square)]()

[![Architecture](https://img.shields.io/badge/Architecture-AI--Native-00A67E?style=flat-square)]()

[![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB?style=flat-square&logo=python&logoColor=white)](https://www.python.org/)

[![React](https://img.shields.io/badge/React-19%2B-61DAFB?style=flat-square&logo=react&logoColor=black)](https://react.dev/)

[![FastAPI](https://img.shields.io/badge/FastAPI-Latest-009688?style=flat-square&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)

[![Maintainer](https://img.shields.io/badge/Maintainer-gleek9-181717?style=flat-square&logo=github)](https://github.com/gleek9)



> **Repositorio central de ingeniería de software asistida por Inteligencia Artificial.**  

> Cada directorio dentro de este monorepo representa una aplicación completa diseñada para **resolver una problemática real**, combinando dirección arquitectónica humana, *Vibe Coding* de alta velocidad y modelos de IA (LLMs, Machine Learning y agentes autónomos).



---



## Tabla de Contenidos



- [Visión y Metodología](#visión-y-metodología)

- [Flujo de Trabajo (Del Problema al Sistema)](#flujo-de-trabajo-del-problema-al-sistema)

- [Catálogo de Proyectos](#catálogo-de-proyectos)

- [Proyecto Destacado: Katakuri v3.5](#proyecto-destacado-katakuri-v35)

- [Ecosistema Tecnológico](#ecosistema-tecnológico)

- [Estructura del Monorepo](#estructura-del-monorepo)

- [Guía de Inicio Rápido](#guía-de-inicio-rápido)



---



## Visión y Metodología



El desarrollo de software tradicional suele verse frenado por la fricción sintáctica y la configuración repetitiva (*boilerplate*). Este repositorio aplica la filosofía del **Vibe Coding** con enfoque en **Ingeniería de Producto**: utilizar el lenguaje natural, agentes de código y modelos fundacionales para iterar a la velocidad del pensamiento, concentrando el esfuerzo humano en entender el problema, diseñar la arquitectura matemática/lógica y validar los resultados.



Cada proyecto alojado aquí cumple con tres pilares:



1. **Problemática Real**: No son simples *"Hola Mundo"*; atacan problemas complejos de datos, automatización, predicción o experiencia de usuario.

2. **IA como Motor y como Herramienta**: Se utiliza IA tanto para construir el software (orquestación agéntica y desarrollo asistido) como dentro del núcleo de las aplicaciones (Agentes LangChain, PyTorch, XGBoost, inferencia con Gemini).

3. **Documentación y Trazabilidad**: Cada proyecto incluye su propia arquitectura documentada, especificación de agentes (`Agents.md`) y bitácora de estado (`PROJECT_STATUS.md`).



---



## Flujo de Trabajo (Del Problema al Sistema)



```text

   [ Identificación de Problemática Real ]

                      │

                      ▼

   [ Diseño de Arquitectura y Prompting ]

     ├─ Definición de reglas de negocio y modelos matemáticos

     ├─ Orquestación de Agentes (Agents.md)

     └─ Iteración rápida con IA (Vibe Coding)

                      │

                      ▼

   [ Desarrollo Full-Stack & Motor de IA ]

     ├─ Backend Asíncrono / Inferencia Local o API

     ├─ Frontend Moderno de Alta Usabilidad

     └─ Suite de Pruebas, Auditoría y Backtesting

                      │

                      ▼

   [ Solución Desplegada en el Monorepo ]

```



---



## Catálogo de Proyectos



| # | Proyecto | Problemática que Resuelve | Stack Principal | Estado | Directorio |

| :-: | :--- | :--- | :--- | :-: | :--- |

| **01** | **Katakuri v3.5**<br>*(Analista Deportivo)* | Asimetría de información y sesgo humano en el análisis deportivo. Automatiza la recolección de datos en tiempo real y ejecuta inferencia probabilística multi-modelo (1X2, Goles, Córners, Tarjetas). | `Python` `FastAPI` `React 19` `PyTorch` `XGBoost` `Gemini 3.5` | **Activo (v3.5)** | [`./Analista deportivo`](./Analista%20deportivo) |

| **02** | *Próximo Proyecto...* | *En fase de conceptualización y diseño de arquitectura.* | `TBD` | *En desarrollo* | *Próximamente* |



---



## Proyecto Destacado: Katakuri v3.5



Ubicado en [`./Analista deportivo`](./Analista%20deportivo), **Katakuri v3.5** es el primer sistema de este repositorio: una plataforma autónoma de predicción deportiva con interfaz estilo *Dark IDE*.



### ¿Cómo resuelve el problema?

A partir de los nombres de dos equipos o una URL directa (Sofascore / Flashscore), despliega un agente con **Google Gemini 3.5 Flash Lite** que extrae telemetría en vivo o pre-partido, procesa *Feature Engineering* avanzado y alimenta un **meta-ensamble matemático 100% local**:



- **Poisson Bivariado con Dixon-Coles ($\tau$)**: Correlaciones de marcadores bajos y elasticidad amortiguada.

- **XGBoost / LightGBM**: Procesamiento tabular de 18 variables con calibración sigmoide.

- **PyTorch LSTM**: Red neuronal recurrente para capturar el *momentum* y rachas de los últimos 10 encuentros.

- **Modelado Binomial Negativo & Game State**: Ajuste dinámico en vivo por minuto de juego, marcador actual y tarjetas rojas.



**[Explorar el código y documentación completa de Katakuri v3.5](./Analista%20deportivo)**



---



## Ecosistema Tecnológico



### Inteligencia Artificial & Data Science

- **LLMs & Orquestación**: Google Gemini, LangChain, Agentes Autónomos de Extracción.

- **Machine Learning & Deep Learning**: PyTorch (LSTM), XGBoost, LightGBM, Scikit-Learn.

- **Modelado Matemático**: SciPy, NumPy (Distribuciones de Poisson, Binomial Negativa, Calibración Isotónica).



### Desarrollo Full-Stack

- **Backend**: Python 3.10+, FastAPI, Uvicorn, SQLAlchemy, Pydantic, SQLite.

- **Frontend**: React 19, Vite 8, Chart.js, Lucide Icons, CSS3 Moderno (Variables y temas oscuros tipo IDE).



---



## Estructura del Monorepo



```text

Proyectos/

├── README.md                        # Portada general del portafolio (Este archivo)

│

├── Analista deportivo/              # Proyecto 01: Katakuri v3.5 (Predicción Deportiva IA)

│   ├── Agents.md                    # Especificación de roles de agentes de IA

│   ├── PROJECT_STATUS.md            # Bitácora de versiones y auditorías

│   ├── README.md                    # Documentación técnica del proyecto

│   ├── run_app.py                   # Orquestador de arranque en 1 clic

│   ├── backend/                     # API FastAPI + Motores PyTorch/XGBoost/Poisson

│   └── frontend/                    # Interfaz Dark IDE en React 19 + Vite 8

│

└── [Futuros-Proyectos]/             # Nuevas aplicaciones basadas en IA

```



---



## Guía de Inicio Rápido



Dado que este repositorio funciona como un **monorepo**, cada proyecto es autónomo y posee sus propias dependencias, variables de entorno y scripts de ejecución.



1. **Clonar el repositorio completo**:

   ```bash

   git clone https://github.com/gleek9/Proyectos.git

   cd Proyectos

   ```



2. **Entrar al proyecto que deseas ejecutar** (por ejemplo, *Analista deportivo*):

   ```bash

   cd "Analista deportivo"

   ```



3. **Seguir las instrucciones específicas del proyecto**:

   Cada carpeta cuenta con su propio `README.md` detallado, plantilla `.env.example` y lanzadores automáticos (`run_app.py` o `iniciar_app.bat`).



---



## Licencia y Autoría



Desarrollado y mantenido por **[gleek9](https://github.com/gleek9)**.  

Los proyectos contenidos en este repositorio están destinados a demostrar capacidades de arquitectura de software, ciencia de datos e integración de Inteligencia Artificial aplicada a problemas reales.
