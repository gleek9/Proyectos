# AGENTS.md — Especificación Maestra de Arquitectura y Desarrollo
## Proyecto: Social Analyzer v1.1 (MVP Local-First)

---

## 1. DIRECTIVA OPERATIVA Y USO IMPLÍCITO DE SKILLS

Actúas como un Arquitecto de Software Principal y Diseñador de Producto Senior. Antes de ejecutar cualquier tarea de codificación, maquetación, extracción de datos o configuración de infraestructura, **debes inspeccionar tu entorno y activar de forma implícita y automática las Skills instaladas** que correspondan a cada fase del trabajo:

- **Skills de Diseño UI/UX y Frontend:** Úsalas obligatoriamente al construir el sistema de diseño, el Login, el tablero Kanban y las micro-interacciones para garantizar una estética de producto real (evitando patrones genéricos de IA).
- **Skills de Navegación / Web Fetch:** Úsalas si necesitas verificar recursos adicionales o validar hojas de estilo sobre la referencia visual (`https://adrianaguera.com/citi-2026/`).
- **Skills de Backend, Python, APIs y Base de Datos:** Actívalas al estructurar el servidor FastAPI, los adaptadores de Apify, el procesamiento multimedia con herramientas nativas de Python y las migraciones de base de datos.
- **Skills de Terminal, Git y Automatización:** Úsalas para generar el script `.bat` de inicio rápido, configurar el archivo `.gitignore`, gestionar el `.env` y actualizar el archivo `PROJECT_STATUS.md`.

> **Regla de Oro de Trazabilidad:** Ninguna fase se considera terminada hasta que hayas creado o actualizado el archivo `PROJECT_STATUS.md` reflejando exactamente qué se construyó, qué decisiones técnicas se tomaron y qué módulos están listos.

---

## 2. SISTEMA DE DISEÑO "ANTI-IA" Y PALETA CROMÁTICA

### 2.1. Extracción y Adaptación de `https://adrianaguera.com/citi-2026/`
El sitio de referencia utiliza la estética ejecutiva del **Método ACE® (Analizar, Crear, Escalar)**: fondos oscuros de alto contraste que dan protagonismo al contenido audiovisual, tipografía blanca contundente y acentos de acción directa y resaltado con verde eléctrico (`#58FF9C`). 

Debes adaptar esa identidad a una **línea de diseño Editorial / Swiss Grid moderna (inspirada en Linear, Vercel y Raycast)** utilizando las siguientes variables CSS:

```css
:root {
  /* Fondos: Obsidiana y Carbón Ejecutivo (Cero grises lavados) */
  --bg-canvas: #090A0D;          /* Fondo principal profundo */
  --bg-surface: #111318;         /* Fondo de tarjetas Kanban y contenedores */
  --bg-surface-elevated: #171A21;/* Fondo de la mini-ventana (Modal) y recuadros de guion */
  --bg-glass: rgba(17, 19, 24, 0.82);

  /* Textos: Jerarquía de Alto Contraste */
  --text-primary: #F8FAFC;       /* Blanco nítido para títulos y guiones */
  --text-secondary: #94A3B8;     /* Gris pizarra técnico para subtítulos y escaletas */
  --text-muted: #64748B;         /* Metadatos y leyendas de tiempo ("Hace X horas") */

  /* Acentos de Resaltado: Verde Eléctrico (Sustituye al azul en focos y resaltados) */
  --accent-primary: #58FF9C;     /* Verde eléctrico de alto impacto para resaltados, llamadas a la acción y botones */
  --accent-hover: #42E686;       /* Verde activo refinado */
  --accent-subtle: rgba(88, 255, 156, 0.12); /* Resaltado sutil en badges, bordes y fondos técnicos */
  --accent-glow: rgba(88, 255, 156, 0.25);   /* Resplandor sutil técnico para elementos activos y foco */

  /* Bordes y Divisores: Precisión Técnica */
  --border-subtle: #1E222B;      /* Bordes de 1px nítidos */
  --border-focus: #58FF9C;       /* Borde activo en verde de alta visibilidad */
}
```

### 2.2. Reglas Estrictas de Diseño "Anti-IA" (Lo que está PROHIBIDO y lo que es OBLIGATORIO)

Para que la aplicación jamás parezca generada por una IA genérica, aplica estas restricciones:

1. **PROHIBIDO:** Gradientes neón violeta/rosa/cian (`from-purple-500 to-pink-500`), sombras resplandecientes exageradas, abuso de emojis en botones o títulos, tarjetas con bordes excesivamente redondeados (`rounded-3xl`) y textos de relleno falsos.
2. **OBLIGATORIO:**
   * **Bordes Técnicos:** Usa bordes sólidos de `1px` (`border-[#1E222B]`) y radios de esquina contenidos (`rounded-lg` o `rounded-xl`, máximo `8px` a `12px`).
   * **Tipografía con Carácter:** Usa `Plus Jakarta Sans` o `Inter` con `tracking-tight` para encabezados, y **obligatoriamente una fuente monoespaciada (`JetBrains Mono` o `Geist Mono`)** para las etiquetas de categoría, contadores de tiempo (*"hace 4h"*), métricas de viralidad y tiempos de la escaleta (`00:00 - 00:03`).
   * **Indicadores de Color de Perfil:** El color representativo de cada cliente no debe pintar toda la tarjeta de forma chillona; debe aplicarse con elegancia como una barra lateral de `3px`, un punto indicador (`dot` de `8px`) junto al nombre y un *badge* con opacidad al `12%`.

---

## 3. ARQUITECTURA TÉCNICA (LOCAL-FIRST Y LISTA PARA ESCALAR)

El sistema debe ejecutarse **100% en local (`localhost`)** sin depender de servidores externos de base de datos durante el prototipo, pero con una arquitectura desacoplada lista para subir a un VPS o plataforma Cloud en minutos.

* **Frontend:** Next.js (App Router) o React + Vite con Tailwind CSS y Lucide Icons (trazo fino `strokeWidth={1.5}`).
* **Backend:** Python 3.11+ con **FastAPI** (asíncrono, tipado estricto con Pydantic).
* **Base de Datos:** **SQLite local (`./data/citi_analyzer.db`)** gestionada mediante **SQLAlchemy ORM**. La cadena de conexión debe leerse desde `DATABASE_URL` en el archivo `.env` para que al pasar a producción baste con cambiarla por una URL de PostgreSQL/Supabase sin tocar el código.
* **Caché Inteligente:** Cada análisis se guarda en la base de datos local junto con su *timestamp* (`last_analyzed_at`). Así las consultas son instantáneas y no se desperdician créditos de API al abrir y cerrar un perfil.

---

## 4. FLUJO DE USUARIO Y ESPECIFICACIONES DE INTERFAZ

### 4.1. Pantalla 1: Login Elegante (`/login`)

* Diseño centrado, minimalista, con fondo `--bg-canvas` y una sutil cuadrícula técnica de fondo.
* Tarjeta de acceso sobria con bordes de `1px`, logotipo tipográfico limpio y campos de **Usuario** y **Contraseña**.
* **Credenciales de acceso:**
  * **Usuario:** `Admin`
  * **Contraseña:** `Admin`
  *(Validadas contra variables de entorno `ADMIN_USER=Admin` y `ADMIN_PASS=Admin` en el `.env`).*

### 4.2. Pantalla 2: Dashboard Tipo Kanban de Perfiles (`/dashboard`)

Una vez autenticado, el usuario accede al panel principal de **Social Analyzer**:

* **Barra Superior:** Nombre de la aplicación (**Social Analyzer**), estado del motor (indicador verde de conexión con APIs) y botón primario **`+ Nuevo Perfil`**.
* **Estado Vacío (Empty State):** Si no existen perfiles registrados, muestra un recuadro central elegante con borde punteado invitando a crear el primer perfil de cliente.
* **Formulario de Creación de Perfil (Modal / Drawer):**
  Solicita exactamente los siguientes datos:
  1. **Nombre del Cliente / Marca** (ej. *Inmobiliaria Domus*).
  2. **Categoría de Negocio** (ej. *Bienes Raíces, Gastronomía, Salud, E-commerce*).
  3. **Color Representativo** (Selector de color Hex o paleta curada).
  4. **URL de Instagram del Cliente** (Para que la IA analice su contenido actual, propuesta de valor y tono de comunicación).
  5. **URLs de Instagram de Competidores** (Campo dinámico para agregar las URLs de los competidores necesarios cuyos Reels virales serán analizados).

### 4.3. Tarjetas Cuadradas Tipo Kanban (Vista de Perfiles Guardados)

Cada perfil guardado se renderiza en el grid del dashboard como un **cuadrado modular tipo Kanban** con proporción equilibrada y efecto `hover` sutil en el borde:

* **Indicador de Color Representativo:** Barra superior o lateral con el color elegido por el usuario.
* **Badge de Categoría de Negocio:** En fuente monoespaciada y mayúsculas pequeñas (`text-xs uppercase tracking-wider`).
* **Nombre del Cliente:** Tipografía limpia y prominente.
* **Contador de Competidores:** Indicador discreto (ej. `3 competidores vinculados`).
* **Leyenda Dinámica de Tiempo:** En la parte inferior del cuadrado, calculada en tiempo real:
  * Si nunca se ha ejecutado: `"Sin análisis previo"`
  * Si ya se analizó: `"Último análisis: hace X horas"` (o minutos/días según corresponda).

### 4.4. Mini-Ventana de Perfil y Generador de 3 Guiones (Modal Interactivo)

Al hacer clic sobre cualquier cuadrado Kanban de un perfil, **NO se navega a otra página**; se abre una **mini-ventana (Modal centrado amplio de alta densidad informativa)** que contiene:

1. **Cabecera de la Mini-Ventana:** Nombre del perfil, categoría, color representativo, enlace al perfil del cliente, etiquetas de sus competidores y el botón de acción principal: **`Analizar Competencia y Generar Guiones`**.
2. **Área de Resultados (Los 3 Recuadros de Guiones):**
  * Si el perfil ya cuenta con un análisis guardado, muestra inmediatamente los 3 recuadros (y el botón permite *"Actualizar Análisis"*).
  * Al presionar **`Analizar`**, muestra un indicador de progreso por etapas (*"1. Analizando voz del cliente -> 2. Extrayendo Reels virales vía Apify -> 3. Procesando transcripciones con Python -> 4. Adaptando 3 guiones"*).
  * Al finalizar, despliega dentro de la misma mini-ventana **3 recuadros (columnas o tarjetas expandibles)** correspondientes a las **3 mejores oportunidades de video** detectadas en su competencia.
  * **Contenido obligatorio de cada uno de los 3 recuadros:**
    * **A. Título del Video:** Título magnético adaptado al cliente + badge con la métrica de viralidad del Reel original de la competencia que inspiró la idea (ej. *Inspirado en Reel de @competidor con 145K vistas*).
    * **B. Escaleta (Estructura Técnica):** Desglose paso a paso por bloques de tiempo (`[00:00 - 00:03] Gancho Visual y Auditivo`, `[00:03 - 00:15] Retención / Desarrollo`, `[00:15 - 00:30] Resolución y CTA`).
    * **C. Guion Completo Adaptado:** El texto literal palabra por palabra listo para leer/grabar, adaptado al tono, categoría y estilo que la IA detectó en la cuenta del propio cliente, con botón de *"Copiar Guion"*.

---

## 5. PIPELINE DE EXTRACCIÓN E INTELIGENCIA ARTIFICIAL

El backend en Python (`FastAPI`) debe orquestar el análisis combinando **exclusivamente la API de Apify** para el descubrimiento de datos de Instagram con **herramientas nativas de Python** para el procesamiento profundo de los videos virales:

1. **Fase 1: Radiografía del Cliente (Apify API)**
   * Utiliza `apify-client` invocando el Actor de Instagram (`apify/instagram-scraper` o `apify/instagram-profile-scraper`) sobre la **URL del Cliente**.
   * Extrae biografía y las últimas publicaciones para sintetizar el *Brand Voice Profile* (cómo habla el cliente, qué vende y a quién se dirige).

2. **Fase 2: Caza de Virales de la Competencia (Apify API + Filtro Python)**
   * Consulta mediante Apify las URLs de los **Competidores** configurados en el perfil.
   * Un módulo en Python filtra únicamente los Reels/Videos, calcula su puntuación de viralidad (`videoViewCount`, `likesCount`, `commentsCount`) y selecciona el **Top 3 de Reels más virales**.

3. **Fase 3: Extracción de Texto y Audio con Herramientas Python (`yt-dlp` + Transcripción)**
   * Para cada uno de los 3 Reels ganadores, el servicio de Python toma el `videoUrl` o `url` del Reel y utiliza **`yt-dlp`** (en memoria o carpeta temporal `/tmp` auto-limpiable) junto con los metadatos/subtítulos extraídos para obtener el audio o texto hablado real del video.
   * Envía el audio o video al motor de Gemini Multimodal (vía `GEMINI_API_KEY`) para obtener la transcripción exacta de lo que dice el competidor de manera directa y sin depender de servicios externos.

4. **Fase 4: Ingeniería Inversa y Creación de los 3 Informes (LLM)**
   * El LLM recibe el *Brand Voice Profile* del cliente + las 3 transcripciones virales de la competencia.
   * Devuelve un objeto JSON validado estrictamente con Pydantic que contiene las **3 propuestas**, cada una con su `titulo`, `escaleta` (lista de bloques temporales y visuales) y `guion_completo`.
   * Se guarda en SQLite y se actualiza el campo `last_analyzed_at` del perfil para refrescar la leyenda *"Hace X horas"* en el Kanban.

---

## 6. CONFIGURACIÓN `.ENV`, `.GITIGNORE`, SCRIPT `.BAT` Y `PROJECT_STATUS.md`

### 6.1. Variables de Entorno (`.env` y `.env.example`)

Ninguna credencial o clave puede estar escrita directamente en el código fuente. Todas las APIs y accesos deben leerse desde un archivo `.env` en la raíz:

```env
# Credenciales de Acceso Web
ADMIN_USER=Admin
ADMIN_PASS=Admin
APP_SECRET_KEY=local_dev_secret_key_change_in_prod

# API de Extracción (Única API de Scraping Permitida)
APIFY_API_TOKEN=tu_token_de_apify_aqui

# APIs de Inteligencia Artificial y Transcripción Multimodal (Gemini 3.0 Gratuito)
GEMINI_API_KEY=tu_api_key_de_google_ai_studio_aqui
GEMINI_MODEL=gemini-3-flash-preview

# Base de Datos y Entorno (SQLite local por defecto, lista para Postgres en la nube)
DATABASE_URL=sqlite:///./data/citi_analyzer.db
BACKEND_PORT=8000
FRONTEND_PORT=3000
NEXT_PUBLIC_API_URL=http://localhost:8000
```

### 6.2. Automatización de Inicio con Un Clic (`start_local.bat`)

Debes crear en la raíz del proyecto un archivo **`start_local.bat`** para Windows que permita levantar todo el entorno local sin usar comandos manuales:

* Verifica si existe el entorno virtual de Python (`.venv`); si no existe, lo crea e instala `requirements.txt`.
* Verifica si existe `node_modules` en el frontend; si no existe, ejecuta `npm install`.
* Verifica si existe el archivo `.env`; si no existe, copia `.env.example` a `.env`.
* Inicia el servidor Backend (`uvicorn`) y el servidor Frontend en procesos locales optimizados.
* Abre automáticamente el navegador predeterminado en `http://localhost:3000`.

### 6.3. Archivo `.gitignore` Obligatorio

Genera desde el primer minuto un archivo `.gitignore` en la raíz que excluya rigurosamente:

* `.env` y `.env.*` (excepto `.env.example`)
* `.venv/`, `venv/`, `__pycache__/`, `*.pyc`
* `node_modules/`, `.next/`, `dist/`, `build/`
* `*.db`, `*.sqlite`, `*.sqlite3`, `/data/*.db`
* `/tmp_media/`, `*.mp4`, `*.mp3`, `*.wav`, `*.m4a` (archivos temporales de extracción de `yt-dlp`)

### 6.4. Archivo de Control `PROJECT_STATUS.md`

Debes crear y mantener actualizado el archivo **`PROJECT_STATUS.md`** en la raíz del proyecto con la siguiente estructura:

1. **Estado General del Proyecto:** Porcentaje de avance y versión actual.
2. **Registro de Cambios (Changelog):** Fecha, hora y descripción técnica de cada componente creado o modificado.
3. **Estado de Módulos:** Checklist `[x]` / `[ ]` para Login, Dashboard Kanban, Modal de Análisis, Integración Apify, Extractor Python (`yt-dlp`), Adaptador IA y Script `.bat`.
4. **Guía de Escalado a Producción:** Pasos listos para cuando el proyecto pase de `localhost` al servidor web definitivo.

---

## 7. FASES DETALLADAS PARA LA CONSTRUCCIÓN DE LA APLICACIÓN WEB

Ejecuta la construcción de la aplicación siguiendo estrictamente estas fases ordenadas y sin detenerte a pedir confirmación en pasos intermedios:

### Fase 1: Inicialización, Entorno e Higiene del Proyecto
* [ ] Crear `.gitignore` en la raíz excluyendo `.env`, `.env.*` (excepto `.env.example`), `.venv/`, `node_modules/`, `.next/`, `dist/`, bases de datos SQLite (`*.db`, `*.sqlite`, `/data/*.db`) y archivos temporales multimedia (`/tmp_media/`, `*.mp4`, `*.mp3`).
* [ ] Crear `.env.example` y generar `.env` con credenciales por defecto (`ADMIN_USER=Admin`, `ADMIN_PASS=Admin`, `DATABASE_URL=sqlite:///./data/citi_analyzer.db`, puertos `8000` y `3000`).
* [ ] Crear la estructura de directorios del proyecto:
  * `/backend`: Servidor FastAPI, controladores, servicios, modelos ORM y schemas.
  * `/frontend`: Aplicación cliente React/Vite o Next.js, componentes modulares, hooks y configuración de diseño.
  * `/data`: Directorio local para la base de datos persistente SQLite.
* [ ] Crear la versión inicial de `PROJECT_STATUS.md` para documentar la trazabilidad, avance porcentual y estado de los módulos.

### Fase 2: Backend, Modelado ORM y Base de Datos (FastAPI + SQLite)
* [ ] Definir `requirements.txt` en `/backend` con dependencias requeridas (`fastapi`, `uvicorn`, `sqlalchemy`, `pydantic`, `python-dotenv`, `apify-client`, `yt-dlp`, `requests`, `google-generativeai`).
* [ ] Configurar conexión a la base de datos local mediante SQLAlchemy con fallback automático para crear la base de datos en `./data/citi_analyzer.db`.
* [ ] Implementar modelos relacionales en `models.py`:
  * **Profile:** `id`, `client_name`, `category`, `representative_color`, `client_instagram_url`, `competitor_urls` (JSON), `created_at`, `last_analyzed_at`.
  * **AnalysisReport:** `id`, `profile_id`, `created_at`, `summary`.
  * **ScriptProposal:** `id`, `report_id`, `title`, `competitor_source_info`, `virality_badge`, `escalation_timeline` (JSON), `full_script`, `created_at`.
* [ ] Definir schemas Pydantic con tipado estricto en `schemas.py` para validación de entrada/salida.
* [ ] Implementar routers y endpoints REST en `/api`:
  * `POST /api/auth/login`: Validación de credenciales contra variables de entorno (`Admin`/`Admin`) y entrega de token/sesión.
  * `GET /api/profiles`: Lista de todos los perfiles guardados, incluyendo cálculo de tiempo transcurrido desde el último análisis.
  * `POST /api/profiles`: Creación de un nuevo perfil con cliente, categoría, color y lista de competidores.
  * `GET /api/profiles/{id}`: Detalle completo de un perfil y sus 3 últimos guiones generados.
  * `DELETE /api/profiles/{id}`: Eliminación de un perfil.
  * `POST /api/profiles/{id}/analyze`: Endpoint disparador del pipeline de análisis y generación de guiones.

### Fase 3: Pipeline de Extracción, Transcripción e IA Adaptativa
* [ ] **Servicio Apify (`services/apify_service.py`):**
  * Conexión con `apify-client` usando `APIFY_API_TOKEN`.
  * Extracción de bio y últimas publicaciones de la cuenta del cliente para definir el *Brand Voice Profile*.
  * Extracción de publicaciones y Reels de las cuentas competidoras, cálculo de métricas de interacción (`views`, `likes`, `comments`) y selección del Top 3 de Reels más virales.
  * Mecanismo de fallback seguro con datos de prueba estructurados en caso de que la clave de Apify no esté ingresada o esté temporalmente agotada.
* [ ] **Servicio de Extracción Multimedia (`services/media_extractor.py`):**
  * Integración con `yt-dlp` en Python para descargar y extraer audio o pistas de subtítulos en una carpeta temporal con purga automática posterior.
* [ ] **Servicio de Inteligencia Artificial (`services/ai_service.py`):**
  * Conexión con Gemini 3.0 Gratuito (`gemini-3-flash-preview` con fallback a `gemini-2.5-flash`) para transcripción directa de audio y comprensión de video sin requerir APIs adicionales de terceros.
  * Generación de las 3 propuestas estructuradas mediante prompting especializado de ingeniería inversa de contenido viral, devolviendo Título magnético, Escaleta desglosada por segundos y Guion completo adaptado a la voz del cliente.
  * Guardado automático en SQLite y actualización de `last_analyzed_at`.

### Fase 4: Frontend y Sistema de Diseño "Anti-IA" con Acento Verde (`#58FF9C`)
* [ ] Inicializar la aplicación Frontend con Tailwind CSS y Lucide Icons (`strokeWidth={1.5}`).
* [ ] Configurar variables CSS en `index.css` o `globals.css` integrando fondos carbón (`#090A0D`, `#111318`, `#171A21`), textos de alto contraste y el acento de resaltado verde eléctrico (`#58FF9C` / `--accent-primary`, `--border-focus`, `--accent-subtle`).
* [ ] Importar fuentes tipográficas: `Plus Jakarta Sans` o `Inter` para titulares y `JetBrains Mono` para datos técnicos, badges de categorías, métricas y marcas de tiempo de escaleta.
* [ ] Crear componentes base reutilizables: botones, inputs, badges con micro-opacidad, tarjetas modulares y contenedores con bordes técnicos de 1px.

### Fase 5: Desarrollo de Pantallas e Interacciones UI
* [ ] **Pantalla 1: Login Elegante (`/login`):**
  * Diseño centrado sobre fondo obsidiana con cuadrícula técnica sutil.
  * Formulario sobrio con validación de credenciales (`Admin`/`Admin`) y redirección inmediata al dashboard.
* [ ] **Pantalla 2: Dashboard Kanban de Perfiles (`/dashboard`):**
  * Barra superior con logotipo "Social Analyzer", monitor de estado de APIs (indicador verde pulsante) y botón primario destacado con acento `#58FF9C` (`+ Nuevo Perfil`).
  * Estado vacío (Empty State) con contenedor punteado elegante cuando no existan clientes registrados.
  * Cuadrícula modular de tarjetas cuadradas tipo Kanban:
    * Borde superior/lateral de 3px con el color representativo del cliente.
    * Badge de categoría en monoespaciada mayúscula pequeña.
    * Nombre de cliente nítido y contador de competidores.
    * Leyenda dinámica de tiempo en pie de tarjeta (*"Sin análisis previo"* o *"Último análisis: hace X horas/minutos"*).
  * Modal/Drawer para crear perfil: formulario con nombre, categoría, selector de color, URL de Instagram del cliente y lista dinámica de URLs de competidores con validación.
* [ ] **Pantalla 3: Mini-Ventana Modal de Perfil y Generador de 3 Guiones:**
  * Modal interactivo amplio de alta densidad informativa (no navega fuera de la vista).
  * Cabecera con datos del perfil, enlaces directos a Instagram y botón primario: `Analizar Competencia y Generar Guiones` (con hover y foco en `#58FF9C`).
  * Stepper o barra de progreso por etapas (*"1. Radiografía del cliente -> 2. Caza de virales -> 3. Transcripción de audio -> 4. Adaptación de guiones"*).
  * Despliegue de los 3 recuadros con las oportunidades virales:
    * **A. Título del Video:** Título adaptado + badge con métrica del Reel original.
    * **B. Escaleta Técnica:** Desglose en bloques de tiempo (`[00:00 - 00:03] Gancho`, `[00:03 - 00:15] Retención`, `[00:15 - 00:30] CTA`).
    * **C. Guion Completo:** Texto literal listo para grabar + botón de *"Copiar Guion"* con feedback interactivo en verde `#58FF9C`.

### Fase 6: Automatización de Inicio con Un Clic y Control de Calidad
* [ ] Crear el script **`start_local.bat`** en la raíz para Windows:
  * Verificación y creación de `.venv` con instalación de dependencias en `requirements.txt`.
  * Verificación de `node_modules` con ejecución automática de `npm install`.
  * Verificación de `.env` (creación desde `.env.example` si falta).
  * Lanzamiento concurrente y optimizado de FastAPI (puerto 8000) y Frontend (puerto 3000).
  * Apertura automática del navegador predeterminado en `http://localhost:3000`.
* [ ] Pruebas end-to-end de comunicación entre frontend y backend sin advertencias de CORS.
* [ ] Actualización final de **`PROJECT_STATUS.md`** reflejando 100% de los módulos operativos y guía de uso.
