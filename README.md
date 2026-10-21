# AI-Driven Problem Solving — Vibe Coding Monorepo



[![Philosophy](https://img.shields.io/badge/Philosophy-Vibe%20Coding-8A2BE2?style=flat-square)]() [![Architecture](https://img.shields.io/badge/Architecture-AI--Native-00A67E?style=flat-square)]() [![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB?style=flat-square&logo=python&logoColor=white)](https://www.python.org/) [![React](https://img.shields.io/badge/React-19%2B-61DAFB?style=flat-square&logo=react&logoColor=black)](https://react.dev/) [![FastAPI](https://img.shields.io/badge/FastAPI-Latest-009688?style=flat-square&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/) [![Maintainer](https://img.shields.io/badge/Maintainer-gleek9-181717?style=flat-square&logo=github)](https://github.com/gleek9)



> **Repositorio central de ingeniería de software asistida por Inteligencia Artificial.** Cada directorio dentro de este monorepo representa una aplicación completa diseñada para **resolver una problemática real**, combinando dirección arquitectónica humana, *Vibe Coding* de alta velocidad y modelos de IA (LLMs, Machine Learning y agentes autónomos).



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



1. **Problemática Real**: No son simples ejemplos básicos; atacan problemas complejos de datos, automatización, predicción o experiencia de usuario.

2. **IA como Motor y como Herramienta**: Se utiliza IA tanto para construir el software (orquestación agéntica y desarrollo asistido) como dentro del núcleo de las aplicaciones (Agentes LangChain, PyTorch, XGBoost, inferencia con Gemini).

3. **Documentación y Trazabilidad**: Cada proyecto incluye su propia arquitectura documentada, especificación de agentes (`Agents.md`) y bitácora de estado (`PROJECT_STATUS.md`).



---



## Flujo de Trabajo (Del Problema al Sistema)



1. **Identificación de Problemática Real**: Análisis del dominio, detección de cuellos de botella o asimetrías de información y definición de métricas de éxito.

2. **Diseño de Arquitectura y Orquestación**: Definición de reglas de negocio, formulación de modelos matemáticos, especificación de roles en `Agents.md` e iteración rápida mediante *Vibe Coding*.

3. **Desarrollo Full-Stack y Motor de IA**: Implementación de backend asíncrono, motores de inferencia local o vía API y construcción de interfaces modernas de alta usabilidad.

4. **Auditoría, Pruebas y Despliegue**: Validación rigurosa mediante suites de pruebas unitarias, *backtesting* cuantitativo y publicación documentada dentro del monorepo.



---



## Catálogo de Proyectos



### 01. [Katakuri v3.5 (Analista Deportivo)](./Analista%20deportivo)



- **Estado**: Activo (v3.5)

- **Directorio**: [`./Analista deportivo`](./Analista%20deportivo)

- **Problemática que Resuelve**: Asimetría de información y sesgo humano en el análisis deportivo. Automatiza la recolección de datos en tiempo real y ejecuta inferencia probabilística multi-modelo (1X2, Goles, Córners, Tarjetas).

- **Stack Principal**: `Python 3.10+` · `FastAPI` · `React 19` · `Vite 8` · `PyTorch` · `XGBoost` · `Gemini 3.5 Flash Lite`



### 02. Próximo Proyecto (En Desarrollo)



- **Estado**: En fase de conceptualización y diseño de arquitectura

- **Directorio**: *Próximamente*

- **Problemática que Resuelve**: Nueva aplicación basada en agentes autónomos e inteligencia artificial aplicada.



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



- **`README.md`**: Portada general del portafolio y catálogo central de proyectos.

- **[`Analista deportivo/`](./Analista%20deportivo)**: Proyecto 01 — Plataforma Katakuri v3.5.

- **`Analista deportivo/Agents.md`**: Especificación de roles y orquestación de agentes de IA.

- **`Analista deportivo/PROJECT_STATUS.md`**: Bitácora detallada de versiones, hitos y auditorías.

- **`Analista deportivo/run_app.py`**: Supervisor unificado para arranque automático en un clic.

- **`Analista deportivo/backend/`**: API REST en FastAPI y motores predictivos (Poisson, XGBoost, PyTorch LSTM).

- **`Analista deportivo/frontend/`**: Interfaz de usuario estilo Dark IDE en React 19 y Vite 8.



---



## Guía de Inicio Rápido



Dado que este repositorio funciona como un **monorepo**, cada proyecto es autónomo y posee sus propias dependencias, variables de entorno y scripts de ejecución:



1. **Clonar el repositorio completo**: `git clone https://github.com/gleek9/Proyectos.git`

2. **Entrar a la carpeta raíz**: `cd Proyectos`

3. **Acceder al proyecto deseado**: `cd "Analista deportivo"`

4. **Iniciar la aplicación**: Seguir la guía del `README.md` interno del proyecto o ejecutar directamente `python run_app.py`.



---



## Licencia y Autoría



Desarrollado y mantenido por **[gleek9](https://github.com/gleek9)**. Los proyectos contenidos en este repositorio están destinados a demostrar capacidades de arquitectura de software, ciencia de datos e integración de Inteligencia Artificial aplicada a problemas reales.
