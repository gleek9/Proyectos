"""
Módulo de Búsqueda y Extracción Web de Estadísticas Deportivas (Katakuri v2.3).
Recopila datos en tiempo real mediante:
1. Conexión resiliente a Sofascore API (vía primp para evitar bloqueos Cloudflare / 403)
   para telemetría en vivo: marcador exacto, minuto activo, córners acumulados, goles e incidencias.
2. Extracción directa de páginas web (Flashscore, Sofascore, etc.) con metadatos de alto valor.
3. Búsqueda web complementaria con DuckDuckGo (DDGS) con desambiguación deportiva y anti-throttling.
"""
import logging
import time
import re
from typing import List, Dict, Any, Optional, Tuple
from ddgs import DDGS

try:
    import primp
    _HAS_PRIMP = True
except ImportError:
    _HAS_PRIMP = False

import httpx
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

class SportsWebScraper:
    def __init__(self, max_results_per_query: int = 3):
        self.max_results = max_results_per_query
        self.last_url_telemetry: Dict[str, Any] = {}

    def get_last_url_telemetry(self) -> Dict[str, Any]:
        """Retorna la última telemetría extraída de una URL de partido online."""
        return dict(self.last_url_telemetry)

    def _get_client(self):
        """Retorna un cliente HTTP resiliente (primp para evitar 403 de Cloudflare o httpx como fallback)."""
        if _HAS_PRIMP:
            try:
                return primp.Client(follow_redirects=True, timeout=8.0)
            except Exception as e:
                logger.warning(f"Error inicializando primp.Client: {e}. Usando httpx.")
        
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
            "Accept-Language": "es-ES,es;q=0.9,en;q=0.8"
        }
        return httpx.Client(timeout=8.0, follow_redirects=True, headers=headers)

    def search_query(self, query: str) -> List[Dict[str, str]]:
        """Realiza una búsqueda de texto en DuckDuckGo y retorna snippets relevantes."""
        results = []
        try:
            with DDGS() as ddgs:
                raw_results = ddgs.text(query, max_results=self.max_results)
                if raw_results:
                    for r in raw_results:
                        results.append({
                            "title": r.get("title", ""),
                            "snippet": r.get("body", ""),
                            "url": r.get("href", "")
                        })
        except Exception as e:
            logger.warning(f"Error buscando '{query}': {e}")
        return results

    def _extract_sofascore_event_id(self, url: str) -> Optional[str]:
        """Extrae el ID numérico de evento de Sofascore desde la URL o el HTML."""
        if not url:
            return None
        # 1. Patrón #id:1234567 o /id:1234567
        m = re.search(r'#id:(\d{6,12})', url) or re.search(r'/id:(\d{6,12})', url)
        if m:
            return m.group(1)
        # 2. Patrón /match/.../1234567
        m2 = re.search(r'/(\d{7,12})(?:/|$|\?|#)', url)
        if m2:
            return m2.group(1)
        return None

    def _scrape_sofascore_api(self, eid: str) -> Tuple[str, Dict[str, Any]]:
        """Consulta directamente la API oficial de Sofascore para extraer datos 100% reales en vivo."""
        telemetry: Dict[str, Any] = {}
        text_lines: List[str] = []
        client = self._get_client()
        try:
            # 1. Evento principal
            r_ev = client.get(f"https://api.sofascore.com/api/v1/event/{eid}")
            if r_ev.status_code == 200:
                ev = r_ev.json().get("event", {})
                h_name = ev.get("homeTeam", {}).get("name", "")
                a_name = ev.get("awayTeam", {}).get("name", "")
                status_info = ev.get("status", {})
                status_desc = status_info.get("description", "En juego")
                status_type = status_info.get("type", "")

                h_score_dict = ev.get("homeScore", {})
                a_score_dict = ev.get("awayScore", {})
                hs = h_score_dict.get("current")
                as_ = a_score_dict.get("current")
                if hs is None:
                    hs = h_score_dict.get("display")
                if as_ is None:
                    as_ = a_score_dict.get("display")

                score_str = f"{hs} - {as_}" if (hs is not None and as_ is not None) else None
                if score_str:
                    telemetry["score"] = score_str

                # Calcular minuto exacto
                minute_str = None
                time_dict = ev.get("time", {})
                curr_period_ts = time_dict.get("currentPeriodStartTimestamp")
                if status_type == "inprogress" and curr_period_ts:
                    elapsed = int(time.time() - curr_period_ts)
                    if "2nd" in status_desc.lower() or status_desc == "2T":
                        m_calc = min(90, max(45, 45 + elapsed // 60))
                        minute_str = f"{m_calc}'"
                    elif "1st" in status_desc.lower() or status_desc == "1T":
                        m_calc = min(45, max(1, elapsed // 60))
                        minute_str = f"{m_calc}'"
                
                if not minute_str:
                    if status_desc.upper() in ["HT", "DESCANSO", "ENTRETIEMPO"]:
                        minute_str = "HT"
                    elif "2nd" in status_desc.lower():
                        minute_str = "2T"
                    elif "1st" in status_desc.lower():
                        minute_str = "1T"
                    elif status_desc:
                        minute_str = status_desc

                if minute_str:
                    telemetry["minute"] = minute_str

                telemetry["home_team"] = h_name
                telemetry["away_team"] = a_name

                text_lines.append(f"--- [DATOS EN VIVO DIRECTOS DE SOFASCORE API (EVENTO #{eid})] ---")
                text_lines.append(f"• Encuentro: {h_name} vs {a_name}")
                text_lines.append(f"• Estado del partido: {status_desc} ({status_type})")
                if score_str:
                    text_lines.append(f"• MARCADOR EN VIVO REAL: {score_str}")
                if minute_str:
                    text_lines.append(f"• MINUTO DE JUEGO ACTUAL: {minute_str}")

                # 2. Estadísticas de Córners y Tiros
                r_st = client.get(f"https://api.sofascore.com/api/v1/event/{eid}/statistics")
                if r_st.status_code == 200:
                    for period in r_st.json().get("statistics", []):
                        if period.get("period") == "ALL":
                            for grp in period.get("groups", []):
                                for item in grp.get("statisticsItems", []):
                                    name_low = item.get("name", "").lower()
                                    if "corner" in name_low:
                                        ch = int(item.get("home", 0))
                                        ca = int(item.get("away", 0))
                                        tot_corn = ch + ca
                                        telemetry["corners"] = tot_corn
                                        text_lines.append(f"• CÓRNERS EN VIVO REALES: {tot_corn} saques de esquina acumulados ({h_name}: {ch}, {a_name}: {ca})")
                                    elif "ball possession" in name_low:
                                        ph = item.get("home")
                                        pa = item.get("away")
                                        try:
                                            telemetry["possession_home"] = float(str(ph).replace("%", "").strip())
                                            telemetry["possession_away"] = float(str(pa).replace("%", "").strip())
                                        except Exception:
                                            pass
                                        text_lines.append(f"• Posesión: {ph}% - {pa}%")
                                    elif "shots on goal" in name_low or "shots on target" in name_low:
                                        sh = item.get("home")
                                        sa = item.get("away")
                                        try:
                                            telemetry["shots_on_target_home"] = int(sh)
                                            telemetry["shots_on_target_away"] = int(sa)
                                        except Exception:
                                            pass
                                        text_lines.append(f"• Tiros a puerta: {sh} - {sa}")
                                    elif "red card" in name_low:
                                        rh = item.get("home", 0)
                                        ra = item.get("away", 0)
                                        try:
                                            telemetry["red_cards_home"] = max(telemetry.get("red_cards_home", 0), int(rh))
                                            telemetry["red_cards_away"] = max(telemetry.get("red_cards_away", 0), int(ra))
                                        except Exception:
                                            pass
                                        text_lines.append(f"• Tarjetas rojas: {rh} - {ra}")

                # 3. Incidencias de goles y tarjetas
                r_inc = client.get(f"https://api.sofascore.com/api/v1/event/{eid}/incidents")
                if r_inc.status_code == 200:
                    incidents = r_inc.json().get("incidents", [])
                    goal_lines = []
                    card_lines = []
                    for it in incidents:
                        itype = it.get("incidentType")
                        itime = it.get("time")
                        pname = it.get("player", {}).get("name", "Jugador")
                        is_home = it.get("isHome", True)
                        if itype in ["goal", "inGamePenalty"]:
                            gh = it.get("homeScore")
                            ga = it.get("awayScore")
                            goal_lines.append(f"Minuto {itime}': Gol de {pname} ({gh}-{ga})")
                        elif itype == "card":
                            card_color = it.get("incidentClass", "tarjeta")
                            card_lines.append(f"Minuto {itime}': {card_color.capitalize()} a {pname}")
                            if card_color in ["red", "yellowRed"]:
                                if is_home:
                                    telemetry["red_cards_home"] = telemetry.get("red_cards_home", 0) + 1
                                else:
                                    telemetry["red_cards_away"] = telemetry.get("red_cards_away", 0) + 1
                    if goal_lines:
                        text_lines.append("• Goles registrados en directo:")
                        text_lines.extend([f"  - {g}" for g in goal_lines[:5]])
                    if card_lines:
                        text_lines.append("• Tarjetas registradas:")
                        text_lines.extend([f"  - {c}" for c in card_lines[:4]])

        except Exception as e:
            logger.warning(f"Error consultando Sofascore API para evento #{eid}: {e}")

        return "\n".join(text_lines), telemetry

    def _get_team_recent_history_from_sofascore(self, team_name: str) -> List[Dict[str, Any]]:
        """Busca un equipo en Sofascore y obtiene sus últimos 5 resultados reales."""
        if not team_name or len(team_name.strip()) < 2:
            return []
        client = self._get_client()
        recent = []
        try:
            r = client.get(f"https://api.sofascore.com/api/v1/search/all?q={team_name.strip()}")
            if r.status_code == 200:
                tid = None
                for it in r.json().get("results", []):
                    if it.get("type") == "team":
                        tid = it.get("entity", {}).get("id")
                        break
                if tid:
                    r_last = client.get(f"https://api.sofascore.com/api/v1/team/{tid}/events/last/0")
                    if r_last.status_code == 200:
                        events = r_last.json().get("events", [])
                        for ev in events[:5]:
                            h = ev.get("homeTeam", {}).get("name")
                            a = ev.get("awayTeam", {}).get("name")
                            hs = ev.get("homeScore", {}).get("current")
                            as_ = ev.get("awayScore", {}).get("current")
                            status = ev.get("status", {}).get("description")
                            if hs is not None and as_ is not None:
                                recent.append({
                                    "match": f"{h} {hs} - {as_} {a}",
                                    "home": h,
                                    "away": a,
                                    "score": f"{hs} - {as_}",
                                    "status": status
                                })
        except Exception as e:
            logger.debug(f"Sofascore team search error para '{team_name}': {e}")
        return recent

    def _extract_flashscore_match_id(self, url: str, html: str = "") -> Optional[str]:
        """Extrae el ID del partido de Flashscore desde la URL o el HTML."""
        if not url:
            return None
        # 1. Parámetro query: ?mid=lYm0NHUa, &mid=lYm0NHUa, ?id=...
        m_q = re.search(r'[?&](?:mid|id)=([a-zA-Z0-9]{7,10})', url)
        if m_q:
            return m_q.group(1)

        # 2. En la ruta después de guión o barra: ej /pegeia-apoel-4EVDq0HO/ o /partido/4EVDq0HO/
        m_slug = re.search(r'[-/]([a-zA-Z0-9]{8})(?:/|$|\?|#)', url)
        if m_slug:
            cand = m_slug.group(1)
            if not cand.isdigit() and cand.lower() not in ['partido', 'futbol', 'general', 'resumen', 'summary']:
                return cand

        # 3. En la ruta completa: cualquier segmento de 8 caracteres alfanuméricos
        m_path = re.findall(r'([a-zA-Z0-9]{8})(?:/|$|\?|#)', url)
        for cand in reversed(m_path):
            if not cand.isdigit() and cand.lower() not in ['partido', 'futbol', 'general', 'resumen', 'summary']:
                return cand

        # 4. En el HTML: event_id_c, event_id o feeds ninja
        if html:
            for pat in [
                r'"event_id_c"\s*:\s*"([a-zA-Z0-9]{7,10})"',
                r'event_id[\'"]?\s*[:=]\s*[\'"]([a-zA-Z0-9]{7,10})[\'"]',
                r'feed/dc_1_([a-zA-Z0-9]{7,10})',
                r'feed/df_st_1_([a-zA-Z0-9]{7,10})',
                r'data-event-id=[\'"]([a-zA-Z0-9]{7,10})[\'"]'
            ]:
                m_h = re.search(pat, html)
                if m_h:
                    return m_h.group(1)

        return None

    def _scrape_flashscore_feed(self, mid: str) -> Tuple[str, Dict[str, Any]]:
        """Consulta directamente los feeds oficiales de Flashscore Ninja para extraer marcador, minuto y córners en vivo."""
        telemetry: Dict[str, Any] = {}
        text_lines: List[str] = []
        client = self._get_client()
        headers = {"x-fsign": "SW9D1eZo"}
        try:
            # 1. Feed dc_1_{mid} (Marcador principal, penaltis y estado de partido)
            r_dc = client.get(f"https://global.flashscore.ninja/2/x/feed/dc_1_{mid}", headers=headers)
            dc_pairs = {}
            if r_dc.status_code == 200 and r_dc.text:
                dc_pairs = dict([item.split("÷") for item in r_dc.text.split("¬") if "÷" in item])

            # 2. Feed df_st_1_{mid} (Estadísticas completas: córners, posesión, tiros)
            r_st = client.get(f"https://global.flashscore.ninja/2/x/feed/df_st_1_{mid}", headers=headers)
            st_text = r_st.text if r_st.status_code == 200 else ""

            # 3. Feed df_sui_1_{mid} (Incidencias: goles, asistencias y tarjetas)
            r_sui = client.get(f"https://global.flashscore.ninja/2/x/feed/df_sui_1_{mid}", headers=headers)
            sui_text = r_sui.text if r_sui.status_code == 200 else ""

            # Extraer Marcador (comprobar pares DE-DF, DG-DH y AG-AH)
            score_str = None
            if dc_pairs.get("DE") is not None and dc_pairs.get("DF") is not None:
                score_str = f"{dc_pairs['DE']} - {dc_pairs['DF']}"
            elif dc_pairs.get("DG") is not None and dc_pairs.get("DH") is not None:
                score_str = f"{dc_pairs['DG']} - {dc_pairs['DH']}"
            elif dc_pairs.get("AG") is not None and dc_pairs.get("AH") is not None:
                score_str = f"{dc_pairs['AG']} - {dc_pairs['AH']}"

            # Extraer Córners en Directo
            corners = None
            if st_text:
                cm = re.search(r"Corner kicks¬SH÷(\d+)¬SI÷(\d+)", st_text)
                if cm:
                    corners = int(cm.group(1)) + int(cm.group(2))

            # Mapear Estado / Minuto
            status_map = {
                "1": "Programado",
                "2": "En directo",
                "12": "1T",
                "13": "2T",
                "38": "HT",
                "46": "HT",
                "6": "Prórroga",
                "7": "Penaltis",
                "3": "Finalizado",
                "10": "Tras la prórroga",
                "11": "Tras los penaltis",
                "45": "Por terminar",
                "42": "En espera",
                "4": "Aplazado",
                "37": "Suspendido"
            }
            db_code = dc_pairs.get("DB", "")
            minute_str = status_map.get(db_code, "En juego" if score_str else None)

            # Buscar minuto más reciente en incidencias si está en juego
            if sui_text and db_code in ["2", "12", "13"]:
                inc_mins = re.findall(r"IB÷(\d{1,2})'", sui_text)
                if inc_mins:
                    minute_str = f"{inc_mins[-1]}'"

            if score_str:
                telemetry["score"] = score_str
            if minute_str:
                telemetry["minute"] = minute_str
            if corners is not None:
                telemetry["corners"] = corners

            text_lines.append(f"--- [DATOS EN VIVO DIRECTOS DE FLASHSCORE (PARTIDO #{mid})] ---")
            if score_str:
                text_lines.append(f"• MARCADOR EN VIVO REAL: {score_str}")
            if minute_str:
                text_lines.append(f"• ESTADO / MINUTO ACTUAL: {minute_str}")
            if corners is not None:
                text_lines.append(f"• CÓRNERS EN VIVO REALES: {corners} saques de esquina acumulados")

            if st_text:
                pos = re.search(r"Ball possession¬SH÷(\d+)%¬SI÷(\d+)%", st_text)
                if pos:
                    text_lines.append(f"• Posesión: {pos.group(1)}% - {pos.group(2)}%")
                sog = re.search(r"Shots on target¬SH÷(\d+)¬SI÷(\d+)", st_text)
                if sog:
                    text_lines.append(f"• Tiros a puerta: {sog.group(1)} - {sog.group(2)}")

            if sui_text:
                goals = re.findall(r"IB÷(\d{1,2}\'?)[^~]*?IF÷([^¬~]+)[^~]*?IK÷Goal", sui_text)
                if goals:
                    text_lines.append("• Goles registrados:")
                    for gmin, gplayer in goals[:5]:
                        text_lines.append(f"  - Minuto {gmin}: Gol de {gplayer}")

        except Exception as e:
            logger.warning(f"Error consultando feeds de Flashscore para #{mid}: {e}")

        return "\n".join(text_lines), telemetry

    def find_live_match(self, home_team: str, away_team: str) -> Tuple[str, Dict[str, Any]]:
        """
        Busca de forma autónoma si los dos clubes están jugando un partido en directo
        en la lista de eventos en vivo de Sofascore. Si existe, extrae telemetría directa y oficial.
        """
        import unicodedata
        telemetry: Dict[str, Any] = {}
        text_lines: List[str] = []
        if not home_team or not away_team:
            return "", telemetry

        def norm_name(s: str) -> str:
            if not s:
                return ""
            s_clean = unicodedata.normalize('NFKD', s).encode('ASCII', 'ignore').decode('utf-8')
            s_clean = re.sub(r'\b(?:fc|cf|club|deportivo|atletico|real|sporting|u14|u17|u19|u20|u21|u23|sub\s*\d+)\b', '', s_clean, flags=re.IGNORECASE)
            return re.sub(r'[^a-z0-9]', '', s_clean.lower())

        nh = norm_name(home_team)
        na = norm_name(away_team)
        if len(nh) < 3 or len(na) < 3:
            return "", telemetry

        client = self._get_client()
        try:
            r = client.get("https://api.sofascore.com/api/v1/sport/football/events/live")
            if r.status_code == 200:
                events = r.json().get("events", [])
                matched_eid = None
                for ev in events:
                    eh = norm_name(ev.get("homeTeam", {}).get("name", ""))
                    ea = norm_name(ev.get("awayTeam", {}).get("name", ""))
                    h_match = (nh in eh or eh in nh) if (len(nh) >= 3 and len(eh) >= 3) else False
                    a_match = (na in ea or ea in na) if (len(na) >= 3 and len(ea) >= 3) else False
                    if (h_match and a_match) or ((nh in ea or ea in nh) and (na in eh or eh in na)):
                        matched_eid = str(ev.get("id"))
                        break

                if matched_eid:
                    logger.info(f"Partido en vivo localizado en Sofascore para {home_team} vs {away_team}: Evento #{matched_eid}")
                    sofa_txt, sofa_telem = self._scrape_sofascore_api(matched_eid)
                    if sofa_telem:
                        self.last_url_telemetry = sofa_telem
                    return sofa_txt, sofa_telem
        except Exception as e:
            logger.debug(f"Error en búsqueda autónoma de partido en vivo en Sofascore: {e}")

        return "", telemetry

    def scrape_url_content(self, url: str) -> str:
        """
        Descarga directamente el contenido textual estructurado de una URL de partido online
        (Flashscore, Sofascore, Google Matches, etc.) para extraer marcadores, minutos y córners exactos.
        """
        if not url or not url.strip():
            return ""

        clean_url = url.strip()
        self.last_url_telemetry = {}

        # 1. Caso Sofascore: Extracción de alta precisión vía API oficial
        if "sofascore.com" in clean_url.lower():
            eid = self._extract_sofascore_event_id(clean_url)
            if not eid:
                try:
                    client = self._get_client()
                    resp = client.get(clean_url)
                    if resp.status_code == 200:
                        m_id = re.search(r'"id":(\d{7,12})', resp.text)
                        if m_id:
                            eid = m_id.group(1)
                except Exception as e:
                    logger.debug(f"Error buscando ID en HTML de Sofascore: {e}")

            if eid:
                sofa_text, sofa_telem = self._scrape_sofascore_api(eid)
                if sofa_text:
                    self.last_url_telemetry = sofa_telem
                    logger.info(f"Telemetría en vivo extraída con éxito de Sofascore API: {self.last_url_telemetry}")
                    return sofa_text

        # 2. Caso Flashscore: Extracción de alta precisión vía Feeds Ninja oficiales
        if "flashscore" in clean_url.lower():
            mid = self._extract_flashscore_match_id(clean_url)
            client = self._get_client()
            resp_text = ""
            try:
                resp = client.get(clean_url)
                if resp.status_code == 200 and resp.text:
                    resp_text = resp.text
                    if not mid:
                        mid = self._extract_flashscore_match_id(clean_url, resp_text)
            except Exception as e:
                logger.debug(f"Error descargando HTML base de Flashscore: {e}")

            if mid:
                fs_text, fs_telem = self._scrape_flashscore_feed(mid)
                if fs_telem.get("score") or fs_telem.get("minute"):
                    self.last_url_telemetry = fs_telem
                    logger.info(f"Telemetría en vivo extraída con éxito de Flashscore Ninja: {self.last_url_telemetry}")
                    return fs_text

        # 3. Caso Genérico u otras páginas web: Descarga HTML con primp/httpx
        try:
            client = self._get_client()
            resp = client.get(clean_url)
            if resp.status_code == 200 and resp.text:
                soup = BeautifulSoup(resp.text, "html.parser")
                page_title = soup.title.string.strip() if soup.title and soup.title.string else ""

                # Extraer metadatos OpenGraph y Description
                og_title = ""
                og_desc = ""
                meta_desc = ""
                og_t = soup.find("meta", property="og:title")
                if og_t and og_t.get("content"):
                    og_title = og_t["content"].strip()
                og_d = soup.find("meta", property="og:description")
                if og_d and og_d.get("content"):
                    og_desc = og_d["content"].strip()
                m_d = soup.find("meta", attrs={"name": "description"})
                if m_d and m_d.get("content"):
                    meta_desc = m_d["content"].strip()

                # Limpiar elementos no textuales
                for tag in soup(["script", "style", "noscript", "svg", "header", "footer", "nav"]):
                    tag.decompose()
                raw_body = soup.get_text(separator=" ", strip=True)
                clean_body = re.sub(r"\s+", " ", raw_body)

                all_search_text = f"{page_title} {og_title} {og_desc} {meta_desc} {clean_body}"

                # Detección de marcador en vivo
                detected_score = None
                score_matches = re.findall(r"\b(\d{1,2})\s*[-–:]\s*(\d{1,2})\b", f"{page_title} {og_title} {og_desc}")
                if not score_matches:
                    score_matches = re.findall(
                        r"(?:marcador|resultado|score|minuto|\'|\’)[^\n\r]{0,25}?(\d{1,2})\s*[-–:]\s*(\d{1,2})",
                        all_search_text,
                        re.IGNORECASE
                    )
                if score_matches:
                    for sm in score_matches:
                        try:
                            g1, g2 = int(sm[0]), int(sm[1])
                            if g1 <= 9 and g2 <= 9:
                                detected_score = f"{g1} - {g2}"
                                if g1 > 0 or g2 > 0:
                                    break
                        except Exception:
                            continue

                # Detección de minuto en vivo
                detected_minute = None
                min_match = re.search(
                    r"\b([1-9][0-9]?)\s*[\'’]\b|\b(?:minuto|min\.?)\s*([1-9][0-9]?)\b|\b(1T|2T|HT|Descanso|Entretiempo)\b",
                    all_search_text,
                    re.IGNORECASE
                )
                if min_match:
                    if min_match.group(1):
                        detected_minute = f"{min_match.group(1)}'"
                    elif min_match.group(2):
                        detected_minute = f"{min_match.group(2)}'"
                    elif min_match.group(3):
                        detected_minute = min_match.group(3).upper()

                # Detección de córners en vivo
                detected_corners = None
                corn_patterns = [
                    r"(?:tiros de esquina|saques de esquina|córners?|corners?)[:\s]*(\d{1,2})\s*[-–:]\s*(\d{1,2})",
                    r"(\d{1,2})\s*[-–:]\s*(\d{1,2})[^\d\n\r]{0,15}(?:tiros de esquina|saques de esquina|córners?|corners?)",
                    r"(?:tiros de esquina|saques de esquina|córners?|corners?)[:\s]*(\d{1,2})\b",
                    r"\b(\d{1,2})\s*(?:tiros de esquina|saques de esquina|córners?|corners?)\b"
                ]
                for cpat in corn_patterns:
                    cm = re.search(cpat, all_search_text, re.IGNORECASE)
                    if cm:
                        try:
                            if cm.lastindex == 2:
                                c1, c2 = int(cm.group(1)), int(cm.group(2))
                                detected_corners = c1 + c2
                                break
                            elif cm.lastindex == 1:
                                v = int(cm.group(1))
                                if 0 <= v <= 25:
                                    detected_corners = v
                                    break
                        except Exception:
                            continue

                if detected_score:
                    self.last_url_telemetry["score"] = detected_score
                if detected_minute:
                    self.last_url_telemetry["minute"] = detected_minute
                if detected_corners is not None:
                    self.last_url_telemetry["corners"] = detected_corners

                header_parts = []
                if page_title:
                    header_parts.append(f"TÍTULO DEL ENCUENTRO: {page_title}")
                if og_title and og_title != page_title:
                    header_parts.append(f"OG TÍTULO: {og_title}")
                if og_desc:
                    header_parts.append(f"DESCRIPCIÓN OFICIAL: {og_desc}")
                if detected_score:
                    header_parts.append(f"MARCADOR EN DIRECTO DETECTADO: {detected_score}")
                if detected_minute:
                    header_parts.append(f"MINUTO DETECTADO: {detected_minute}")
                if detected_corners is not None:
                    header_parts.append(f"CÓRNERS EN DIRECTO DETECTADOS: {detected_corners}")

                combined_text = "\n".join(header_parts) + "\n" + clean_body
                if len(combined_text) > 4000:
                    combined_text = combined_text[:4000]

                logger.info(f"Contenido web descargado ({len(combined_text)} car.) | Telemetría: {self.last_url_telemetry}")
                return combined_text
        except Exception as e:
            logger.warning(f"Error al descargar URL '{clean_url}': {e}")

        return ""

    def extract_teams_from_url_and_page(self, url: str) -> Tuple[Optional[str], Optional[str]]:
        """
        Extrae de forma autónoma los nombres de los dos equipos involucrados
        a partir de la URL y del contenido HTML de la página (título, og:title, h1 o slug).
        """
        if not url or not url.strip():
            return None, None

        clean_url = url.strip()
        home = None
        away = None

        # 1. Si es Sofascore con ID de evento, obtener nombres oficiales desde la API
        if "sofascore.com" in clean_url.lower():
            eid = self._extract_sofascore_event_id(clean_url)
            if eid:
                try:
                    client = self._get_client()
                    r_ev = client.get(f"https://api.sofascore.com/api/v1/event/{eid}")
                    if r_ev.status_code == 200:
                        ev = r_ev.json().get("event", {})
                        h = ev.get("homeTeam", {}).get("name")
                        a = ev.get("awayTeam", {}).get("name")
                        if h and a:
                            return h, a
                except Exception as e:
                    logger.debug(f"Sofascore event team fetch failed: {e}")

        # 2. Intentar extraer del HTML (og:title o title)
        try:
            client = self._get_client()
            resp = client.get(clean_url)
            if resp.status_code == 200 and resp.text:
                soup = BeautifulSoup(resp.text, "html.parser")
                raw_title = ""
                og = soup.find("meta", property="og:title")
                if og and og.get("content"):
                    raw_title = og.get("content").strip()
                elif soup.title and soup.title.string:
                    raw_title = soup.title.string.strip()

                if raw_title:
                    clean_title = re.sub(r"\s*\|\s*.*$", "", raw_title, flags=re.IGNORECASE)
                    clean_title = re.sub(
                        r"\s*[-–—]\s*(?:resumen|en vivo|resultados|en directo|h2h|alineaciones|marcadores|clasificación|noticias|espn|marca|as|fútbol|futbol).*$",
                        "",
                        clean_title,
                        flags=re.IGNORECASE
                    )
                    clean_title = re.sub(r"\s+(?:en vivo|en directo|live)\s*$", "", clean_title, flags=re.IGNORECASE)
                    clean_title = re.sub(r"\(?\b\d{1,2}\s*[-–:]\s*\d{1,2}\b\)?", "", clean_title).strip()

                    parts = re.split(r"\s+(?:vs\.?|v\.?|-|–|—)\s+", clean_title, maxsplit=1, flags=re.IGNORECASE)
                    if len(parts) == 2 and len(parts[0].strip()) >= 2 and len(parts[1].strip()) >= 2:
                        home = parts[0].strip()
                        away = parts[1].strip()
        except Exception as e:
            logger.warning(f"No se pudo extraer equipos del HTML de la URL: {e}")

        # 3. Si no se obtuvo del HTML, extraer del slug de la URL
        if not home or not away:
            clean_lower = clean_url.lower()
            slug_match = re.search(r"(?:partido|match|football|game|encuentro)/([a-z0-9\-]+?)(?:/|$|\?)", clean_lower) or \
                         re.search(r"sofascore\.com/(?:[a-z]{2}/)?([a-z0-9\-]+?)(?:/[a-zA-Z0-9]+|/|$)", clean_lower)
            if slug_match:
                slug = slug_match.group(1)
                slug_parts = []
                if "-vs-" in slug:
                    slug_parts = slug.split("-vs-")
                elif "-v-" in slug:
                    slug_parts = slug.split("-v-")
                elif "-" in slug:
                    raw_split = slug.split("-")
                    if len(raw_split) == 2:
                        slug_parts = raw_split
                    elif len(raw_split) > 2:
                        if raw_split[-1].isdigit():
                            raw_split = raw_split[:-1]
                        mid = len(raw_split) // 2
                        slug_parts = ["-".join(raw_split[:mid]), "-".join(raw_split[mid:])]
                if len(slug_parts) == 2:
                    def title_slug(s):
                        return " ".join([w.capitalize() for w in s.replace("_", " ").replace("-", " ").split() if w])
                    h_cand = title_slug(slug_parts[0])
                    a_cand = title_slug(slug_parts[1])
                    if len(h_cand) >= 2 and len(a_cand) >= 2:
                        home = h_cand
                        away = a_cand

        return home, away

    def gather_match_context(
        self,
        home_team: str,
        away_team: str,
        competition: str = "General",
        is_live: bool = False,
        match_url: str = None
    ) -> str:
        """
        Ejecuta búsquedas exhaustivas y precisas en tiempo real con desambiguación deportiva.
        1. Si match_url está presente, extrae telemetría directa online (vía Sofascore API o Web).
        2. Consulta partidos recientes reales de ambos clubes en Sofascore para asegurar datos 100% fidedignos.
        3. Realiza búsquedas específicas en DuckDuckGo con pausas para evitar 'No results found'.
        """
        aggregated_text = []
        seen_snippets = set()

        # 1. Si se especificó una URL, descargar sus datos directos primero
        if match_url and match_url.strip():
            url_data = self.scrape_url_content(match_url)
            if url_data:
                aggregated_text.append(f"--- [DATOS DIRECTOS EN VIVO DESDE LA URL OFICIAL: {match_url.strip()}] ---")
                aggregated_text.append(url_data)

        # 1.1 Si no hay datos en vivo aún o no se pasó URL, verificar si el partido está en vivo en Sofascore
        if home_team and away_team and not self.last_url_telemetry.get("score"):
            live_txt, live_telem = self.find_live_match(home_team, away_team)
            if live_txt and live_telem:
                aggregated_text.append("--- [DATOS EN VIVO EN TIEMPO REAL DETECTADOS AUTÓNOMAMENTE (SOFASCORE)] ---")
                aggregated_text.append(live_txt)

        # 2. Historial reciente real de ambos clubes desde Sofascore
        if home_team and away_team:
            home_recent = self._get_team_recent_history_from_sofascore(home_team)
            away_recent = self._get_team_recent_history_from_sofascore(away_team)
            if home_recent or away_recent:
                hist_lines = ["--- [HISTORIAL Y FORMA RECIENTE CONFIRMADA (SOFASCORE)] ---"]
                if home_recent:
                    hist_lines.append(f"• Últimos partidos confirmados de {home_team}:")
                    for m in home_recent[:4]:
                        hist_lines.append(f"  - {m['match']} ({m['status']})")
                if away_recent:
                    hist_lines.append(f"• Últimos partidos confirmados de {away_team}:")
                    for m in away_recent[:4]:
                        hist_lines.append(f"  - {m['match']} ({m['status']})")
                aggregated_text.append("\n".join(hist_lines))

        # 3. Búsqueda web complementaria DuckDuckGo
        search_plan = [
            (
                "Estado en Directo, Marcador Actual y Minuto",
                f"{home_team} vs {away_team} live flashscore sofascore"
            ),
            (
                "Tiros de Esquina y Córners en Directo y Promedios",
                f"{home_team} vs {away_team} corners tiros de esquina"
            ),
            (
                "Estadísticas H2H y Goles Recientes",
                f"{home_team} vs {away_team} h2h estadisticas futbol"
            )
        ]

        if is_live:
            search_plan.append((
                "Minuto de Juego y Tiros de Esquina en Vivo",
                f"{home_team} vs {away_team} directo minuto corners"
            ))

        for idx, (label, q) in enumerate(search_plan):
            if idx > 0:
                time.sleep(0.3)  # Pausa breve anti-throttling para DuckDuckGo

            snippets = self.search_query(q)
            section_items = []
            for s in snippets:
                snip_text = s.get("snippet", "").strip()
                if snip_text and snip_text not in seen_snippets:
                    seen_snippets.add(snip_text)
                    section_items.append(f"• [{s.get('title', 'Fuente')}]: {snip_text}")

            if section_items:
                aggregated_text.append(f"--- [Sección: {label}] ---")
                aggregated_text.extend(section_items)

        if not aggregated_text:
            return f"Búsqueda deportiva para el encuentro de fútbol {home_team} vs {away_team} en {competition}."

        return "\n".join(aggregated_text)

# Instancia singleton del scraper
scraper = SportsWebScraper()
