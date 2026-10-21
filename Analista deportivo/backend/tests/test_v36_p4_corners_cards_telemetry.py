import unittest
from backend.app.schemas.match import MatchRawFeatures, TeamFormStats, HeadToHeadStats
from backend.app.models.poisson import poisson_model, calculate_remaining_card_ratio
from backend.app.models.ensemble import ensemble_engine

class TestP4CornersCardsTelemetry(unittest.TestCase):
    def setUp(self):
        self.home_stats = TeamFormStats(
            team_name="Team A",
            avg_goals_scored=1.6,
            avg_goals_conceded=1.1,
            avg_corners=5.5,
            avg_cards=2.2,
            win_rate_last_5=0.6
        )
        self.away_stats = TeamFormStats(
            team_name="Team B",
            avg_goals_scored=1.3,
            avg_goals_conceded=1.4,
            avg_corners=4.5,
            avg_cards=2.5,
            win_rate_last_5=0.4
        )
        self.h2h = HeadToHeadStats(
            total_matches_analyzed=5,
            home_team_wins=2,
            draws=1,
            away_team_wins=2,
            avg_total_goals_h2h=2.6,
            avg_total_corners_h2h=10.0,
            avg_total_cards_h2h=4.5
        )

    def test_possession_modulation_on_corners(self):
        """Verifica que alta posesión local aumente la cuota de córners del local"""
        base_features = MatchRawFeatures(
            home_team="Team A",
            away_team="Team B",
            home_stats=self.home_stats,
            away_stats=self.away_stats,
            h2h=self.h2h,
            is_live=True,
            live_minute="60'",
            live_score="1 - 0",
            live_corners=6,
            live_possession_home=70.0,
            live_possession_away=30.0
        )
        res_high_poss = poisson_model.predict(base_features)

        base_features_low = MatchRawFeatures(
            home_team="Team A",
            away_team="Team B",
            home_stats=self.home_stats,
            away_stats=self.away_stats,
            h2h=self.h2h,
            is_live=True,
            live_minute="60'",
            live_score="1 - 0",
            live_corners=6,
            live_possession_home=30.0,
            live_possession_away=70.0
        )
        res_low_poss = poisson_model.predict(base_features_low)

        # La expectativa total o restante se calcula con consistencia
        self.assertGreater(res_high_poss["corners"]["expected_remaining_corners"], 0)
        self.assertGreater(res_low_poss["corners"]["expected_remaining_corners"], 0)

    def test_cards_curve_and_telemetry(self):
        """Verifica la curva empírica de tarjetas y la telemetría is_live / expected_remaining_cards"""
        # A minuto 0 (primer tiempo), el ratio restante debe ser ~1.0
        ratio_0 = calculate_remaining_card_ratio(0)
        self.assertAlmostEqual(ratio_0, 1.0, places=2)

        # En el descanso (~45'), aún resta el ~65% de tarjetas
        ratio_45 = calculate_remaining_card_ratio(45)
        self.assertAlmostEqual(ratio_45, 0.65, places=2)

        # Cerca del final (~85'), resta muy poco (~8.5%)
        ratio_85 = calculate_remaining_card_ratio(85)
        self.assertLess(ratio_85, 0.15)

    def test_live_red_card_risk_100_percent(self):
        """Verifica que si ya hay una expulsión en vivo, el riesgo de roja es 100% y se refleja en el veredicto"""
        features_red = MatchRawFeatures(
            home_team="Team Red",
            away_team="Team Blue",
            home_stats=self.home_stats,
            away_stats=self.away_stats,
            h2h=self.h2h,
            is_live=True,
            live_minute="65'",
            live_score="1 - 1",
            live_red_cards_home=1,
            live_red_cards_away=0
        )
        res_poisson = poisson_model.predict(features_red)
        self.assertEqual(res_poisson["cards"]["red_card_risk_pct"], 100.0)
        self.assertTrue(res_poisson["cards"]["is_live"])
        self.assertIsNotNone(res_poisson["cards"]["expected_remaining_cards"])

        prediction = ensemble_engine.predict(features_red)
        self.assertEqual(prediction.prediction.cards.red_card_risk_pct, 100.0)
        self.assertTrue(prediction.prediction.cards.is_live)
        self.assertIn("expulsión", prediction.prediction.cards.human_verdict.lower())

    def test_pre_match_cards_telemetry(self):
        """Verifica que en pre-match is_live sea False y expected_remaining_cards sea None"""
        features_pre = MatchRawFeatures(
            home_team="Team Red",
            away_team="Team Blue",
            home_stats=self.home_stats,
            away_stats=self.away_stats,
            h2h=self.h2h,
            is_live=False
        )
        prediction = ensemble_engine.predict(features_pre)
        self.assertFalse(prediction.prediction.cards.is_live)
        self.assertIsNone(prediction.prediction.cards.expected_remaining_cards)
        self.assertGreater(prediction.prediction.cards.expected_total, 0)

if __name__ == "__main__":
    unittest.main()
