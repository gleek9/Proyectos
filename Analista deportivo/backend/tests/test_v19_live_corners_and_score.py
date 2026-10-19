"""
Test suite de validación para Katakuri v1.9:
- Conteo y condicionamiento de córners en tiempo real.
- Actualización de marcador en vivo sin sobrescritura involuntaria.
"""

import sys
import os

# Añadir raíz al sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from backend.app.schemas.match import MatchRawFeatures, TeamFormStats, HeadToHeadStats
from backend.app.models.poisson import poisson_model
from backend.app.models.ensemble import ensemble_engine

def test_live_corners_conditioning():
    raw_live = MatchRawFeatures(
        home_team="Arsenal",
        away_team="Chelsea",
        competition="Premier League",
        is_live=True,
        live_minute="75'",
        live_score="2 - 1",
        live_corners=8,  # 8 córners ya ocurridos
        home_stats=TeamFormStats(
            team_name="Arsenal",
            avg_goals_scored=2.0,
            avg_goals_conceded=1.0,
            avg_corners=6.0,
            avg_cards=1.5
        ),
        away_stats=TeamFormStats(
            team_name="Chelsea",
            avg_goals_scored=1.5,
            avg_goals_conceded=1.2,
            avg_corners=5.0,
            avg_cards=2.0
        ),
        h2h=HeadToHeadStats(
            total_matches_analyzed=5,
            avg_total_goals_h2h=2.8,
            avg_total_corners_h2h=11.0,
            avg_total_cards_h2h=4.0
        )
    )

    p_res = poisson_model.predict(raw_live)
    corners_data = p_res["corners"]

    print("\n--- TEST KATAKURI v1.9: CÓRNERS EN VIVO CONDICIONADOS ---")
    print(f"Córners actuales: {corners_data['current_corners']}")
    print(f"Córners esperados restantes: {corners_data['expected_remaining_corners']}")
    print(f"Total esperado final: {corners_data['expected_total']}")
    print(f"Over 8.5 Córners: {corners_data['over_8_5_pct']}%")
    print(f"Over 9.5 Córners: {corners_data['over_9_5_pct']}%")
    print(f"Over 10.5 Córners: {corners_data['over_10_5_pct']}%")

    assert corners_data["current_corners"] == 8
    # Total esperado debe ser mayor a 8 (8 + córners restantes)
    assert corners_data["expected_total"] >= 8.0
    # Over 8.5 necesita solo 1 córner más en 15 min con base de ~11 córners por 90 min
    assert corners_data["over_8_5_pct"] > 50.0
    # Estricta monotonía
    assert corners_data["over_8_5_pct"] >= corners_data["over_9_5_pct"] >= corners_data["over_10_5_pct"]

    # Ensamble
    ensemble_res = ensemble_engine.predict(raw_live)
    c_pred = ensemble_res.prediction.corners
    print(f"Ensamble Córners: {c_pred.expected_total} totales, actuales: {c_pred.current_corners}")
    print(f"Veredicto Córners: {c_pred.human_verdict}")
    assert c_pred.current_corners == 8
    assert "8 córners actuales" in c_pred.human_verdict
    print("✅ Prueba de córners en vivo condicionada superada con éxito.")

if __name__ == "__main__":
    test_live_corners_conditioning()
