"""
Pruebas Unitarias para Katakuri v2.1:
1. Des-sesgo matemático de córners pre-match en Poisson (dinámico basado en tasas ofensivas).
2. Activación de Modo En Vivo gobernada EXCLUSIVAMENTE por la presencia de `match_url`.
3. Preservación y persistencia de `match_url` en respuestas y base de datos SQLite.
"""
import unittest
from backend.app.schemas.match import MatchRawFeatures, TeamFormStats, HeadToHeadStats
from backend.app.models.poisson import poisson_model
from backend.app.models.ensemble import ensemble_engine
from backend.app.agent.parser import parser
from backend.app.db import SessionLocal, MatchPrediction, init_db

class TestKatakuriV21UrlLiveAndCorners(unittest.TestCase):

    def setUp(self):
        init_db()

    def test_unbiased_prematch_corners_calculation(self):
        """Verifica que los córners pre-match no caigan en el sesgo de 5.0 + 5.0 o 9.5 estáticos."""
        # 1. Partido ofensivo de alta presión (ej. Manchester City vs Sheffield)
        high_features = MatchRawFeatures(
            home_team="Manchester City",
            away_team="Sheffield United",
            competition="Premier League",
            is_live=False,
            home_stats=TeamFormStats(
                team_name="Manchester City",
                avg_goals_scored=2.9,
                avg_goals_conceded=0.7,
                avg_corners=8.2,
                avg_cards=1.5,
                win_rate_last_5=0.8
            ),
            away_stats=TeamFormStats(
                team_name="Sheffield United",
                avg_goals_scored=0.6,
                avg_goals_conceded=2.4,
                avg_corners=3.1,
                avg_cards=2.8,
                win_rate_last_5=0.2
            ),
            h2h=HeadToHeadStats(
                total_matches_analyzed=5,
                home_team_wins=4,
                draws=1,
                away_team_wins=0,
                avg_total_goals_h2h=3.5,
                avg_total_corners_h2h=11.4,
                avg_total_cards_h2h=3.8
            )
        )
        corners_high = poisson_model.predict(high_features)["corners"]
        self.assertGreater(corners_high["expected_total"], 10.5, "Partidos de alta presión ofensiva deben proyectar > 10.5 córners")
        self.assertGreater(corners_high["over_9_5_pct"], 60.0, "La probabilidad de Over 9.5 debe ser alta en partidos ofensivos")

        # 2. Partido cerrado / defensivo (ej. Getafe vs Mallorca)
        low_features = MatchRawFeatures(
            home_team="Getafe",
            away_team="Mallorca",
            competition="LaLiga",
            is_live=False,
            home_stats=TeamFormStats(
                team_name="Getafe",
                avg_goals_scored=0.8,
                avg_goals_conceded=0.9,
                avg_corners=3.5,
                avg_cards=3.1,
                win_rate_last_5=0.4
            ),
            away_stats=TeamFormStats(
                team_name="Mallorca",
                avg_goals_scored=0.7,
                avg_goals_conceded=1.0,
                avg_corners=3.2,
                avg_cards=2.9,
                win_rate_last_5=0.4
            ),
            h2h=HeadToHeadStats(
                total_matches_analyzed=5,
                home_team_wins=1,
                draws=3,
                away_team_wins=1,
                avg_total_goals_h2h=1.5,
                avg_total_corners_h2h=6.8,
                avg_total_cards_h2h=5.5
            )
        )
        corners_low = poisson_model.predict(low_features)["corners"]
        self.assertLess(corners_low["expected_total"], 8.5, "Partidos de bajo ritmo deben proyectar < 8.5 córners")
        self.assertNotEqual(corners_low["expected_total"], 9.8, "No debe caer en el promedio estático previo de 9.8")

    def test_live_mode_strictly_driven_by_match_url(self):
        """Verifica que el modo en vivo SOLO se active si se provee match_url."""
        raw_text_snippet = """
        Flashscore Live: Arsenal 1 - 0 Chelsea. Minuto 34'. 
        Estadísticas: Tiros de esquina Arsenal 3, Chelsea 1. Total córners: 4.
        """

        # A. Sin match_url -> Obligatoriamente Pre-Match
        parsed_pre = parser.parse_match(
            home_team="Arsenal",
            away_team="Chelsea",
            competition="Premier League",
            search_context=raw_text_snippet,
            match_url=None
        )
        self.assertFalse(parsed_pre.is_live, "Sin match_url debe forzarse estrictamente a Pre-Match (is_live=False)")
        self.assertIsNone(parsed_pre.live_minute, "En Pre-Match el minuto debe ser nulo")
        self.assertIsNone(parsed_pre.live_score, "En Pre-Match el marcador debe ser nulo")
        self.assertIsNone(parsed_pre.live_corners, "En Pre-Match los córners en vivo deben ser nulos")
        self.assertIsNone(parsed_pre.match_url, "match_url debe ser None")

        # B. Con match_url -> Modo En Vivo Activo
        test_url = "https://www.flashscore.es/partido/arsenal-chelsea"
        parsed_live = parser.parse_match(
            home_team="Arsenal",
            away_team="Chelsea",
            competition="Premier League",
            search_context=raw_text_snippet,
            match_url=test_url
        )
        self.assertTrue(parsed_live.is_live, "Con match_url debe estar en Modo En Vivo (is_live=True)")
        self.assertEqual(parsed_live.match_url, test_url, "Debe preservar la URL ingresada")
        self.assertEqual(parsed_live.live_score, "1 - 0")
        self.assertEqual(parsed_live.live_minute, "34'")
        self.assertEqual(parsed_live.live_corners, 4)

    def test_ensemble_and_database_persistence_of_match_url(self):
        """Verifica que el ensamble y la base de datos conserven match_url."""
        test_url = "https://www.sofascore.com/real-madrid-barcelona/Egb"
        features = MatchRawFeatures(
            home_team="Real Madrid",
            away_team="FC Barcelona",
            competition="LaLiga",
            match_url=test_url,
            is_live=True,
            live_score="2 - 1",
            live_minute="65'",
            live_corners=7,
            home_stats=TeamFormStats(
                team_name="Real Madrid",
                avg_goals_scored=2.2,
                avg_goals_conceded=1.0,
                avg_corners=6.1,
                avg_cards=2.0,
                win_rate_last_5=0.8
            ),
            away_stats=TeamFormStats(
                team_name="FC Barcelona",
                avg_goals_scored=2.0,
                avg_goals_conceded=1.1,
                avg_corners=5.4,
                avg_cards=2.2,
                win_rate_last_5=0.6
            ),
            h2h=HeadToHeadStats(
                total_matches_analyzed=5,
                home_team_wins=2,
                draws=1,
                away_team_wins=2,
                avg_total_goals_h2h=3.2,
                avg_total_corners_h2h=9.8,
                avg_total_cards_h2h=4.5
            )
        )

        resp = ensemble_engine.predict(features)
        self.assertEqual(resp.match.match_url, test_url, "La respuesta del ensamble debe contener match_url")
        self.assertTrue(resp.match.is_live)
        self.assertEqual(resp.match.live_score, "2 - 1")

        # Persistir en SQLite serializando a JSON (mode="json")
        db = SessionLocal()
        try:
            pred_db = MatchPrediction(
                home_team=features.home_team,
                away_team=features.away_team,
                match_url=test_url,
                winner_home_pct=resp.prediction.winner.home_win_pct,
                winner_draw_pct=resp.prediction.winner.draw_pct,
                winner_away_pct=resp.prediction.winner.away_win_pct,
                human_verdict=resp.prediction.winner.human_verdict,
                expected_goals=resp.prediction.goals.expected_total,
                over_2_5_pct=resp.prediction.goals.over_2_5_pct,
                expected_corners=resp.prediction.corners.expected_total,
                expected_cards=resp.prediction.cards.expected_total,
                prediction_data=resp.model_dump(mode="json"),
                raw_stats=features.model_dump(mode="json")
            )
            db.add(pred_db)
            db.commit()
            db.refresh(pred_db)

            # Recuperar y verificar
            fetched = db.query(MatchPrediction).filter(MatchPrediction.id == pred_db.id).first()
            self.assertIsNotNone(fetched)
            self.assertEqual(fetched.match_url, test_url, "La base de datos SQLite debe almacenar match_url correctamente")
        finally:
            db.close()

if __name__ == '__main__':
    unittest.main()
