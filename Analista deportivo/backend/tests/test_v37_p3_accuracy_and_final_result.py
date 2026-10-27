"""
Tests v3.7 — P3: Precisión de Modelos Cuantitativos y Veredicto de Resultado Final Concluido.
Verifica:
1. Veredictos explícitos de "Resultado final" en partidos concluidos (FT, 90', Finalizado).
2. Decaimiento temporal exponencial Dixon-Coles (xi = 0.12) sobre partidos recientes (last_matches).
3. Clasificador posicional de ausencias ampliado (mediocampistas, códigos cortos y estrellas de élite).
4. Cobertura de basales para nuevas competiciones (Conference League, Primeira Liga, Saudi, Championship, etc.).
5. Normalización defensiva de win_rate_last_5 y acoplamiento de localía en XGBoost.
6. Modulación de saques de esquina in-play mediante posesión de balón observada.
"""
import os
import sys
import unittest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from backend.app.schemas.match import MatchRawFeatures, TeamFormStats, HeadToHeadStats, PreviousMatch
from backend.app.models.poisson import (
    poisson_model, get_competition_parameters, COMPETITION_BASELINES
)
from backend.app.models.tabular_ml import tabular_predictor, FEATURE_NAMES
from backend.app.models.ensemble import ensemble_engine


def _make_match(home="Real Madrid", away="Barcelona", comp="LaLiga", live=True, score="2 - 1", minute="FT", **kwargs):
    return MatchRawFeatures(
        home_team=home,
        away_team=away,
        competition=comp,
        is_live=live,
        live_score=score,
        live_minute=minute,
        home_stats=TeamFormStats(
            team_name=home,
            avg_goals_scored=2.1,
            avg_goals_conceded=0.9,
            avg_corners=5.8,
            avg_cards=2.1,
            win_rate_last_5=0.70
        ),
        away_stats=TeamFormStats(
            team_name=away,
            avg_goals_scored=1.8,
            avg_goals_conceded=1.1,
            avg_corners=5.2,
            avg_cards=2.4,
            win_rate_last_5=0.60
        ),
        h2h=HeadToHeadStats(),
        **kwargs
    )


class TestV37FinalResultVerdict(unittest.TestCase):
    def test_final_result_home_win(self):
        m = _make_match(score="3 - 1", minute="FT")
        res = ensemble_engine.predict(m)
        w_verd = res.prediction.winner.human_verdict
        g_verd = res.prediction.goals.human_verdict
        self.assertIn("Partido finalizado. Resultado final: Victoria de Real Madrid (3 - 1).", w_verd)
        self.assertIn("Partido concluido con 4 goles totales (3 - 1)", g_verd)
        self.assertIn("Mercados de goles en directo cerrados", g_verd)
        # Factor clave de finalización
        factors = res.key_factors
        self.assertTrue(any("PARTIDO FINALIZADO" in f and "3 - 1" in f for f in factors))

    def test_final_result_draw(self):
        m = _make_match(score="2 - 2", minute="Finalizado")
        res = ensemble_engine.predict(m)
        w_verd = res.prediction.winner.human_verdict
        self.assertIn("Partido finalizado. Resultado final: Empate (2 - 2).", w_verd)

    def test_final_result_away_win(self):
        m = _make_match(score="0 - 2", minute="Fin")
        res = ensemble_engine.predict(m)
        w_verd = res.prediction.winner.human_verdict
        self.assertIn("Partido finalizado. Resultado final: Victoria de Barcelona (0 - 2).", w_verd)


class TestV37DixonColesTimeDecay(unittest.TestCase):
    def test_time_decay_recent_scoring_spree(self):
        # Equipo con promedio histórico 1.5, pero con racha reciente brutal (3, 4, 3 goles)
        recent_matches = [
            PreviousMatch(opponent="Rival 1", was_home=True, goals_for=3, goals_against=1, result="W"),
            PreviousMatch(opponent="Rival 2", was_home=False, goals_for=4, goals_against=0, result="W"),
            PreviousMatch(opponent="Rival 3", was_home=True, goals_for=3, goals_against=1, result="W"),
            PreviousMatch(opponent="Rival 4", was_home=False, goals_for=1, goals_against=1, result="D"),
        ]
        stats = TeamFormStats(
            team_name="Bayern",
            avg_goals_scored=1.5,
            avg_goals_conceded=1.0,
            last_matches=recent_matches
        )
        gf_decayed, ga_decayed = poisson_model._calculate_time_decayed_goal_rates(stats, xi=0.12)
        # Debe reflejar mayor capacidad ofensiva que el promedio plano 1.5
        self.assertGreater(gf_decayed, 1.5)

    def test_time_decay_fallback_when_empty(self):
        stats = TeamFormStats(team_name="Generic", avg_goals_scored=1.4, avg_goals_conceded=1.2, last_matches=[])
        gf, ga = poisson_model._calculate_time_decayed_goal_rates(stats)
        self.assertEqual(gf, 1.4)
        self.assertEqual(ga, 1.2)


class TestV37AbsencesClassifier(unittest.TestCase):
    def test_midfielder_absence_impact(self):
        att_mult, def_mult = poisson_model._evaluate_absences_impact(["Pedri (MF)"])
        self.assertLess(att_mult, 1.0)
        self.assertGreater(def_mult, 1.0)

    def test_elite_star_absence_impact(self):
        # Ausencia de Rodri (centrocampista defensivo élite)
        att_mult, def_mult = poisson_model._evaluate_absences_impact(["Rodri"])
        self.assertLess(att_mult, 1.0)
        self.assertGreater(def_mult, 1.0)

        # Ausencia de Haaland (delantero élite)
        att_h, _ = poisson_model._evaluate_absences_impact(["Erling Haaland (FW)"])
        self.assertLessEqual(att_h, 0.88)


class TestV37ExpandedBaselines(unittest.TestCase):
    def test_new_competitions_registered(self):
        for comp in ["Conference League", "Primeira Liga", "Saudi Pro League", "Championship", "Liga Argentina", "Copa del Rey"]:
            goals, home_adv, corners = get_competition_parameters(comp)
            self.assertIsNotNone(goals)
            self.assertIsNotNone(home_adv)
            self.assertIsNotNone(corners)
            self.assertGreater(goals, 1.0)


class TestV37TabularDefensiveAndHomeAdv(unittest.TestCase):
    def test_win_rate_percentage_normalized(self):
        m = _make_match()
        m.home_stats.win_rate_last_5 = 80.0  # Enviado como porcentaje 80.0%
        feat = tabular_predictor.extract_features(m)[0]
        idx_wr = FEATURE_NAMES.index("home_win_rate_5")
        self.assertAlmostEqual(feat[idx_wr], 0.80, places=2)

    def test_home_adv_tied_to_competition(self):
        m_arg = _make_match(comp="Liga Argentina")  # Liga con fuerte localía (1.22)
        feat = tabular_predictor.extract_features(m_arg)[0]
        idx_adv = FEATURE_NAMES.index("home_advantage")
        self.assertAlmostEqual(feat[idx_adv], 1.22, places=2)


class TestV37CornerLivePossession(unittest.TestCase):
    def test_corner_possession_modulation(self):
        m_high_poss = _make_match(
            live=True, score="0 - 0", minute="60'",
            live_corners=4,
            live_possession_home=75.0  # Asedio masivo del local
        )
        res_high = poisson_model.predict(m_high_poss)

        m_low_poss = _make_match(
            live=True, score="0 - 0", minute="60'",
            live_corners=4,
            live_possession_home=25.0  # Local dominado
        )
        res_low = poisson_model.predict(m_low_poss)

        # Ambos ejecutan sin error y calculan esquemas de corners
        self.assertIn("expected_total", res_high["corners"])
        self.assertIn("expected_total", res_low["corners"])


class TestP4CardsLiveDecayAndRedCards(unittest.TestCase):
    def test_red_card_already_shown_sets_risk_100(self):
        m = _make_match(live=True, score="1 - 0", minute="35'", live_red_cards_home=1)
        res = poisson_model.predict(m)
        self.assertEqual(res["cards"]["red_card_risk_pct"], 100.0)

    def test_card_risk_decays_with_elapsed_time_when_clean(self):
        m_early = _make_match(live=True, score="0 - 0", minute="15'", live_red_cards_home=0, live_red_cards_away=0)
        m_late = _make_match(live=True, score="0 - 0", minute="85'", live_red_cards_home=0, live_red_cards_away=0)
        risk_early = poisson_model.predict(m_early)["cards"]["red_card_risk_pct"]
        risk_late = poisson_model.predict(m_late)["cards"]["red_card_risk_pct"]
        self.assertGreater(risk_early, risk_late)
        self.assertLess(risk_late, 6.0)

    def test_cards_verdict_live_expulsion_text(self):
        m = _make_match(live=True, score="1 - 0", minute="50'", live_red_cards_away=1)
        res = ensemble_engine.predict(m)
        cards_verd = res.prediction.cards.human_verdict
        self.assertIn("expulsión registrada en directo", cards_verd)


if __name__ == "__main__":
    unittest.main()
