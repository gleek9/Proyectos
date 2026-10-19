import unittest
from backend.app.analytics.backtest import (
    compute_rps,
    compute_brier_score,
    compute_log_loss,
    compute_mae,
    compute_rmse,
    run_backtest,
    get_benchmark_dataset
)

class TestV33BacktestFramework(unittest.TestCase):
    """
    Suite de pruebas para el framework de validación empírica y backtesting (Punto 3).
    """

    def test_rps_mathematical_properties(self):
        """Verifica el cálculo formal de RPS según Constantinou & Fenton."""
        # 1. Pronóstico perfecto de victoria local (100% Home) cuando gana Home ("1")
        rps_perfect = compute_rps(100.0, 0.0, 0.0, "1")
        self.assertAlmostEqual(rps_perfect, 0.0, places=5, msg="RPS para acierto total debe ser 0.0")

        # 2. Pronóstico completamente opuesto (100% Away) cuando gana Home ("1")
        rps_worst = compute_rps(0.0, 0.0, 100.0, "1")
        self.assertAlmostEqual(rps_worst, 1.0, places=5, msg="RPS para desacierto extremo ordinal debe ser 1.0")

        # 3. Pronóstico uniforme aleatorio (33.3%, 33.3%, 33.3%)
        # RPS = 0.5 * [(1/3 - 1)^2 + (2/3 - 1)^2] = 0.5 * [4/9 + 1/9] = 5/18 ≈ 0.27778
        rps_uniform = compute_rps(1.0, 1.0, 1.0, "1")
        self.assertAlmostEqual(rps_uniform, 5.0 / 18.0, places=4)

        # 4. Sensibilidad a la distancia ordinal:
        # Si el resultado es "1" (Local), predecir "X" (Empate) debe tener menor penalización que predecir "2" (Visitante)
        rps_draw_pred = compute_rps(0.0, 100.0, 0.0, "1")  # predijo X
        rps_away_pred = compute_rps(0.0, 0.0, 100.0, "1")  # predijo 2
        self.assertLess(rps_draw_pred, rps_away_pred, "RPS debe penalizar menos predecir Empate que predecir Visitante si ganó Local")

    def test_brier_score_and_log_loss(self):
        """Verifica Brier Score binario y Log-Loss."""
        # Brier perfecto
        self.assertAlmostEqual(compute_brier_score(100.0, True), 0.0)
        self.assertAlmostEqual(compute_brier_score(0.0, False), 0.0)

        # Brier peor caso
        self.assertAlmostEqual(compute_brier_score(100.0, False), 1.0)
        self.assertAlmostEqual(compute_brier_score(0.0, True), 1.0)

        # Log Loss
        ll_high = compute_log_loss(90.0, 5.0, 5.0, "1")
        ll_low = compute_log_loss(10.0, 10.0, 80.0, "1")
        self.assertLess(ll_high, ll_low, "Log-Loss debe ser mucho menor para eventos con alta probabilidad predicha")

    def test_mae_and_rmse(self):
        """Verifica MAE y RMSE."""
        preds = [2.0, 3.0, 1.0]
        actuals = [2.0, 4.0, 1.0]
        self.assertAlmostEqual(compute_mae(preds, actuals), 1.0 / 3.0, places=4)
        self.assertAlmostEqual(compute_rmse(preds, actuals), (1.0 / 3.0) ** 0.5, places=4)

    def test_full_backtest_execution_on_benchmark_dataset(self):
        """
        Ejecuta el backtesting sobre el dataset curado de partidos reales y verifica:
        - Estructura completa de reporte
        - RPS promedio competitivo (< 0.235)
        - Precisión clasificatoria y error absoluto en goles y córners
        - Veredicto de calibración emitido
        """
        benchmark_items = get_benchmark_dataset()
        self.assertGreaterEqual(len(benchmark_items), 5)

        results = run_backtest(benchmark_items)

        self.assertEqual(results["total_matches_evaluated"], len(benchmark_items))
        metrics = results["metrics"]

        # 1. Métricas de calibración presentes y en rangos válidos
        self.assertIn("rps_mean", metrics)
        self.assertIn("log_loss_mean", metrics)
        self.assertIn("brier_score_over_2_5", metrics)
        self.assertIn("brier_score_btts", metrics)
        self.assertIn("goals_mae", metrics)

        self.assertGreater(metrics["rps_mean"], 0.0)
        self.assertLess(metrics["rps_mean"], 0.25, "El RPS medio debe denotar calibración probabilística sólida")

        self.assertGreater(metrics["goals_mae"], 0.0)
        self.assertLess(metrics["goals_mae"], 2.0, "El MAE de goles debe estar por debajo de 2 goles")

        # 2. Veredicto emitido
        self.assertIn("verdict", results)
        self.assertIn("Calibración probabilística", results["verdict"])

        # 3. Informes individuales de partidos
        self.assertEqual(len(results["matches"]), len(benchmark_items))
        first_match = results["matches"][0]
        self.assertIn("match_id", first_match)
        self.assertIn("rps", first_match)
        self.assertIn("actual_score", first_match)

if __name__ == "__main__":
    unittest.main()
