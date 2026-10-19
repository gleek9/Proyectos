"""
Coordinador del Agente de Ingesta Deportiva.
Orquesta la búsqueda web y la estructuración con Gemini 2.5 Flash, con soporte de caché.
"""
import logging
from datetime import datetime, timedelta
from typing import Optional
from backend.app.schemas.match import MatchRawFeatures
from backend.app.agent.scraper import scraper
from backend.app.agent.parser import parser
from backend.app.db import SessionLocal, MatchPrediction

logger = logging.getLogger(__name__)

class MatchDataCollector:
    def __init__(self):
        self.scraper = scraper
        self.parser = parser

    def get_cached_raw_features(self, home_team: str, away_team: str, max_age_hours: int = 12) -> Optional[dict]:
        """Verifica si existe un análisis reciente en la base de datos local SQLite."""
        db = SessionLocal()
        try:
            cutoff = datetime.utcnow() - timedelta(hours=max_age_hours)
            record = db.query(MatchPrediction).filter(
                MatchPrediction.home_team.ilike(home_team.strip()),
                MatchPrediction.away_team.ilike(away_team.strip()),
                MatchPrediction.analyzed_at >= cutoff
            ).order_by(MatchPrediction.analyzed_at.desc()).first()

            if record and record.raw_stats:
                # Si el registro no tiene soporte de is_live o es un partido en vivo, limitar la caché a 5 minutos
                raw = record.raw_stats
                if "is_live" not in raw:
                    logger.info(f"Registro en caché previo sin campos live para {home_team} vs {away_team}. Forzando actualización.")
                    return None
                if raw.get("is_live"):
                    live_cutoff = datetime.utcnow() - timedelta(minutes=5)
                    if record.analyzed_at < live_cutoff:
                        logger.info(f"Caché de partido en vivo expirada (> 5 min) para {home_team} vs {away_team}. Refrescando...")
                        return None

                logger.info(f"Caché SQLite válida encontrada para {home_team} vs {away_team}")
                return record.raw_stats
        except Exception as e:
            logger.warning(f"Error consultando caché SQLite: {e}")
        finally:
            db.close()
        return None

    def get_latest_raw_features(self, home_team: str, away_team: str) -> Optional[MatchRawFeatures]:
        """Obtiene el último estado registrado del encuentro para mantener estabilidad y continuidad."""
        db = SessionLocal()
        try:
            from sqlalchemy import or_, and_
            record = db.query(MatchPrediction).filter(
                or_(
                    and_(MatchPrediction.home_team.ilike(home_team.strip()), MatchPrediction.away_team.ilike(away_team.strip())),
                    and_(MatchPrediction.home_team.ilike(away_team.strip()), MatchPrediction.away_team.ilike(home_team.strip()))
                )
            ).order_by(MatchPrediction.analyzed_at.desc()).first()
            if record and record.raw_stats:
                return MatchRawFeatures.model_validate(record.raw_stats)
        except Exception as e:
            logger.warning(f"Error recuperando estado previo de SQLite: {e}")
        finally:
            db.close()
        return None

    def collect(
        self,
        home_team: str,
        away_team: str,
        competition: str = "General",
        force_refresh: bool = False,
        is_live: Optional[bool] = None,
        live_score: Optional[str] = None,
        live_minute: Optional[str] = None,
        live_corners: Optional[int] = None,
        live_red_cards_home: Optional[int] = None,
        live_red_cards_away: Optional[int] = None,
        live_shots_on_target_home: Optional[int] = None,
        live_shots_on_target_away: Optional[int] = None,
        match_url: Optional[str] = None
    ) -> MatchRawFeatures:
        """
        Flujo completo:
        1. Comprueba si hay datos en caché en SQLite (si no se fuerza refresco).
        2. Si se actualiza, recupera el estado previo para mantener consistencia de fondo.
        3. Si match_url está presente, activa modo en vivo y descarga datos directos del partido online.
        4. Pasa el contexto recopilado y previo a Gemini / Parser asegurando continuidad.
        5. Retorna el objeto MatchRawFeatures validado.
        """
        home_clean = home_team.strip() if home_team else ""
        away_clean = away_team.strip() if away_team else ""
        clean_url = match_url.strip() if match_url and match_url.strip() else None

        # Si se proporciona una URL, extraer equipos y verificar correspondencia con los equipos solicitados
        if clean_url:
            url_home, url_away = self.scraper.extract_teams_from_url_and_page(clean_url)
            if url_home and url_away:
                if not home_clean or not away_clean:
                    # El usuario no ingresó nombres arriba, solo pegó la URL -> Usar nombres de la URL
                    logger.info(f"Equipos extraídos autónomamente desde la URL: '{url_home}' vs '{url_away}'")
                    home_clean = url_home
                    away_clean = url_away
                else:
                    # El usuario ingresó nombres arriba. Verificar si la URL corresponde a estos equipos.
                    import re
                    h_norm = re.sub(r'[^a-zA-Z0-9]', '', home_clean.lower())
                    a_norm = re.sub(r'[^a-zA-Z0-9]', '', away_clean.lower())
                    uh_norm = re.sub(r'[^a-zA-Z0-9]', '', url_home.lower())
                    ua_norm = re.sub(r'[^a-zA-Z0-9]', '', url_away.lower())

                    matches = (h_norm in uh_norm or uh_norm in h_norm) or (a_norm in ua_norm or ua_norm in a_norm) or \
                              (h_norm in ua_norm or ua_norm in h_norm) or (a_norm in uh_norm or uh_norm in a_norm)

                    if matches:
                        logger.info(f"URL confirmada para {home_clean} vs {away_clean}. Nombres oficiales: '{url_home}' vs '{url_away}'")
                        home_clean = url_home
                        away_clean = url_away
                    else:
                        logger.info(
                            f"La URL proporcionada ({clean_url}) contiene '{url_home}' vs '{url_away}'. "
                            f"Adoptando nombres oficiales detectados en el enlace en vivo para mantener sincronización."
                        )
                        home_clean = url_home
                        away_clean = url_away

        if not force_refresh and not clean_url and home_clean and away_clean:
            cached_data = self.get_cached_raw_features(home_clean, away_clean)
            if cached_data:
                try:
                    return MatchRawFeatures.model_validate(cached_data)
                except Exception as e:
                    logger.warning(f"Error reconstruyendo MatchRawFeatures desde caché: {e}")

        # Recuperar estado previo del encuentro para preservar estabilidad de la temporada
        previous_features = self.get_latest_raw_features(home_clean, away_clean) if (home_clean and away_clean) else None
        effective_live = bool(clean_url) or (is_live if is_live is not None else (previous_features.is_live if previous_features else False))

        logger.info(f"Iniciando búsqueda web para {home_clean} vs {away_clean} (en vivo: {effective_live}, url: {clean_url})...")
        search_context = self.scraper.gather_match_context(
            home_clean, away_clean, competition, is_live=effective_live, match_url=clean_url
        )

        logger.info(f"Estructurando estadísticas con Gemini / Parser (con anclaje de continuidad)...")
        raw_features = self.parser.parse_match(
            home_team=home_clean,
            away_team=away_clean,
            competition=competition,
            search_context=search_context,
            previous_features=previous_features,
            is_live=effective_live,
            match_url=clean_url
        )

        # Integrar telemetría directa oficial detectada en la página o API de la URL
        url_telem = self.scraper.get_last_url_telemetry()
        if (raw_features.is_live or effective_live) and url_telem:
            raw_features.is_live = True
            if url_telem.get("score"):
                logger.info(f"Aplicando marcador oficial en directo: {url_telem['score']}")
                raw_features.live_score = str(url_telem["score"]).strip()
            if url_telem.get("minute"):
                logger.info(f"Aplicando minuto oficial en directo: {url_telem['minute']}")
                raw_features.live_minute = str(url_telem["minute"]).strip()
            if url_telem.get("corners") is not None:
                logger.info(f"Aplicando córners oficiales en directo: {url_telem['corners']}")
                raw_features.live_corners = int(url_telem["corners"])
            if url_telem.get("red_cards_home") is not None:
                raw_features.live_red_cards_home = int(url_telem["red_cards_home"])
            if url_telem.get("red_cards_away") is not None:
                raw_features.live_red_cards_away = int(url_telem["red_cards_away"])
            if url_telem.get("shots_on_target_home") is not None:
                raw_features.live_shots_on_target_home = int(url_telem["shots_on_target_home"])
            if url_telem.get("shots_on_target_away") is not None:
                raw_features.live_shots_on_target_away = int(url_telem["shots_on_target_away"])
            if url_telem.get("possession_home") is not None:
                raw_features.live_possession_home = float(url_telem["possession_home"])
            if url_telem.get("possession_away") is not None:
                raw_features.live_possession_away = float(url_telem["possession_away"])

        # Aplicar datos explícitos enviados por el cliente si están presentes y no hay datos del scraper
        if is_live is not None:
            raw_features.is_live = is_live
            if not is_live:
                raw_features.live_score = None
                raw_features.live_minute = None
                raw_features.live_corners = None
                raw_features.live_red_cards_home = 0
                raw_features.live_red_cards_away = 0
        if raw_features.is_live:
            # Solo utilizar datos del cliente si el scraper/parser online no detectó ninguno
            if live_score is not None and live_score.strip() and not raw_features.live_score:
                raw_features.live_score = live_score.strip()
            if live_minute is not None and live_minute.strip() and not raw_features.live_minute:
                raw_features.live_minute = live_minute.strip()
            if live_corners is not None and raw_features.live_corners is None:
                raw_features.live_corners = live_corners
            if live_red_cards_home is not None and (raw_features.live_red_cards_home == 0 or raw_features.live_red_cards_home is None):
                raw_features.live_red_cards_home = live_red_cards_home
            if live_red_cards_away is not None and (raw_features.live_red_cards_away == 0 or raw_features.live_red_cards_away is None):
                raw_features.live_red_cards_away = live_red_cards_away
            if live_shots_on_target_home is not None and raw_features.live_shots_on_target_home is None:
                raw_features.live_shots_on_target_home = live_shots_on_target_home
            if live_shots_on_target_away is not None and raw_features.live_shots_on_target_away is None:
                raw_features.live_shots_on_target_away = live_shots_on_target_away

            # Si el partido está confirmado en directo y aún no hay goles registrados, asegurar marcador base '0 - 0'
            if not raw_features.live_score:
                raw_features.live_score = "0 - 0"
            if not raw_features.live_minute:
                raw_features.live_minute = "En juego"

        # Asegurar nombres no vacíos
        if not raw_features.home_team or not raw_features.home_team.strip():
            raw_features.home_team = home_clean or "Equipo Local"
        if not raw_features.away_team or not raw_features.away_team.strip():
            raw_features.away_team = away_clean or "Equipo Visitante"

        return raw_features

collector = MatchDataCollector()
