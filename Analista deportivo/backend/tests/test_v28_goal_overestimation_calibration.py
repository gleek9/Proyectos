"""
Test de Validación Katakuri v2.8:
Calibración y Erradicación de Sobreestimación de Goles (Pre-Match e In-Play):
1. Control de picos goleadores extremos mediante Shrinkage Bayesiano y Amortiguamiento Elástico (gamma=0.65).
2. Eliminación de sesgo artificial de Over 2.5 en Tabular XGBoost.
3. Modulación de momentum en LSTM sin inyección de goles brutos descalibrados.
"""
import sys
import os
import unittest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from backend.app.schemas.match import MatchRawFeatures, TeamFormStats, HeadToHeadStats
from backend.app.models.ensemble import ensemble_engine

class TestGoalOverestimationCalibration(unittest.TestCase):

    def test_extreme_favorite_goal_capping(self):
        """Valida que un favorito aplastante con estadísticas altas no proyecte más de 3.85 goles totales."""
        # Man City (2.5 anotados, 0.8 concedidos) vs Burnley (0.9 anotados, 1.9 concedidos)
        m = MatchRawFeatures(
            home_team="Manchester City",
            away_team="Burnley",
            competition="Premier League",
            home_stats=TeamFormStats(team_name="Manchester City", avg_goals_scored=2.5, avg_goals_conceded=0.8),
            away_stats=TeamFormStats(team_name="Burnley", avg_goals_scored=0.9, avg_goals_conceded=1.9),
            h2h=HeadToHeadStats(total_matches_analyzed=0, home_team_wins=0, away_team_wins=0, draws=0, avg_total_goals_h2h=2.5)
        )
        res = ensemble_engine.predict(m)
        exp_goals = res.prediction.goals.expected_total
        top_score = res.prediction.goals.most_likely_score

        # Debe estar acotado en un rango realista (entre 3.0 y 3.75)
        self.assertLessEqual(exp_goals, 3.75, f"La expectativa de goles ({exp_goals}) no debe sobreestimar más de 3.75")
        self.assertGreaterEqual(exp_goals, 2.90, f"La expectativa de goles ({exp_goals}) debe ser sólida para un favorito")

        # El marcador más probable no debe ser un astronómico 4-0
        self.assertIn(top_score, ["2 - 0", "2 - 1", "3 - 0", "3 - 1"], f"Marcador '{top_score}' debe ser realista")

    def test_tactical_low_scoring_match(self):
        """Valida que partidos tácticos (LaLiga/Serie A) mantengan expectativa calibrada entre 2.0 y 2.5 goles."""
        # Atlético de Madrid vs Athletic Club
        m = MatchRawFeatures(
            home_team="Atletico Madrid",
            away_team="Athletic Club",
            competition="LaLiga",
            home_stats=TeamFormStats(team_name="Atletico Madrid", avg_goals_scored=1.4, avg_goals_conceded=0.8),
            away_stats=TeamFormStats(team_name="Athletic Club", avg_goals_scored=1.2, avg_goals_conceded=0.9),
            h2h=HeadToHeadStats(total_matches_analyzed=3, home_team_wins=1, away_team_wins=1, draws=1, avg_total_goals_h2h=2.0)
        )
        res = ensemble_engine.predict(m)
        exp_goals = res.prediction.goals.expected_total
        over_2_5 = res.prediction.goals.over_2_5_pct
        top_score = res.prediction.goals.most_likely_score

        self.assertLessEqual(exp_goals, 2.55, f"Duelo cerrado en LaLiga no debe exceder 2.55 goles ({exp_goals})")
        self.assertGreaterEqual(exp_goals, 2.05, f"Duelo cerrado no debe colapsar a 0-0 irreal ({exp_goals})")
        self.assertLessEqual(over_2_5, 48.0, f"Over 2.5 en duelo táctico debe ser < 48% ({over_2_5}%)")
        self.assertIn(top_score, ["1 - 1", "1 - 0", "2 - 1", "0 - 1"], f"Marcador '{top_score}' debe reflejar fútbol profesional")

    def test_balanced_top_tier_derby(self):
        """Valida un clásico de alto ritmo (Liverpool vs Man City) en un rango equilibrado de 2.9 a 3.4 goles."""
        m = MatchRawFeatures(
            home_team="Liverpool",
            away_team="Manchester City",
            competition="Premier League",
            home_stats=TeamFormStats(team_name="Liverpool", avg_goals_scored=2.3, avg_goals_conceded=1.0),
            away_stats=TeamFormStats(team_name="Manchester City", avg_goals_scored=2.2, avg_goals_conceded=0.9),
            h2h=HeadToHeadStats(total_matches_analyzed=4, home_team_wins=1, away_team_wins=1, draws=2, avg_total_goals_h2h=2.75)
        )
        res = ensemble_engine.predict(m)
        exp_goals = res.prediction.goals.expected_total

        self.assertLessEqual(exp_goals, 3.45, f"Clásico Premier no debe exceder 3.45 goles ({exp_goals})")
        self.assertGreaterEqual(exp_goals, 2.85, f"Clásico Premier debe mantener ritmo alto ({exp_goals})")

if __name__ == "__main__":
    unittest.main()
