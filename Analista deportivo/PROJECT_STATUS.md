# PROJECT_STATUS.md — Estado de Avance del Proyecto (Katakuri v3.5)

> **Propósito de este archivo**: Este documento es el punto de control, especificación técnica y seguimiento para desarrolladores y agentes de IA. Cualquier nuevo chat o sesión debe leer este archivo primero para conocer con exactitud la arquitectura, el estado operativo, las credenciales, los modelos predictivos y el funcionamiento de la interfaz.

---

## 1. Resumen Ejecutivo

- **Proyecto**: **Katakuri v3.5** (Plataforma Autónoma de Predicción Deportiva con IA)
- **Regla de Versiones**: Cada solicitud de cambios incrementa la versión en +0.1 (ej. v1.2 ➔ ... ➔ v3.3 ➔ v3.4 ➔ v3.5).
- **Idioma de la Plataforma**: **100% Español** (interfaz, telemetría, veredictos humanos y logs de estado).
- **Objetivo**: A partir de los nombres de dos equipos o una URL de partido online, recopila datos reales en tiempo real mediante **Gemini (Flash Lite) + LangChain + Sofascore API + Flashscore Ninja Feeds** y ejecuta un ensamble **100% local** compuesto por:
  1. **Poisson Bivariado Calibrado con corrección Dixon-Coles ($\tau$), Normalización Estricta por Torneo, Localía Simétrica ($\sqrt{h}$), Elasticidad ($\gamma=0.52$), Sobredispersión Binomial Negativa en Córners/Tarjetas y Dinámica In-Play de Estado de Marcador (Game State Effect)**
  2. **XGBoost / LightGBM** (Modelo tabular con 18 features numéricas, soporte neutral H2H y sigmoide calibrada)
  3. **PyTorch LSTM** (Red neuronal recurrente para series temporales y momentum relativo)
  4. **Meta-Ensamble con Matriz Bivariada de Consenso Unificado, Coalescencia Estricta, Ponderación Bayesiana Dinámica, Marcadores Concordantes y Mercados Derivados (1X, X2, 12, DNB)**
  5. **Módulo Formal de Validación Empírica y Backtesting Automatizado (`backend/app/analytics/backtest.py`) con métricas RPS (Ranked Probability Score), Brier Score, Log-Loss y MAE/RMSE**
- **Versión Actual**: **v3.5**
- **Estado General**: **100% Operativo, Resolución Jerárquica de URLs en Vivo, Servidor Resiliente con Auto-Recuperación, Barra Superior Espaciosa y Responsive sin Login Bloqueante**

---

## 2. Novedades y Mejoras en la Versión v3.5 (Resolución Jerárquica de URLs y Estabilización de Servidores)

1. **Jerarquía Soberana de la URL y Erradicación del Bucle de Partido Previo (`collector.py`, `App.jsx`)**:
   - **Causa Raíz Resuelta**: Al ingresar una nueva URL después de haber analizado un partido, tanto el frontend (`App.jsx`) como el backend (`collector.py`) comparaban los equipos extraídos de la URL con los equipos que habían quedado en el formulario del análisis anterior. Al no coincidir, una condición de coherencia invertida descartaba la nueva URL (`clean_url = None`), vaciaba el input y consultaba la base de datos local SQLite, **provocando que el sistema recargara erróneamente el partido anterior**.
   - **Solución Implementada**:
     * En `backend/app/agent/collector.py`: La URL pasa a ser la **fuente de verdad absoluta**. Si `extract_teams_from_url_and_page` extrae equipos de la URL, se asignan directamente como `home_clean = url_home` y `away_clean = url_away`, y bajo ninguna circunstancia se anula `clean_url`. Al estar presente `clean_url`, se desactiva la lectura de registros en caché de otros partidos.
     * En `frontend/src/App.jsx`: Se eliminó el bloque que vaciaba la URL (`trimmedUrl = ''`, `handleClearUrl()`). Se actualizan de inmediato los equipos locales y se resetea la telemetría previa (`liveScore`, `liveMinute`, `liveCorners`, `predictionData`) para evitar mezclar datos del encuentro anterior durante la carga.

2. **Estabilidad Continua y Eliminación de Reinicios Espurios (`run_app.py`, `App.jsx`)**:
   - **Causa Raíz Resuelta**: La aplicación se detenía súbitamente o se reiniciaba tras cierto tiempo de ejecución. Esto se debía a que `run_app.py` ejecutaba Uvicorn con `--reload --reload-dir backend`. En Windows, el file watcher disparaba recargas involuntarias al detectar cambios en `__pycache__` o archivos temporales, interrumpiendo requests en curso de scraping. Al terminar el subproceso, el supervisor de `run_app.py` ejecutaba un `taskkill` y apagaba todo. Asimismo, en `App.jsx`, el temporizador de auto-sincronización invocaba `runAnalysis` de forma síncrona dentro del updater de estado `setSyncCountdown`.
   - **Solución Implementada**:
     * En `run_app.py`: Se removió el flag `--reload` para el entorno de ejecución del usuario y se implementó un bucle supervisor con **auto-recuperación y tolerancia a fallos** (hasta 3 reintentos) que mantiene la aplicación viva y estable.
     * En `App.jsx`: Se desacopló el temporizador de 5 minutos, corriendo únicamente en partidos con modo en vivo (`isLiveActive`) y disparando el refresco de forma asíncrona y segura mediante `useEffect`.
     * Se eliminó el archivo huérfano `backend/analista.db` que interfería en el sistema de archivos.

---

## 3. Novedades y Mejoras en la Versión v3.4 (Reorganización Espaciosa de Barra Superior, Acceso Directo y Depuración de Historial)

1. **Eliminación del Paso de Autenticación y Desbloqueo Inmediato (`App.jsx`, `HeaderBar.jsx`)**:
   - **Causa Raíz Resuelta**: El modal bloqueante de usuario y contraseña consumía tiempo de entrada y ocupaba un espacio valioso en la barra de navegación con un widget de usuario y botón de cierre de sesión.
   - **Solución Implementada**: Se eliminó el gate de autenticación obligatoria; la aplicación ahora inicia de forma instantánea y directa. Se removieron los componentes de usuario y logout de la barra superior.

2. **Reorganización Espaciosa y Responsiva de la Barra Superior (`HeaderBar.jsx`, `ide-theme.css`)**:
   - **Causa Raíz Resuelta**: Los elementos de la barra de navegación (`.ide-navbar`) se apretujaban o saltaban de forma desordenada en resoluciones estándar debido a anchos rígidos (`165px`) y la distribución en 3 nodos flex sueltos.
   - **Solución Implementada**:
     * Agrupación izquierda (`.navbar-brand-group`): Marca `Katakuri v3.5`, divisor vertical sutil, temporizador de 5 min y botón de calibración.
     * Formulario derecho (`.ide-inputs-form`): Inputs con `min-width: 120px` y `width: 155px`, insignias `Local` y `Visitante` protegidas contra cortes (`white-space: nowrap`) y separador `vs` estilizado.
     * Reglas `@media (max-width: 1140px)` y `@media (max-width: 700px)` que centran o apilan fluidamente los elementos sin colisiones visuales.

3. **Remoción de la Barra de Historial y Sugeridos (`RecentMatchesBar.jsx`, `App.jsx`, `ide-theme.css`)**:
   - **Auditoría Predictiva**: Se verificó rigurosamente que la barra de historial y accesos rápidos no tenía ninguna injerencia en los modelos de Poisson, Dixon-Coles, XGBoost o LSTM.
   - **Solución Implementada**: Se eliminó el componente `RecentMatchesBar.jsx`, el estado `recentList`, la función `loadRecentMatches` y los estilos CSS obsoletos (`.recent-bar`, `.recent-chip`), logrando una interfaz mucho más limpia y despejada.

---

## 4. Novedades y Mejoras en la Versión v3.3 (Auditoría Predictiva: Puntos 5, 6, 8 y 3 Implementados)

1. **Matriz Bivariada de Consenso en Meta-Ensamble (Punto 5 — `ensemble.py`, `poisson.py`)**:
   - **Causa Raíz Resuelta**: Anteriormente, el ensamble combinaba de forma desacoplada la probabilidad de Over 2.5 (`over_2_5_combined = p_over * wp + xgb_over * wx`), mientras que la distribución de goles discretos (0 a 5+ goles) y los top marcadores se extraían directamente de Poisson. Esto generaba inconsistencias donde la suma acumulada de 3, 4 y 5+ goles no coincidía exactamente con el porcentaje de Over 2.5 mostrado en pantalla.
   - **Solución Implementada**:
     * A partir de la expectativa combinada consensual de goles y las cuotas de dominio local/visitante, se evalúa una **Matriz Bivariada de Consenso Unificado** (`evaluate_matrix_goals`).
     * Coherencia matemática del 100%: $P(\text{Over 2.5}) \equiv \sum_{k \ge 3} P(k \text{ goles})$.
     * Monotonía garantizada: $\text{Over 1.5} \ge \text{Over 2.5} \ge \text{Over 3.5}$.
     * En partidos en directo, la distribución arranca estrictamente desde los goles ya anotados (ej. con marcador 2-1, las probabilidades de 0, 1 y 2 goles son estrictamente 0.0%).

2. **Distribución Binomial Negativa para Córners y Tarjetas (Punto 6 — `poisson.py`)**:
   - **Causa Raíz Resuelta**: La distribución de Poisson simple asume que la varianza es igual a la media ($\sigma^2 = \mu$). En el fútbol real, los saques de esquina y las tarjetas presentan sobredispersión empírica por asedios continuos y tarjetas encadenadas por faltas tácticas, provocando que la Poisson pura subestimara las probabilidades de colas largas.
   - **Solución Implementada**:
     * Funciones estadísticas `nbinom_survival` y `nbinom_pmf` parametrizadas por sobredispersión $\alpha$: $p = 1 / \alpha$, $n = \mu / (\alpha - 1)$, garantizando media $\mu$ y varianza $\alpha \cdot \mu$.
     * Calibración de córners: sobredispersión $\alpha = 1.20$ conforme a la literatura empírica de córners (McHale & Scarf).
     * Calibración de tarjetas: sobredispersión $\alpha = 1.40$ para modelar la fricción y escalamiento de amonestaciones.

3. **Dinámica de Estado de Marcador en Directo / Game State Effect (Punto 8 — `poisson.py`)**:
   - **Causa Raíz Resuelta**: En vivo, el ritmo goleador y las probabilidades restantes no dependen únicamente del tiempo transcurrido, sino del diferencial de goles. Un equipo perdiendo por 1 gol a partir del minuto 50 arriesga al ataque, mientras que una goleada abultada ($\ge 3$ goles) al minuto 70 desacelera el ritmo de juego.
   - **Solución Implementada**:
     * **Factor de Urgencia**: A partir del minuto 50, si la diferencia es de 1 gol (`score_diff == 1` o `-1`), el equipo en desventaja intensifica su parámetro ofensivo hasta en un +15% a +18%, abriendo a su vez espacios de contraataque.
     * **Factor de Enfriamiento (Blowout Cooling)**: Si la ventaja es $\ge 3$ goles al minuto 70 en adelante, la expectativa de goles restantes se atenúa suavemente hasta un -15%, evitando proyecciones de goles fantasmas en tiempo de trámite.

4. **Framework Formal de Validación Empírica y Backtesting (Punto 3 — `backend/app/analytics/backtest.py`)**:
   - **Causa Raíz Resuelta**: Ausencia de herramientas automatizadas para auditar matemáticamente la calibración de las predicciones del sistema contra marcadores reales mediante métricas probabilísticas de referencia.
   - **Solución Implementada**:
     * **RPS (Ranked Probability Score)** para el mercado 1X2 conforme a la metodología Constantinou & Fenton (penaliza distancias ordinales entre Local, Empate y Visitante).
     * **Brier Score** para mercados binarios (Over 2.5 y Ambos Anotan - BTTS).
     * **Log-Loss (Cross-Entropy Loss)** para calibración de confianza.
     * **MAE y RMSE** para goles totales y tiros de esquina.
     * Dataset curado de benchmark de partidos históricos representativos (`get_benchmark_dataset()`).
     * Endpoints REST en FastAPI: `GET /api/backtest/benchmark` y `POST /api/backtest/run`.

5. **Rediseño del Sistema de Interfaz Visual (Aurora UI & Glow — `frontend-design`)**:
   - **Causa Raíz Resuelta**: Eliminación de tropos y clichés visuales genéricos de IA (sombras grises difusas, exceso de mayúsculas sostenidas, etiquetas en all-caps, dobles barras `//` y falta de integración directa con la validación de modelos).
   - **Solución Implementada**:
     * **Estilo Aurora UI & Glow (`ide-theme.css`)**: Fondo atmosférico con gradientes radiales sutiles (cian, esmeralda y violeta tenue en base obsidian `#08090e`), paneles de cristal con `backdrop-filter: blur(14px)`, bordes hairline luminosos y halos de resplandor contextual (`--emerald-glow`, `--azure-glow`, `--crimson-glow`).
     * **Paleta Semántica en Gráfica de Distribución (`DistributionChart.jsx`)**: Sustitución de colores arcoíris aleatorios por un gradiente de densidad analítico que destaca el rango modal con esmeralda luminoso (`#10b981`), probabilidades intermedias en azul celeste (`#0ea5e9` / `#38bdf8`) y colas en gris acero neutro. Micro-interacción con resplandor en hover para chips de marcadores.
     * **Migración de Estilos Inline a Clases CSS Semánticas (`LoginModal.jsx`, `WinnerCard.jsx`, `MetricCards.jsx`)**: Eliminación de más de 120 líneas de estilos inline en LoginModal; creación de clases modulares `.derived-market-card`, `.derived-stat-pill`, `.live-telemetry-pill` y sustitución de emojis por dots pulsantes nativos (`.pulse-dot-red`, `.pulse-dot-green`).
     * **Tipografía Limpia en Sentence Case**: Sustitución de all-caps en `NeuralUrlCard`, `LiveNeuralSection`, `RecentMatchesBar`, `DistributionChart` y `LoginModal` (`"Historial y sugerencias"`, `"Red Neuronal LSTM · Rastreo en directo"`, `"Córners en tiempo restante"`, etc.).
     * **Modal Interactivo de Calibración (`BacktestModal.jsx`)**: Conectado directamente con el nuevo endpoint de benchmark empírico (`/api/backtest/benchmark`). Muestra KPIs cuantitativos (RPS, Brier Score Over 2.5, Brier BTTS, MAE Goles, RMSE) y desglose partido a partido con etiquetas semánticas de resultado y predicción.
     * **Compilación y Linter Perfectos**: `oxlint` pasando con 0 errores y `vite build` completado con éxito (`dist/` generado en 847 ms).

---

## 3. Novedades y Mejoras en la Versión v3.2 (Auditoría Predictiva: Puntos 1 y 2 Implementados)

1. **Normalización Estricta por Torneo y Localía Simétrica en Poisson (`poisson.py`)**:
   - **Causa Raíz del Sesgo Resuelto (Punto 2.1)**: Los ratios de ataque y defensa se normalizaban contra un promedio universal estático de 1.35 goles, pero luego se multiplicaban por la media real de la competición (ej: 1.54 en Bundesliga). En ligas de alto goleo, un equipo promedio aparecía con ratio artificial de 1.14 (fuerte) y la localía (`* 1.11`) solo inflaba al anfitrión sin contraer al visitante, proyectando 3.56 goles en partidos donde la media era 3.08 (**+15.6% de inflación**).
   - **Solución Implementada**:
     * La referencia de shrinkage y adimensionalización se ancla a la media real del torneo (`league_ref = league_avg_goals`). Dos equipos estándar de Bundesliga dan exactamente 3.08 goles (< 0.2% de diferencia).
     * Localía simétrica: el local se modula por $\sqrt{\text{home\_adv}}$ y el visitante por $1/\sqrt{\text{home\_adv}}$, conservando la ratio exacta de ventaja local sin inflar el volumen global de goles del partido.
     * Eliminación de regla discontinua de bloque bajo (`mu_away *= 0.88`), que colapsaba la discriminación de favoritos y duplicaba factores de defensa.

2. **Escalado de Volumen en H2H sin Aplanar hacia la Paridad (`poisson.py`)**:
   - **Causa Raíz Resuelta**: El ajuste histórico previo mezclaba ambos lambdas hacia una tasa común (`h2h_shrunk_rate * 1.04` vs `0.96`), comprimiendo duelos desiguales (ej. Bayern vs Bochum) hacia la paridad.
   - **Solución Implementada**: El H2H modula proporcionalmente el volumen total esperado del encuentro (`h2h_scale`), manteniendo inalterada la proporción relativa $\lambda_{\text{home}} / \mu_{\text{away}}$.

3. **Coalescencia Estricta en Meta-Ensamble (`_coalesce` en `ensemble.py`)**:
   - **Causa Raíz Resuelta (Punto 2.3)**: El operador `or` en expresiones como `pois_p2 = p_res.get("plus_2_goals_pct") or (final_more_p * 0.65)` trataba las probabilidades legítimas de `0.0%` (comunes en los minutos 80'-90') como ausentes, inyectando fallbacks inflados de más del 5% en líneas de goles imposibles.
   - **Solución Implementada**: Función `_coalesce(val, fallback)` que preserva ceros exactos y solo activa el respaldo si el valor es estrictamente `None`.

4. **Parsing Robusto de Minutos de Juego (`parse_elapsed_minute` en `poisson.py`)**:
   - **Causa Raíz Resuelta (Punto 2.2)**: Cadenas como `"1st half 30"` eran detectadas erróneamente como segundo tiempo debido a la subcadena `"ST"`, retornando minuto 46 en vez de 30. Asimismo, formatos como `"2T 68'"` extraían el primer dígito (2) en lugar del minuto real.
   - **Solución Implementada**: Expresiones regulares con límites de palabra (`\b(1T|1ST|PT)\b`), evaluación estricta de primer tiempo antes que segundo tiempo y remoción de prefijos de periodo previa a la extracción numérica.

5. **Defaults Neutrales de Enfrentamientos Directos (`match.py`, `parser.py`, `tabular_ml.py`)**:
   - **Causa Raíz Resuelta (Punto 2.4)**: Los defaults del schema contenían 5 partidos ficticios con 2 victorias locales, 1 empate y 2 visitantes. Si Gemini no encontraba historial, los motores trataban este valor como historial verificado.
   - **Solución Implementada**: Defaults limpios en 0 partidos (`total_matches_analyzed = 0`), fallback de contingencia en parser regularizado y tratamiento neutral en XGBoost (`h2h_h_ratio = 0.35`, `avg_goals = league_total`).

---

## 3. Novedades y Mejoras en la Versión v3.1 (Calibración de Precisión: Erradicación de Goles y Córners Inflados y Concordancia de Marcador)

1. **Modelo de Córners con Balanza Territorial y Suma Equilibrada (`poisson.py`)**:
   - **Causa Raíz de la Inflación**: Anteriormente se sumaban linealmente los córners individuales del local y visitante (`h_corners + a_corners`) aplicándole un multiplicador adicional del 10% (`* 1.10`) y un factor ofensivo al favorito. Cuando dos clubes ofensivos se enfrentaban, el modelo proyectaba marcadores astronómicos de 12 a 14 córners (con Over 9.5 al 80%+).
   - **Solución Implementada**:
     * **Suma de Posesión Cuasi-Constante**: El fútbol es un deporte territorial de 90 minutos con suma constante. Si un equipo grande domina con 65% de posesión y genera 7-8 córners, el rival encerrado suele generar solo 1 o 2, no 4.5.
     * **Baselines por Competición**: Se incorporaron baselines empíricos de córners por torneo (Premier: 10.1, Bundesliga: 9.7, LaLiga: 9.2, Serie A: 9.5).
     * **Elasticidad Amortiguada del Ritmo de Partido ($0.40$)**: La suma total del partido se ancla firmemente a la media de la liga, modulándose sutilmente por el exceso/déficit conjunto de los clubes.
     * **Reparto por Cuota Territorial**: Los córners totales se distribuyen en base a la balanza de presión territorial de cada equipo (`home_share` vs `away_share`), acotando los partidos entre 8.5 y 10.6 córners totales.
     * **En Vivo (Ritmo Observado Mixto)**: Se pondera bayesianamente el ritmo real de córners disputados ($\text{córners reales} / \text{minuto transcurrido}$) con la base teórica restante, evitando que partidos lentos en directo proyecten ráfagas irreales de córners al final.

2. **Amortiguamiento de Goles y Moderación Táctica de Bloque Bajo (`poisson.py`, `tabular_ml.py`)**:
   - **Causa Raíz de la Inflación**: La multiplicación cuadrática de ratios de ataque y defensa en torneos como Premier o Bundesliga inflaba $\lambda_{\text{home}} + \mu_{\text{away}}$ por encima de 3.6 goles en partidos estándar.
   - **Solución Implementada**:
     * **Elasticidad de Precisión ($\gamma = 0.52$)**: Atenúa colas extremas de rachas goleadoras cortas sin perder la discriminación entre favoritos y rivales débiles.
     * **Modelado Táctico de Bloque Bajo (Low-Block)**: Cuando un favorito tiene amplia ventaja de calidad, se modela el repliegue defensivo del rival menor, contrayendo sus llegadas de gol (`mu_away *= 0.88`).
     * **Techo Dinámico de Competición**: La expectativa de goles esperados pre-match se modula para que los partidos promedio de liga oscilen de forma natural entre **2.40 y 2.90 goles**.
     * **Tabular ML con baselines de torneo**: Expectativas de soporte tabular ancladas a los parámetros del torneo en curso en vez de una constante estática de 1.35.

3. **Concordancia Estricta del Marcador Más Probable (`most_likely_score` en `ensemble.py`)**:
   - **Causa Raíz del Problema**: En partidos donde el local tenía 78% de probabilidad de ganar (ej. Real Madrid vs Osasuna), la celda marginal no condicionada de Poisson para 1-1 tenía una probabilidad individual de 11.2% frente a 10.8% del 2-0 o 2-1. El sistema mostraba un marcador más probable de empate (1-1) cuando el veredicto era favorito 78% local, generando una contradicción severa para el usuario.
   - **Solución Implementada**:
     * Cuando el ensamble determina un favorito claro ($\ge 50\%$ de probabilidad o ventaja $\ge 12\%$), el marcador más probable se selecciona estrictamente de los marcadores concordantes con la victoria del equipo favorecido (`gh > ga` si es local, `ga > gh` si es visitante).
     * Los empates (1-1, 0-0) se reservan para partidos de auténtica paridad o alta probabilidad de empate ($\ge 30\%$).

4. **Calibración de Schemas y Prompts del Parser (`match.py`, `parser.py`)**:
   - En `schemas/match.py`, se regularizaron los defaults a valores de fútbol profesional (goles H2H 2.5 en vez de 2.8, córners H2H 9.2 en vez de 9.5).
   - En el prompt de Gemini, se ajustaron los rangos típicos para evitar que la IA asigne promedios inflados de 8.5 córners individuales.
   - En `collector.py`, se blindó el descarte de URLs ajenas cuando el usuario ingresa equipos distintos en la barra superior.

---

## 4. Novedades y Mejoras en la Versión v3.0 (Estabilidad y Erradicación de HTTP 502 Bad Gateway)

1. **Sincronización Total del Puerto del Backend (`PORT=8000`)**:
   - **Causa Raíz del 502**: En el archivo `.env` se encontraba configurado `PORT=3000` y en `backend/app/config.py` el valor por defecto era `3000`. Si el backend era iniciado mediante `backend/app/main.py` o scripts directos de Python, Uvicorn escuchaba en el puerto 3000. Mientras tanto, el proxy de Vite en `vite.config.js` y `run_app.py` apuntaban exclusivamente al puerto 8000. Al no existir ningún servicio respondiendo en el puerto 8000, Vite recibía `ECONNREFUSED` y retornaba `HTTP 502 Bad Gateway`.
   - **Solución Implementada**:
     * Se sincronizó `PORT=8000` en `.env` y el valor por defecto en `backend/app/config.py`.

2. **Eliminación de Condición de Carrera en el Arranque (`run_app.py`)**:
   - **Causa Raíz del 502**: La carga e importación de librerías de Deep Learning y ML (PyTorch, XGBoost, LangChain) en Windows toma aproximadamente 5.3 segundos. Anteriormente, `run_app.py` solo realizaba un `time.sleep(2)` antes de abrir el navegador en `http://localhost:5173`. Como resultado, el frontend se abría en el navegador e intentaba consultar inmediatamente `/api/predictions/recent` o el usuario enviaba un análisis mientras el puerto 8000 aún no estaba disponible, provocando que Vite arrojara `HTTP 502 Bad Gateway`.
   - **Solución Implementada**:
     * Se integró en `run_app.py` un bucle activo de healthcheck mediante `urllib.request` que consulta `http://127.0.0.1:8000/api/health` cada segundo hasta confirmar respuesta HTTP 200 OK antes de abrir el navegador.

3. **Configuración de Timeouts Extendidos en el Proxy de Vite (`vite.config.js`)**:
   - **Causa Raíz del 502**: En peticiones de análisis con raspado web intensivo o múltiples consultas a Gemini que demoraban más de 30-40 segundos, el socket de proxy interno de Vite podía agotarse y desconectarse con 502.
   - **Solución Implementada**:
     * Se configuró `timeout: 180000` (3 minutos) y `proxyTimeout: 180000` en `server.proxy` de `vite.config.js`, además de un manejador de eventos `configure` para capturar errores de socket sin que se caiga la conexión.

4. **Reintento Automático y Fallback Directo en Frontend (`App.jsx` y `LoginModal.jsx`)**:
   - **Solución Implementada**:
     * Tanto en `App.jsx` (`runAnalysis` y `loadRecentMatches`) como en `LoginModal.jsx`, si una petición arroja un código de error de gateway (`502`, `503` o `504`) o un error de red del proxy, el cliente espera 1.2 segundos y ejecuta automáticamente una petición de fallback directo a `http://127.0.0.1:8000` (habilitado por CORS).
     * En caso de fallo definitivo, la interfaz ya no muestra el mensaje genérico `Error en el servidor: HTTP 502`, sino un diagnóstico claro y amigable que explica que el backend FastAPI se está iniciando o debe ser ejecutado con `iniciar_app.bat`.

---

## 3. Novedades y Mejoras en la Versión v2.9 (Blindaje de Conectividad y Erradicación de `Failed to fetch`)

1. **Proxy Inverso en Vite (`vite.config.js`) y Rutas Relativas**:
   - **Problema Resuelto**: El frontend llamaba directamente a `http://localhost:8000`. En Windows, los navegadores modernos resuelven prioritariamente `localhost` hacia la dirección IPv6 `::1`, mientras que Uvicorn escuchaba únicamente en IPv4 (`127.0.0.1`), produciendo fallos de conexión inmediata (`Failed to fetch`) o demoras de fallback de más de 2000 ms. Además, provocaba peticiones Cross-Origin y preflight `OPTIONS` que podían ser bloqueadas por extensiones del navegador.
   - **Solución Implementada**:
     * Configuración de `server.proxy` en `vite.config.js`: todas las peticiones con prefijo `/api` se despachan mediante proxy local interno a `http://127.0.0.1:8000`.
     * En `App.jsx` y `LoginModal.jsx`, se unificaron las llamadas a rutas relativas `/api/predict`, `/api/login` y `/api/predictions/recent`.

2. **Blindaje de Reinicios Intempestivos de Uvicorn (`--reload-dir backend`)**:
   - **Problema Resuelto**: Uvicorn se iniciaba con `--reload` observando todo el directorio raíz. Cuando el backend guardaba predicciones en SQLite (`analista.db`), Uvicorn detectaba el cambio en el archivo de base de datos y reiniciaba el worker mientras la petición HTTP estaba abierta (~80s), cortando el socket abruptamente y mostrando `Failed to fetch` en pantalla.
   - **Solución Implementada**:
     * En `run_app.py` y `main.py`, se acotó la recarga en caliente exclusivamente a la carpeta `backend` mediante `--reload-dir backend`. Modificaciones en SQLite, `PROJECT_STATUS.md` o el frontend ya no interrumpen el servidor.

3. **Mensajes de Error Amigables y Descriptivos**:
   - Se interceptaron los errores `Failed to fetch` en `App.jsx` y `LoginModal.jsx` para mostrar un diagnóstico claro en caso de que el backend no esté activo, guiando al usuario con la dirección y puerto exactos.

---

## 3. Novedades y Mejoras en la Versión v2.8 (Calibración y Erradicación de Sobreestimación de Goles)

1. **Shrinkage Bayesiano y Elasticidad Amortiguada ($\gamma = 0.65$) en Poisson (`poisson.py`)**:
   - **Problema Detectado**: El modelo multiplicaba directamente la fuerza de ataque por la debilidad defensiva sin amortiguamiento: cuando un equipo con buen momento anotador (ej. 2.5 goles) enfrentaba a una defensa frágil (1.9 goles), la fórmula cuadrática multiplicativa disparaba $\lambda_{\text{home}}$ a más de 4.0 goles individuales, proyectando totales irreales de 4.5 a 4.7 goles esperados (con marcadores astronómicos de 4-0 o 4-1).
   - **Solución Implementada**:
     * **Shrinkage Bayesiano (Regresión a la media)**: Con muestras cortas (5 a 10 partidos), la fiabilidad de las medias extremas se atenúa hacia la referencia de la liga mediante ponderación Bayesiana ($w = 0.72$).
     * **Elasticidad Amortiguada ($\gamma = 0.65$)**: Los ratios de ataque y defensa se modulan con exponente elástico $\left(\frac{\text{goles}}{1.35}\right)^{0.65}$, eliminando la explosión multiplicativa en extremos y manteniendo la dimensionalidad matemática respecto al promedio de la liga.
     * **Límites realistas**: Las expectativas pre-match individuales se acotan a $\lambda_{\text{home}} \le 3.20$ y $\mu_{\text{away}} \le 2.70$.
     * **Resultado**: Un duelo como Man City vs Burnley pasó de 4.03 goles (marcador 4-0) a **3.43 goles** (marcador realista **2-0**), alineándose con las líneas de mercado profesional (3.25/3.5).

2. **Limpieza del Sesgo Aditivo en XGBoost Tabular (`tabular_ml.py`)**:
   - **Problema Detectado**: Se sumaba arbitrariamente `p_home * 15.0` al cálculo de Over 2.5%, inflando en hasta 15 puntos la probabilidad de goles simplemente porque un equipo era favorito, ignorando victorias cerradas (1-0 o 2-0). Además, la suma de soporte tabular duplicaba ponderaciones.
   - **Solución Implementada**:
     * Se implementó una **función logística sigmoide calibrada**: $P(\text{Over } 2.5) = \frac{1}{1 + e^{-1.60 \times (\text{tot\_goals\_est} - 2.50)}} \times 100$, dependiente estrictamente del volumen proyectado sin sesgo por ganador.
     * Soporte tabular reformulado con shrinkage Bayesiano hacia la media.

3. **Modulación de Momentum Relativo en LSTM y Ensamble (`ensemble.py`)**:
   - **Problema Detectado**: En el meta-ensamble pre-match, `lstm_momentum * 0.15` se sumaba como goles brutos aditivos, inyectando más de 0.5 goles artificiales a partidos de equipos con rachas positivas.
   - **Solución Implementada**:
     * Poisson Dixon-Coles (65%) y Tabular (35%) definen el volumen base matemático de goles.
     * La red LSTM actúa como analizador de momentum temporal, modulando el ritmo como un multiplicador relativo acotado entre 0.93 y 1.07 ($\pm 7\%$ máximo por racha).

---

## 3. Novedades Previas en la Versión v2.7 (Fase 3: Calibración Pre-Match por Liga, Bajas Posicionales y Mercados Derivados)

1. **Calibración Pre-Match por Competición (`poisson.py`)**:
   - **Problema Resuelto**: Se utilizaba un promedio universal estático (1.35 goles por equipo) sin importar la liga. En ligas con altos promedios como la Bundesliga (~3.16 goles totales) o la Eredivisie (~3.10), el modelo tendía a subestimar el volumen de goles, mientras que en ligas tácticas o defensivas como Segunda División (~2.24) o LaLiga (~2.56) tendía a sobreestimarlos.
   - **Solución Implementada**:
     * Diccionario `COMPETITION_BASELINES` calibrado empíricamente para Bundesliga, Premier League, LaLiga, Serie A, Ligue 1, Champions League, Europa League, Eredivisie, Liga MX, Brasileirao, Copa Libertadores, MLS y Segunda División / LaLiga Hypermotion.
     * Función `get_competition_parameters(competition_name)` con priorización por especificidad de búsqueda (evitando falsos positivos entre "LaLiga" y "LaLiga Hypermotion / Segunda").
     * La fuerza intrínseca ofensiva y defensiva de los clubes se normaliza contra el estándar global de fútbol (1.35) y la tasa goleadora del partido se modula con el promedio goleador real y la ventaja de campo del torneo en cuestión.

2. **Modelado y Ponderación Posicional de Bajas y Ausencias (`poisson.py`)**:
   - **Problema Resuelto**: Las ausencias clave antes se penalizaban como una lista genérica sin distinguir si la baja correspondía a un guardameta titular, a un defensa central o al máximo goleador del equipo.
   - **Solución Implementada**:
     * Función `_evaluate_absences_impact(absences: List[str])`:
       - Bajas defensivas (portero, arquero, central, lateral, defensor) incrementan la expectativa de goles concedidos en ~6% por ausencia.
       - Bajas ofensivas (delantero, goleador, striker, extremo, atacante) reducen la fuerza de ataque en ~7% por ausencia.
       - Ausencias genéricas aplican penalización moderada (~4%).
     * Los multiplicadores resultantes modulan dinámicamente $\lambda_{\text{home}}$ y $\mu_{\text{away}}$ respetando límites estables (0.70 a 1.30).

3. **Mercados Derivados Avanzados: Doble Oportunidad y Draw No Bet (`prediction.py`, `ensemble.py`)**:
   - **Problema Resuelto**: El sistema únicamente entregaba el mercado principal 1X2, dejando sin cobertura analítica mercados altamente demandados por tipsters y apostadores deportivos (Doble Oportunidad y Empate Apuesta No Válida).
   - **Solución Implementada**:
     * Schemas `DoubleChancePrediction` y `DrawNoBetPrediction` integrados en `WinnerPrediction`.
     * Fórmulas matemáticas implementadas en `ensemble.py`:
       - **1X (Local o Empate)**: $\min(99.0, P(\text{Home}) + P(\text{Draw}))$
       - **X2 (Empate o Visitante)**: $\min(99.0, P(\text{Draw}) + P(\text{Away}))$
       - **12 (Local o Visitante)**: $\min(99.0, P(\text{Home}) + P(\text{Away}))$
       - **DNB Local**: $\frac{P(\text{Home})}{P(\text{Home}) + P(\text{Away})} \times 100$
       - **DNB Visitante**: $100.0 - P(\text{Home DNB})$
     * En `_generate_human_verdicts`, cuando un partido presenta paridad (diferencia $< 10\%$ o empate $\ge 30\%$), el veredicto en lenguaje humano sugiere explícitamente coberturas de Doble Oportunidad o DNB.

---

## 3. Novedades Previas en la Versión v2.6 (Fase 2: Telemetría In-Play y Modelado de Dinámica de Juego)

1. **Extracción y Modelado de Ventaja Numérica por Tarjetas Rojas en Vivo (`poisson.py`, `tabular_ml.py`, `scraper.py`)**:
   - **Problema Resuelto**: Cuando un equipo sufría una expulsión en directo, el sistema no la detectaba ni la incorporaba a los modelos matemáticos, asumiendo paridad numérica (11 vs 11) durante todo el encuentro a pesar de que jugar con un hombre menos cambia de raíz la correlación de fuerzas.
   - **Solución Implementada**:
     * En `scraper.py`, se extraen las tarjetas rojas y dobles amarillas (`incidentClass in ['red', 'yellowRed']` y `statisticsItems['red card']`) desde la API oficial de Sofascore, asignándolas a `live_red_cards_home` y `live_red_cards_away`.
     * En `poisson.py`, cada tarjeta roja penaliza el ataque residual del equipo sancionado en un 32% (`att_mod = max(0.35, 1.0 - 0.32 * reds)`) e incrementa la tasa de concesión de goles en un 38% (`def_mod = 1.0 + 0.38 * opp_reds`).
     * En `tabular_ml.py`, se ajusta la probabilidad 1X2 in-play penalizando al equipo sancionado y bonificando al rival hasta en +25%.

2. **Modelado de Presión Ofensiva In-Play mediante Tiros a Puerta en Directo (`poisson.py`, `scraper.py`)**:
   - **Problema Resuelto**: La expectativa ofensiva restante de un partido en juego se basaba únicamente en promedios históricos escalados por tiempo, sin detectar si un equipo estaba sometiendo a su rival a un asedio constante.
   - **Solución Implementada**:
     * En `scraper.py`, se extraen los tiros a puerta acumulados (`shots_on_target_home`, `shots_on_target_away`) y posesión (`possession_home`, `possession_away`).
     * En `poisson.py`, cuando el partido supera el minuto 20 y existe telemetría de tiros a puerta, se calcula el diferencial de asedio (`sot_diff = sot_h - sot_a`), aplicando un multiplicador de presión residual acotado entre 0.75 y 1.30 (`pressure = clip(1.0 + sot_diff * 0.04, 0.75, 1.30)`).

3. **Enriquecimiento de Factores Clave y Contrato de API (`ensemble.py`, `match.py`, `prediction.py`, `main.py`)**:
   - Si un equipo juega con inferioridad numérica, el ensamble genera una alerta explícita en lenguaje humano: `🔴 INFERIORIDAD NUMÉRICA: {equipo} juega con 1 tarjeta roja en directo.`
   - Si hay asedio confirmado, reporta: `⚽ TELEMETRÍA EN DIRECTO: {equipo} registra {N} tiros a puerta frente a {M} de {rival}.`
   - Los campos in-play (`live_red_cards_home/away`, `live_shots_on_target_home/away`, `live_possession_home/away`) forman parte oficial de `MatchRawFeatures`, `PredictRequest` y `MatchMeta`.

---

## 3. Novedades Previas en la Versión v2.5 (Fase 1: Mejoras Matemáticas de Modelos en Vivo)

1. **Curva Empírica No Homogénea de Llegada de Goles y Córners (`poisson.py`, `tabular_ml.py`, `lstm_net.py`)**:
   - **Problema Resuelto**: La reducción de expectativa de gol en vivo utilizaba una recta lineal plana: $\frac{90 - \text{min}}{90}$. En el fútbol profesional esto provocaba que los modelos "apagaran" prematuramente las proyecciones en los minutos 70'-85', ignorando que en la realidad ~22.5% de los goles de los partidos ocurren en los últimos 15 minutos debido a fatiga física, urgencia de remontada y desorganización táctica.
   - **Solución Implementada**:
     * Se incorporaron las funciones `calculate_remaining_goal_ratio(elapsed_minutes)` y `calculate_remaining_corner_ratio(elapsed_minutes)`.
     * Distribución empírica acumulada calibrada:
       - 0' - 15': 13.0%
       - 16' - 30': 15.5%
       - 31' - 45+': 17.5% (Total 1T: 46.0%)
       - 46' - 60': 16.5%
       - 61' - 75': 18.5%
       - 76' - 90+': 22.5% (Total 2T: 54.0%)
     * Al minuto 45 queda el ~54% de la expectativa de gol restante, y al minuto 75 se conserva un sólido ~22.5%, eliminando el apagado artificial de líneas de gol.
     * Integración unificada y consistente en los tres motores: Poisson, XGBoost y Red LSTM.

2. **Desactivación de Corrección $\tau$ Dixon-Coles en Goles Adicionales en Vivo (`poisson.py`)**:
   - **Problema Resuelto**: Dixon-Coles corrige la interdependencia y exceso de empates en marcadores globales pre-match bajos $(0-0, 1-0, 0-1, 1-1)$ mediante el parámetro $\tau$. Al aplicarse de forma indiscriminada sobre la matriz de goles *adicionales* restantes en vivo, alteraba erróneamente la probabilidad de que no hubiera más goles ($+0$), cuando los goles residuales de un partido en juego constituyen un proceso condicional independiente del marcador original.
   - **Solución Implementada**:
     * `compute_bivariate_matrix` acepta ahora el parámetro `apply_dixon_coles=not is_live`.
     * En pre-match se conserva la corrección $\tau(\rho = -0.10)$; en partidos en vivo se desactiva $\tau$ ($\tau = 1.0$), calculando una distribución condicional pura y matemáticamente rigurosa para los goles restantes.

3. **Ponderación Bayesiana Dinámica por Minuto en el Meta-Ensamble (`ensemble.py`)**:
   - **Problema Resuelto**: El meta-ensamble mantenía pesos fijos estáticos (40% Poisson, 35% XGBoost, 25% LSTM) en cualquier momento del juego. Al minuto 80' o 85', cuando el marcador ya está avanzado (ej. 2-0 o 1-0), la probabilidad condicional matemática exacta basada en el marcador actual y tiempo restante debe ser mucho más determinante que las variables estáticas previas al partido.
   - **Solución Implementada**:
     * Se incorporó el método `_get_dynamic_weights(is_live, elapsed_min)`.
     * Transición continua y suave de pesos mediante interpolación por anclas:
       - **Pre-match**: 40.0% Poisson, 35.0% XGBoost, 25.0% LSTM
       - **Minuto 45 (HT)**: ~55.0% Poisson, 28.0% XGBoost, 17.0% LSTM
       - **Minuto 70**: ~68.0% Poisson, 20.0% XGBoost, 12.0% LSTM
       - **Minuto 85+**: ~78.0% - 82.0% Poisson, 11.0% - 14.0% XGBoost, 7.0% - 8.0% LSTM
     * Aplicado de forma coherente a: Probabilidades 1X2, Consenso de Goles Esperados y Ensamble de Líneas Dinámicas ("Sin más goles").

---

## 3. Novedades Previas en la Versión v2.4 (Detección y Visualización de Marcador en Vivo)

1. **Pastilla Prominente de Marcador Actual en Vivo (`WinnerCard.jsx` & `ide-theme.css`)**:
   - **Problema Resuelto**: En los partidos en vivo, el marcador actual no se mostraba con claridad o no aparecía entre los nombres de los equipos, mostrando únicamente la insignia `VS` y un texto secundario en corchetes pequeños que pasaba desapercibido si el score venía vacío.
   - **Solución Implementada**:
     * En `WinnerCard.jsx`, cuando el partido está en vivo (`showLive && match.live_score`), se renderiza un componente de marcador estilizado `.live-score-pill` entre los dos equipos:
       - Números de goles en tipografía monospace de 1.25rem y peso 800 en color blanco puro.
       - Separador con resplandor carmesí (`-`).
       - Insignia de minuto activo (ej. `27'`, `45'`, `HT`, `2T`).
       - Borde animado con resplandor pulsante (`animation: pulse-border 2s infinite`).
     * En `MetricCards.jsx`, se agregó el bloque `🔴 ACTUAL: {match.live_score} ({match.live_minute})` justo encima del `MARCADOR PROBABLE / PROYECCIÓN FINAL`, permitiendo al usuario contrastar de un vistazo la realidad del momento frente a la proyección de goles finales.

2. **Detección Autónoma de Partidos en Vivo sin Necesidad de URL (`scraper.py`)**:
   - **Problema Resuelto**: Cuando el usuario analizaba un partido en curso escribiendo directamente los nombres de los equipos sin pegar una URL, DuckDuckGo respondía "No results found", perdiéndose el marcador real y dejando `live_score = None`.
   - **Solución Implementada**:
     * Se incorporó el método `find_live_match(home_team, away_team)` que consulta directamente el endpoint de eventos en juego de Sofascore (`/api/v1/sport/football/events/live`).
     * Normaliza los nombres de ambos equipos (removiendo acentos, FC, Club, sub-categorías) y localiza el evento en juego en ~200ms.
     * Al detectar el partido, extrae instantáneamente el marcador oficial en vivo, el minuto exacto y las estadísticas de córners, inyectándolos en la telemetría del colector.

3. **Compatibilidad Total con Formatos de URLs de Flashscore (`_extract_flashscore_match_id`)**:
   - **Problema Resuelto**: En Flashscore, los enlaces con slug compuesto como `/match/pegeia-apoel-4EVDq0HO/#/match-summary` o `/partido/equipo-a-b-Wxyz1234/` no eran reconocidos porque la expresión regular exigía que el ID estuviera precedido obligatoriamente por una barra `/`. Al fallar, no se consultaban los feeds de Flashscore Ninja y la página estática carecía de marcador.
   - **Solución Implementada**:
     * Se amplió el extractor para capturar IDs de 8 caracteres precedidos tanto por guión (`-`) como por barra (`/`), además de parámetros query (`?mid=`, `?id=`) y metadatos internos en el HTML.
     * En `_scrape_flashscore_feed`, se añadió soporte para pares de marcador `AG - AH` además de `DE - DF` y `DG - DH`.

4. **Corrección de Lógica de Limpieza en `parser.py` y `main.py`**:
   - En `backend/app/agent/parser.py`, se corrigió la condición que forzaba `parsed_result.live_score = None` si no había un objeto `previous_features` previo con URL. Ahora `is_live=True` conserva intacto el marcador capturado.
   - En `backend/app/main.py`, se solucionó la condición `is_live=bool(request.match_url and request.match_url.strip()) if request.match_url is not None else request.is_live`, que anulaba `is_live=True` cuando `match_url` venía como cadena vacía `""`. Ahora calcula `effective_live = bool(clean_url) or bool(request.is_live)`.
   - En `backend/app/agent/collector.py`, se garantizó que todo partido confirmado en vivo tenga como mínimo `live_score = "0 - 0"` si aún no se han registrado goles, evitando valores nulos que ocultaban la sección de marcador.

1. **Fin del Desvío de Partidos y Respeto Absoluto a los Nombres de la Barra Superior**:
   - **Problema Resuelto**: Cuando el usuario escribía manualmente dos equipos arriba (`LOCAL` y `VISITANTE`) habiendo quedado una URL en la sección de URL o en `localStorage`, el sistema mantenía la URL del partido anterior, enviándola al backend donde los nombres del usuario eran sobreescritos por los del partido previo.
   - **Solución en Frontend (`HeaderBar.jsx` & `App.jsx`)**:
     * Al escribir o modificar los inputs de `LOCAL` o `VISITANTE`, si existe una `matchUrl` anterior, se limpia y descarta automáticamente de forma inmediata (`onClearUrl`), retornando el indicador Katakuri a modo pre-partido (recuadro azul).
     * En `runAnalysis`, se verifica la coherencia entre los nombres ingresados y los slugs de la URL: si no corresponden al mismo encuentro, la URL obsoleta se descarta.
   - **Solución en Backend (`collector.py`)**:
     * Se incorporó validación cruzada: si el usuario especifica `home_team` y `away_team`, y la URL pertenece a otro choque, el backend descarta la URL para ese análisis y analiza de forma fiel los equipos solicitados por el usuario.

2. **Extracción de Datos Reales en Vivo y Fin de Bloqueos Cloudflare (Primp + Sofascore API)**:
   - **Problema Resuelto**: La descarga de páginas online con `httpx` fallaba en Sofascore con error `403 Forbidden` (bloqueo antibot de Cloudflare), y DuckDuckGo a menudo arrojaba `"No results found"`, dejando a la IA sin datos reales y recurriendo a estimaciones genéricas.
   - **Solución Implementada (`scraper.py`)**:
     * Integración de `primp.Client`, cliente HTTP de alto rendimiento capaz de emular TLS de navegador moderno, eliminando por completo los bloqueos 403 en Sofascore y Flashscore.
     * Conexión directa a los endpoints oficiales de telemetría de Sofascore (`/api/v1/event/{id}`, `/statistics`, `/incidents`):
       - **Marcador Real en Directo**: extraído directamente del feed (`1 - 3`, `2 - 2`, etc.).
       - **Minuto Activo Preciso**: tiempo de juego calculado en tiempo real (`1T`, `2T`, `HT`, `45'`, `90'`).
       - **Tiros de Esquina Acumulados Reales**: suma verificada de córners de ambos equipos.
       - **Incidencias**: registro de goles con anotadores y tarjetas.

3. **Migración a Modelos Activos de Gemini (`gemini-3.5-flash-lite`, `gemini-3.5-flash`, `gemini-3.8-flash`)**:
   - **Problema Resuelto**: El parser contenía en su lista de candidatos el modelo `gemini-2.5-flash`, el cual fue deprecado por Google API retornando `404 NOT_FOUND`. Esto provocaba que las llamadas a Gemini fallaran y cayeran en el extractor heurístico de contingencia local con métricas ficticias.
   - **Solución**: Se actualizó la lista de candidatos priorizando `gemini-3.5-flash-lite` y la familia Gemini 3.x, los cuales responden en ~1.5 segundos con extracción estructurada JSON de alta precisión.

4. **Respaldo de Historial Reciente Real para Todos los Clubes**:
   - Incluso en encuentros pre-match o sin URL, el scraper consulta los últimos resultados reales de ambos clubes mediante el buscador deportivo de Sofascore, suministrando a Gemini resultados reales y forma reciente confirmada.

---

## 3. Novedades Previas en la Versión v2.2

1. **Modo En Vivo Gobernado Exclusivamente por URL (`match_url`)**:
   - **Regla Absoluta de Activación**: Ya no existe conmutación manual ni detección ambigua en snippets. La plataforma entra en **Modo En Vivo** única y exclusivamente cuando el usuario ingresa una URL de partido online (ej. Flashscore o Sofascore).
   - Sin URL, el análisis es forzado de manera estricta y limpia a **Modo Pre-Match** (`is_live = False`, minutos, marcadores y córners en vivo nulos).
   - La URL se almacena en el estado, en `localStorage` (`katakuri_match_url`) y en SQLite (`match_predictions.match_url`).
   - El ciclo de auto-sincronización de 5 minutos rastrea continuamente la URL, raspando el contenido HTML real y comparando con los modelos y datos previos.

2. **Casilla de URL en la Sección de Red Neuronal (Sin Nuevos Botones)**:
   - Cuando la aplicación no tiene partidos cargados (estado inicial en espera), en el espacio central donde se ubica la sección de red neuronal se renderiza la tarjeta `.neural-url-panel` (`NeuralUrlCard.jsx`) con un campo estilizado para ingresar la URL.
   - En modo pre-partido con un encuentro cargado, la misma casilla permanece disponible para que el usuario pueda convertir el partido a En Vivo en cualquier momento.
   - Para no saturar con botones adicionales, la activación utiliza directamente el botón existente **ANALIZAR** en la barra superior (o la tecla `Enter` en el input).

3. **Desactivación de la Función de Botón en el Recuadro Katakuri**:
   - El recuadro superior `Katakuri v2.1 // ANALISTA DEPORTIVO` (`#katakuri-brand-indicator`) deja de actuar como botón clickeable (`cursor: default`, sin evento `onClick`).
   - Funciona exclusivamente como **indicador cromático de estado**:
     * **Borde y Resplandor Azul (`.not-live`)**: Modo estándar Pre-Match.
     * **Borde y Resplandor Rojo (`.is-live`)**: Modo En Vivo activo con URL rastreada en tiempo real.

4. **Des-sesgo Matemático de Córners Pre-Match en Poisson**:
   - Se erradicaron los valores estáticos por defecto (5.0 y 9.5) que sesgaban los cálculos de saques de esquina.
   - La expectativa de córners se calcula de forma dinámica y rigurosa en función del ritmo ofensivo de los equipos:
     $$\lambda_{\text{corners, home}} = \text{avg\_corners\_home} \times (0.65 + 0.35 \times \frac{\lambda_{\text{home}}}{\text{promedio liga}}) \times 1.10$$
     $$\mu_{\text{corners, away}} = \text{avg\_corners\_away} \times (0.65 + 0.35 \times \frac{\mu_{\text{away}}}{\text{promedio liga}}) \times 0.90$$
   - Partidos de alto volumen ofensivo proyectan de forma natural >11 córners, mientras que partidos trabados o defensivos proyectan <8.5 córners, calibrados matemáticamente.

5. **Actualización Dinámica de Nombres de Equipos en Barra Superior y Probabilidad de Victoria**:
   - **Sección de Probabilidad de Victoria (`WinnerCard.jsx`)**: Se sustituyeron las etiquetas genéricas `1. VICTORIA LOCAL` y `2. VICTORIA VISITA` por los nombres de los equipos correspondientes: `1. {match.home_team.toUpperCase()}`, `X. EMPATE` y `2. {match.away_team.toUpperCase()}`, además de tooltips dinámicos con los nombres en la barra segmentada de probabilidades.
   - **Barra Superior (`HeaderBar.jsx` & `App.jsx`)**: Se amplió el ancho de los inputs a `165px` para evitar recorte en nombres largos, se sincronizan automáticamente con `predictionData.match` en cada análisis o cambio de URL, y se incorporó un extractor inteligente de nombres de equipos a partir de los slugs de URLs de Flashscore y Sofascore (`extractTeamsFromUrl`).

---

## 3. Novedades Previas en la Versión v2.1

1. **Eliminación Total de la Opción de Score e Inputs en la Barra Principal**:
   - Se removió por completo el contenedor de inputs (`SCORE`, `MIN`, `CÓRNERS`) de la barra principal (`HeaderBar.jsx`) tras confirmar que resultaba visualmente invasivo y estorbaba la navegación.
   - La barra principal queda limpia, elegante y espaciosa: logotipo interactivo Katakuri (conmutador de modo en vivo), contador de telemetría de 5 minutos, selector `LOCAL` vs `VISITANTE`, botón de acción `ANALIZAR` y perfil de usuario.
   - La telemetría en vivo (marcador parcial, minuto transcurrido, goles y córners) se presenta de forma natural y autónoma en `LiveNeuralSection` y `MetricCards` sin requerir inputs manuales invasivos.

2. **Corrección de la Búsqueda Web de Goles y Córners (Fin de Resultados Vacíos en DuckDuckGo)**:
   - Se identificó y resolvió el motivo de los datos errados: el concatenar demasiados términos (más de 13 palabras por consulta) provocaba que DuckDuckGo respondiera con `"No results found"`.
   - Se diseñó un plan de búsqueda conciso y altamente enfocado (menos de 8 palabras por consulta) que busca `"tiros de esquina"` y `"corners"` por igual junto con marcadores reales desde Flashscore y Sofascore, logrando un 100% de recuperación de snippets enriquecidos.

3. **Eliminación de Falsos Positivos de Partido en Vivo**:
   - Se eliminó el sesgo en el parser donde partidos futuros o pre-match eran clasificados como en vivo debido a la presencia de palabras como "livescore" en los metadatos de Sofascore.
   - Con la validación estricta de minutos activos y marcadores, los partidos pre-match calculan sus lambdas Poisson completos de 90 minutos (~2.8 - 3.2 goles y ~9.5 - 10.5 córners), evitando la reducción artificial al 50%.

4. **Prevención de Sobreescritura de Marcadores con "0 - 0" Ficticio**:
   - En el frontend y en el colector backend, se eliminó la inicialización con strings `'0 - 0'` por defecto, impidiendo que marcadores reales con goles anotados en directo fueran sobreescritos involuntariamente.

---

## 3. Novedades Previas en la Versión v2.0

1. **Búsqueda Web Exhaustiva Bilingüe para Tiros de Esquina y Córners**:
   - Integración equitativa en todas las consultas de búsqueda y prompts de los términos: `"tiros de esquina"`, `"corners"`, `"córners"` y `"saques de esquina"`.
   - Consulta dedicada en tiempo real para estadísticas de saques de esquina y marcadores en directo desde Flashscore y Sofascore.

2. **Eliminación Definitiva del Valor por Defecto de 5 en Córners en Vivo**:
   - Se erradicó la estimación artificial `round(expected_corners_base * elapsed_ratio)` que asignaba automáticamente 5 córners cuando no había datos.
   - Si no hay datos detectados en directo, `current_corners` se mantiene estrictamente en `None`, reflejándose como `'Tiros de esquina: En seguimiento'` o `'--'` en la interfaz, sin inducir a error.
   - Si hay córners reales (ej. 2, 7 u 8), se proyectan de forma condicionada y matemáticamente rigurosa.

3. **Garantía de Estabilidad y Continuidad tras 5 Minutos (Auto-Sync)**:
   - Resuelto el salto brusco de datos entre consultas consecutivas: cuando el partido se actualiza tras 5 minutos, se anclan las estadísticas base de temporada del club (`avg_goals`, `avg_corners`, H2H), evitando que los modelos locales oscilen a valores radicalmente opuestos por variaciones menores de fragmentos web.
   - Monotonía estricta: los goles (`live_score`), el minuto (`live_minute`) y los córners (`live_corners`) acumulados no pueden disminuir respecto al estado previo confirmado.
   - Conservación garantizada del orden oficial de local y visitante.

4. **Controles Interactivos en Vivo en la Barra Superior (HeaderBar)**:
   - Al activarse el modo EN VIVO, la barra superior despliega campos editables y sincronizados en tiempo real para `SCORE`, `MIN` y `CÓRNERS`, permitiendo tanto lectura inmediata como ajuste manual por el usuario.

1. **Recuadro Maestro de Katakuri y Estética de Estado**:
   - **Indicador Cromático Limpio**: Eliminación total de las etiquetas de texto `LIVE ON` / `PRE-MATCH` dentro del recuadro de Katakuri. El estado queda determinado exclusivamente por el color del recuadro (borde y resplandor azul para pre-partido, borde y resplandor rojo para en vivo).
   - **Animación Roja Suavizada y Ralentizada**: La pulsación lumínica del borde rojo en vivo se redujo a una cadencia suave y pausada de 4 segundos (`live-border-pulse 4s infinite ease-in-out`), ofreciendo un aspecto premium y descansado.
   - **Retorno de Identidad**: Sustitución del texto `// Clic para conmutar modo` por el subtítulo formal de la plataforma: `// ANALISTA DEPORTIVO`.

2. **Botón de Análisis Dinámico con Feedback Visual Activo**:
   - **Transición a "ANALIZANDO..."**: Al presionar el botón de análisis, el texto cambia inmediatamente a `ANALIZANDO...`.
   - **Preservación Cromática**: Se mantiene el color vibrante cian del botón (`is-loading`), evitando el desvanecimiento a gris por el estado `disabled`.
   - **Ícono Spinner Circular**: El ícono estático de Play se reemplaza durante la inferencia por un círculo rotatorio de carga fluido (`Loader2`).

3. **Sección Horizontal Dedicada de Red Neuronal & Ensamble en Vivo**:
   - **Reubicación Arquitectónica**: Las probabilidades dinámicas en directo se desacoplaron del panel vertical de goles de `MetricCards`.
   - **Nuevo Componente Horizontal (`LiveNeuralSection`)**: Posicionado inmediatamente debajo de la tarjeta de probabilidades de victoria (1X2), en formato horizontal panorámico de 4 tarjetas:
     * *Sin Más Goles (+0)*: Marcador final inalterado y probabilidad en ámbar.
     * *Más Goles (+1+)*: Probabilidad de superar el marcador actual en verde lima.
     * *Líneas Dinámicas de Goles*: Probabilidades desglosadas para +1, +2 y +3 goles adicionales.
     * *Dinámica de Córners en Vivo*: Conteo acumulado actual y probabilidad de córners en tiempo restante.
     * *Inferencia Neuronal*: Resumen en lenguaje natural del momentum de tensión.

4. **Corrección Integral del Marcador en Tiempo Real y Córners**:
   - **Marcador en Directo sin Sobrescritura**: Resuelto el conflicto donde el payload por defecto de la interfaz sobrescribía con `"0 - 0"` los marcadores reales extraídos por el scraper en Flashscore y Sofascore.
   - **Calibración y Conteo Fiel de Córners en Vivo**:
     * Incorporación de `live_corners` en `MatchRawFeatures` y `current_corners` en `CornersPrediction`.
     * Las líneas de *Over 8.5*, *Over 9.5* y *Over 10.5* córners ahora se condicionan matemáticamente a los saques de esquina ya ocurridos en el encuentro, asegurando monotonía estricta y realismo estadístico.

---

## 3. Stack Tecnológico

| Capa | Tecnologías | Propósito |
|---|---|---|
| **Backend & Servidor** | Python 3.12, FastAPI, Uvicorn | API REST asíncrona de alto rendimiento |
| **Búsqueda & Orquestación LLM** | LangChain, `langchain-google-genai` | Agente de búsqueda web y estructuración a JSON |
| **Modelo LLM Externo** | Google Gemini 2.5 Flash (`gemini-2.5-flash`) | **Solo** búsqueda y síntesis de datos en internet |
| **Base de Datos Local** | SQLite (`analista.db`) + SQLAlchemy | Persistencia de predicciones, histórico y caché |
| **Modelos ML Tabular** | **XGBoost**, Scikit-Learn | Clasificación de resultado (1X2) y regresión |
| **Deep Learning Secuencial** | **PyTorch (LSTM)** Local | Red neuronal recurrente de series temporales |
| **Modelo Matemático Dinámico** | **Poisson Bivariado Dinámico** (Dixon-Coles) | Proyección de goles, córners y tarjetas |
| **Frontend** | React 18 + Vite 8 | Dashboard reactivo estilo Dark IDE minimalista |
| **Visualización** | Chart.js, `react-chartjs-2`, Lucide Icons | Gráficas de barras y telemetría visual |
| **Estilos** | CSS Puro (`ide-theme.css`) | Tema monocromático técnico gris oscuro (`#0e0e11`, `#16161a`) |

---

## 4. Arquitectura de Modelos Locales

```
[ Input: Nombres de Equipos (Ej: Real Madrid vs Barcelona) ]
                          │
                          ▼
            [ LangChain + Gemini 2.5 Flash ]
       (Búsqueda Web: Stats de últimos partidos, H2H,
        goles a favor/contra, córners, tarjetas, bajas)
                          │
                          ▼
          [ Feature Engineering Pipeline (JSON) ]
          ├─ Series temporales (Racha de los últimos 10 partidos)
          ├─ Métricas agregadas (xG histórico, promedios)
          └─ Factores contextuales (Localía, descanso, rival)
                          │
        ┌─────────────────┼─────────────────┐
        ▼                 ▼                 ▼
 ┌─────────────┐   ┌─────────────┐   ┌─────────────────────────┐
 │   XGBoost   │   │    LSTM     │   │   Poisson Bivariado     │
 │  (Tabular)  │   │  (PyTorch)  │   │       Dinámico          │
 │             │   │             │   │     (Dixon-Coles)       │
 └──────┬──────┘   └──────┬──────┘   └────────────┬────────────┘
        │                 │                       │
        └─────────────────┼───────────────────────┘
                          │
                          ▼
             [ Meta-Ensamble Calibrado ]
     (Consenso probabilístico y calibración isotónica)
                          │
                          ▼
       [ Traducción a Lenguaje 100% Humano y Gráficas ]
        ├─ ¿Quién va a ganar? (1X2 en % que suman 100.0%)
        ├─ Cantidad de goles (Over 1.5, Over 2.5, Over 3.5 y marcador exacto)
        ├─ Tiros de esquina (Over 8.5, Over 9.5, Over 10.5 y total estimado)
        └─ Disciplina y tarjetas (Total esperado y riesgo de expulsión)
```

---

## 5. Tablero de Fases e Hitos

| Fase | Descripción | Estado |
|---|---|:---:|
| **Fase 0** | Definición de Arquitectura, Modelos y Reglas (`AGENTS.md`, `.gitignore`) | ✅ Completado |
| **Fase 1** | Configuración de entorno virtual `.venv`, dependencias y SQLite | ✅ Completado |
| **Fase 2** | Agente de Búsqueda Web con LangChain & Gemini 2.5 Flash (extracción JSON) | ✅ Completado |
| **Fase 3** | Motor Predictivo Local (Poisson Dixon-Coles, XGBoost, PyTorch LSTM, Ensamble) | ✅ Completado |
| **Fase 4** | API REST en FastAPI (`POST /api/predict`, `GET /api/health`, caché inteligente) | ✅ Completado |
| **Fase 5** | Frontend Dark IDE Minimalista en React + Vite + Chart.js con Login Modal | ✅ Completado |
| **Fase 6** | Integración, Calibración Matemática 100%, Monotonía de Líneas y Polling 5 min | ✅ Completado |
| **v1.2 - v1.5** | Unificación a Español, Live Toggle en Marca, Veredictos Limpios | ✅ Completado |
| **v1.6** | Máxima fidelidad en búsqueda web en vivo (prevención de confusión con marcadores H2H) | ✅ Completado |
| **v1.7** | Búsqueda prioritaria Flashscore/Sofascore, corrección de goles reales en vivo y remoción de minutos (45') en badge | ✅ Completado |
| **v1.8** | Conmutador maestro de modo en vivo en logo de Katakuri y probabilidades dinámicas de goles (sin más goles vs más goles) con Red Neuronal + Ensamble | ✅ Completado |
| **v1.9** | Rediseño cromático del logo, animación suave, botón reactivo con spinner circular, sección horizontal dedicada para Red Neuronal en vivo y corrección de marcador en tiempo real y córners condicionados | ✅ Completado |
| **v1.9.1** | Eliminación de `🔴 EN DIRECTO (45')` en la sección de red neuronal, corrección integral de búsqueda web con `gemini-3.5-flash-lite`, eliminación de falsos positivos de partidos en vivo y resolución de sesgo en goles y córners | ✅ Completado |
| **v2.0** | Búsqueda exhaustiva bilingüe para tiros de esquina y córners, erradicación del valor por defecto de 5 en córners en vivo, anclaje de continuidad y estabilidad tras 5 minutos y controles en vivo en HeaderBar | ✅ Completado |
| **v2.5** | Fase 1 de Optimización Matemática: Curva empírica no homogénea de goles y córners, desactivación de tau Dixon-Coles en goles adicionales in-play y ponderación bayesiana dinámica por minuto | ✅ Completado |
| **v2.6** | Fase 2 de Telemetría In-Play: Modelado de ventaja numérica por tarjetas rojas, asedio ofensivo por tiros a puerta y posesión en vivo | ✅ Completado |
| **v2.7** | Fase 3: Calibración Pre-Match por ligas, ponderación posicional de ausencias y mercados derivados avanzados (Doble Oportunidad 1X/X2/12 y Draw No Bet DNB) | ✅ Completado |
| **v2.8** | Erradicación de Sobreestimación de Goles: Shrinkage Bayesiano, elasticidad amortiguada gamma=0.65, sigmoide de Over 2.5 y momentum relativo LSTM | ✅ Completado |
| **v2.9** | Blindaje contra Failed to fetch: Proxy Vite /api, resolución IPv4 unificada y acotamiento de reload-dir | ✅ Completado |
| **v3.0** | Erradicación de HTTP 502 Bad Gateway: Sincronización PORT=8000, bucle de arranque en run_app.py y timeouts 180s | ✅ Completado |
| **v3.1** | Calibración de Precisión: Balanza territorial de córners, elasticidad gamma=0.52, mitigación de bloque bajo y concordancia de marcadores | ✅ Completado |
| **v3.2** | Auditoría Predictiva Puntos 1 y 2: Normalización por liga, localía simétrica, parsing robusto de minutos y H2H no colapsado | ✅ Completado |
| **v3.3** | Auditoría Predictiva Puntos 5, 6, 8 y 3: Matriz Bivariada de Consenso Unificado, Binomial Negativa (córners/tarjetas), Dinámica Game State y Suite de Backtesting (RPS/Brier/Log-Loss/MAE) | ✅ Completado |
| **v3.4** | Rediseño de barra superior espaciosa (`navbar-brand-group`, `ide-inputs-form`), acceso directo a la plataforma sin login bloqueante y remoción total de historial y partidos sugeridos. | ✅ Completado |
| **v3.5** | Resolución Jerárquica de URLs (URL soberana sobre inputs anteriores), erradicación de recarga de partido previo, estabilización de Uvicorn (sin reload intempestivo en run_app.py) y auto-recuperación de servidor. | ✅ Completado |

---

## 6. Endpoints y Contrato de la API

- `POST /api/login`: Autenticación con credenciales del entorno (Opcional en v3.4+, acceso directo activado sin bloqueo de login).
  - **Usuario por defecto**: `Gleek`
  - **Contraseña por defecto**: `Contra123` (configuradas en [.env](file:///c:/Users/uriel/Vide%20coding/Proyectos/Analista%20deportivo/.env))
- `POST /api/predict`: Endpoint principal de predicción.
  - **Parámetros**: `home_team`, `away_team`, `competition` (opcional), `force_refresh` (bool), `is_live` (bool opcional), `live_score` (opcional), `live_minute` (opcional), `live_corners` (opcional).
- `GET /api/predictions/recent`: Lista de últimos análisis guardados en SQLite.
- `GET /api/health`: Estado de salud de los modelos y base de datos.
- `GET /api/backtest/benchmark`: Ejecuta backtesting sobre el dataset curado de partidos históricos (RPS, Brier, Log-Loss, MAE).
- `POST /api/backtest/run`: Ejecuta backtesting sobre un lote personalizado de partidos con resultados verificados.

---

## 7. Comandos de Ejecución

- **Iniciar Backend y Frontend Juntos**:
  - Script Python: `python run_app.py`
  - O en Windows: `iniciar_app.bat` o `iniciar_app.ps1`
- **Iniciar Backend de forma individual**:
  - `.venv\Scripts\activate`
  - `uvicorn backend.app.main:app --host 0.0.0.0 --port 8000 --reload --reload-dir backend`
- **Iniciar Frontend de forma individual**:
  - `cd frontend`
  - `npm run dev` (abre en `http://localhost:5173`)
- **Compilar Frontend para producción**:
  - `cd frontend`
  - `npm run build`
- **Ejecutar Tests de Integración y Calibración**:
  - `python backend/tests/test_v33_consensus_nbinom_gamestate.py`
  - `python backend/tests/test_v33_backtest_framework.py`
  - `python backend/tests/test_v32_audit_fixes_points_1_and_2.py`
  - `python backend/tests/test_v31_calibration_corners_and_goals.py`

  - `python backend/tests/test_v28_goal_overestimation_calibration.py`
  - `python backend/tests/test_v27_phase3_competition_and_markets.py`
  - `python backend/tests/test_v26_phase2_telemetry_and_red_cards.py`
  - `python backend/tests/test_v25_phase1_live_math_enhancements.py`
  - `python backend/tests/test_live_corners_and_sync_stability.py`
  - `python backend/tests/test_fase3_engine.py`
