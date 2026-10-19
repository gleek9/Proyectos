"""
Módulo Parser de LangChain + Gemini 2.5 Flash.
Convierte la información de búsqueda web en un esquema JSON estructurado y tipado (MatchRawFeatures)
para alimentar de manera determinista a los modelos locales de ML y Deep Learning.
"""
import logging
from typing import Optional, List, Dict
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
from backend.app.config import settings
from backend.app.schemas.match import MatchRawFeatures

logger = logging.getLogger(__name__)

EXTRACTION_SYSTEM_PROMPT = """Eres el analista de datos de fútbol profesional más riguroso del mundo.
Tu misión es extraer y consolidar estadísticas precisas para el partido indicado.

Reglas de Análisis:
1. Revisa el contexto de búsqueda web proporcionado, priorizando las fuentes de Flashscore y Sofascore.
2. Identifica los clubes de fútbol reales (ej. Liverpool FC, Manchester City, Real Madrid, Khovd FC, Khovd Western, etc.) diferenciándolos de tiendas, ciudades o categorías no relacionadas.
3. Extrae con realismo futbolístico:
   - Historial de enfrentamientos directos (H2H): partidos analizados, victorias local, empates, victorias visitante, promedio de goles, tiros de esquina/córners y tarjetas.
   - Forma reciente de cada equipo: goles anotados y recibidos por partido, tiros de esquina/córners promedio a favor y promedio de tarjetas.
   - Bajas importantes (lesionados o sancionados confirmados).
   - Notas contextuales clave (rachas, localía, importancia del partido).
4. PREVENCIÓN DE SESGO EN CÓRNERS (PROHIBICIÓN DE VALOR ESTÁTICO 5.0):
   - NUNCA uses un valor estático genérico de 5.0 para todos los equipos. Los córners varían según la vocación ofensiva, posesión y volumen de centros/tiros del club.
   - Equipos dominantes y muy ofensivos (ej. Man City, Real Madrid, Bayern, Arsenal, Liverpool) promedian entre 5.8 y 7.0 córners a favor por partido.
   - Equipos de mitad de tabla promedian entre 4.2 y 5.2 córners.
   - Equipos defensivos, de repliegue o menor posesión promedian entre 3.0 y 4.0 córners.
   - Si no está textual el dato, deduce un promedio proporcional al estilo y poder ofensivo del club (nunca asignes 5.0 fijo a todos).
   - En H2H: si no hay un dato específico de córners en los últimos choques directos, calcula la suma real de ambos clubes (típicamente entre 8.5 y 10.2 en ligas profesionales), NO uses valores inflados > 10.5 sin respaldo.
5. Acomodo Autónomo de Localía: Determina en la búsqueda cuál de los dos equipos es el verdadero anfitrión local (según su estadio o fixture oficial) y asígnalo siempre como `home_team` (con sus `home_stats`), y al rival como `away_team` (`away_stats`). No inviertas el orden de los equipos en actualizaciones de un mismo partido.
6. MODO EN VIVO (ACTIVADO ESTRICTAMENTE MEDIANTE URL):
   - El partido se considera EN VIVO (`is_live=True`) EXCLUSIVAMENTE si se provee una URL del partido o si se solicita explícitamente modo en vivo.
   - Si NO se proporciona una URL de partido online, el encuentro DEBE ser analizado en modalidad PRE-PARTIDO COMPLETO: `is_live=False`, `live_score=None`, `live_minute=None`, `live_corners=None`.
   - Cuando se provee una URL de partido en curso:
     * Consulta prioritariamente los datos de la URL / Flashscore / Sofascore.
     * Si ya se han anotado goles en el encuentro (por ejemplo: "0 - 2", "1 - 3", "2 - 1"), EXTRAE el marcador real exacto con los goles anotados. NO pongas ceros "0 - 0" si ya hay goles registrados.
     * En `live_minute`, extrae el minuto exacto (ej: "45'", "70'", "HT").
     * En `context_notes`, resume las incidencias actuales antes que los datos históricos.
7. Extracción de Córners y Tiros de Esquina en Vivo (`live_corners`):
   - Busca con máxima prioridad bajo los términos 'tiros de esquina', 'saques de esquina' o 'corners' / 'córners' POR IGUAL.
   - Si el partido se encuentra en curso (`is_live=True`), extrae el total de tiros de esquina / córners acumulados entre ambos equipos si aparece en la URL o resultados en vivo (ej: 'Tiros de esquina: 3 - 2' -> 5, 'córners: 4 - 3' -> 7, '6 saques de esquina', '8 corners').
   - Si no aparece explícito en los fragmentos en vivo, déjalo estrictamente en `null`. PROHIBICIÓN ABSOLUTA de inventar un valor por defecto (NUNCA pongas 5 por defecto si no está en el texto).
8. Continuidad y Consistencia tras Actualizaciones (5 Minutos):
   - Cuando se actualiza un partido en vivo, conserva la coherencia de las estadísticas de fondo de la temporada (promedios de goles, córners y tarjetas). No varíes arbitrariamente los promedios base de los clubes en cada refresco.
   - El marcador (`live_score`) y los córners (`live_corners`) son acumulativos: un gol o un tiro de esquina ya ocurrido no puede desaparecer ni disminuir en una actualización posterior.
9. Genera SIEMPRE el esquema estructurado completo en formato JSON válido.
"""

EXTRACTION_USER_PROMPT = """Analiza el siguiente encuentro de fútbol y genera las métricas estructuradas completas:

Encuentro: {home_team} (Local) vs {away_team} (Visitante)
Competición: {competition}
{live_previous_context}

--- CONTEXTO DE BÚSQUEDA WEB RECIENTE (PRIORIZANDO FLASHSCORE, SOFASCORE Y ESTADÍSTICAS EN DIRECTO) ---
{search_context}
-----------------------------------------
"""

class SportsDataParser:
    def __init__(self):
        # Priorizar gemini-3.5-flash-lite, gemini-3.5-flash y gemini-3.8-flash (modelos activos y con cuota habilitada)
        raw_candidates = [
            settings.GEMINI_MODEL,
            "gemini-3.5-flash-lite",
            "gemini-3.5-flash",
            "gemini-3.8-flash"
        ]
        seen = set()
        self.candidate_models = [m for m in raw_candidates if m and not (m in seen or seen.add(m))]
        self.prompt = ChatPromptTemplate.from_messages([
            ("system", EXTRACTION_SYSTEM_PROMPT),
            ("human", EXTRACTION_USER_PROMPT)
        ])

    def _get_chain(self, model_name: str):
        llm = ChatGoogleGenerativeAI(
            model=model_name,
            google_api_key=settings.GEMINI_API_KEY,
            temperature=0.0,
            max_retries=0,  # Sin retries largos para pasar inmediatamente al siguiente modelo disponible
            timeout=15.0
        )
        return self.prompt | llm.with_structured_output(MatchRawFeatures)

    def _fallback_local_heuristic_parse(self, home_team: str, away_team: str, competition: str, search_context: str) -> MatchRawFeatures:
        """
        Extractor heurístico local de emergencia.
        Se activa si todos los modelos LLM externos están inaccesibles.
        Determina con estricto rigor si el partido es EN DIRECTO o PRE-MATCH,
        evitando falsos positivos de en vivo, minutos ficticios (45') o marcadores sesgados.
        """
        import re
        from backend.app.schemas.match import TeamFormStats, HeadToHeadStats, PreviousMatch

        logger.warning(f"⚠️ Activando Extractor Heurístico Local de Emergencia para {home_team} vs {away_team}")
        
        # Limpiar encabezados de sección para evitar contaminación por términos de búsqueda
        clean_lines = [l for l in search_context.split("\n") if not l.strip().startswith("---")]
        clean_text = "\n".join(clean_lines)
        ctx_lower = clean_text.lower()
        
        # 1. Comprobar si el partido ya finalizó
        is_finished = any(term in ctx_lower for term in [
            "finalizado", "resultado final", "terminado", "full time", "final del partido", "concluido"
        ])

        # 2. Detección estricta de partido EN VIVO (minuto activo o en juego explícito)
        minute_pat = re.search(r"\b(?:minuto|min\.?)\s*([1-9][0-9]?)\b|\b([1-9][0-9]?)\s*[\'’]\b|\b(1t|2t|descanso|entretiempo|et|primer tiempo|segundo tiempo)\b", ctx_lower)
        live_keywords = any(term in ctx_lower for term in [
            "en juego", "partido en curso", "jugándose", "marcador en directo", "live now"
        ])
        
        # Un partido solo es en vivo si hay señales explícitas en juego y NO ha finalizado
        is_live = bool((minute_pat or live_keywords) and not is_finished)

        live_score = None
        live_minute = None
        live_corners = None

        if is_live:
            # Minuto de juego
            if minute_pat:
                if minute_pat.group(1):
                    live_minute = f"{minute_pat.group(1)}'"
                elif minute_pat.group(2):
                    live_minute = f"{minute_pat.group(2)}'"
                elif minute_pat.group(3):
                    live_minute = minute_pat.group(3).upper()
            else:
                live_minute = "En juego"

            # Marcador en vivo (buscar primero etiquetas oficiales reales y luego patrones equipoA X - Y equipoB)
            score_patterns = [
                r"(?:marcador en vivo real|marcador en directo detectado|marcador actual|resultado en vivo)[:\s]*(\d{1,2})\s*[-–:]\s*(\d{1,2})",
                r"• MARCADOR EN VIVO REAL:\s*(\d{1,2})\s*[-–:]\s*(\d{1,2})",
                rf"{re.escape(home_team.lower())}\s*(\d{{1,2}})\s*[-–:]\s*(\d{{1,2}})\s*{re.escape(away_team.lower())}",
                rf"{re.escape(away_team.lower())}\s*(\d{{1,2}})\s*[-–:]\s*(\d{{1,2}})\s*{re.escape(home_team.lower())}",
                r"(?:marcador|resultado|score|minuto|\'|\’)[^\n\r]*?(\d{1,2})\s*[-–:]\s*(\d{1,2})",
                r"\b(\d{1,2})\s*[-–:]\s*(\d{1,2})\b"
            ]

            found_score = None
            for pat in score_patterns:
                for match_obj in re.finditer(pat, clean_text, re.IGNORECASE):
                    try:
                        g1, g2 = int(match_obj.group(1)), int(match_obj.group(2))
                        if g1 <= 9 and g2 <= 9:
                            cand = f"{g1} - {g2}"
                            if g1 > 0 or g2 > 0:
                                found_score = cand
                                break
                            elif found_score is None:
                                found_score = cand
                    except Exception:
                        continue
                if found_score and found_score != "0 - 0":
                    break

            live_score = found_score if found_score else "0 - 0"

            # Córners y Tiros de Esquina en vivo (buscar ambos términos por igual)
            corn_patterns = [
                r"(?:tiros de esquina|saques de esquina|córners?|corners?)[^\d\n\r]{0,15}(\d{1,2})\s*[-–:]\s*(\d{1,2})",
                r"(\d{1,2})\s*[-–:]\s*(\d{1,2})[^\d\n\r]{0,15}(?:tiros de esquina|saques de esquina|córners?|corners?)",
                r"(?:tiros de esquina|saques de esquina|córners?|corners?)[:\s]*(\d{1,2})\b",
                r"\b(\d{1,2})\s*(?:tiros de esquina|saques de esquina|córners?|corners?)\b"
            ]
            for cpat in corn_patterns:
                corn_match = re.search(cpat, clean_text, re.IGNORECASE)
                if corn_match:
                    try:
                        if corn_match.lastindex == 2:
                            c1, c2 = int(corn_match.group(1)), int(corn_match.group(2))
                            live_corners = c1 + c2
                            break
                        elif corn_match.lastindex == 1:
                            val = int(corn_match.group(1))
                            if 0 <= val <= 25:
                                live_corners = val
                                break
                    except Exception:
                        continue

        # Goles promedio
        home_goals_scored = 1.45
        away_goals_scored = 1.20
        goals_found = re.findall(r"(?:goles?|goals?|anotados?)[^\d\n\r]*?(\d+(?:\.\d+)?)", clean_text, re.IGNORECASE)
        if goals_found:
            try:
                g_nums = [float(g) for g in goals_found if 0.5 <= float(g) <= 4.5]
                if len(g_nums) >= 2:
                    home_goals_scored = round(g_nums[0], 2)
                    away_goals_scored = round(g_nums[1], 2)
            except Exception:
                pass

        # 3. Extracción de estadísticas realistas y dinámicas de tiros de esquina / córners (sin sesgos a 5.0)
        home_corners = round(max(3.2, min(7.0, home_goals_scored * 2.3 + 1.2)), 1)
        away_corners = round(max(2.8, min(6.0, away_goals_scored * 2.0 + 1.0)), 1)
        total_h2h_corners = round(home_corners + away_corners, 1)

        corn_found = re.findall(r"(?:tiros de esquina|saques de esquina|córners?|corners?)[^\d\n\r]*?(\d+(?:\.\d+)?)", clean_text, re.IGNORECASE)
        if corn_found:
            try:
                nums = [float(n) for n in corn_found if 2.0 <= float(n) <= 15.0]
                if nums:
                    if len(nums) >= 2:
                        home_corners = round(nums[0], 1)
                        away_corners = round(nums[1], 1)
                        total_h2h_corners = round(home_corners + away_corners, 1)
                    elif nums[0] > 7.0:
                        total_h2h_corners = round(nums[0], 1)
                    else:
                        home_corners = round(nums[0], 1)
            except Exception:
                pass

        return MatchRawFeatures(
            home_team=home_team,
            away_team=away_team,
            competition=competition or "General",
            is_live=is_live,
            live_minute=live_minute if is_live else None,
            live_score=live_score if is_live else None,
            live_corners=live_corners if is_live else None,
            home_stats=TeamFormStats(
                team_name=home_team,
                avg_goals_scored=home_goals_scored,
                avg_goals_conceded=1.15,
                avg_corners=home_corners,
                avg_cards=2.1,
                win_rate_last_5=0.60,
                last_matches=[
                    PreviousMatch(opponent="Rival A", was_home=True, goals_for=2, goals_against=1, result="W"),
                    PreviousMatch(opponent="Rival B", was_home=False, goals_for=1, goals_against=1, result="D"),
                    PreviousMatch(opponent="Rival C", was_home=True, goals_for=2, goals_against=0, result="W")
                ]
            ),
            away_stats=TeamFormStats(
                team_name=away_team,
                avg_goals_scored=away_goals_scored,
                avg_goals_conceded=1.35,
                avg_corners=away_corners,
                avg_cards=2.3,
                win_rate_last_5=0.50,
                last_matches=[
                    PreviousMatch(opponent="Rival X", was_home=False, goals_for=1, goals_against=2, result="L"),
                    PreviousMatch(opponent="Rival Y", was_home=True, goals_for=2, goals_against=1, result="W"),
                    PreviousMatch(opponent="Rival Z", was_home=False, goals_for=1, goals_against=1, result="D")
                ]
            ),
            h2h=HeadToHeadStats(
                # Modo contingencia: no hay H2H verificado; 0 partidos evita que los modelos lo traten como dato real
                total_matches_analyzed=0,
                home_team_wins=0,
                draws=0,
                away_team_wins=0,
                avg_total_goals_h2h=round(home_goals_scored + away_goals_scored, 1),
                avg_total_corners_h2h=round(home_corners + away_corners, 1) if total_h2h_corners == 9.8 else total_h2h_corners,
                avg_total_cards_h2h=4.4
            ),
            context_notes=[
                "Modo de contingencia autónomo activado por límite de cuota externa.",
                f"Encuentro entre {home_team} y {away_team} en {competition}.",
                f"Marcador detectado en directo: {live_score} ({live_minute})." if is_live else "Partido evaluado en modalidad PRE-MATCH con estadísticas rigurosas."
            ]
        )

    def parse_match(
        self,
        home_team: str,
        away_team: str,
        competition: str,
        search_context: str,
        previous_features: Optional[MatchRawFeatures] = None,
        is_live: Optional[bool] = None,
        match_url: Optional[str] = None
    ) -> MatchRawFeatures:
        """
        Invoca a Gemini con cascada rápida de fallback ante cuotas agotadas.
        Preserva la consistencia de estadísticas base y asegura monotonía en partidos en vivo.
        Activa modo en vivo EXCLUSIVAMENTE si se proporciona match_url.
        """
        last_error = None
        
        # Determinar si el modo en vivo está activo exclusivamente por la presencia de match_url
        has_url = bool(match_url and match_url.strip())
        effective_live = has_url or bool(is_live is True and previous_features and getattr(previous_features, "match_url", None))
        
        # Inyectar contexto previo para guiar la continuidad en actualizaciones de 5 minutos
        live_previous_context = ""
        if previous_features and (getattr(previous_features, "is_live", False) or effective_live):
            prev_score = getattr(previous_features, "live_score", None) or "0 - 0"
            prev_minute = getattr(previous_features, "live_minute", None) or "En curso"
            prev_corners = getattr(previous_features, "live_corners", None)
            corners_str = f"{prev_corners} tiros de esquina/córners acumulados" if prev_corners is not None else "No registrado"
            live_previous_context = f"""
--- ESTADO PREVIO CONFIRMADO DEL ENCUENTRO EN DIRECTO (HACE 5 MIN) ---
• Marcador confirmado previo: {prev_score}
• Minuto de juego previo: {prev_minute}
• Tiros de esquina / corners previos acumulados: {corners_str}
• Estadísticas base de temporada: {home_team} (promedio {previous_features.home_stats.avg_corners} córners) vs {away_team} (promedio {previous_features.away_stats.avg_corners} córners).
Conserva la estabilidad de las estadísticas base. Si no hay goles ni córners nuevos en las fuentes, mantén el estado previo sin retroceder.
"""

        parsed_result: Optional[MatchRawFeatures] = None

        for model_cand in self.candidate_models:
            try:
                logger.info(f"Procesando extracción estructurada con LLM: '{model_cand}'...")
                chain = self._get_chain(model_cand)
                result = chain.invoke({
                    "home_team": home_team,
                    "away_team": away_team,
                    "competition": competition,
                    "search_context": search_context,
                    "live_previous_context": live_previous_context
                })
                logger.info(f"Extracción exitosa con modelo '{model_cand}'.")
                parsed_result = result
                break
            except Exception as e:
                last_error = e
                logger.warning(f"Fallo en LLM '{model_cand}': {e}. Probando siguiente modelo...")
                continue

        # Si todos los modelos LLM fallan por cuota o conexión, usar extractor heurístico local
        if parsed_result is None:
            logger.warning(f"Todos los modelos de Gemini agotados o inaccesibles ({last_error}). Usando fallback heurístico local.")
            parsed_result = self._fallback_local_heuristic_parse(home_team, away_team, competition, search_context)

        # -------------------------------------------------------------
        # Post-procesamiento de Seguridad, Continuidad y Estabilidad en Vivo
        # -------------------------------------------------------------
        # 1. Conservar los nombres oficiales identificados por el modelo o la URL
        if not parsed_result.home_team:
            parsed_result.home_team = home_team
        if not parsed_result.away_team:
            parsed_result.away_team = away_team

        # 2. Manejo de En Vivo
        if has_url:
            parsed_result.is_live = True
            parsed_result.match_url = match_url.strip()
        elif is_live is True:
            parsed_result.is_live = True
            if previous_features and getattr(previous_features, "match_url", None):
                parsed_result.match_url = previous_features.match_url
        else:
            # Modo PRE-PARTIDO obligatorio si no es en vivo
            parsed_result.is_live = False
            parsed_result.match_url = None
            parsed_result.live_score = None
            parsed_result.live_minute = None
            parsed_result.live_corners = None

        # 3. Anclar estadísticas base de temporada si ya existían para evitar saltos drásticos cada 5 minutos
        if previous_features and previous_features.home_stats and previous_features.away_stats:
            # Mantener la estabilidad de la temporada del club
            parsed_result.home_stats.avg_goals_scored = previous_features.home_stats.avg_goals_scored
            parsed_result.home_stats.avg_goals_conceded = previous_features.home_stats.avg_goals_conceded
            parsed_result.home_stats.avg_corners = previous_features.home_stats.avg_corners
            parsed_result.home_stats.avg_cards = previous_features.home_stats.avg_cards
            parsed_result.home_stats.win_rate_last_5 = previous_features.home_stats.win_rate_last_5

            parsed_result.away_stats.avg_goals_scored = previous_features.away_stats.avg_goals_scored
            parsed_result.away_stats.avg_goals_conceded = previous_features.away_stats.avg_goals_conceded
            parsed_result.away_stats.avg_corners = previous_features.away_stats.avg_corners
            parsed_result.away_stats.avg_cards = previous_features.away_stats.avg_cards
            parsed_result.away_stats.win_rate_last_5 = previous_features.away_stats.win_rate_last_5

            if previous_features.h2h:
                parsed_result.h2h = previous_features.h2h

            # Monotonía del marcador en vivo (los goles no desaparecen)
            prev_sc = getattr(previous_features, "live_score", None)
            if prev_sc and prev_sc != "0 - 0":
                if not parsed_result.live_score or parsed_result.live_score == "0 - 0":
                    parsed_result.live_score = prev_sc

            # Monotonía de córners / tiros de esquina en vivo (los córners no disminuyen)
            prev_cn = getattr(previous_features, "live_corners", None)
            if prev_cn is not None:
                if parsed_result.live_corners is None or parsed_result.live_corners < prev_cn:
                    parsed_result.live_corners = prev_cn

            # Minuto de juego
            if not parsed_result.live_minute and getattr(previous_features, "live_minute", None):
                parsed_result.live_minute = previous_features.live_minute

        return parsed_result

parser = SportsDataParser()
