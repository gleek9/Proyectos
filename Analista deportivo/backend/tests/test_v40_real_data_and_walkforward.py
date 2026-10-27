"""
Test Suite v4.0 — Katakuri v4: Validación de Datos Reales, Elo Dinámico y Backtesting Temporal Walk-Forward.
Verifica:
1. Integridad de la base de datos real oficial (más de 3,000 partidos, promedio de goles ~2.86, tasa de empate ~25%).
2. Calibración y jerarquía de Elo Dinámico (clubes de élite > 1850 vs clubes estándar 1550-1700).
3. Modulación del modelo Poisson Dixon-Coles por Elo y Splits Home/Away.
4. Inferencia del ensamble v4 (XGBoost 23 features + PyTorch LSTM + Poisson).
5. Evaluación temporal walk-forward out-of-sample y simulación de apuestas de valor (Value Betting vs Bet365).
"""
import unittest
import numpy as np
from backend.app.db import SessionLocal, HistoricalMatch, Team
from backend.app.services.league_database import league_db
from backend.app.models.ensemble import ensemble_engine
from backend.app.schemas.match import MatchRawFeatures, TeamFormStats, HeadToHeadStats
from backend.app.analytics.backtest import run_walk_forward_backtest, compute_rps

class TestV40RealDataAndWalkForward(unittest.TestCase):

    def setUp(self):
        self.db = SessionLocal()

    def tearDown(self):
        self.db.close()

    def test_01_real_database_integrity(self):
        """Valida que la base de datos contenga partidos reales oficiales con estadísticas macro correctas."""
        total_matches = self.db.query(HistoricalMatch).count()
        self.assertGreaterEqual(total_matches, 3000, f"Se esperaban >= 3000 partidos reales, encontrados: {total_matches}")

        # Comprobar promedio de goles real (en ligas europeas oscila entre 2.6 y 3.1)
        matches = self.db.query(HistoricalMatch).limit(500).all()
        total_goals = sum(m.home_goals + m.away_goals for m in matches)
        avg_goals = total_goals / len(matches)
        self.assertGreater(avg_goals, 2.4, f"Promedio de goles demasiado bajo: {avg_goals}")
        self.assertLess(avg_goals, 3.4, f"Promedio de goles corrupto o inflado: {avg_goals}")

        # Comprobar tasa de empates real (en ligas europeas oscila entre 22% y 29%)
        draws = sum(1 for m in matches if m.home_goals == m.away_goals)
        draw_rate = (draws / len(matches)) * 100.0
        self.assertGreater(draw_rate, 20.0, f"Tasa de empates anómalamente baja: {draw_rate}%")
        self.assertLess(draw_rate, 32.0, f"Tasa de empates anómalamente alta: {draw_rate}%")

    def test_02_dynamic_elo_hierarchy(self):
        """Valida que los ratings Elo calculados cronológicamente reflejen la verdadera jerarquía deportiva."""
        rm = league_db.normalize_team("Real Madrid", db=self.db)
        mci = league_db.normalize_team("Manchester City", db=self.db)
        bay = league_db.normalize_team("Bayern Munich", db=self.db)
        getafe = league_db.normalize_team("Getafe", db=self.db)

        self.assertIsNotNone(rm, "Real Madrid debe estar indexado")
        self.assertIsNotNone(mci, "Manchester City debe estar indexado")
        self.assertIsNotNone(bay, "Bayern Munich debe estar indexado")
        self.assertIsNotNone(getafe, "Getafe debe estar indexado")

        self.assertGreater(rm.elo_rating, 1850.0, f"Elo de Real Madrid ({rm.elo_rating}) debe ser élite")
        self.assertGreater(mci.elo_rating, 1850.0, f"Elo de Manchester City ({mci.elo_rating}) debe ser élite")
        self.assertGreater(bay.elo_rating, 1850.0, f"Elo de Bayern ({bay.elo_rating}) debe ser élite")

        # Diferencia de nivel marcada entre élite y zona media/baja
        self.assertGreater(rm.elo_rating - getafe.elo_rating, 200.0, "Diferencia de Elo debe ser sustancial")

    def test_03_ensemble_prediction_coherence(self):
        """Valida la coherencia probabilística de las predicciones de Katakuri v4."""
        raw = league_db.get_match_raw_features("Manchester City", "Southampton", "Premier League")
        self.assertIsNotNone(raw)

        pred_res = ensemble_engine.predict(raw)
        pred = pred_res.prediction

        # Probabilidades 1X2 suman 100%
        sum_prob = pred.winner.home_win_pct + pred.winner.draw_pct + pred.winner.away_win_pct
        self.assertAlmostEqual(sum_prob, 100.0, delta=0.5)

        # Manchester City como favorito claro en casa
        self.assertGreater(pred.winner.home_win_pct, 60.0)
        self.assertLess(pred.winner.away_win_pct, 18.0)

        # Consistencia de goles
        self.assertGreater(pred.goals.expected_total, 2.0)
        self.assertLess(pred.goals.expected_total, 4.0)

    def test_04_walk_forward_backtest_execution(self):
        """Valida la ejecución del backtesting temporal walk-forward sobre partidos oficiales reales."""
        res = run_walk_forward_backtest(n_matches=60)
        self.assertEqual(res["total_matches_evaluated"], 60)

        metrics = res["metrics"]
        # Calibración estricta Constantinou-Fenton
        self.assertLess(metrics["rps_mean"], 0.22, f"RPS ({metrics['rps_mean']}) debe ser <= 0.22")
        self.assertLess(metrics["goals_mae"], 1.45, f"MAE de goles ({metrics['goals_mae']}) debe ser < 1.45")

        # Verificación de simulación Value Betting
        self.assertIn("walk_forward_simulation", res)
        wf_sim = res["walk_forward_simulation"]
        self.assertIn("value_betting", wf_sim)
        vb = wf_sim["value_betting"]
        self.assertGreater(vb["total_bets_placed"], 0, "Debe identificar oportunidades de valor")
        self.assertIn("roi_pct", vb)

if __name__ == "__main__":
    unittest.main()
