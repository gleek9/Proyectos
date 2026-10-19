import unittest
import numpy as np
from backend.app.schemas.match import MatchRawFeatures, TeamFormStats, HeadToHeadStats
from backend.app.models.poisson import poisson_model, nbinom_survival, nbinom_pmf
from backend.app.models.ensemble import ensemble_engine

class TestV33ConsensusNbinomGameState(unittest.TestCase):
    """
    Suite de verificación formal para las mejoras v3.3:
    - Punto 5: Matriz Bivariada de Consenso Coherente en Meta-Ensamble.
    - Punto 6: Distribución Binomial Negativa (Sobredispersión) para córners y tarjetas.
    - Punto 8: Dinámica de Estado de Marcador (Game State Effect) en partidos en vivo.
    """

    def setUp(self):
        self.sample_features = MatchRawFeatures(
            home_team="Arsenal",
            away_team="Chelsea",
            competition="Premier League",
            is_live=False,
            home_stats=TeamFormStats(
                team_name="Arsenal",
                avg_goals_scored=2.1,
                avg_goals_conceded=0.9,
                avg_corners=6.2,
                avg_cards=1.8,
                win_rate_last_5=0.8
            ),
            away_stats=TeamFormStats(
                team_name="Chelsea",
                avg_goals_scored=1.6,
                avg_goals_conceded=1.3,
                avg_corners=5.1,
                avg_cards=2.3,
                win_rate_last_5=0.6
            ),
            h2h=HeadToHeadStats(
                total_matches_analyzed=5,
                home_team_wins=3,
                draws=1,
                away_team_wins=1,
                avg_total_goals_h2h=2.8,
                avg_total_corners_h2h=10.4,
                avg_total_cards_h2h=4.0
            )
        )

    def test_point_5_consensus_matrix_mathematical_coherence(self):
        """
        Verifica que el ensamble aplique la Matriz Bivariada de Consenso:
        - Monotonía estricta: Over 1.5 >= Over 2.5 >= Over 3.5
        - Coherencia entre distribución de goles y Over 2.5
        - Suma de distribución de goles en chart_data igual al 100% (+/- 0.5%)
        """
        res = ensemble_engine.predict(self.sample_features)
        goals = res.prediction.goals

        # 1. Monotonía de líneas Over
        self.assertGreaterEqual(goals.over_1_5_pct, goals.over_2_5_pct, "Over 1.5 debe ser >= Over 2.5")
        self.assertGreaterEqual(goals.over_2_5_pct, goals.over_3_5_pct, "Over 2.5 debe ser >= Over 3.5")

        # 2. Suma de la distribución de goles
        dist = res.chart_data.goals_distribution
        total_p = sum(item.probability for item in dist)
        self.assertAlmostEqual(total_p, 100.0, delta=0.5, msg="La distribución de goles debe sumar ~100%")

        # 3. Coherencia entre Over 2.5 y la distribución acumulada (3, 4, 5+ goles)
        # distribution items: 0 Goles, 1 Gol, 2 Goles, 3 Goles, 4 Goles, 5+ Goles
        prob_3_plus = sum(item.probability for item in dist if item.goals in ["3 Goles", "4 Goles", "5+ Goles"])
        self.assertAlmostEqual(goals.over_2_5_pct, prob_3_plus, delta=0.5,
                               msg=f"Over 2.5 ({goals.over_2_5_pct}%) debe coincidir con suma de 3+ goles ({prob_3_plus}%)")

        # 4. Top marcadores deben ser coherentes con el 1X2 dominante
        self.assertTrue(len(res.chart_data.top_scores) >= 5, "Deben retornar al menos 5 marcadores probables")
        top_score = res.chart_data.top_scores[0]
        self.assertGreater(top_score.probability, 0.0)

    def test_point_6_negative_binomial_corners_and_cards(self):
        """
        Verifica que córners y tarjetas utilicen Binomial Negativa con sobredispersión calibrada:
        - Monotonía de líneas: Over 8.5 >= Over 9.5 >= Over 10.5
        - Tarjetas: Over 3.5 >= Over 4.5
        - Sobredispersión de Binomial Negativa genera colas más realistas que Poisson pura
        """
        res = ensemble_engine.predict(self.sample_features)
        corners = res.prediction.corners
        cards = res.prediction.cards

        # Monotonía de córners
        self.assertGreaterEqual(corners.over_8_5_pct, corners.over_9_5_pct)
        self.assertGreaterEqual(corners.over_9_5_pct, corners.over_10_5_pct)
        self.assertGreater(corners.expected_total, 8.0)
        self.assertLess(corners.expected_total, 12.0)

        # Monotonía de tarjetas
        self.assertGreaterEqual(cards.over_3_5_pct, cards.over_4_5_pct)
        self.assertGreater(cards.expected_total, 2.0)
        self.assertLess(cards.expected_total, 7.0)

        # Verificación directa de funciones de distribución NBinom
        mean_cn = 10.0
        # Con sobredispersión alpha=1.20, la probabilidad de extremos (0 córners o >16 córners) es mayor que Poisson
        nb_zero = nbinom_pmf(0, mean_cn, overdispersion=1.20)
        from scipy.stats import poisson as sc_poisson
        poiss_zero = sc_poisson.pmf(0, mean_cn)
        self.assertGreater(nb_zero, poiss_zero, "NBinom debe reflejar mayor probabilidad de dispersión en colas que Poisson")

    def test_point_8_game_state_dynamics_in_live_match(self):
        """
        Verifica el efecto de Game State (dinámica de urgencia y enfriamiento) en directo:
        - Minuto 65, perdiendo 1-0: el equipo en desventaja aumenta su urgencia ofensiva
        - Minuto 75, goleada 4-0: el ritmo se desacelera por enfriamiento del juego
        """
        # Caso A: Empate 1-1 en minuto 65
        tied_features = MatchRawFeatures(
            home_team="Arsenal",
            away_team="Chelsea",
            competition="Premier League",
            is_live=True,
            match_url="https://www.flashscore.com/match/tied65",
            live_minute="65'",
            live_score="1 - 1",
            home_stats=self.sample_features.home_stats,
            away_stats=self.sample_features.away_stats,
            h2h=self.sample_features.h2h
        )
        res_tied = poisson_model.predict(tied_features)

        # Caso B: Visitante perdiendo 2-1 en minuto 65 (score_diff = +1)
        # El visitante debe mostrar incremento por urgencia ofensiva
        trailing_features = MatchRawFeatures(
            home_team="Arsenal",
            away_team="Chelsea",
            competition="Premier League",
            is_live=True,
            match_url="https://www.flashscore.com/match/trailing65",
            live_minute="65'",
            live_score="2 - 1",
            home_stats=self.sample_features.home_stats,
            away_stats=self.sample_features.away_stats,
            h2h=self.sample_features.h2h
        )
        res_trailing = poisson_model.predict(trailing_features)

        # La expectativa de gol visitante restante (mu_away) debe ser superior cuando va perdiendo por 1 gol
        self.assertGreater(res_trailing["mu_away"], res_tied["mu_away"],
                           "El equipo visitante perdiendo por 1 al 65' debe tener mayor intensidad ofensiva que en empate")

        # Caso C: Goleada 4-0 en minuto 75 (abs(score_diff) >= 3, cooling_factor activo)
        blowout_features = MatchRawFeatures(
            home_team="Arsenal",
            away_team="Chelsea",
            competition="Premier League",
            is_live=True,
            match_url="https://www.flashscore.com/match/blowout75",
            live_minute="75'",
            live_score="4 - 0",
            home_stats=self.sample_features.home_stats,
            away_stats=self.sample_features.away_stats,
            h2h=self.sample_features.h2h
        )
        res_blowout = poisson_model.predict(blowout_features)

        # En empate 0-0 al 75', la expectativa de goles restantes
        tied75_features = MatchRawFeatures(
            home_team="Arsenal",
            away_team="Chelsea",
            competition="Premier League",
            is_live=True,
            match_url="https://www.flashscore.com/match/tied75",
            live_minute="75'",
            live_score="0 - 0",
            home_stats=self.sample_features.home_stats,
            away_stats=self.sample_features.away_stats,
            h2h=self.sample_features.h2h
        )
        res_tied75 = poisson_model.predict(tied75_features)

        rem_goals_blowout = res_blowout["lambda_home"] + res_blowout["mu_away"]
        rem_goals_tied75 = res_tied75["lambda_home"] + res_tied75["mu_away"]
        self.assertLess(rem_goals_blowout, rem_goals_tied75,
                        "Un 4-0 al 75' debe enfriar el ritmo restante de goles respecto a un partido cerrado")

    def test_point_5_live_consensus_distribution_starts_from_current_score(self):
        """
        En un partido en vivo 2-1 (3 goles), la distribución de goles totales debe
        concentrarse exclusivamente en >= 3 goles (probabilidad para 0, 1 y 2 goles debe ser 0%).
        """
        live_features = MatchRawFeatures(
            home_team="Arsenal",
            away_team="Chelsea",
            competition="Premier League",
            is_live=True,
            match_url="https://www.flashscore.com/match/live21",
            live_minute="60'",
            live_score="2 - 1",
            home_stats=self.sample_features.home_stats,
            away_stats=self.sample_features.away_stats,
            h2h=self.sample_features.h2h
        )
        res = ensemble_engine.predict(live_features)
        dist = res.chart_data.goals_distribution

        # Con 3 goles ya anotados:
        # '0 Goles', '1 Gol', '2 Goles' deben tener 0% de probabilidad
        for item in dist:
            if item.goals in ["0 Goles", "1 Gol", "2 Goles"]:
                self.assertEqual(item.probability, 0.0, f"{item.goals} no puede tener probabilidad > 0 cuando ya van 3 goles")

        # Over 1.5 y Over 2.5 deben ser 100%
        self.assertEqual(res.prediction.goals.over_1_5_pct, 100.0)
        self.assertEqual(res.prediction.goals.over_2_5_pct, 100.0)


if __name__ == "__main__":
    unittest.main()
