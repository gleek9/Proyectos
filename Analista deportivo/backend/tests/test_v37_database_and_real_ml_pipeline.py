"""
Suite de Pruebas Unitarias y de Integración: Katakuri v3.7
Valida:
1. Base de Datos de Ligas Grandes: Consulta ultrarrápida (<50ms).
2. Normalización de Equipos y Alias (Man City, Atleti, BVB, etc.).
3. Fallback seguro a None para equipos no catalogados.
4. Coeficiente rho de Dixon-Coles dinámico por competición.
5. Acoplamiento in-play de córners con Game State Effect.
6. Inferencia de modelos reentrenados con datos reales (XGBoost y LSTM).
"""
import unittest
import time
from backend.app.services.league_database import league_db
from backend.app.models.poisson import (
    poisson_model, get_competition_rho, COMPETITION_BASELINES
)
from backend.app.models.tabular_ml import tabular_predictor
from backend.app.models.lstm_net import lstm_predictor
from backend.app.models.ensemble import ensemble_engine
from backend.app.schemas.match import (
    MatchRawFeatures, TeamFormStats, HeadToHeadStats, PreviousMatch
)

class TestV37DatabaseAndRealML(unittest.TestCase):
    def test_database_fast_lookup(self):
        """Verifica que un partido de liga grande se resuelva desde SQLite en menos de 50 ms."""
        t0 = time.time()
        raw = league_db.get_match_raw_features("Real Madrid", "Barcelona")
        elapsed_ms = (time.time() - t0) * 1000.0

        self.assertIsNotNone(raw)
        self.assertEqual(raw.home_team, "Real Madrid")
        self.assertEqual(raw.away_team, "Barcelona")
        self.assertEqual(raw.competition, "LaLiga")
        self.assertGreater(len(raw.home_stats.last_matches), 3)
        self.assertGreater(raw.h2h.total_matches_analyzed, 0)
        self.assertLess(elapsed_ms, 50.0, f"La consulta demoró {elapsed_ms:.1f}ms, esperada <50ms")

    def test_alias_normalization(self):
        """Comprueba que alias informales resuelvan al nombre canónico oficial del club."""
        cases = [
            ("man city", "Manchester City"),
            ("atleti", "Atletico Madrid"),
            ("bvb", "Borussia Dortmund"),
            ("leverkusen", "Bayer Leverkusen"),
            ("chivas", "Guadalajara"),
            ("inter milan", "Inter"),
            ("paris", "PSG")
        ]
        for query, expected_canonical in cases:
            team = league_db.normalize_team(query)
            self.assertIsNotNone(team, f"No se encontró equipo para alias '{query}'")
            self.assertEqual(team.name, expected_canonical)

    def test_unknown_team_fallback_returns_none(self):
        """Garantiza que equipos desconocidos retornen None para que collector.py use scraping web."""
        raw = league_db.get_match_raw_features("Equipo Fantasma A", "Equipo Fantasma B")
        self.assertIsNone(raw)

    def test_dynamic_competition_rho(self):
        """Verifica que el coeficiente rho de Dixon-Coles se adapte a la naturaleza táctica de cada torneo."""
        self.assertEqual(get_competition_rho("Bundesliga"), -0.05)
        self.assertEqual(get_competition_rho("Serie A"), -0.13)
        self.assertEqual(get_competition_rho("LaLiga 2 / Segunda"), -0.15)
        self.assertEqual(get_competition_rho("Premier League"), -0.10)
        self.assertEqual(get_competition_rho("Eredivisie"), -0.04)
        self.assertEqual(get_competition_rho("Torneo Desconocido"), -0.10)

    def test_corner_game_state_coupling_in_play(self):
        """Verifica que un equipo local en desventaja por 1 gol al min 70 acelere su tasa de córners restantes."""
        raw_level = MatchRawFeatures(
            home_team="Real Madrid",
            away_team="Sevilla",
            competition="LaLiga",
            is_live=True,
            live_minute="70'",
            live_score="1 - 1",
            live_corners=6,
            home_stats=TeamFormStats(team_name="Real Madrid", avg_goals_scored=2.2, avg_goals_conceded=0.8, avg_corners=6.0, avg_cards=1.8),
            away_stats=TeamFormStats(team_name="Sevilla", avg_goals_scored=1.1, avg_goals_conceded=1.4, avg_corners=4.0, avg_cards=2.4),
            h2h=HeadToHeadStats()
        )
        p_res_level = poisson_model.predict(raw_level)

        raw_trailing = MatchRawFeatures(
            home_team="Real Madrid",
            away_team="Sevilla",
            competition="LaLiga",
            is_live=True,
            live_minute="70'",
            live_score="1 - 2",  # Local perdiendo por 1 gol: asedio en recta final
            live_corners=6,
            home_stats=TeamFormStats(team_name="Real Madrid", avg_goals_scored=2.2, avg_goals_conceded=0.8, avg_corners=6.0, avg_cards=1.8),
            away_stats=TeamFormStats(team_name="Sevilla", avg_goals_scored=1.1, avg_goals_conceded=1.4, avg_corners=4.0, avg_cards=2.4),
            h2h=HeadToHeadStats()
        )
        p_res_trailing = poisson_model.predict(raw_trailing)

        rem_level = p_res_level["corners"]["expected_remaining_corners"]
        rem_trailing = p_res_trailing["corners"]["expected_remaining_corners"]
        self.assertGreater(rem_trailing, rem_level, "Los córners residuales deben acelerarse cuando el local va perdiendo en el min 70'")

    def test_real_trained_models_inference_and_ensemble(self):
        """Verifica que los modelos entrenados con datos reales produzcan distribuciones coherentes y sumen 100.0%."""
        raw = league_db.get_match_raw_features("Manchester City", "Arsenal")
        self.assertIsNotNone(raw)

        xgb_res = tabular_predictor.predict(raw)
        self.assertEqual(xgb_res["model_name"], "xgboost_tabular")
        p_tot_xgb = sum(xgb_res["winner_probs"].values())
        self.assertAlmostEqual(p_tot_xgb, 100.0, places=1)

        lstm_res = lstm_predictor.predict(raw)
        self.assertEqual(lstm_res["model_name"], "lstm_recurrent_net")
        p_tot_lstm = sum(lstm_res["winner_probs"].values())
        self.assertAlmostEqual(p_tot_lstm, 100.0, places=1)

        ens_res = ensemble_engine.predict(raw)
        p_tot_ens = ens_res.prediction.winner.home_win_pct + ens_res.prediction.winner.draw_pct + ens_res.prediction.winner.away_win_pct
        self.assertAlmostEqual(p_tot_ens, 100.0, places=1)
        self.assertTrue(len(ens_res.prediction.winner.human_verdict) > 5)

if __name__ == "__main__":
    unittest.main()
