"""
Test de Validación Katakuri v2.7 (Fase 3: Calibración Pre-Match por Liga, Ausencias Posicionales y Mercados Derivados):
1. Calibración de parámetros empíricos por competición (Bundesliga vs Segunda).
2. Ponderación de bajas por posición (ataque vs defensa).
3. Mercados derivados avanzados: Doble Oportunidad (1X, X2, 12) y Draw No Bet (DNB).
"""
import sys
import os
import unittest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from backend.app.schemas.match import MatchRawFeatures, TeamFormStats, HeadToHeadStats
from backend.app.models.poisson import poisson_model, get_competition_parameters, COMPETITION_BASELINES
from backend.app.models.ensemble import ensemble_engine

class TestPhase3CompetitionAndMarkets(unittest.TestCase):

    def test_competition_baselines(self):
        """Valida que los baselines por competición modulen adecuadamente los parámetros de liga."""
        avg_buli, adv_buli = get_competition_parameters("Bundesliga")
        self.assertGreaterEqual(avg_buli, 1.50)
        self.assertGreaterEqual(adv_buli, 1.10)

        avg_seg, adv_seg = get_competition_parameters("LaLiga Hypermotion / Segunda")
        self.assertLessEqual(avg_seg, 1.20)

        # General / desconocido debe retornar (1.35, 1.15)
        avg_gen, adv_gen = get_competition_parameters("Liga Desconocida 99")
        self.assertEqual(avg_gen, 1.35)
        self.assertEqual(adv_gen, 1.15)

        # Con mismas estadísticas, Bundesliga debe proyectar más goles esperados que Segunda
        team_h = TeamFormStats(team_name="Bayern", avg_goals_scored=1.5, avg_goals_conceded=1.2, clean_sheets_pct=0.25, win_rate_last_5=0.5)
        team_a = TeamFormStats(team_name="Dortmund", avg_goals_scored=1.4, avg_goals_conceded=1.3, clean_sheets_pct=0.20, win_rate_last_5=0.4)
        h2h = HeadToHeadStats(total_matches_analyzed=0, home_team_wins=0, away_team_wins=0, draws=0, avg_total_goals_h2h=2.5)

        match_buli = MatchRawFeatures(
            home_team="Bayern", away_team="Dortmund",
            competition="Bundesliga",
            home_stats=team_h, away_stats=team_a, h2h=h2h
        )
        match_seg = MatchRawFeatures(
            home_team="Burgos", away_team="Huesca",
            competition="Segunda Division",
            home_stats=team_h, away_stats=team_a, h2h=h2h
        )

        pred_buli = poisson_model.predict(match_buli)
        pred_seg = poisson_model.predict(match_seg)

        self.assertGreater(
            pred_buli["goals"]["expected_total"],
            pred_seg["goals"]["expected_total"],
            "Bundesliga debe proyectar más goles que Segunda División bajo las mismas estadísticas base"
        )

    def test_absence_positional_impact(self):
        """Valida la ponderación posicional de ausencias (defensivas vs ofensivas)."""
        # Sin bajas
        att_base, def_base = poisson_model._evaluate_absences_impact([])
        self.assertEqual(att_base, 1.0)
        self.assertEqual(def_base, 1.0)

        # Baja de delantero / goleador: reduce ataque, no afecta defensa concedida
        att_off, def_off = poisson_model._evaluate_absences_impact(["Erling Haaland (Delantero centro)"])
        self.assertLess(att_off, 1.0)
        self.assertEqual(def_off, 1.0)

        # Baja de defensa / portero: aumenta goles concedidos proyectados
        att_def, def_def = poisson_model._evaluate_absences_impact(["Thibaut Courtois (Portero)", "Eder Militao (Defensa central)"])
        self.assertEqual(att_def, 1.0)
        self.assertGreater(def_def, 1.0)

    def test_derived_markets_double_chance_and_dnb(self):
        """Valida el cálculo y coherencia matemática de Doble Oportunidad y Draw No Bet (DNB)."""
        team_h = TeamFormStats(team_name="Arsenal", avg_goals_scored=1.7, avg_goals_conceded=1.1, clean_sheets_pct=0.3, win_rate_last_5=0.6)
        team_a = TeamFormStats(team_name="Chelsea", avg_goals_scored=1.3, avg_goals_conceded=1.4, clean_sheets_pct=0.2, win_rate_last_5=0.4)
        h2h = HeadToHeadStats(total_matches_analyzed=4, home_team_wins=2, away_team_wins=1, draws=1, avg_total_goals_h2h=2.5)

        match = MatchRawFeatures(
            home_team="Arsenal",
            away_team="Chelsea",
            competition="Premier League",
            home_stats=team_h,
            away_stats=team_a,
            h2h=h2h
        )

        res = ensemble_engine.predict(match)
        winner = res.prediction.winner

        # Verificar que existan los objetos de mercados derivados
        self.assertIsNotNone(winner.double_chance, "Doble oportunidad debe estar calculada")
        self.assertIsNotNone(winner.draw_no_bet, "Draw No Bet (DNB) debe estar calculado")

        dc = winner.double_chance
        dnb = winner.draw_no_bet

        # Coherencia 1X, X2, 12
        self.assertAlmostEqual(dc.home_or_draw_pct, round(min(99.0, winner.home_win_pct + winner.draw_pct), 1), delta=0.15)
        self.assertAlmostEqual(dc.draw_or_away_pct, round(min(99.0, winner.draw_pct + winner.away_win_pct), 1), delta=0.15)
        self.assertAlmostEqual(dc.home_or_away_pct, round(min(99.0, winner.home_win_pct + winner.away_win_pct), 1), delta=0.15)

        # Coherencia DNB: suman 100.0%
        self.assertEqual(round(dnb.home_dnb_pct + dnb.away_dnb_pct, 1), 100.0)

        # Si el local tiene más probabilidad que el visitante, su DNB debe ser > 50%
        if winner.home_win_pct > winner.away_win_pct:
            self.assertGreater(dnb.home_dnb_pct, 50.0)

        # Veredicto humano debe contener texto legible
        self.assertGreater(len(winner.human_verdict), 10)

if __name__ == "__main__":
    unittest.main()
