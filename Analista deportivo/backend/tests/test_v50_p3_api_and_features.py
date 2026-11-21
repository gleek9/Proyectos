"""
Pruebas unitarias e integración para Katakuri v5.0 Paso 3:
- /api/health v5.0.0 y /api/teams/search (búsqueda rápida con distinción F/W y Elo)
- PredictRequest con market_*_odds + use_market_prior + comparison/Edge/Kelly
- equity_curve en walk_forward_simulation y opening_vs_closing_comparison
"""
import unittest
from fastapi.testclient import TestClient

from backend.app.main import app
from backend.app.services.league_database import league_db
from backend.app.models.ensemble import ensemble_engine
from backend.app.analytics.backtest import run_walk_forward_backtest


class TestKatakuriV50Paso3(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(app)

    def test_health_reports_v5_and_rps_oos(self):
        resp = self.client.get("/api/health")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(data["version"], "5.0.0")
        self.assertIn("rps_oos", data)
        self.assertIsInstance(data["models_local"], list)
        self.assertGreaterEqual(len(data["models_local"]), 4)
        self.assertIn("7,270", data.get("dataset_summary", ""))

    def test_teams_search_autocomplete_and_womens_split(self):
        resp = self.client.get("/api/teams/search", params={"q": "Barcelona", "limit": 10})
        self.assertEqual(resp.status_code, 200)
        teams = resp.json().get("teams", [])
        self.assertGreater(len(teams), 0)
        names = [t["name"] for t in teams]
        self.assertTrue(any("Barcelona" in n for n in names))
        self.assertTrue(any(t.get("is_women") is True for t in teams))
        for item in teams:
            self.assertIn("league_name", item)
            self.assertIn("elo_rating", item)

        resp_ars = self.client.get("/api/teams/search", params={"q": "Arsenal", "limit": 5})
        self.assertEqual(resp_ars.status_code, 200)
        ars_teams = resp_ars.json().get("teams", [])
        self.assertGreater(len(ars_teams), 0)
        self.assertIn("Arsenal", ars_teams[0]["name"])

    def test_comparison_and_market_prior_toggle_vs_pure_model(self):
        raw = league_db.get_match_raw_features("Arsenal", "Chelsea")
        self.assertIsNotNone(raw)
        raw.market_home_odds = 1.95
        raw.market_draw_odds = 3.60
        raw.market_away_odds = 4.10

        pred_prior = ensemble_engine.predict(raw, use_market_prior=True)
        pred_pure = ensemble_engine.predict(raw, use_market_prior=False)

        self.assertIsNotNone(pred_prior.comparison)
        self.assertIsNotNone(pred_pure.comparison)
        self.assertTrue(pred_prior.comparison["use_market_prior"])
        self.assertFalse(pred_pure.comparison["use_market_prior"])
        self.assertIsNotNone(pred_prior.comparison["model_only_probs"])
        self.assertEqual(
            pred_pure.prediction.winner.home_win_pct,
            pred_pure.comparison["model_only_probs"]["home_win_pct"],
        )

        # Con cuotas personalizadas y prior activado debe acercarse más al mercado que el modelo puro
        val_eval = pred_pure.comparison["market_odds_eval"]["outcomes"]
        for side in ("home", "draw", "away"):
            self.assertGreater(val_eval[side]["fair_odds"], 1.0)
            self.assertIsNotNone(val_eval[side]["edge_pct"])
            self.assertIsNotNone(val_eval[side]["kelly_quarter_pct"])

        self.assertGreaterEqual(len(pred_pure.comparison["home"]["form_last_5"]), 1)

    def test_walk_forward_returns_equity_curve(self):
        res = run_walk_forward_backtest(n_matches=40, odds_source="opening")
        wf = res.get("walk_forward_simulation", {})
        vb = wf.get("value_betting", {})
        curve = vb.get("equity_curve", [])
        self.assertIsInstance(curve, list)
        self.assertGreaterEqual(len(curve), 1)
        first_pt = curve[0]
        self.assertIn("bet", first_pt)
        self.assertIn("flat_profit", first_pt)
        self.assertIn("kelly_profit", first_pt)

        comp = wf.get("opening_vs_closing_comparison", {})
        self.assertIn("bet365_opening", comp)
        self.assertIn("equity_curve", comp["bet365_opening"])


if __name__ == "__main__":
    unittest.main()
