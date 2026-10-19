"""
Test de Validación Katakuri v2.5 (Fase 1 de Mejoras Matemáticas en Vivo):
1. Curva empírica no lineal de llegada de goles (Goal Arrival Rate no homogéneo) vs reducción lineal plana.
2. Desactivación rigurosa de corrección tau Dixon-Coles en cálculo de goles adicionales en vivo.
3. Ponderación dinámica bayesiana por minuto del meta-ensamble (Poisson condicional gana peso en el cierre).
"""
import sys
import os
import unittest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from backend.app.schemas.match import MatchRawFeatures, TeamFormStats, HeadToHeadStats
from backend.app.models.poisson import (
    poisson_model,
    parse_elapsed_minute,
    calculate_remaining_goal_ratio,
    calculate_remaining_corner_ratio
)
from backend.app.models.tabular_ml import tabular_predictor
from backend.app.models.lstm_net import lstm_predictor
from backend.app.models.ensemble import ensemble_engine

class TestPhase1LiveMath(unittest.TestCase):

    def test_non_linear_goal_arrival_curve(self):
        """Verifica que la curva de goles refleje que el 2do tiempo y los minutos finales concentran mayor peligro."""
        # Al minuto 45 (descanso), queda ~54% del poder de gol (en fútbol profesional se anota más en el 2T)
        ratio_45 = calculate_remaining_goal_ratio(45)
        self.assertAlmostEqual(ratio_45, 0.540, places=2)
        self.assertGreater(ratio_45, 0.50, "En el descanso debe quedar más del 50% de los goles (curva 2T)")

        # Al minuto 75, la lineal daría (90-75)/90 = 0.166. La curva empírica da ~0.225 (fatiga/urgencia)
        ratio_75 = calculate_remaining_goal_ratio(75)
        self.assertAlmostEqual(ratio_75, 0.225, places=2)
        self.assertGreater(ratio_75, 0.166, "Al min 75 debe proyectar más expectativa que una simple recta lineal")

        # Monotonía decreciente estricta
        r0 = calculate_remaining_goal_ratio(0)
        r30 = calculate_remaining_goal_ratio(30)
        r60 = calculate_remaining_goal_ratio(60)
        r85 = calculate_remaining_goal_ratio(85)
        self.assertTrue(r0 > r30 > ratio_45 > r60 > ratio_75 > r85)

    def test_dixon_coles_tau_deactivation_in_live(self):
        """Verifica que en modo en vivo no se penalice con tau los goles adicionales restantes."""
        lambda_val, mu_val = 0.6, 0.5
        # En pre-match: aplica tau (0,0) -> 1 - lambda * mu * (-0.10) > 1.0
        mat_prematch = poisson_model.compute_bivariate_matrix(lambda_val, mu_val, apply_dixon_coles=True)
        # En live: tau=1.0 (Poisson bivariado condicional independiente sobre goles restantes)
        mat_live = poisson_model.compute_bivariate_matrix(lambda_val, mu_val, apply_dixon_coles=False)

        self.assertNotEqual(mat_prematch[0, 0], mat_live[0, 0], "La matriz en vivo debe prescindir del tau artificial pre-match")
        self.assertAlmostEqual(float(mat_live.sum()), 1.0, places=4)

    def test_dynamic_weights_by_minute(self):
        """Verifica que Poisson condicional gane peso relativo a medida que avanza el partido hacia el minuto 90."""
        # Pre-match: 40% Poisson, 35% XGB, 25% LSTM
        w_pre = ensemble_engine._get_dynamic_weights(is_live=False)
        self.assertEqual(w_pre, (0.40, 0.35, 0.25))

        # En vivo minuto 10
        wp_10, wx_10, wl_10 = ensemble_engine._get_dynamic_weights(is_live=True, elapsed_min=10)
        # En vivo minuto 45
        wp_45, wx_45, wl_45 = ensemble_engine._get_dynamic_weights(is_live=True, elapsed_min=45)
        # En vivo minuto 80
        wp_80, wx_80, wl_80 = ensemble_engine._get_dynamic_weights(is_live=True, elapsed_min=80)

        # Poisson condicional debe crecer con el tiempo
        self.assertGreater(wp_45, wp_10)
        self.assertGreater(wp_80, wp_45)
        self.assertGreaterEqual(wp_80, 0.70, "Al minuto 80 el modelo condicional matemático debe tener al menos 70% del peso")

        # XGBoost y LSTM deben ceder peso de forma controlada
        self.assertLess(wx_80, wx_10)
        self.assertLess(wl_80, wl_10)

        # Todos deben sumar 1.0 exacto
        self.assertAlmostEqual(wp_80 + wx_80 + wl_80, 1.0, places=5)

    def test_end_to_end_live_minute_80_progression(self):
        """Prueba de integración en vivo: Minuto 82 con marcador 1 - 0 para Real Madrid."""
        raw = MatchRawFeatures(
            home_team="Real Madrid",
            away_team="Sevilla",
            competition="LaLiga",
            is_live=True,
            live_minute="82'",
            live_score="1 - 0",
            home_stats=TeamFormStats(team_name="Real Madrid", avg_goals_scored=2.2, avg_goals_conceded=0.9),
            away_stats=TeamFormStats(team_name="Sevilla", avg_goals_scored=1.1, avg_goals_conceded=1.5),
            h2h=HeadToHeadStats()
        )

        res = ensemble_engine.predict(raw)
        winner = res.prediction.winner
        goals = res.prediction.goals

        # Al min 82 ganando 1-0, la probabilidad local debe ser dominante y sólida
        self.assertGreaterEqual(winner.home_win_pct, 75.0)
        self.assertAlmostEqual(winner.home_win_pct + winner.draw_pct + winner.away_win_pct, 100.0, places=1)

        # Los goles proyectados no pueden ser menores a 1.0
        self.assertGreaterEqual(goals.expected_total, 1.0)
        self.assertIsNotNone(goals.no_more_goals_pct)
        self.assertIsNotNone(goals.more_goals_pct)
        self.assertAlmostEqual(goals.no_more_goals_pct + goals.more_goals_pct, 100.0, places=1)

if __name__ == "__main__":
    unittest.main()
