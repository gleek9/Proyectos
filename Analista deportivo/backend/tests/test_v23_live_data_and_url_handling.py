"""
Pruebas Unitarias para Katakuri v2.3:
1. Prevención de secuestro de nombres: si el usuario ingresa equipos en la barra superior,
   una URL obsoleta o perteneciente a otro encuentro NO sobreescribe los nombres del usuario.
2. Extracción de datos reales en vivo mediante Sofascore API / primp (score, minuto, córners).
3. Disponibilidad y vigencia de modelos Gemini 3.5/3.8 en el parser para evitar caídas a fallback.
"""
import unittest
from backend.app.schemas.match import MatchRawFeatures
from backend.app.agent.collector import collector
from backend.app.agent.scraper import scraper
from backend.app.agent.parser import parser
from backend.app.db import init_db

class TestKatakuriV23LiveDataAndUrlHandling(unittest.TestCase):

    def setUp(self):
        init_db()

    def test_mismatched_url_does_not_override_user_teams(self):
        """Verifica que una URL de otro partido previo no suplante los equipos que el usuario escribió arriba."""
        user_home = "Real Madrid"
        user_away = "Barcelona"
        # URL de un partido diferente (ej. Australia o Liga MX)
        foreign_url = "https://www.sofascore.com/football/match/perth-glory-adelaide-united/17226504"

        raw = collector.collect(
            home_team=user_home,
            away_team=user_away,
            competition="LaLiga",
            force_refresh=True,
            match_url=foreign_url
        )

        self.assertIn(user_home, raw.home_team, "El equipo local ingresado por el usuario debe prevalecer sobre la URL ajena")
        self.assertIn(user_away, raw.away_team, "El equipo visitante ingresado por el usuario debe prevalecer sobre la URL ajena")
        self.assertNotIn("Perth", raw.home_team, "No debe incluir nombres del partido de la URL ajena")
        self.assertFalse(raw.is_live, "Al descartarse la URL ajena, no debe forzarse en vivo erróneamente")

    def test_live_data_extraction_with_real_telemetry(self):
        """Verifica que el scraper extraiga telemetría en vivo sin bloqueos 403."""
        # Evento de prueba en Sofascore
        url = "https://www.sofascore.com/football/match/china-u23-uzbekistan-u23/17226436"
        content = scraper.scrape_url_content(url)
        telem = scraper.get_last_url_telemetry()

        self.assertGreater(len(content), 0, "El contenido raspado no debe estar vacío")
        self.assertIn("score", telem, "Debe detectar el marcador del partido")
        self.assertIn("minute", telem, "Debe detectar el minuto o estado")
        self.assertEqual(telem.get("home_team"), "China U23")
        self.assertEqual(telem.get("away_team"), "Uzbekistan U23")

    def test_parser_uses_active_gemini_models(self):
        """Verifica que el parser priorice modelos vigentes de Gemini sin errores 404."""
        self.assertIn("gemini-3.5-flash-lite", parser.candidate_models)
        self.assertNotIn("gemini-2.5-flash", parser.candidate_models, "gemini-2.5-flash está obsoleto y debe ser excluido")

if __name__ == "__main__":
    unittest.main()
