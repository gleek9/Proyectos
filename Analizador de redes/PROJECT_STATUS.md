# PROJECT_STATUS.md — Control y Trazabilidad de Social Analyzer

## 1. Estado General del Proyecto
- **Nombre del Proyecto:** `Social Analyzer`
- **Versión Actual:** `2.0` (`v2`)
- **Porcentaje de Avance Global:** `100%` (Todas las Fases completadas, pulidas bajo Dark Minimalist v2 y documentadas)
- **Arquitectura:** Local-First (`FastAPI v2.0` + `SQLite` + motor multimodal `Gemini 3.0` + `React / Vite` + `Tailwind CSS`).
- **Estado Operativo:** Lanzador automático `start_local.bat` con detección de puertos libres (`8000+` Backend / `3000+` Frontend).

---

## 2. Registro de Cambios (Changelog)

### [2026-11-21 00:56] — Botón Primario Blanco y Mayor Distinción de Color por Cliente
- **Botón Primario Blanco (`Button.tsx`):** Eliminado el morado `#5664C4`; botones primarios (`Nuevo perfil`, `Analizar`, `Guardar`, `Entrar`) restaurados en blanco limpio `#F4F4F5` sobre `#09090B`.
- **Mayor Distinción Cromática por Cliente (`clientColors.ts`, `ProfileCard.tsx`, `Modal.tsx`, `ProfileDetailModal.tsx`):**
  - Paleta de clientes renovada con colores nítidos y distinguibles sin neón (`#38BDF8`, `#34D399`, `#F59E0B`, `#A78BFA`, `#F472B6`, `#FB7185`, `#94A3B8`).
  - Barras de `3px`, lavado superior de tarjeta y etiquetas/pestañas activas con mayor presencia cromática; actualizado el cliente `Andorra` en SQLite a `#38BDF8`.

### [2026-11-21 00:50] — Lanzamiento v2: Eliminación Total de Neón, Paleta Editorial por Cliente y Pulido UX
- **Eliminación Total de Neón (Backend + Frontend + Docs):**
  - Reemplazado cualquier rastro restante de `#58FF9C` en `backend/models.py`, `backend/schemas.py`, `backend/routers/profiles.py`, `README.md` y componentes del frontend por la paleta mate Dark Minimalist.
  - Añadido `frontend/src/utils/clientColors.ts` con `resolveClientColor()` para remapear automáticamente colores neón heredados en perfiles existentes de SQLite hacia la nueva paleta editorial.
- **Pulido con Skills de Diseño (`frontend-design` + `ui-ux-pro-max`):**
  - Nueva paleta curada de 7 tonos mates por cliente (*Grafito Azul*, *Musgo Mate*, *Ciruela Gris*, *Bronce Suave*, *Burdeos Polvo*, *Petróleo Mate*, *Taupe Mineral*), editable también inline desde `ProfileDetailModal.tsx`.
  - Mejora de contraste AA (`>= 4.5:1`), foco visible WCAG (`focus-visible:outline-2`), atributos `aria-hidden` en iconos decorativos, medida legible `max-w-[70ch]` y contador de palabras en guiones de 60–90s.
- **Actualización Global a Versión `v2` (`2.0`):**
  - Actualizada la versión en `backend/main.py`, `frontend/package.json`, `frontend/index.html`, `App.tsx`, `Navbar.tsx`, `LoginView.tsx`, `start_local.bat`, `README.md` y `PROJECT_STATUS.md`.

### [2026-11-21 00:45] — Pulido Editorial Dark Minimalist y Diferenciación Elegante por Cliente
- **Equilibrio Cromático Sin Neón ni Blanco Estridente:**
  - Ajustada la paleta a carbón mate (`#0B0C0E`, `#121316`, `#191B20`), bordes finos (`#22242B`), texto suave (`#E4E5E9` / `#9499A6` / `#646975`) y botones primarios en índigo pizarra sobrio (`#5664C4`).
- **Diferenciación Elegante por Cliente (`ProfileCard.tsx`, `CreateProfileModal.tsx`, `ProfileDetailModal.tsx`, `Modal.tsx`):**
  - Nueva paleta curada de tonos editoriales desaturados (Acero pizarra, Salvia, Lavanda apagado, Ocre arena, Rosa seco, Azul petróleo, Terracota).
  - Cada tarjeta Kanban y su modal asociado integran el color del cliente con una línea superior sutil de `2px`, un lavado ambiental suave (~7% de opacidad) y etiquetas de tiempo/categoría personalizadas.

### [2026-11-21 00:39] — Ajuste Final: Dark Minimalist sin Neón, Guiones 60–90s y Escaleta Unificada por Sección
- **Dark Minimalist Moderno (Sin Neón):**
  - Reemplazada toda la paleta neón (`#58FF9C` / `#42E686`) por un sistema monocromático oscuro tipo IDE moderno (`#09090B` canvas, `#111114` superficie, `#18181B` elevado, `#27272A` bordes de 1px y `#FAFAFA` texto/acción primaria).
- **Guiones 60–90s y Escaleta Unificada por Sección:**
  - Ajustada la duración objetivo de los guiones a **60–90 segundos** (160–225 palabras habladas en 5 actos) en `gemini_service.py` y `analyzer_service.py`.
  - Agregado `_ensure_unified_timeline` en el backend y `getUnifiedSections` en `ProfileDetailModal.tsx` para garantizar que **cada sección de la escaleta muestre exactamente qué decir en esa sección**, incluso en reportes anteriores.

### [2026-11-21 00:35] — Estética Dark Minimalist, Guiones Virales 30–90s Unificados y 10 Referencias
- **Rediseño Dark Minimalist (`frontend/src/`):**
  - Aplicadas las directrices de `frontend-design` y `ui-ux-pro-max` (*Minimalism & Swiss Style*): eliminados resplandores neón, desenfoques radiales y bordes recargados; jerarquía limpia con `#090A0D`, `#0F1115`, `#161920`, bordes de `1px` (`#1C2029`), `prefers-reduced-motion` y foco visible por teclado.
- **Guiones Virales 30–90s con Hooks y Escaleta Unificada (`gemini_service.py`, `analyzer_service.py`, `ProfileDetailModal.tsx`):**
  - Ampliado el largo objetivo de cada guion a **30–90 segundos** (115–210 palabras habladas en estructura de 5 actos: *Hook → Contexto y Tensión → Re-Hook → Payoff → Remate y CTA*, aplicando arquetipos de `viral-short-form` y ritmo natural de `guion`).
  - Unificada la **Escaleta + Guion Completo** bloque por bloque (`time_range`, `phase`, `on_screen_text`, `description` y `spoken_text`), con análisis explícito de la referencia original y botones para copiar *"escaleta + guion"* o *"solo locución"*.
- **Capacidad de hasta 10 Referencias (`CreateProfileModal.tsx`, `ProfileDetailModal.tsx`, `apify_service.py`, `schemas.py`):**
  - Incrementado el límite de cuentas/Reels de referencia a **10 por cliente**, con edición inline en el modal de detalle y extracción ampliada en Apify (`direct_urls[:10]`, `resultsLimit` dinámico hasta 30).

### [2026-11-12 16:40] — Corrección de `start_local.bat` y Detección Automática de Puertos Libres
- **Corrección de Arranque en `start_local.bat`:**
  - Añadido `cd /d "%~dp0"` para asegurar la ejecución desde la raíz del proyecto incluso al ejecutar como Administrador o desde otra ruta.
  - Reemplazado el lanzamiento de ventanas por `start "..." /D "%~dp0backend"` y `start "..." /D "%~dp0frontend"` para evitar conflictos de comillas anidadas en rutas con espacios y asegurar formato `CRLF`.
- **Detección Dinámica de Puertos Libres (`start_local.bat` + `frontend/vite.config.ts`):**
  - Verificación automática con `netstat` de puertos libres comenzando en `8000` (Backend) y `3000` (Frontend).
  - Sincronización mediante `VITE_PORT` y `VITE_API_PORT` en `frontend/vite.config.ts` para que el proxy `/api` apunte al puerto real asignado al Backend.

### [2026-11-10 02:26] — Lanzamiento v1.1: Renombrado a Social Analyzer y Documentación README.md
- **Renombrado Integral a `Social Analyzer v1.1`:**
  - Actualizada la identidad del producto eliminando "Citi" en toda la interfaz de usuario (`Navbar.tsx`, `LoginView.tsx`, `App.tsx`, `CreateProfileModal.tsx`, `index.html`, `package.json`), en el servidor Backend (`main.py`, `auth.py`, `health.py`, `apify_service.py`) y en el lanzador automático (`start_local.bat`).
- **Documentación Principal (`README.md`):**
  - Creado y actualizado `README.md` para **Social Analyzer v1.1** con insignias de versión, arquitectura del pipeline de 4 fases, novedades de la versión 1.1, guía de instalación, ejecución en 1 clic y tabla de endpoints REST.

### [2026-10-27 14:15] — Fases 4, 5 y 6: Sistema de Diseño "Anti-IA", Interfaz de Usuario y Automatización
- **Sistema de Diseño "Anti-IA" y Paleta Cromática (`frontend/src/index.css`):**
  - Implementación estricta de la paleta editorial Swiss Grid con fondos obsidiana y carbón (`#090A0D`, `#111318`, `#171A21`).
  - Integración del acento verde eléctrico (`#58FF9C`) para focos, bordes activos, botones primarios y badges de alta visibilidad.
  - Tipografías integradas: `Plus Jakarta Sans` para encabezados y `JetBrains Mono` para datos técnicos, métricas, marcas de tiempo y badges.
  - Cuadrícula técnica sutil de fondo (`bg-tech-grid`) y scrollbars minimalistas oscuras.
- **Componentes UI Base (`frontend/src/components/ui/`):**
  - `Button.tsx`: Botones técnicos con variantes `primary` (acento `#58FF9C`), `secondary` y `ghost`, con estados de carga interactivos.
  - `Badge.tsx`: Etiquetas con opacidades sutiles (`12%`) y soporte para colores de clientes personalizados.
  - `Input.tsx`: Campos con iconos integrados y bordes de precisión técnica.
  - `Modal.tsx`: Mini-ventana modal centrada con `backdrop-blur` y animaciones de entrada.
  - `InstagramIcon.tsx`: Componente SVG nativo para evitar dependencias faltantes.
- **Pantalla 1: Login Elegante (`LoginView.tsx`):**
  - Vista de acceso sobria con tarjeta centrada de 1px de borde sobre fondo obsidiana con cuadrícula técnica.
  - Validación de credenciales contra endpoints del backend (`Admin` / `Admin`).
  - Manejo de token de autenticación en `localStorage` con sesión persistente.
- **Pantalla 2: Dashboard Kanban de Perfiles (`DashboardView.tsx`):**
  - **Barra Superior (`Navbar.tsx`):** Nombre "Social Analyzer v1.1", monitor con indicador pulsante verde de conexión de APIs (`/api/health`), botón `+ Nuevo Perfil` y logout.
  - **Tarjetas Cuadradas Kanban (`ProfileCard.tsx`):** Barra superior de 3px con el color del cliente, punto indicador de 8px, badge de categoría en monoespaciada mayúscula, contador de competidores y leyenda dinámica en tiempo real (*"Sin análisis previo"* o *"Último análisis: hace X horas"*).
  - **Buscador y Filtro por Categorías:** Filtrado en memoria instantáneo por nombre de cliente, usuario de Instagram o categoría de negocio.
  - **Estado Vacío (`EmptyState.tsx`):** Recuadro central elegante con borde punteado invitando a registrar el primer cliente.
  - **Modal de Creación (`CreateProfileModal.tsx`):** Formulario modular para nombre, categoría, paleta de colores curada y campo dinámico para múltiples competidores.
- **Pantalla 3: Mini-Ventana Modal de Detalle y Guiones (`ProfileDetailModal.tsx`):**
  - Modal interactivo amplio de alta densidad informativa (ancho `6xl`) sin abandonar la vista principal.
  - Cabecera con enlaces directos a Instagram del cliente y competidores.
  - Stepper de progreso por etapas animado al presionar `Analizar Competencia y Generar Guiones`.
  - Despliegue de los 3 recuadros con las mejores oportunidades de video:
    - **A. Título del Video:** Título magnético adaptado + badge con métrica del Reel original.
    - **B. Escaleta Técnica:** Desglose en bloques de tiempo (`[00:00 - 00:03]` Gancho, `[00:03 - 00:15]` Retención, `[00:15 - 00:30]` CTA).
    - **C. Guion Completo:** Texto redactado adaptado al tono del cliente con botón interactivo de "Copiar Guion" (feedback verde `#58FF9C`).
- **Fase 6: Automatización de Inicio con Un Clic (`start_local.bat`):**
  - Script `.bat` creado en la raíz para Windows:
    - Verifica y crea el entorno virtual `.venv` e instala `requirements.txt`.
    - Verifica `frontend/node_modules` y ejecuta `npm install` si es necesario.
    - Verifica y crea `.env` desde `.env.example`.
    - Lanza FastAPI (8000) y Vite (3000) en ventanas independientes.
    - Abre automáticamente el navegador predeterminado en `http://localhost:3000`.

### [2026-10-27 13:14] — Fase 3: Pipeline de Extracción, Transcripción e IA Adaptativa
- **Normalización Dinámica de Entradas del Usuario (`apify_service.py`):**
  - Implementado `normalize_instagram_input()` para admitir cualquier formato ingresado por el usuario en el formulario (`@usuario`, `usuario`, `https://instagram.com/usuario/`, `https://instagram.com/reel/CODE/`, URLs con query params).
- **Optimización de Recursos y Almacenamiento en Apify:**
  - Configurado `memory_mbytes=256` y `max_items=4` (perfil) y `max_items=9` (reels) para minimizar el consumo de Compute Units (CUs).
  - Implementado mecanismo de **purga inmediata de datasets y runs** (`self.client.dataset(id).delete()` y `self.client.run(id).delete()`) para que las consultas y pruebas consuman **0 bytes de almacenamiento persistente** en la cuenta gratuita de Apify.
- **Optimización de Archivos Temporales en Disco (`media_extractor.py`):**
  - Limpieza atómica con bloque `try...finally` de cualquier archivo generado por `yt-dlp` (`.mp3`, `.m4a`, `.part`, `.ytdl`).
  - Purga automática `purge_all_tmp()` ejecutada al inicio y cierre del servidor FastAPI.
- **Prueba End-to-End con Gemini 3.0 Gratuito (`gemini-3-flash-preview`):**
  - Ejecutado análisis completo y generación validada de 3 propuestas estructuradas.

### [2026-10-27 13:05] — Fase 2: Backend, Modelado ORM y Base de Datos (FastAPI + SQLite)
- **Base de Datos SQLite Local (`./data/citi_analyzer.db`):** Implementado `database.py` con resolución persistente y creación automática de esquemas.
- **Modelos Relacionales (`models.py`):** `Profile`, `AnalysisReport` y `ScriptProposal`.
- **Esquemas Pydantic (`schemas.py`):** Tipado estricto con cálculo en tiempo real (*"Sin análisis previo"*, *"hace Xm"*, *"hace Xh"*).
- **Routers REST (`routers/`):** Autenticación (`/api/auth/login`), CRUD de Perfiles (`/api/profiles`), Monitoreo (`/api/health`) y Disparador de Análisis (`/api/profiles/{id}/analyze`).
- **Punto de Entrada (`main.py`):** Servidor FastAPI con CORS y gestión de ciclo de vida.

### [2026-10-27 12:41] — Fase 1: Inicialización, Entorno e Higiene del Proyecto
- **`.gitignore`:** Creado con reglas estrictas para `.env`, `.venv/`, `node_modules/`, `data/*.db` y `/tmp_media/`.
- **`.env` y `.env.example`:** Configurados con las claves verificadas y modelo `gemini-3-flash-preview`.
- **Verificación en Vivo:** Apify API y Gemini API operativas al 100%.

---

## 3. Estado de Módulos
- [x] **Fase 1:** Inicialización, `.gitignore`, `.env` / `.env.example`, estructura base y validación de APIs.
- [x] **Fase 2:** Backend, Modelado ORM y Base de Datos (FastAPI + SQLite + Endpoints REST).
  - [x] Conexión y migración automática de base de datos (`backend/database.py`).
  - [x] Modelos relacionales ORM (`backend/models.py`).
  - [x] Esquemas Pydantic con tipado estricto (`backend/schemas.py`).
  - [x] Autenticación administrativa (`backend/routers/auth.py`).
  - [x] CRUD de Perfiles y cálculo dinámico de tiempo (`backend/routers/profiles.py`).
  - [x] Monitoreo de APIs y estado del motor (`backend/routers/health.py`).
  - [x] Adaptador Gemini 3.0 gratuito (`backend/services/gemini_service.py`).
  - [x] Extractor Apify de Instagram con fallback seguro (`backend/services/apify_service.py`).
  - [x] Extractor multimedia con `yt-dlp` (`backend/services/media_extractor.py`).
  - [x] Orquestador de análisis (`backend/services/analyzer_service.py`).
- [x] **Fase 3:** Pipeline de Extracción, Transcripción e IA Adaptativa.
  - [x] Normalización dinámica de URLs de Instagram agregadas por el usuario.
  - [x] Purga automática de datasets de Apify tras cada consulta (0 almacenamiento consumido).
  - [x] Purga automática de archivos temporales multimedia en disco (`tmp_media`).
  - [x] Prueba end-to-end con Gemini 3.0 y validación de los 3 guiones estructurados.
  - [x] Base de datos SQLite optimizada y limpia (VACUUM).
- [x] **Fase 4:** Frontend y Sistema de Diseño "Anti-IA" con Acento Verde (`#58FF9C`).
  - [x] Paleta cromática ejecutiva con fondos `#090A0D`, `#111318`, `#171A21` y acento `#58FF9C`.
  - [x] Tipografía `Plus Jakarta Sans` y `JetBrains Mono`.
  - [x] Cuadrícula técnica sutil de fondo y bordes sólidos de 1px.
  - [x] Componentes UI modulares (`Button`, `Badge`, `Input`, `Modal`).
- [x] **Fase 5:** Desarrollo de Pantallas e Interacciones UI.
  - [x] Pantalla 1: Login sobrio centrado (`/login`) con credenciales `Admin` / `Admin`.
  - [x] Pantalla 2: Dashboard Kanban con tarjetas cuadradas proporcionales y buscador/filtro.
  - [x] Modal de creación de clientes con soporte dinámico para URLs de competidores.
  - [x] Pantalla 3: Mini-ventana modal de 6xl con stepper en tiempo real y 3 guiones completos (escaleta + guion literal + botón de copiado).
- [x] **Fase 6:** Script de Inicio Automático (`start_local.bat`) y Entrega Final.
  - [x] Script `start_local.bat` listo para Windows con verificación automática de dependencias y apertura en navegador.

---

## 4. Guía de Uso Local Rápido
1. **Inicio en 1 Clic:** Haz doble clic sobre [start_local.bat](file:///c:/Users/uriel/Vibe%20coding/Proyectos/Analizador%20de%20redes/start_local.bat) en la raíz del proyecto.
2. **Acceso Web:** Navega a `http://localhost:3000`.
3. **Credenciales:**
   - **Usuario:** `Admin`
   - **Contraseña:** `Admin`
4. **Flujo de Trabajo:**
   - Presiona `+ Nuevo Perfil` en la barra superior.
   - Ingresa el nombre de la marca, categoría, selecciona un color, coloca el Instagram del cliente y añade las URLs de sus competidores.
   - Haz clic sobre la tarjeta creada en el tablero Kanban.
   - Presiona `Analizar Competencia y Generar Guiones` para recibir las 3 propuestas estructuradas.

---

## 5. Guía de Escalado a Producción
1. **Base de Datos:** Reemplazar `DATABASE_URL=sqlite:///./data/citi_analyzer.db` en `.env` por una cadena de conexión PostgreSQL (ej. Supabase o Neon: `postgresql://user:pass@host:5432/dbname`) e instalar `psycopg2-binary`.
2. **Backend (FastAPI):** Desplegar el directorio `/backend` en Railway, Render o Fly.io configurando el comando de inicio `uvicorn main:app --host 0.0.0.0 --port $PORT` y asegurando que `ffmpeg` esté disponible en el contenedor si se procesa audio con `yt-dlp`.
3. **Frontend:** Desplegar `/frontend` en Vercel o Cloudflare Pages apuntando `NEXT_PUBLIC_API_URL` al dominio HTTPS del backend en producción.
4. **Seguridad:** Cambiar `ADMIN_USER`, `ADMIN_PASS` y `APP_SECRET_KEY` por valores de alta entropía en las variables de entorno del servidor.
