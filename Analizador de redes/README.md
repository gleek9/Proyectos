# 🎬 Social Analyzer v2 — Inteligencia Competitiva de Reels & Generador de Guiones con IA

[![Version](https://img.shields.io/badge/Version-v2-F4F4F5?style=flat-square&labelColor=0B0C0E)]()
[![Python](https://img.shields.io/badge/Python-3.11%2B-3776AB?style=flat-square&logo=python&logoColor=white)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115%2B-009688?style=flat-square&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![React](https://img.shields.io/badge/React-18-61DAFB?style=flat-square&logo=react&logoColor=black)](https://react.dev/)
[![TypeScript](https://img.shields.io/badge/TypeScript-5.x-3178C6?style=flat-square&logo=typescript&logoColor=white)](https://www.typescriptlang.org/)
[![Tailwind CSS](https://img.shields.io/badge/Tailwind%20CSS-3.4-06B6D4?style=flat-square&logo=tailwindcss&logoColor=white)](https://tailwindcss.com/)
[![Gemini Multimodal](https://img.shields.io/badge/Google%20Gemini-3.0%20Flash-8E75B2?style=flat-square&logo=google&logoColor=white)](https://aistudio.google.com/)

> **Social Analyzer v2** es una plataforma *Local-First* de inteligencia competitiva para Instagram y generación automatizada de contenido audiovisual corto (Reels). Extrae la voz de marca de tus clientes, analiza hasta **10 cuentas o Reels de referencia** mediante **Apify**, transcribe el audio real con **`yt-dlp` + Google Gemini 3.0 Multimodal** y redacta **3 propuestas de guiones de 60 a 90 segundos** listas para grabar, con cada sección de escaleta unida directamente a su locución.

---

## 📑 Tabla de Contenidos

- [¿Qué Problema Resuelve?](#-qué-problema-resuelve)
- [Novedades de la Versión 2](#-novedades-de-la-versión-2)
- [Flujo del Pipeline de IA (4 Fases)](#-flujo-del-pipeline-de-ia-4-fases)
- [Características Principales](#-características-principales)
- [Sistema de Diseño Dark Minimalist](#-sistema-de-diseño-dark-minimalist)
- [Stack Tecnológico](#-stack-tecnológico)
- [Estructura del Proyecto](#-estructura-del-proyecto)
- [Requisitos e Instalación](#-requisitos-e-instalación)
- [Ejecución en 1 Clic (`start_local.bat`)](#-ejecución-en-1-clic-start_localbat)
- [Endpoints de la API](#-endpoints-de-la-api)
- [Guía de Escalado a Producción](#-guía-de-escalado-a-producción)

---

## 🎯 ¿Qué Problema Resuelve?

Las agencias de marketing, creadores de contenido y estrategas digitales suelen invertir horas buscando qué contenido le está funcionando a la competencia en Instagram, transcribiendo videos manualmente y tratando de adaptarlos al tono de cada cliente.

**Social Analyzer v2** automatiza todo el ciclo desde un tablero Kanban centralizado:
1. Gestiona múltiples perfiles de clientes diferenciados con una paleta editorial sobria por marca.
2. Analiza el perfil del cliente para sintetizar su *Brand Voice Profile* (tono, oferta y audiencia).
3. Rastrea hasta **10 referencias** por cliente y detecta matemáticamente el **Top 3 de Reels más virales**.
4. Extrae y transcribe el audio hablado de esos videos y genera **3 guiones de 60–90 segundos** adaptados palabra por palabra, uniendo cada bloque de escaleta con lo que debe decirse en esa sección.

---

## 🆕 Novedades de la Versión 2

- **Diseño Dark Minimalist Refinado (Sin Neón):** Estética monocromática en carbón mate (`#0B0C0E`, `#121316`, `#191B20`), botones primarios en blanco limpio (`#F4F4F5`) y diferenciación clara por cliente con paleta definida (`#38BDF8`, `#34D399`, `#F59E0B`, `#A78BFA`, `#F472B6`, `#FB7185`, `#94A3B8`).
- **Guiones de 60 a 90 Segundos con Hooks Virales:** Estructura causal de 5 actos (*Hook → Contexto y Tensión → Re-Hook → Payoff → Remate y CTA*) optimizada para retención y lectura natural (160–225 palabras).
- **Escaleta Unificada con Guion por Sección:** Cada sección temporal muestra juntos el tiempo, la fase/hook, el texto en pantalla, la dirección de escena y el texto exacto que decir, con copiado completo o solo locución.
- **Hasta 10 Referencias por Cliente:** Creación y edición inline de hasta 10 cuentas de competencia o URLs directas de Reels.
- **Lanzador Inteligente con Puertos Libres (`start_local.bat`):** Detecta automáticamente puertos libres en Windows y sincroniza el proxy de Vite con FastAPI.

---

## 🧠 Flujo del Pipeline de IA (4 Fases)

```text
   [ URL de Instagram del Cliente ]        [ Hasta 10 Referencias ]
                  │                                    │
                  ▼                                    ▼
      ┌───────────────────────┐            ┌───────────────────────┐
      │ 1. Radiografía Apify  │            │ 2. Caza de Virales    │
      │  (Bio + Posts + Tono) │            │ (Filtro Top 3 Reels)  │
      └───────────┬───────────┘            └───────────┬───────────┘
                  │                                    │
                  │                                    ▼
                  │                        ┌───────────────────────┐
                  │                        │ 3. Extracción yt-dlp  │
                  │                        │ + Transcripción Audio │
                  │                        └───────────┬───────────┘
                  │                                    │
                  └─────────────────┬──────────────────┘
                                    ▼
                  ┌────────────────────────────────────┐
                  │ 4. Ingeniería Inversa (Gemini 3.0) │
                  │  ├─ A. Arquetipo de Hook + Métrica │
                  │  ├─ B. Escaleta 5 Actos (60–90s)   │
                  │  └─ C. Locución Unificada por Paso │
                  └─────────────────┬──────────────────┘
                                    ▼
                  [ Persistencia SQLite + Modal Kanban ]
```

---

## ✨ Características Principales

- **Normalización Universal de Entradas (`apify_service.py`)**: Acepta cualquier formato de entrada para clientes y referencias (`@usuario`, `usuario`, `https://instagram.com/usuario/`, enlaces directos a Reels o URLs con parámetros).
- **Consumo 0 Bytes de Almacenamiento en Apify**: Tras cada extracción (`memory_mbytes=256`), el sistema purga automáticamente los datasets y ejecuciones en la nube de Apify (`dataset.delete()` / `run.delete()`).
- **Higiene Atómica de Archivos Multimedia (`media_extractor.py`)**: Los audios descargados por `yt-dlp` en `/tmp_media/` se eliminan inmediatamente en bloques `try...finally` tras su transcripción.
- **Tablero Kanban con Diferenciación por Cliente**: Tarjetas modulares con buscador instantáneo, filtro por categoría y tiempo dinámico desde la última auditoría.
- **Modal de Alta Legibilidad (`6xl`)**: Edición inline de referencias y color de cliente, selector de las 3 propuestas y lectura unificada de escaleta + locución sección por sección.

---

## 🎨 Sistema de Diseño Dark Minimalist

- **Fondos Carbón Mate**: Lienzo `#0B0C0E`, superficies `#121316` y controles `#191B20` con bordes finos de `1px` (`#22242B`).
- **Paleta Editorial por Cliente**: 7 tonos desaturados (*Grafito Azul*, *Musgo Mate*, *Ciruela Gris*, *Bronce Suave*, *Burdeos Polvo*, *Petróleo Mate*, *Taupe Mineral*) aplicados en una línea superior de `2px`, un degradado ambiental sutil y etiquetas personalizadas.
- **Tipografía y Accesibilidad**: `Plus Jakarta Sans` para lectura cómoda (`max-w-[70ch]` en guiones) y `JetBrains Mono` para tiempos y metadatos, respetando `prefers-reduced-motion` y foco visible por teclado.

---

## 🛠 Stack Tecnológico

| Capa | Tecnología | Propósito |
| :--- | :--- | :--- |
| **Backend** | `Python 3.11+` · `FastAPI` · `Uvicorn` | API REST asíncrona, orquestación del pipeline y validación estricta con Pydantic. |
| **Base de Datos** | `SQLite` · `SQLAlchemy ORM` | Persistencia local en `./data/` lista para migrar a PostgreSQL vía `.env`. |
| **Scraping Social** | `apify-client` | Extracción de perfiles, publicaciones y métricas de hasta 10 referencias en Instagram. |
| **Multimedia & IA** | `yt-dlp` · `Google Gemini 3.0 Flash` | Extracción temporal de audio, transcripción multimodal y guiones de 60–90 segundos. |
| **Frontend** | `React` · `TypeScript` · `Vite` · `Tailwind CSS` | Interfaz SPA minimalista con iconografía `Lucide Icons` (`strokeWidth={1.5}`). |

---

## 📁 Estructura del Proyecto

```text
Analizador de redes/
├── .env.example              # Plantilla de configuración y claves de API
├── .gitignore                # Reglas de exclusión (.env, .venv, *.db, tmp_media/)
├── AGENTS.md                 # Especificación base del proyecto
├── PROJECT_STATUS.md         # Bitácora de versiones, changelog y estado de módulos
├── README.md                 # Documentación principal de Social Analyzer v2
├── start_local.bat           # Lanzador automático con detección de puertos libres
├── data/                     # Directorio de base de datos SQLite local autogenerada
├── tmp_media/                # Directorio temporal autolimpiable para yt-dlp
│
├── backend/
│   ├── requirements.txt      # Dependencias de Python
│   ├── main.py               # Punto de entrada FastAPI v2, CORS y ciclo de vida
│   ├── config.py             # Carga centralizada de variables de entorno
│   ├── database.py           # Motor SQLAlchemy y sesión de base de datos
│   ├── models.py             # Modelos ORM (Profile, AnalysisReport, ScriptProposal)
│   ├── schemas.py            # Esquemas Pydantic (hasta 10 referencias y TimelineBlock unificado)
│   ├── routers/
│   │   ├── auth.py           # Autenticación administrativa (/api/auth/login)
│   │   ├── profiles.py       # CRUD de perfiles y disparo de análisis (/api/profiles)
│   │   └── health.py         # Estado del motor y conectividad API (/api/health)
│   └── services/
│       ├── apify_service.py  # Extracción de Instagram (hasta 10 referencias) y purga Apify
│       ├── media_extractor.py# Descarga de audio con yt-dlp y limpieza atómica
│       ├── gemini_service.py # Transcripción multimodal y guiones 60–90s con hooks virales
│       └── analyzer_service.py # Orquestador integral de las 4 fases
│
└── frontend/
    ├── package.json          # Dependencias React, TypeScript y Tailwind CSS (v2.0.0)
    ├── vite.config.ts        # Configuración dinámica de puertos y proxy /api
    ├── tailwind.config.js    # Tokens Dark Minimalist
    └── src/
        ├── App.tsx           # Enrutamiento de vistas y control de sesión
        ├── api.ts            # Cliente HTTP hacia el backend FastAPI
        ├── index.css         # Variables CSS, scrollbars y reduced-motion
        ├── utils/
        │   └── clientColors.ts # Paleta editorial curada y normalización de colores
        └── components/
            ├── views/        # LoginView.tsx y DashboardView.tsx
            ├── kanban/       # ProfileCard.tsx y EmptyState.tsx
            ├── modals/       # CreateProfileModal.tsx y ProfileDetailModal.tsx
            ├── layout/       # Navbar.tsx
            └── ui/           # Button.tsx, Badge.tsx, Input.tsx, Modal.tsx, InstagramIcon.tsx
```

---

## 💻 Requisitos e Instalación

1. **Python 3.10 / 3.11+** y **Node.js 18+** instalados en Windows.
2. **Claves de API** (configuradas en `.env` a partir de `.env.example`):
   ```env
   ADMIN_USER=Admin
   ADMIN_PASS=Admin
   APIFY_API_TOKEN=tu_token_de_apify_aqui
   GEMINI_API_KEY=tu_api_key_de_google_ai_studio_aqui
   GEMINI_MODEL=gemini-3-flash-preview
   DATABASE_URL=sqlite:///./data/citi_analyzer.db
   BACKEND_PORT=8000
   FRONTEND_PORT=3000
   ```

---

## 🚀 Ejecución en 1 Clic (`start_local.bat`)

Para iniciar **Social Analyzer v2** en Windows sin ejecutar comandos manuales, haz doble clic en **`start_local.bat`** o ejecútalo desde la terminal:

```bat
.\start_local.bat
```

El script realiza automáticamente:
1. Verificación/creación del entorno virtual `.venv` e instalación de `backend/requirements.txt`.
2. Verificación e instalación de `frontend/node_modules`.
3. Creación de `.env` desde `.env.example` si no existe.
4. Detección automática de puertos libres para Backend (`8000+`) y Frontend (`3000+`).
5. Arranque concurrente y apertura automática del navegador en el puerto asignado.

- **Credenciales por defecto en pantalla de Login**:
  - **Usuario**: `Admin`
  - **Contraseña**: `Admin`

---

## 🔌 Endpoints de la API

| Método | Endpoint | Descripción |
| :--- | :--- | :--- |
| `POST` | `/api/auth/login` | Valida las credenciales administrativas y devuelve el token de sesión. |
| `GET` | `/api/health` | Verifica el estado del servidor y la presencia de las claves Apify y Gemini. |
| `GET` | `/api/profiles` | Lista todos los perfiles del tablero Kanban con leyenda dinámica de tiempo. |
| `POST` | `/api/profiles` | Registra un nuevo cliente con su categoría, color editorial y hasta 10 referencias. |
| `GET` | `/api/profiles/{id}` | Obtiene el detalle del perfil junto con su último reporte y los 3 guiones unificados. |
| `PUT` | `/api/profiles/{id}` | Actualiza los datos, color y referencias del perfil. |
| `DELETE` | `/api/profiles/{id}` | Elimina un perfil y su historial de análisis asociado. |
| `POST` | `/api/profiles/{id}/analyze` | Ejecuta el pipeline completo de 4 fases (Apify $\to$ `yt-dlp` $\to$ Gemini 3.0 $\to$ SQLite). |

---

## 🌐 Guía de Escalado a Producción

1. **Base de Datos**: Sustituir `DATABASE_URL` en `.env` por una instancia PostgreSQL (`postgresql://user:pass@host:5432/dbname` en Supabase o Neon) y añadir `psycopg2-binary`.
2. **Backend**: Desplegar `/backend` en Railway, Render o Fly.io con `uvicorn main:app --host 0.0.0.0 --port $PORT` (incluyendo `ffmpeg` en la imagen para extracción de audio con `yt-dlp`).
3. **Frontend**: Desplegar `/frontend` en Vercel o Cloudflare Pages apuntando `VITE_API_URL` / `NEXT_PUBLIC_API_URL` al dominio HTTPS del backend.
4. **Seguridad**: Actualizar `ADMIN_USER`, `ADMIN_PASS` y `APP_SECRET_KEY` con credenciales seguras de producción.
