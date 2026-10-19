"""
Test de Validación: Priorización de Partidos En Vivo y Actualización cada 5 Minutos.
"""
import sys
import os
from datetime import datetime

# Añadir raíz al sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from backend.app.schemas.match import MatchRawFeatures, TeamFormStats, HeadToHeadStats, PreviousMatch
from backend.app.models.poisson import poisson_model
from backend.app.models.tabular_ml import tabular_predictor
from backend.app.models.ensemble import ensemble_engine

def test_live_priority_and_poisson_conditioning():
    print("\n--- TEST: PRIORIZACIÓN DE DATOS EN VIVO EN POISSON Y ENSAMBLE ---")

    # Partido En Vivo: Real Madrid ganando 2-0 al minuto 75 vs Barcelona
    live_match = MatchRawFeatures(
        home_team="Real Madrid",
        away_team="FC Barcelona",
        competition="LaLiga",
        is_live=True,
        live_minute="75'",
        live_score="2 - 0",
        home_stats=TeamFormStats(
            team_name="Real Madrid",
            avg_goals_scored=2.1,
            avg_goals_conceded=0.9,
            avg_corners=6.0,
            avg_cards=2.0,
            win_rate_last_5=0.8
        ),
        away_stats=TeamFormStats(
            team_name="FC Barcelona",
            avg_goals_scored=1.9,
            avg_goals_conceded=1.2,
            avg_corners=5.5,
            avg_cards=2.4,
            win_rate_last_5=0.6
        ),
        h2h=HeadToHeadStats(
            total_matches_analyzed=5,
            home_team_wins=2,
            draws=1,
            away_team_wins=2,
            avg_total_goals_h2h=3.0,
            avg_total_corners_h2h=10.0,
            avg_total_cards_h2h=4.5
        ),
        context_notes=["Real Madrid domina la posesión en vivo con 62% y 2 goles de ventaja."]
    )

    # 1. Test Poisson Bivariado con condicionamiento en vivo
    poisson_res = poisson_model.predict(live_match)
    print("Poisson Live 1X2 Probs:", poisson_res["winner_probs"])
    print("Poisson Live Goles esperados:", poisson_res["goals"]["expected_total"])
    print("Poisson Live Marcador más probable:", poisson_res["goals"]["most_likely_score"])
    print("Poisson Live Over 1.5:", poisson_res["goals"]["over_1_5_pct"])

    # Aserciones Poisson en Vivo
    assert poisson_res["winner_probs"]["home_win"] > 80.0, "Real Madrid ganando 2-0 al min 75 debe tener prob > 80%"
    assert poisson_res["goals"]["expected_total"] >= 2.0, "Total esperado de goles debe ser >= 2.0"
    assert poisson_res["goals"]["over_1_5_pct"] == 100.0, "Con 2 goles anotados en vivo, Over 1.5 debe ser 100%"
    # El marcador más probable debe tener al menos 2 goles de local
    most_likely_h = int(poisson_res["goals"]["most_likely_score"].split("-")[0].strip())
    assert most_likely_h >= 2, "El marcador más probable debe mantener los goles ya anotados"

    # 2. Test Ensamble Calibrado con prioridad en vivo
    ensemble_res = ensemble_engine.predict(live_match)
    print("\nEnsamble Live Resultado:", ensemble_res.prediction.winner.model_dump())
    print("Veredicto Ganador Live:", ensemble_res.prediction.winner.human_verdict)
    print("Veredicto Goles Live:", ensemble_res.prediction.goals.human_verdict)
    print("Factores Clave:", ensemble_res.key_factors)

    assert "Favorito claro: Real Madrid" in ensemble_res.prediction.winner.human_verdict
    assert "2 - 0" in str(ensemble_res.key_factors)
    assert ensemble_res.match.is_live is True
    assert ensemble_res.match.live_score == "2 - 0"
    assert ensemble_res.match.live_minute == "75'"
    assert ensemble_res.prediction.winner.home_win_pct + ensemble_res.prediction.winner.draw_pct + ensemble_res.prediction.winner.away_win_pct == 100.0

    print("\n✅ Todas las pruebas de priorización en vivo pasaron exitosamente.")

if __name__ == "__main__":
    test_live_priority_and_poisson_conditioning()
