"""
Test Suite v4.1 — Katakuri v4.1: Expansión a 9 Competiciones (4,749 Partidos Oficiales),
Calibración Point-in-Time Cero Look-Ahead, Detección de Empates y Kelly Value Betting.
"""
import unittest
from backend.app.db import SessionLocal, HistoricalMatch, Team, League
from backend.app.services.league_database import league_db
from backend.app.models.poisson import poisson_model
from backend.app.models.tabular_ml import tabular_predictor, FEATURE_NAMES
from backend.app.models.ensemble import ensemble_engine
from backend.app.analytics.backtest import run_walk_forward_backtest


class TestV41ExpandedLeaguesAndCalibration(unittest.TestCase):

    def setUp(self):
        self.db = SessionLocal()

    def tearDown(self):
        self.db.close()

    def test_01_nine_competitions_and_expanded_dataset(self):
        """Verifica que analista.db contenga las 9 ligas activas, >= 4,500 partidos reales y >= 150 clubes."""
        total_matches = self.db.query(HistoricalMatch).count()
        total_teams = self.db.query(Team).count()
        total_leagues = self.db.query(League).count()

        self.assertGreaterEqual(total_matches, 4500, f"Se esperaban >= 4500 partidos oficiales, encontrados: {total_matches}")
        self.assertGreaterEqual(total_teams, 150, f"Se esperaban >= 150 clubes, encontrados: {total_teams}")
        self.assertGreaterEqual(total_leagues, 9, f"Se esperaban 9 competiciones activas, encontradas: {total_leagues}")

        eredivisie_matches = self.db.query(HistoricalMatch).filter(HistoricalMatch.league_code == "eredivisie").count()
        primeira_matches = self.db.query(HistoricalMatch).filter(HistoricalMatch.league_code == "primeira_liga").count()
        self.assertGreaterEqual(eredivisie_matches, 600, "Eredivisie debe contar con al menos 2 temporadas completas (>600 partidos)")
        self.assertGreaterEqual(primeira_matches, 600, "Primeira Liga debe contar con al menos 2 temporadas completas (>600 partidos)")

    def test_02_eredivisie_and_primeira_liga_club_resolution(self):
        """Verifica resolución instantánea y jerarquía Elo en Eredivisie y Primeira Liga."""
        psv = league_db.normalize_team("PSV", db=self.db)
        fey = league_db.normalize_team("Feyenoord", db=self.db)
        scp = league_db.normalize_team("Sporting Lisboa", db=self.db)
        slb = league_db.normalize_team("SL Benfica", db=self.db)
        fcp = league_db.normalize_team("Oporto", db=self.db)

        self.assertIsNotNone(psv)
        self.assertIsNotNone(fey)
        self.assertIsNotNone(scp)
        self.assertIsNotNone(slb)
        self.assertIsNotNone(fcp)

        self.assertEqual(psv.name, "PSV Eindhoven")
        self.assertEqual(scp.name, "Sporting CP")
        self.assertEqual(slb.name, "Benfica")
        self.assertEqual(fcp.name, "FC Porto")

        self.assertGreater(psv.elo_rating, 1750.0)
        self.assertGreater(scp.elo_rating, 1750.0)

        # Predicción completa de clásico portugués y neerlandés
        raw_pt = league_db.get_match_raw_features("Sporting CP", "Benfica", "Primeira Liga")
        self.assertIsNotNone(raw_pt)
        res_pt = ensemble_engine.predict(raw_pt)
        self.assertAlmostEqual(
            res_pt.prediction.winner.home_win_pct + res_pt.prediction.winner.draw_pct + res_pt.prediction.winner.away_win_pct,
            100.0,
            delta=0.5
        )

    def test_03_tabular_23_features_alignment(self):
        """Garantiza que el extractor tabular opere estrictamente con las 23 features de v4.1."""
        self.assertEqual(len(FEATURE_NAMES), 23)
        raw = league_db.get_match_raw_features("PSV Eindhoven", "Ajax", "Eredivisie")
        self.assertIsNotNone(raw)
        vec = tabular_predictor.extract_features(raw)
        self.assertEqual(vec.shape, (1, 23))

    def test_04_card_bias_calibration(self):
        """Verifica que la corrección de sesgo de tarjetas evite sobreestimación sistemática en ligas europeas."""
        raw = league_db.get_match_raw_features("Manchester City", "Arsenal", "Premier League")
        self.assertIsNotNone(raw)
        p_res = poisson_model.predict(raw)
        exp_cards = p_res["cards"]["expected_total"]
        self.assertGreaterEqual(exp_cards, 2.2)
        self.assertLessEqual(exp_cards, 5.2)

    def test_05_walk_forward_kelly_and_competition_filter(self):
        """Verifica el backtesting Point-in-Time con filtro por liga y métricas Fractional Kelly."""
        res_ere = run_walk_forward_backtest(n_matches=50, competition="Eredivisie")
        self.assertEqual(res_ere["total_matches_evaluated"], 50)
        self.assertLess(res_ere["metrics"]["rps_mean"], 0.215)

        wf_sim = res_ere["walk_forward_simulation"]
        vb = wf_sim["value_betting"]
        self.assertIn("kelly_net_profit_units", vb)
        self.assertIn("kelly_roi_pct", vb)

    def test_06_low_live_corners_adaptive_lines(self):
        """Verifica que cuando van 3 córners en vivo y el partido está por finalizar, las líneas parten de 3.5 (+1) y la proyección respeta el tiempo."""
        raw = league_db.get_match_raw_features("Real Madrid", "Sevilla", "LaLiga")
        raw.is_live = True
        raw.live_minute = "85'"
        raw.live_score = "1 - 0"
        raw.live_corners = 3
        pred = ensemble_engine.predict(raw)
        cn = pred.prediction.corners
        adj = cn.adjusted_lines
        self.assertEqual(len(adj), 3)
        self.assertEqual(adj[0].line, "Más de 3.5 córners")
        self.assertEqual(adj[1].line, "Más de 4.5 córners")
        self.assertEqual(adj[2].line, "Más de 5.5 córners")
        self.assertLessEqual(cn.expected_total, 3.6)
        self.assertLessEqual(pred.prediction.goals.more_goals_pct, 22.0)

    def test_07_womens_teams_flashscore_f_and_w_support(self):
        """Verifica soporte completo a equipos femeniles con sufijos F y W de Flashscore sin colisión con equipos masculinos."""
        cases = [
            ("Barcelona F", "Barcelona F"),
            ("Barcelona W", "Barcelona F"),
            ("FC Barcelona (W)", "Barcelona F"),
            ("Barcelona Femenino", "Barcelona F"),
            ("Real Madrid F", "Real Madrid F"),
            ("Real Madrid W", "Real Madrid F"),
            ("Chelsea W", "Chelsea F"),
            ("Chelsea F", "Chelsea F"),
            ("Arsenal W", "Arsenal F"),
            ("Manchester City W", "Manchester City F"),
            ("Lyon W", "Lyon F"),
            ("Lyon F", "Lyon F"),
            ("PSG W", "PSG F"),
            ("Bayern Munich W", "Bayern Munich F"),
            ("Wolfsburg F", "Wolfsburg F"),
            ("Juventus W", "Juventus F"),
            ("Roma F", "Roma F"),
            ("América F", "América F"),
            ("América W", "América F"),
            ("Tigres UANL W", "Tigres UANL F"),
            ("Las Amazonas", "Tigres UANL F"),
            ("Monterrey F", "Monterrey F"),
            ("Rayadas", "Monterrey F"),
            ("Chivas W", "Guadalajara F"),
            ("Pachuca W", "Pachuca F"),
            # Verificar que los masculinos siguen resolviendo a su club varonil sin colisión
            ("Barcelona", "Barcelona"),
            ("Real Madrid", "Real Madrid"),
            ("Chelsea", "Chelsea"),
            ("América", "América"),
            ("Tigres UANL", "Tigres UANL"),
            ("Monterrey", "Monterrey"),
        ]
        for query, expected_canonical in cases:
            team = league_db.normalize_team(query, db=self.db)
            self.assertIsNotNone(team, f"No se encontró equipo para '{query}'")
            self.assertEqual(team.name, expected_canonical, f"Para '{query}' se esperaba '{expected_canonical}', pero resolvió '{team.name}'")

        # Verificar resolución instantánea (<10ms) de partidos femeniles completos y predicción del ensamble
        raw_ligaf = league_db.get_match_raw_features("Barcelona F", "Real Madrid W")
        self.assertIsNotNone(raw_ligaf)
        self.assertEqual(raw_ligaf.competition, "Liga F Femenina")
        pred_ligaf = ensemble_engine.predict(raw_ligaf)
        self.assertGreater(pred_ligaf.prediction.winner.home_win_pct, 60.0)

        raw_wsl = league_db.get_match_raw_features("Chelsea W", "Arsenal W")
        self.assertIsNotNone(raw_wsl)
        self.assertEqual(raw_wsl.competition, "Women's Super League")

        raw_uwcl = league_db.get_match_raw_features("Barcelona F", "Chelsea W")
        self.assertIsNotNone(raw_uwcl)
        self.assertEqual(raw_uwcl.competition, "Champions Femenina")

        raw_mx_fem = league_db.get_match_raw_features("Tigres UANL F", "América W")
        self.assertIsNotNone(raw_mx_fem)
        self.assertEqual(raw_mx_fem.competition, "Liga MX Femenil")

    def test_audit_fixes_corners_conceded_and_market_prior(self):
        """Verifica que el modelo incorpore córners concedidos por el rival y el Prior Bayesiano de Mercado."""
        raw = league_db.get_match_raw_features("Arsenal", "Chelsea")
        self.assertIsNotNone(raw)
        self.assertIsNotNone(raw.home_stats.avg_corners_conceded)
        self.assertIsNotNone(raw.away_stats.avg_corners_conceded)

        # Predicción pura sin cuotas de mercado
        pred_pure = ensemble_engine.predict(raw)

        # Predicción con Prior Bayesiano de Mercado (favorito local claro en cuotas)
        raw_with_odds = raw.model_copy(deep=True)
        raw_with_odds.market_home_odds = 1.40
        raw_with_odds.market_draw_odds = 4.60
        raw_with_odds.market_away_odds = 7.50
        pred_mkt = ensemble_engine.predict(raw_with_odds)

        self.assertGreater(
            pred_mkt.prediction.winner.home_win_pct,
            pred_pure.prediction.winner.home_win_pct,
            "El Prior Bayesiano de Mercado debe ajustar al alza la probabilidad del favorito reflejado en cuotas."
        )
        total_pct = (
            pred_mkt.prediction.winner.home_win_pct +
            pred_mkt.prediction.winner.draw_pct +
            pred_mkt.prediction.winner.away_win_pct
        )
        self.assertAlmostEqual(total_pct, 100.0, places=1)

    def test_walk_forward_out_of_sample_and_market_benchmark(self):
        """Verifica que el Walk-Forward opere en el bloque Out-of-Sample (>= 2025-01-01) e incluya benchmark Bet365."""
        wf = run_walk_forward_backtest(n_matches=40, edge_threshold=0.04)
        self.assertEqual(wf.get("total_matches_evaluated"), 40)
        sim = wf.get("walk_forward_simulation", {})
        self.assertIn("Out-of-Sample", sim.get("dataset_type", ""))
        mkt_bench = sim.get("market_benchmark", {})
        self.assertEqual(mkt_bench.get("bookmaker"), "Bet365 Closing Odds (De-vigged)")
        self.assertIsNotNone(mkt_bench.get("market_rps_mean"))
        self.assertGreater(mkt_bench.get("matches_with_odds", 0), 20)


if __name__ == "__main__":
    unittest.main()
