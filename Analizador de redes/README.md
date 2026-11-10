# 🎬 Social Analyzer v1.1 — Inteligencia Competitiva de Reels & Generador de Guiones con IA

[![Version](https://img.shields.io/badge/Version-v1.1-58FF9C?style=flat-square&labelColor=090A0D)]()
[![Python](https://img.shields.io/badge/Python-3.11%2B-3776AB?style=flat-square&logo=python&logoColor=white)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115%2B-009688?style=flat-square&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![React](https://img.shields.io/badge/React-18-61DAFB?style=flat-square&logo=react&logoColor=black)](https://react.dev/)
[![TypeScript](https://img.shields.io/badge/TypeScript-5.x-3178C6?style=flat-square&logo=typescript&logoColor=white)](https://www.typescriptlang.org/)
[![Tailwind CSS](https://img.shields.io/badge/Tailwind%20CSS-3.4-06B6D4?style=flat-square&logo=tailwindcss&logoColor=white)](https://tailwindcss.com/)
[![Gemini Multimodal](https://img.shields.io/badge/Google%20Gemini-3.0%20Flash-8E75B2?style=flat-square&logo=google&logoColor=white)](https://aistudio.google.com/)

> **Social Analyzer v1.1** es una plataforma *Local-First* de inteligencia competitiva para Instagram y generación automatizada de contenido audiovisual corto (Reels) basada en el **Método ACE® (Analizar, Crear, Escalar)**. Extrae la voz de marca de tus clientes, rastrea los Reels más virales de sus competidores mediante **Apify**, transcribe el audio real con **`yt-dlp` + Google Gemini 3.0 Multimodal** y redacta **3 propuestas de guiones listas para grabar** con escaleta técnica segundo a segundo.

---

## 📑 Tabla de Contenidos

- [¿Qué Problema Resuelve?](#-qué-problema-resuelve)
- [Novedades de la Versión 1.1](#-novedades-de-la-versión-11)
- [Flujo del Pipeline de IA (4 Fases)](#-flujo-del-pipeline-de-ia-4-fases)
- [Características Principales](#-características-principales)
- [Sistema de Diseño "Anti-IA" (Swiss Grid & Verde Eléctrico)](#-sistema-de-diseño-anti-ia-swiss-grid--verde-eléctrico)
- [Stack Tecnológico](#-stack-tecnológico)
- [Estructura del Proyecto](#-estructura-del-proyecto)
- [Requisitos e Instalación](#-requisitos-e-instalación)
- [Ejecución en 1 Clic (`start_local.bat`)](#-ejecución-en-1-clic-start_localbat)
- [Endpoints de la API](#-endpoints-de-la-api)
- [Guía de Escalado a Producción](#-guía-de-escalado-a-producción)

---

## 🎯 ¿Qué Problema Resuelve?

Las agencias de marketing, creadores de contenido y estrategas digitales suelen invertir horas buscando qué contenido le está funcionando a la competencia en Instagram, transcribiendo videos manualmente y tratando de adaptarlos al tono de cada cliente.

**Social Analyzer v1.1** automatiza todo el ciclo desde un tablero Kanban centralizado:
1. Gestiona múltiples perfiles de clientes categorizados por industria y color identificativo.
2. Analiza el perfil del cliente para sintetizar su *Brand Voice Profile* (tono, oferta y audiencia).
3. Detecta matemáticamente el **Top 3 de Reels más virales** entre todos los competidores vinculados.
4. Extrae y transcribe el audio hablado de esos videos y genera **3 guiones adaptados palabra por palabra** con gancho (`00:00 - 00:03`), retención (`00:03 - 00:15`) y llamado a la acción (`00:15 - 00:30`).

---

## 🆕 Novedades de la Versión 1.1

- **Renombrado Oficial a Social Analyzer v1.1**: Identidad unificada en interfaz web (Login, Navbar, Títulos HTML), servidor API (`FastAPI v1.1`) y scripts de automatización local.
- **Normalización Universal de Entradas de Instagram**: Soporte transparente para `@usuario`, `usuario`, URLs completas (`https://www.instagram.com/usuario/`), enlaces directos a Reels o URLs con parámetros de seguimiento.
- **Consumo 0 Bytes de Almacenamiento Persistente en Apify**: Purga inmediata de datasets y registros de ejecución en la nube (`dataset.delete()` y `run.delete()`) tras cada análisis.
- **Higiene Atómica en Disco (`tmp_media`)**: Limpieza instantánea garantizada de pistas de audio temporales descargadas por `yt-dlp`.

---

## 🧠 Flujo del Pipeline de IA (4 Fases)

```text
   [ URL de Instagram del Cliente ]        [ URLs de Competidores ]
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
                  │  ├─ A. Título Magnético + Métrica  │
                  │  ├─ B. Escaleta por Segundos       │
                  │  └─ C. Guion Literal Adaptado      │
                  └─────────────────┬──────────────────┘
                                    ▼
                  [ Persistencia SQLite + Modal Kanban ]
```

---

## ✨ Características Principales

- **Normalización Universal de Entradas (`apify_service.py`)**: Acepta cualquier formato de entrada para clientes y competidores (`@usuario`, `usuario`, `https://instagram.com/usuario/`, enlaces directos a Reels o URLs con parámetros).
- **Consumo 0 Bytes de Almacenamiento en Apify**: Tras cada extracción (`memory_mbytes=256`), el sistema purga automáticamente los datasets y ejecuciones en la nube de Apify (`dataset.delete()` / `run.delete()`), protegiendo la cuota gratuita de la cuenta.
- **Higiene Atómica de Archivos Multimedia (`media_extractor.py`)**: Los audios descargados por `yt-dlp` en `/tmp_media/` se eliminan inmediatamente en bloques `try...finally` tras su transcripción, además de contar con purga completa al iniciar y apagar el servidor.
- **Tablero Kanban de Perfiles con Tiempo Dinámico**: Tarjetas cuadradas modulares con buscador instantáneo, filtro por categoría de negocio y cálculo en tiempo real desde la última auditoría (*"Sin análisis previo"*, *"hace 12m"*, *"hace 4h"*).
- **Mini-Ventana Modal Interactiva (`6xl`)**: Visualización de alta densidad sin recargar ni cambiar de página, con *stepper* de progreso en vivo y botón de copiado de guiones con feedback instantáneo.

---

## 🎨 Sistema de Diseño "Anti-IA" (Swiss Grid & Verde Eléctrico)

Inspirado en la estética ejecutiva del **Método ACE®** y herramientas de precisión como Linear, Vercel y Raycast:

- **Fondos Obsidiana y Carbón**: Lienzo profundo `#090A0D`, superficies `#111318` y contenedores elevados `#171A21` con cuadrícula técnica sutil (`bg-tech-grid`).
- **Acento Verde Eléctrico (`#58FF9C`)**: Reservado para llamadas a la acción primarias, indicadores de conexión API, estados activos y bordes en foco.
- **Tipografía con Carácter**: `Plus Jakarta Sans` para titulares y lectura de guiones, combinada con `JetBrains Mono` para badges de categoría, contadores de tiempo, métricas de vistas y marcas de tiempo de escaleta (`[00:00 - 00:03]`).
- **Bordes Técnicos de `1px`**: Cero gradientes neón genéricos ni sombras difusas exageradas; indicadores de color de cliente aplicados con elegancia en barras de `3px` y badges al `12%` de opacidad.

---

## 🛠 Stack Tecnológico

| Capa | Tecnología | Propósito |
| :--- | :--- | :--- |
| **Backend** | `Python 3.11+` · `FastAPI` · `Uvicorn` | API REST asíncrona, orquestación del pipeline y validación estricta con Pydantic. |
| **Base de Datos** | `SQLite` · `SQLAlchemy ORM` | Persistencia local en `./data/` lista para migrar a PostgreSQL vía `.env`. |
| **Scraping Social** | `apify-client` | Extracción de perfiles, publicaciones y métricas de Reels en Instagram con fallback seguro. |
| **Multimedia & IA** | `yt-dlp` · `Google Gemini 3.0 Flash` | Extracción temporal de pistas de audio, transcripción multimodal e ingeniería inversa de guiones. |
| **Frontend** | `React` · `TypeScript` · `Vite` · `Tailwind CSS` | Interfaz SPA de alto rendimiento con iconografía `Lucide Icons` (`strokeWidth={1.5}`). |

---

## 📁 Estructura del Proyecto

```text
Analizador de redes/
├── .env.example              # Plantilla de configuración y claves de API
├── .gitignore                # Reglas de exclusión (.env, .venv, *.db, tmp_media/)
├── AGENTS.md                 # Especificación maestra de arquitectura y diseño
├── PROJECT_STATUS.md         # Bitácora de versiones, changelog y estado de módulos
├── README.md                 # Documentación principal de Social Analyzer v1.1
├── start_local.bat           # Lanzador automático en 1 clic para Windows
├── data/                     # Directorio de base de datos SQLite local autogenerada
├── tmp_media/                # Directorio temporal autolimpiable para yt-dlp
│
├── backend/
│   ├── requirements.txt      # Dependencias de Python
│   ├── main.py               # Punto de entrada FastAPI, CORS y ciclo de vida
│   ├── config.py             # Carga centralizada de variables de entorno
│   ├── database.py           # Motor SQLAlchemy y sesión de base de datos
│   ├── models.py             # Modelos ORM (Profile, AnalysisReport, ScriptProposal)
│   ├── schemas.py            # Esquemas Pydantic y cálculo de tiempo relativo
│   ├── routers/
│   │   ├── auth.py           # Autenticación administrativa (/api/auth/login)
│   │   ├── profiles.py       # CRUD de perfiles y disparo de análisis (/api/profiles)
│   │   └── health.py         # Estado del motor y conectividad API (/api/health)
│   └── services/
│       ├── apify_service.py  # Extracción de Instagram y purga de almacenamiento Apify
│       ├── media_extractor.py# Descarga de audio con yt-dlp y limpieza atómica
│       ├── gemini_service.py # Transcripción multimodal y generación de los 3 guiones
│       └── analyzer_service.py # Orquestador integral de las 4 fases del pipeline
│
└── frontend/
    ├── package.json          # Dependencias React, TypeScript y Tailwind CSS (v1.1.0)
    ├── vite.config.ts        # Configuración de Vite (puerto 3000)
    ├── tailwind.config.js    # Tokens de diseño Swiss Grid y paleta #58FF9C
    └── src/
        ├── App.tsx           # Enrutamiento de vistas y control de sesión
        ├── api.ts            # Cliente HTTP hacia el backend FastAPI
        ├── index.css         # Variables CSS, cuadrícula técnica y scrollbars
        └── components/
            ├── views/        # LoginView.tsx y DashboardView.tsx
            ├── kanban/       # ProfileCard.tsx y EmptyState.tsx
            ├── modals/       # CreateProfileModal.tsx y ProfileDetailModal.tsx
            ├── layout/       # Navbar.tsx con monitor de salud en vivo
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

Para iniciar todo el entorno local de **Social Analyzer v1.1** en Windows sin ejecutar comandos manuales, haz doble clic en **`start_local.bat`** o ejecútalo desde la terminal:

```bat
.\start_local.bat
```

El script realiza automáticamente:
1. Verificación/creación del entorno virtual `.venv` e instalación de `backend/requirements.txt`.
2. Verificación e instalación de `frontend/node_modules`.
3. Creación de `.env` desde `.env.example` si no existe.
4. Arranque concurrente del **Backend FastAPI** (`http://localhost:8000`) y **Frontend Vite** (`http://localhost:3000`).
5. Apertura automática del navegador en `http://localhost:3000`.

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
| `POST` | `/api/profiles` | Registra un nuevo cliente con su categoría, color, Instagram y competidores. |
| `GET` | `/api/profiles/{id}` | Obtiene el detalle del perfil junto con su último reporte y los 3 guiones generados. |
| `DELETE` | `/api/profiles/{id}` | Elimina un perfil y su historial de análisis asociado. |
| `POST` | `/api/profiles/{id}/analyze` | Ejecuta el pipeline completo de 4 fases (Apify $\to$ `yt-dlp` $\to$ Gemini 3.0 $\to$ SQLite). |

---

## 🌐 Guía de Escalado a Producción

1. **Base de Datos**: Sustituir `DATABASE_URL` en `.env` por una instancia PostgreSQL (`postgresql://user:pass@host:5432/dbname` en Supabase o Neon) y añadir `psycopg2-binary`.
2. **Backend**: Desplegar `/backend` en Railway, Render o Fly.io con `uvicorn main:app --host 0.0.0.0 --port $PORT` (incluyendo `ffmpeg` en la imagen para extracción de audio con `yt-dlp`).
3. **Frontend**: Desplegar `/frontend` en Vercel o Cloudflare Pages apuntando `VITE_API_URL` / `NEXT_PUBLIC_API_URL` al dominio HTTPS del backend.
4. **Seguridad**: Actualizar `ADMIN_USER`, `ADMIN_PASS` y `APP_SECRET_KEY` con credenciales seguras de producción.
