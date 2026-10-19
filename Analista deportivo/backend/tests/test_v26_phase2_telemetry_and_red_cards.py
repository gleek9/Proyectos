"""
Test de Validación Katakuri v2.6 (Fase 2 de Enriquecimiento de Telemetría In-Play):
1. Modelado de Ventaja Numérica (Tarjetas Rojas en Directo) en Poisson y XGBoost.
2. Modelado de Presión Ofensiva In-Play (Tiros a Puerta en Directo).
3. Inyección y Mapeo en MatchMeta y Factores Clave Human-Readable.
"""
import sys
import os
import unittest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from backend.app.schemas.match import MatchRawFeatures, TeamFormStats, HeadToHeadStats
from backend.app.models.poisson import poisson_model
from backend.app.models.tabular_ml import tabular_predictor
from backend.app.models.ensemble import ensemble_engine

class TestPhase2InPlayTelemetry(unittest.TestCase):

    def test_red_card_impact_on_lambdas(self):
        """Valida que una tarjeta roja en vivo reduzca el ataque y aumente la concesión de goles."""
        # Escenario base: 11 vs 11, minuto 35, 0 - 0
        base_match = MatchRawFeatures(
            home_team="Chelsea",
            away_team="Tottenham",
            is_live=True,
            live_minute="35'",
            live_score="0 - 0",
            live_red_cards_home=0,
            live_red_cards_away=0,
            home_stats=TeamFormStats(team_name="Chelsea", avg_goals_scored=1.8, avg_goals_conceded=1.2),
            away_stats=TeamFormStats(team_name="Tottenham", avg_goals_scored=1.8, avg_goals_conceded=1.2),
            h2h=HeadToHeadStats()
        )
        res_base = poisson_model.predict(base_match)
        lambda_h_base = res_base["lambda_home"]
        mu_a_base = res_base["mu_away"]

        # Escenario con 1 tarjeta roja para el local Chelsea (10 vs 11)
        red_match = MatchRawFeatures(
            home_team="Chelsea",
            away_team="Tottenham",
            is_live=True,
            live_minute="35'",
            live_score="0 - 0",
            live_red_cards_home=1,
            live_red_cards_away=0,
            home_stats=TeamFormStats(team_name="Chelsea", avg_goals_scored=1.8, avg_goals_conceded=1.2),
            away_stats=TeamFormStats(team_name="Tottenham", avg_goals_scored=1.8, avg_goals_conceded=1.2),
            h2h=HeadToHeadStats()
        )
        res_red = poisson_model.predict(red_match)
        lambda_h_red = res_red["lambda_home"]
        mu_a_red = res_red["mu_away"]

        # El ataque del equipo con 10 debe caer (~32%)
        self.assertLess(lambda_h_red, lambda_h_base, "El ataque del equipo con 10 hombres debe reducirse")
        # El ataque del rival debe subir (~38%) por los espacios
        self.assertGreater(mu_a_red, mu_a_base, "El ataque del rival con superioridad numérica debe incrementarse")

        # La probabilidad de victoria visitante debe subir en el ensamble
        ens_base = ensemble_engine.predict(base_match)
        ens_red = ensemble_engine.predict(red_match)
        self.assertGreater(
            ens_red.prediction.winner.away_win_pct,
            ens_base.prediction.winner.away_win_pct,
            "La probabilidad de victoria visitante debe aumentar notablemente con roja del local"
        )

    def test_shots_on_target_pressure_multiplier(self):
        """Valida que una asimetría de tiros a puerta module la expectativa ofensiva restante."""
        # Minuto 50, 0 - 0: Local dominando con 8 tiros a puerta vs 1 del visitante
        dominated_match = MatchRawFeatures(
            home_team="Manchester City",
            away_team="Everton",
            is_live=True,
            live_minute="50'",
            live_score="0 - 0",
            live_shots_on_target_home=8,
            live_shots_on_target_away=1,
            home_stats=TeamFormStats(team_name="Manchester City", avg_goals_scored=2.5, avg_goals_conceded=0.8),
            away_stats=TeamFormStats(team_name="Everton", avg_goals_scored=1.0, avg_goals_conceded=1.8),
            h2h=HeadToHeadStats()
        )
        res_press = poisson_model.predict(dominated_match)

        # Mismo partido sin telemetría de tiros
        neutral_match = MatchRawFeatures(
            home_team="Manchester City",
            away_team="Everton",
            is_live=True,
            live_minute="50'",
            live_score="0 - 0",
            home_stats=TeamFormStats(team_name="Manchester City", avg_goals_scored=2.5, avg_goals_conceded=0.8),
            away_stats=TeamFormStats(team_name="Everton", avg_goals_scored=1.0, avg_goals_conceded=1.8),
            h2h=HeadToHeadStats()
        )
        res_neut = poisson_model.predict(neutral_match)

        # El asedio de 8 tiros a puerta debe impulsar la expectativa de gol restante del City
        self.assertGreater(res_press["lambda_home"], res_neut["lambda_home"])
        self.assertLess(res_press["mu_away"], res_neut["mu_away"])

    def test_key_factors_reflect_red_cards_and_telemetry(self):
        """Valida que los factores clave en lenguaje humano incluyan las incidencias in-play."""
        match_info = MatchRawFeatures(
            home_team="Atletico Madrid",
            away_team="Valencia",
            is_live=True,
            live_minute="60'",
            live_score="1 - 0",
            live_red_cards_home=0,
            live_red_cards_away=1,
            live_shots_on_target_home=6,
            live_shots_on_target_away=1,
            home_stats=TeamFormStats(team_name="Atletico Madrid", avg_goals_scored=1.8, avg_goals_conceded=0.7),
            away_stats=TeamFormStats(team_name="Valencia", avg_goals_scored=1.0, avg_goals_conceded=1.6),
            h2h=HeadToHeadStats()
        )

        res = ensemble_engine.predict(match_info)
        factors = res.key_factors

        # Debe alertar sobre la expulsión del Valencia
        has_red_alert = any("INFERIORIDAD NUMÉRICA" in f and "Valencia" in f for f in factors)
        self.assertTrue(has_red_alert, f"Debe reportar alerta de tarjeta roja. Factores: {factors}")

        # Debe reportar telemetría de tiros a puerta
        has_shots_telemetry = any("TELEMETRÍA EN DIRECTO" in f for f in factors)
        self.assertTrue(has_shots_telemetry, f"Debe reportar telemetría de tiros. Factores: {factors}")

        # Comprobar metadatos en MatchMeta
        self.assertEqual(res.match.live_red_cards_away, 1)
        self.assertEqual(res.match.live_shots_on_target_home, 6)

if __name__ == "__main__":
    unittest.main()
