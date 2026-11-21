import json
import os
import unittest

from backend.app.models.dixon_coles_mle import dixon_coles_mle
from backend.app.models.ensemble import ensemble_engine
from backend.app.models.lstm_net import FEATURES_PER_STEP, TIMESTEPS, lstm_predictor
from backend.app.models.poisson import poisson_model
from backend.app.models.tabular_ml import FEATURE_NAMES, _HAS_LGB, tabular_predictor
from backend.app.schemas.prediction import MatchMeta
from backend.app.services.league_database import league_db


class TestKatakuriV5Paso2ModelsAndCalibration(unittest.TestCase):
    def setUp(self):
        self.raw = league_db.get_match_raw_features("Arsenal", "Liverpool", "Premier League")
        self.assertIsNotNone(self.raw)

    def test_01_dixon_coles_mle_loaded_pre_cutoff(self):
        self.assertEqual(dixon_coles_mle.cutoff_date, "2025-01-01")
        self.assertIn("premier_league", dixon_coles_mle.leagues)
        mle = dixon_coles_mle.get_match_lambdas("Premier League", "Arsenal", "Liverpool")
        self.assertIsNotNone(mle)
        lam_h, mu_a, rho = mle
        self.assertGreaterEqual(lam_h, 0.35)
        self.assertLessEqual(lam_h, 3.40)
        self.assertGreaterEqual(mu_a, 0.25)
        self.assertLessEqual(mu_a, 2.90)
        self.assertGreaterEqual(rho, -0.30)
        self.assertLessEqual(rho, 0.30)

    def test_02_poisson_hybrid_xg_and_cards_referee_sensitivity(self):
        raw_high_xg = self.raw.model_copy(deep=True)
        raw_high_xg.home_stats.avg_xg_for = 2.45
        raw_high_xg.away_stats.avg_xg_against = 1.75
        raw_low_xg = self.raw.model_copy(deep=True)
        raw_low_xg.home_stats.avg_xg_for = 0.85
        raw_low_xg.away_stats.avg_xg_against = 0.70

        p_high = poisson_model.predict(raw_high_xg)
        p_low = poisson_model.predict(raw_low_xg)
        self.assertGreater(p_high["lambda_home"], p_low["lambda_home"])

        raw_strict_ref = self.raw.model_copy(deep=True)
        raw_strict_ref.referee_avg_cards = 6.4
        raw_strict_ref.home_stats.avg_fouls_for = 14.5
        raw_strict_ref.away_stats.avg_fouls_for = 14.0

        raw_lenient_ref = self.raw.model_copy(deep=True)
        raw_lenient_ref.referee_avg_cards = 2.3
        raw_lenient_ref.home_stats.avg_fouls_for = 8.0
        raw_lenient_ref.away_stats.avg_fouls_for = 8.5

        c_strict = poisson_model.predict(raw_strict_ref)
        c_lenient = poisson_model.predict(raw_lenient_ref)
        self.assertGreaterEqual(c_strict["cards"]["expected_total"], c_lenient["cards"]["expected_total"] + 0.8)
        self.assertGreater(
            c_strict["cards"]["over_4_5_pct"],
            c_lenient["cards"]["over_4_5_pct"],
        )

    def test_03_tabular_v5_44_features_and_lightgbm_loaded(self):
        self.assertEqual(len(FEATURE_NAMES), 44)
        self.assertIsNotNone(tabular_predictor.model)
        self.assertEqual(tabular_predictor.model.num_features(), 44)
        if _HAS_LGB:
            self.assertIsNotNone(tabular_predictor.lgb_model)
            self.assertEqual(tabular_predictor.lgb_model.num_feature(), 44)

        vec = tabular_predictor.extract_features(self.raw)
        self.assertEqual(vec.shape, (1, 44))
        res_tab = tabular_predictor.predict(self.raw)
        probs = res_tab["winner_probs"]
        self.assertAlmostEqual(sum(probs.values()), 100.0, delta=0.2)
        for p in probs.values():
            self.assertGreater(p, 1.0)

    def test_04_lstm_v5_14_features_and_calibration_file(self):
        self.assertEqual(FEATURES_PER_STEP, 14)
        self.assertIsNotNone(lstm_predictor.model)
        seq = lstm_predictor._build_sequence_tensor(
            self.raw.home_stats.last_matches,
            self.raw.home_stats.avg_goals_scored,
            self.raw.home_stats.avg_goals_conceded,
        )
        self.assertEqual(tuple(seq.shape), (1, TIMESTEPS, 14))
        res_lstm = lstm_predictor.predict(self.raw)
        probs = res_lstm["winner_probs"]
        self.assertAlmostEqual(sum(probs.values()), 100.0, delta=0.2)

        calib_path = os.path.join("backend", "weights", "ensemble_calibration.json")
        self.assertTrue(os.path.exists(calib_path))
        with open(calib_path, "r", encoding="utf-8") as f:
            calib = json.load(f)
        self.assertEqual(calib.get("cutoff_date"), "2025-01-01")
        total_w = calib["weight_poisson"] + calib["weight_xgboost"] + calib["weight_lstm"]
        self.assertAlmostEqual(total_w, 1.0, places=3)

    def test_05_ensemble_exposes_sub_models_in_response(self):
        raw_test = self.raw.model_copy(deep=True)
        raw_test.referee_name = "Michael Oliver"
        resp = ensemble_engine.predict(raw_test)
        self.assertIsNotNone(resp.sub_models)
        for key in ("poisson_dixon_coles", "tabular_ml", "rich_lstm", "weights"):
            self.assertIn(key, resp.sub_models)
        self.assertEqual(resp.match.referee_name, "Michael Oliver")
        w = resp.prediction.winner
        total_pct = w.home_win_pct + w.draw_pct + w.away_win_pct
        self.assertAlmostEqual(total_pct, 100.0, delta=0.3)


if __name__ == "__main__":
    unittest.main()

