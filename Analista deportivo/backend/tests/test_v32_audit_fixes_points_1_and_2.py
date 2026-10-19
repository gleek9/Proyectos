"""
Test Suite de Validación Katakuri v3.2:
Verificación de Mejoras y Correcciones de Auditoría (Puntos 1 y 2):
1. Normalización estricta por liga en Poisson y ventaja de localía simétrica (erradicación de sesgo del +15% en ligas goleadoras).
2. Parsing robusto de tiempos de juego (prevención de falso segundo tiempo en '1st half' / '1T' y correcta extracción de minuto).
3. Coalescencia estricta en el ensamble (preservación de probabilidades legítimas de 0.0% en minutos finales sin fallback erróneo).
4. Defaults neutrales de H2H (0 enfrentamientos analizados) sin inyección de datos ficticios.
5. Escalado de volumen en H2H conservando la discriminación ofensiva/defensiva (sin aplanar hacia la paridad).
"""
import sys
import os
import unittest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from backend.app.schemas.match import MatchRawFeatures, TeamFormStats, HeadToHeadStats
from backend.app.models.poisson import (
    poisson_model,
    parse_elapsed_minute,
    COMPETITION_BASELINES,
    get_competition_parameters
)
from backend.app.models.ensemble import ensemble_engine, _coalesce
from backend.app.models.tabular_ml import tabular_predictor


class TestV32AuditFixesPoints1And2(unittest.TestCase):

    def test_minute_parsing_accuracy(self):
        """Verifica que '1st half' y prefijos de periodo no confundan el cálculo del minuto."""
        cases = [
            ("1st half 30", 30),
            ("1T 15'", 15),
            ("1er tiempo 40'", 40),
            ("HT", 45),
            ("Descanso", 45),
            ("Entretiempo", 45),
            ("2T 68'", 68),
            ("2T 23'", 68),       # 45 + 23 = 68
            ("ST 75'", 75),
            ("2nd half 10'", 55), # 45 + 10 = 55
            ("88'", 88),
            ("90+4'", 89),        # Acotado a 89
        ]
        for text, expected in cases:
            actual = parse_elapsed_minute(text)
            self.assertEqual(actual, expected, f"Fallo al parsear '{text}': esperado {expected}, obtenido {actual}")

    def test_league_goal_normalization_unbiased(self):
        """
        Dos equipos con estadísticas exactamente iguales al promedio de su liga deben proyectar
        una suma de goles esperados prácticamente idéntica a la media real del torneo (±2%),
        eliminando el anterior sesgo inflacionario del +15% en ligas como Bundesliga y Eredivisie.
        """
        test_leagues = [
            ("Bundesliga", 1.54, 3.08),
            ("Premier League", 1.41, 2.82),
            ("Eredivisie", 1.52, 3.04),
            ("LaLiga", 1.26, 2.52),
            ("Segunda", 1.12, 2.24)
        ]

        for league_name, team_avg, league_total in test_leagues:
            m = MatchRawFeatures(
                home_team="Equipo Local",
                away_team="Equipo Visita",
                competition=league_name,
                home_stats=TeamFormStats(team_name="Equipo Local", avg_goals_scored=team_avg, avg_goals_conceded=team_avg),
                away_stats=TeamFormStats(team_name="Equipo Visita", avg_goals_scored=team_avg, avg_goals_conceded=team_avg),
                h2h=HeadToHeadStats(total_matches_analyzed=0)
            )
            lh, mu = poisson_model._calculate_lambdas(m)
            total_proj = lh + mu
            pct_diff = abs(total_proj - league_total) / league_total * 100.0

            self.assertLess(
                pct_diff, 2.5,
                f"En {league_name}, la proyección ({total_proj:.3f}) difiere más del 2.5% de la media real ({league_total})"
            )
            # Localía simétrica: el local debe superar al visitante
            self.assertGreater(lh, mu, f"El local debe mantener ventaja en {league_name}")

    def test_coalesce_preserves_zero_probabilities(self):
        """Verifica que _coalesce mantenga valores 0.0 y solo reemplace None."""
        self.assertEqual(_coalesce(0.0, 45.0), 0.0)
        self.assertEqual(_coalesce(0, 10), 0)
        self.assertEqual(_coalesce(None, 45.0), 45.0)
        self.assertEqual(_coalesce(12.5, 45.0), 12.5)

    def test_neutral_h2h_defaults(self):
        """Verifica que el schema por defecto tenga 0 partidos analizados y no invente historial."""
        h2h_default = HeadToHeadStats()
        self.assertEqual(h2h_default.total_matches_analyzed, 0)
        self.assertEqual(h2h_default.home_team_wins, 0)
        self.assertEqual(h2h_default.draws, 0)
        self.assertEqual(h2h_default.away_team_wins, 0)

        # Inferencia con H2H neutro debe funcionar fluidamente en tabular y poisson
        m = MatchRawFeatures(
            home_team="Real Madrid",
            away_team="Sevilla",
            competition="LaLiga",
            home_stats=TeamFormStats(team_name="Real Madrid", avg_goals_scored=2.1, avg_goals_conceded=0.9),
            away_stats=TeamFormStats(team_name="Sevilla", avg_goals_scored=1.2, avg_goals_conceded=1.4),
            h2h=h2h_default
        )
        res = ensemble_engine.predict(m)
        self.assertIsNotNone(res.prediction.winner.home_win_pct)
        self.assertGreater(res.prediction.winner.home_win_pct, 50.0)

    def test_h2h_scaling_preserves_discrimination(self):
        """
        El H2H debe escalar el volumen total sin comprimir la ventaja de un favorito claro hacia la paridad.
        """
        # Favorito claro con H2H de 5 partidos de alto volumen de goles
        m_with_h2h = MatchRawFeatures(
            home_team="Bayern Munich",
            away_team="Bochum",
            competition="Bundesliga",
            home_stats=TeamFormStats(team_name="Bayern Munich", avg_goals_scored=2.8, avg_goals_conceded=0.9),
            away_stats=TeamFormStats(team_name="Bochum", avg_goals_scored=1.0, avg_goals_conceded=2.1),
            h2h=HeadToHeadStats(total_matches_analyzed=5, home_team_wins=4, draws=1, away_team_wins=0, avg_total_goals_h2h=4.2)
        )
        m_no_h2h = MatchRawFeatures(
            home_team="Bayern Munich",
            away_team="Bochum",
            competition="Bundesliga",
            home_stats=TeamFormStats(team_name="Bayern Munich", avg_goals_scored=2.8, avg_goals_conceded=0.9),
            away_stats=TeamFormStats(team_name="Bochum", avg_goals_scored=1.0, avg_goals_conceded=2.1),
            h2h=HeadToHeadStats(total_matches_analyzed=0)
        )
        lh_no, mu_no = poisson_model._calculate_lambdas(m_no_h2h)
        ratio_no = lh_no / max(0.1, mu_no)

        lh_h2h, mu_h2h = poisson_model._calculate_lambdas(m_with_h2h)
        ratio_h2h = lh_h2h / max(0.1, mu_h2h)

        # La proporción de superioridad del favorito se conserva intacta (no se comprime a la paridad)
        self.assertAlmostEqual(ratio_h2h, ratio_no, places=4, msg="El escalado de H2H debe conservar intacta la discriminación táctica")
        self.assertGreater(ratio_h2h, 2.0, f"La ratio lambda_h/mu_a ({ratio_h2h:.2f}) debe reflejar superioridad del favorito")


if __name__ == "__main__":
    unittest.main()
