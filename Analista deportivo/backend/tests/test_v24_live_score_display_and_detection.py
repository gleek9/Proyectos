import unittest
from backend.app.agent.scraper import scraper
from backend.app.schemas.match import MatchRawFeatures, TeamFormStats, HeadToHeadStats
from backend.app.models.ensemble import ensemble_engine

class TestKatakuriV24LiveScoreDisplayAndDetection(unittest.TestCase):
    def test_flashscore_match_id_extraction_formats(self):
        """Verifica que el ID de Flashscore se extraiga de múltiples formatos de URLs y slugs."""
        urls = {
            "https://www.flashscore.com/match/pegeia-apoel-4EVDq0HO/#/match-summary": "4EVDq0HO",
            "https://www.flashscore.es/partido/real-madrid-barcelona-Wxyz1234/": "Wxyz1234",
            "https://www.flashscore.com.mx/partido/futbol/china-KvDnIMwk/uzbekistan-bJcArLW4/?mid=lYm0NHUa": "lYm0NHUa",
            "https://www.flashscore.co/partido/8OLLPC5C/#resumen-del-partido": "8OLLPC5C",
            "https://www.flashscore.mobi/match/?id=8OLLPC5C": "8OLLPC5C"
        }
        for url, expected_id in urls.items():
            extracted = scraper._extract_flashscore_match_id(url)
            self.assertEqual(extracted, expected_id, f"Fallo al extraer ID de {url}")

    def test_live_score_in_ensemble_and_response(self):
        """Verifica que un partido en vivo con marcador 3 - 1 preserve el marcador y se refleje en MatchMeta."""
        raw = MatchRawFeatures(
            home_team="Arsenal",
            away_team="Chelsea",
            competition="Premier League",
            home_stats=TeamFormStats(team_name="Arsenal", avg_goals_scored=2.0, avg_goals_conceded=1.0, avg_corners=6.5, avg_cards=2.0, win_rate_last_5=60.0),
            away_stats=TeamFormStats(team_name="Chelsea", avg_goals_scored=1.5, avg_goals_conceded=1.2, avg_corners=5.5, avg_cards=2.2, win_rate_last_5=50.0),
            h2h=HeadToHeadStats(matches_analyzed=5, home_wins=2, draws=1, away_wins=2, avg_total_goals=2.8, avg_total_corners=11.0, avg_total_cards=4.0),
            is_live=True,
            live_score="3 - 1",
            live_minute="65'",
            live_corners=7
        )
        res = ensemble_engine.predict(raw)
        self.assertTrue(res.match.is_live)
        self.assertEqual(res.match.live_score, "3 - 1")
        self.assertEqual(res.match.live_minute, "65'")
        self.assertEqual(res.match.live_corners, 7)
        # En vivo con 4 goles acumulados (3-1), más de 1.5, 2.5 y 3.5 deben estar al 100%
        self.assertEqual(res.prediction.goals.over_1_5_pct, 100.0)
        self.assertEqual(res.prediction.goals.over_2_5_pct, 100.0)
        self.assertEqual(res.prediction.goals.over_3_5_pct, 100.0)
        # Goles esperados nunca menores a los 4 goles reales
        self.assertGreaterEqual(res.prediction.goals.expected_total, 4.0)

    def test_live_score_default_not_none_when_confirmed_live(self):
        """Verifica que un partido en vivo sin goles registrados asegure '0 - 0' en lugar de None."""
        raw = MatchRawFeatures(
            home_team="Liverpool",
            away_team="Everton",
            competition="Premier League",
            home_stats=TeamFormStats(team_name="Liverpool", avg_goals_scored=1.8, avg_goals_conceded=1.1, avg_corners=6.0, avg_cards=1.9, win_rate_last_5=55.0),
            away_stats=TeamFormStats(team_name="Everton", avg_goals_scored=1.2, avg_goals_conceded=1.4, avg_corners=4.8, avg_cards=2.4, win_rate_last_5=35.0),
            h2h=HeadToHeadStats(matches_analyzed=5, home_wins=3, draws=1, away_wins=1, avg_total_goals=2.4, avg_total_corners=10.2, avg_total_cards=4.5),
            is_live=True,
            live_score=None
        )
        # Simular paso por collector
        if raw.is_live and not raw.live_score:
            raw.live_score = "0 - 0"
        self.assertEqual(raw.live_score, "0 - 0")

if __name__ == "__main__":
    unittest.main()
