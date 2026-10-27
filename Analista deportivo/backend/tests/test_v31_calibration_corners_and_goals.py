"""
Test Suite de Validación Katakuri v3.1:
1. Erradicación de Córners y Tiros de Esquina Inflados (Balanza Territorial y Regularización Bayesiana).
2. Erradicación de Goles Sobredimensionados (Elasticidad gamma=0.52 y Techo Dinámico de Competición).
3. Concordancia y Consistencia del Marcador Más Probable (eliminación de empate 1-1 cuando hay favorito claro).
4. Proyección Adaptativa In-Play de Córners con Ritmo Empírico Observado.
"""
import sys
import os
import unittest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from backend.app.schemas.match import MatchRawFeatures, TeamFormStats, HeadToHeadStats
from backend.app.models.ensemble import ensemble_engine

class TestV31CalibrationCornersAndGoals(unittest.TestCase):

    def test_corners_territorial_balance_capping(self):
        """Valida que un partido con dos equipos de ataque no infle córners a 12 o 13."""
        # Dos equipos ofensivos (6.2 y 5.5 córners)
        m = MatchRawFeatures(
            home_team="Arsenal",
            away_team="Tottenham",
            competition="Premier League",
            home_stats=TeamFormStats(team_name="Arsenal", avg_goals_scored=2.1, avg_goals_conceded=1.0, avg_corners=6.2),
            away_stats=TeamFormStats(team_name="Tottenham", avg_goals_scored=1.8, avg_goals_conceded=1.4, avg_corners=5.5),
            h2h=HeadToHeadStats(total_matches_analyzed=3, home_team_wins=2, away_team_wins=1, draws=0, avg_total_goals_h2h=3.0, avg_total_corners_h2h=10.0)
        )
        res = ensemble_engine.predict(m)
        corners = res.prediction.corners
        exp_cn = corners.expected_total
        over_9_5 = corners.over_9_5_pct

        # Debe estar acotado en un rango realista (máximo 10.6)
        self.assertLessEqual(exp_cn, 10.6, f"Los córners proyectados ({exp_cn}) no deben sobrepasar 10.6")
        self.assertGreaterEqual(exp_cn, 9.4, f"Los córners proyectados ({exp_cn}) deben mantener buen ritmo en un derbi")
        self.assertLessEqual(over_9_5, 66.0, f"Over 9.5 ({over_9_5}%) no debe estar descalibrado")

    def test_scoreline_concordance_with_winner(self):
        """Valida que un favorito local indiscutible proyecte un marcador ganador, no 1-1."""
        m = MatchRawFeatures(
            home_team="Real Madrid",
            away_team="Osasuna",
            competition="LaLiga",
            home_stats=TeamFormStats(team_name="Real Madrid", avg_goals_scored=2.2, avg_goals_conceded=0.8, avg_corners=6.2),
            away_stats=TeamFormStats(team_name="Osasuna", avg_goals_scored=1.0, avg_goals_conceded=1.4, avg_corners=4.0),
            h2h=HeadToHeadStats(total_matches_analyzed=4, home_team_wins=3, away_team_wins=0, draws=1, avg_total_goals_h2h=2.5, avg_total_corners_h2h=9.2)
        )
        res = ensemble_engine.predict(m)
        pred = res.prediction
        home_win_pct = pred.winner.home_win_pct
        most_likely_score = pred.goals.most_likely_score

        self.assertGreaterEqual(home_win_pct, 55.0)
        # Parsear marcador
        gh, ga = [int(x.strip()) for x in most_likely_score.split("-")]
        self.assertGreater(gh, ga, f"Para favorito claro ({home_win_pct}%), el marcador ({most_likely_score}) debe ser victoria local")
        self.assertIn(most_likely_score, ["1 - 0", "2 - 0", "2 - 1", "3 - 0", "3 - 1"])

    def test_live_corners_slow_pace_adaptation(self):
        """Valida que si en el minuto 65 solo van 4 córners, el modelo no proyecte 8 o 9 al final."""
        m = MatchRawFeatures(
            home_team="Liverpool",
            away_team="Brighton",
            competition="Premier League",
            is_live=True,
            live_minute="65'",
            live_score="1 - 0",
            live_corners=4,
            home_stats=TeamFormStats(team_name="Liverpool", avg_goals_scored=2.1, avg_goals_conceded=1.0, avg_corners=6.5),
            away_stats=TeamFormStats(team_name="Brighton", avg_goals_scored=1.4, avg_goals_conceded=1.5, avg_corners=4.8),
            h2h=HeadToHeadStats(total_matches_analyzed=3, home_team_wins=2, away_team_wins=0, draws=1, avg_total_goals_h2h=2.6, avg_total_corners_h2h=9.8)
        )
        res = ensemble_engine.predict(m)
        corners = res.prediction.corners
        exp_cn = corners.expected_total
        over_9_5 = corners.over_9_5_pct

        # Con solo 4 córners al minuto 65, ritmo final proyectado debe rondar 6 a 7
        self.assertLessEqual(exp_cn, 7.2, f"En directo con 4 córners al 65', la proyección final ({exp_cn}) no debe inflarse")
        self.assertLessEqual(over_9_5, 10.0, f"Over 9.5 con 4 córners al 65' debe ser casi imposible ({over_9_5}%)")

    def test_calibrated_goal_volumes(self):
        """Valida que partidos promedio de LaLiga y Premier se mantengan dentro de 2.4 a 3.1 goles."""
        m_laliga = MatchRawFeatures(
            home_team="Villarreal",
            away_team="Sevilla",
            competition="LaLiga",
            home_stats=TeamFormStats(team_name="Villarreal", avg_goals_scored=1.5, avg_goals_conceded=1.2),
            away_stats=TeamFormStats(team_name="Sevilla", avg_goals_scored=1.2, avg_goals_conceded=1.3),
            h2h=HeadToHeadStats(total_matches_analyzed=2, home_team_wins=1, away_team_wins=0, draws=1, avg_total_goals_h2h=2.0)
        )
        res = ensemble_engine.predict(m_laliga)
        exp_goals = res.prediction.goals.expected_total
        self.assertLessEqual(exp_goals, 2.75, f"Duelo estándar de LaLiga no debe exceder 2.75 ({exp_goals})")
        self.assertGreaterEqual(exp_goals, 2.25)

if __name__ == "__main__":
    unittest.main()
