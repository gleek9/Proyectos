"""
Test de Validación Katakuri v1.8:
Probabilidades Dinámicas en Vivo (Sin más goles vs Más goles) y Conmutador de Modo.
"""
import sys
import os

# Añadir raíz al sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from backend.app.schemas.match import MatchRawFeatures, TeamFormStats, HeadToHeadStats
from backend.app.models.poisson import poisson_model
from backend.app.models.tabular_ml import tabular_predictor
from backend.app.models.lstm_net import lstm_predictor
from backend.app.models.ensemble import ensemble_engine

def test_v18_live_dynamic_probabilities_with_3_goals():
    print("\n--- TEST KATAKURI v1.8: PROBABILIDADES DINÁMICAS EN VIVO CON 3 GOLES (2 - 1) ---")

    # Partido en vivo: 3 goles en total (2 - 1) al minuto 65
    live_match = MatchRawFeatures(
        home_team="Arsenal",
        away_team="Chelsea",
        competition="Premier League",
        is_live=True,
        live_minute="65'",
        live_score="2 - 1",
        home_stats=TeamFormStats(
            team_name="Arsenal",
            avg_goals_scored=2.2,
            avg_goals_conceded=0.8,
            avg_corners=6.2,
            avg_cards=1.9,
            win_rate_last_5=0.75
        ),
        away_stats=TeamFormStats(
            team_name="Chelsea",
            avg_goals_scored=1.7,
            avg_goals_conceded=1.4,
            avg_corners=5.1,
            avg_cards=2.3,
            win_rate_last_5=0.55
        ),
        h2h=HeadToHeadStats(
            total_matches_analyzed=5,
            home_team_wins=3,
            draws=1,
            away_team_wins=1,
            avg_total_goals_h2h=3.2,
            avg_total_corners_h2h=10.2,
            avg_total_cards_h2h=4.0
        ),
        context_notes=["Arsenal lidera 2-1 en un derbi de alta intensidad."]
    )

    # 1. Test Poisson Bivariado
    p_res = poisson_model.predict(live_match)
    print("Poisson Live Goals:", p_res["goals"]["current_goals"], "goles actuales")
    print("Poisson Sin más goles (+0):", p_res["goals"]["no_more_goals_pct"], "%")
    print("Poisson Más goles (+1+):", p_res["goals"]["more_goals_pct"], "%")
    print("Poisson Líneas Dinámicas:", p_res["goals"]["live_lines"])

    assert p_res["goals"]["current_goals"] == 3
    assert p_res["goals"]["no_more_goals_pct"] > 0
    assert p_res["goals"]["more_goals_pct"] > 0
    assert round(p_res["goals"]["no_more_goals_pct"] + p_res["goals"]["more_goals_pct"], 1) == 100.0

    # 2. Test Red Neuronal LSTM
    lstm_res = lstm_predictor.predict(live_match)
    print("\nLSTM Momentum Goals:", lstm_res["momentum_goals"])
    print("LSTM Live No More Goals:", lstm_res["live_no_more_goals_pct"], "%")
    print("LSTM Live More Goals:", lstm_res["live_more_goals_pct"], "%")
    assert lstm_res["live_no_more_goals_pct"] is not None
    assert lstm_res["live_more_goals_pct"] is not None
    assert round(lstm_res["live_no_more_goals_pct"] + lstm_res["live_more_goals_pct"], 1) == 100.0

    # 3. Test Tabular XGBoost
    xgb_res = tabular_predictor.predict(live_match)
    print("\nXGB Live No More Goals:", xgb_res["live_no_more_goals_pct"], "%")
    print("XGB Live More Goals:", xgb_res["live_more_goals_pct"], "%")
    assert xgb_res["live_no_more_goals_pct"] is not None
    assert xgb_res["live_more_goals_pct"] is not None

    # 4. Test Meta-Ensamble Calibrado
    ensemble_res = ensemble_engine.predict(live_match)
    g = ensemble_res.prediction.goals
    c = ensemble_res.prediction.corners

    print("\nEnsamble Goles Esperados:", g.expected_total)
    print("Ensamble Sin más goles (+0):", g.no_more_goals_pct, "%")
    print("Ensamble Más goles (+1+):", g.more_goals_pct, "%")
    print("Veredicto Goles:", g.human_verdict)
    print("Líneas Dinámicas Ensamble:")
    for l in g.live_lines:
        print(f"  • {l.line}: {l.probability}%")

    assert g.is_live is True
    assert g.current_goals == 3
    assert g.no_more_goals_pct is not None
    assert g.more_goals_pct is not None
    assert round(g.no_more_goals_pct + g.more_goals_pct, 1) == 100.0
    assert len(g.live_lines) == 4
    # Monotonía: P(>=1 gol) >= P(>=2 goles) >= P(>=3 goles)
    p_add1 = g.live_lines[1].probability
    p_add2 = g.live_lines[2].probability
    p_add3 = g.live_lines[3].probability
    assert p_add1 >= p_add2 >= p_add3, f"Violación de monotonía: {p_add1} >= {p_add2} >= {p_add3}"

    # Córners en vivo
    assert c.is_live is True
    assert len(c.live_corners_lines) >= 3

    print("\n✅ Test 1 (Partido en vivo con 3 goles) superado exitosamente.")

def test_v18_toggle_to_prematch():
    print("\n--- TEST KATAKURI v1.8: CONMUTACIÓN MANUAL A PRE-PARTIDO (is_live=False) ---")

    # Mismo partido pero con is_live=False (como cuando el usuario hace clic en Katakuri)
    prematch = MatchRawFeatures(
        home_team="Arsenal",
        away_team="Chelsea",
        competition="Premier League",
        is_live=False,
        live_minute=None,
        live_score=None,
        home_stats=TeamFormStats(
            team_name="Arsenal",
            avg_goals_scored=2.2,
            avg_goals_conceded=0.8,
            avg_corners=6.2,
            avg_cards=1.9,
            win_rate_last_5=0.75
        ),
        away_stats=TeamFormStats(
            team_name="Chelsea",
            avg_goals_scored=1.7,
            avg_goals_conceded=1.4,
            avg_corners=5.1,
            avg_cards=2.3,
            win_rate_last_5=0.55
        ),
        h2h=HeadToHeadStats(
            total_matches_analyzed=5,
            home_team_wins=3,
            draws=1,
            away_team_wins=1,
            avg_total_goals_h2h=3.2,
            avg_total_corners_h2h=10.2,
            avg_total_cards_h2h=4.0
        ),
        context_notes=["Análisis pre-partido estándar."]
    )

    ensemble_res = ensemble_engine.predict(prematch)
    g = ensemble_res.prediction.goals

    assert ensemble_res.match.is_live is False
    assert g.is_live is False
    assert g.current_goals is None
    assert g.no_more_goals_pct is None
    assert len(g.live_lines) == 0
    print("Pre-match Goles esperados:", g.expected_total)
    print("Pre-match Over 2.5:", g.over_2_5_pct, "%")
    print("Pre-match Veredicto:", g.human_verdict)

    print("\n✅ Test 2 (Conmutación a pre-partido) superado exitosamente.")

if __name__ == "__main__":
    test_v18_live_dynamic_probabilities_with_3_goals()
    test_v18_toggle_to_prematch()
