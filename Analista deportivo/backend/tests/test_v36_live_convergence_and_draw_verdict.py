"""
Tests v3.6 — P1/P2: veredicto con empate dominante, partidos finalizados,
convergencia temporal in-play de XGBoost/LSTM y líneas en vivo desde la matriz de consenso.
"""
import os
import sys
import unittest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from backend.app.schemas.match import MatchRawFeatures, TeamFormStats, HeadToHeadStats
from backend.app.models.poisson import (
    parse_elapsed_minute, calculate_remaining_goal_ratio, condition_1x2_on_live_state
)
from backend.app.models.tabular_ml import tabular_predictor
from backend.app.models.lstm_net import lstm_predictor
from backend.app.models.ensemble import ensemble_engine


def _raw(score=None, minute=None, live=True):
    return MatchRawFeatures(
        home_team="Real Madrid", away_team="Alaves", competition="LaLiga",
        is_live=live, live_score=score, live_minute=minute,
        home_stats=TeamFormStats(team_name="Real Madrid", avg_goals_scored=2.2, avg_goals_conceded=0.9),
        away_stats=TeamFormStats(team_name="Alaves", avg_goals_scored=0.9, avg_goals_conceded=1.6),
        h2h=HeadToHeadStats(),
    )


class TestV36P1DrawVerdictAndFinishedMatch(unittest.TestCase):
    def test_finished_match_strings_parse_to_90(self):
        for s in ["FT", "Final", "Terminado", "Finalizado", "Full-Time"]:
            self.assertEqual(parse_elapsed_minute(s), 90, s)
        self.assertEqual(parse_elapsed_minute("HT"), 45)
        self.assertEqual(parse_elapsed_minute("90+4'"), 89)
        self.assertEqual(calculate_remaining_goal_ratio(90), 0.0)

    def test_finished_match_is_deterministic(self):
        res = ensemble_engine.predict(_raw("2 - 1", "FT"))
        self.assertEqual(res.prediction.winner.home_win_pct, 100.0)
        self.assertEqual(res.prediction.goals.no_more_goals_pct, 100.0)
        self.assertEqual(res.prediction.goals.most_likely_score, "2 - 1")

    def test_draw_dominant_verdict_and_score(self):
        res = ensemble_engine.predict(_raw("0 - 0", "85'"))
        w = res.prediction.winner
        self.assertGreater(w.draw_pct, w.home_win_pct)
        self.assertIn("empate es el desenlace más probable", w.human_verdict)
        self.assertNotIn("Ligera ventaja", w.human_verdict)
        self.assertEqual(res.prediction.goals.most_likely_score, "0 - 0")


class TestV36P2LiveConvergence(unittest.TestCase):
    def test_conditioning_is_time_sensitive(self):
        early = condition_1x2_on_live_state(0.5, 0.25, 0.25, 2.7, 1, 0, calculate_remaining_goal_ratio(5))
        late = condition_1x2_on_live_state(0.5, 0.25, 0.25, 2.7, 1, 0, calculate_remaining_goal_ratio(88))
        self.assertGreater(late[0], early[0])
        self.assertGreater(late[0], 0.90)

    def test_kickoff_preserves_prematch(self):
        ph, pd, pa = condition_1x2_on_live_state(0.55, 0.25, 0.20, 2.7, 0, 0, 1.0)
        self.assertAlmostEqual(ph, 0.55, delta=0.03)
        self.assertAlmostEqual(pd, 0.25, delta=0.03)

    def test_xgb_and_lstm_converge_to_draw_at_0_0_late(self):
        for model in (tabular_predictor, lstm_predictor):
            wp = model.predict(_raw("0 - 0", "85'"))["winner_probs"]
            self.assertGreater(wp["draw"], 60.0, model.__class__.__name__)

    def test_red_card_penalizes_sanctioned_team(self):
        base = condition_1x2_on_live_state(0.45, 0.28, 0.27, 2.6, 0, 0, calculate_remaining_goal_ratio(30))
        red = condition_1x2_on_live_state(0.45, 0.28, 0.27, 2.6, 0, 0, calculate_remaining_goal_ratio(30), reds_h=1)
        self.assertLess(red[0], base[0])
        self.assertGreater(red[2], base[2])

    def test_live_lines_match_consensus_and_are_monotone(self):
        g = ensemble_engine.predict(_raw("1 - 1", "75'")).prediction.goals
        self.assertAlmostEqual(g.no_more_goals_pct + g.plus_1_goal_pct, 100.0, places=1)
        self.assertGreaterEqual(g.plus_1_goal_pct, g.plus_2_goals_pct)
        self.assertGreaterEqual(g.plus_2_goals_pct, g.plus_3_goals_pct)
        # Coherencia con la línea Over: Over (cg + 0.5) == +1 gol adicional
        self.assertAlmostEqual(g.over_2_5_pct, g.plus_1_goal_pct, delta=0.2)


if __name__ == "__main__":
    unittest.main()
