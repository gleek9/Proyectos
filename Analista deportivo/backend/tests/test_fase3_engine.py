"""
Test suite de validación integral para la Fase 3: Motor Predictivo Local.
Prueba Poisson Dixon-Coles, XGBoost Tabular, PyTorch LSTM y el Meta-Ensamble Calibrado.
"""
import sys
import os

# Asegurar path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from backend.app.schemas.match import (
    MatchRawFeatures, TeamFormStats, HeadToHeadStats, PreviousMatch
)
from backend.app.models.poisson import poisson_model
from backend.app.models.tabular_ml import tabular_predictor
from backend.app.models.lstm_net import lstm_predictor
from backend.app.models.ensemble import ensemble_engine

def build_mock_real_match() -> MatchRawFeatures:
    """Crea datos realistas de un partido clásico (Real Madrid vs Barcelona) para evaluar inferencia."""
    return MatchRawFeatures(
        home_team="Real Madrid",
        away_team="FC Barcelona",
        competition="LaLiga",
        home_stats=TeamFormStats(
            team_name="Real Madrid",
            last_matches=[
                PreviousMatch(opponent="Espanyol", was_home=True, goals_for=4, goals_against=1, corners_for=7, cards_total=2, result="W"),
                PreviousMatch(opponent="Stuttgart", was_home=True, goals_for=3, goals_against=1, corners_for=6, cards_total=3, result="W"),
                PreviousMatch(opponent="Real Sociedad", was_home=False, goals_for=2, goals_against=0, corners_for=5, cards_total=4, result="W"),
                PreviousMatch(opponent="Real Betis", was_home=True, goals_for=2, goals_against=0, corners_for=8, cards_total=1, result="W"),
                PreviousMatch(opponent="Las Palmas", was_home=False, goals_for=1, goals_against=1, corners_for=6, cards_total=2, result="D"),
            ],
            avg_goals_scored=2.4,
            avg_goals_conceded=0.8,
            avg_corners=6.4,
            avg_cards=2.1,
            win_rate_last_5=0.8,
            key_absences=["David Alaba"]
        ),
        away_stats=TeamFormStats(
            team_name="FC Barcelona",
            last_matches=[
                PreviousMatch(opponent="Villarreal", was_home=False, goals_for=5, goals_against=1, corners_for=8, cards_total=3, result="W"),
                PreviousMatch(opponent="Monaco", was_home=False, goals_for=1, goals_against=2, corners_for=4, cards_total=4, result="L"),
                PreviousMatch(opponent="Girona", was_home=False, goals_for=4, goals_against=1, corners_for=7, cards_total=3, result="W"),
                PreviousMatch(opponent="Valladolid", was_home=True, goals_for=7, goals_against=0, corners_for=9, cards_total=1, result="W"),
                PreviousMatch(opponent="Rayo Vallecano", was_home=False, goals_for=2, goals_against=1, corners_for=5, cards_total=3, result="W"),
            ],
            avg_goals_scored=2.8,
            avg_goals_conceded=1.1,
            avg_corners=6.6,
            avg_cards=2.4,
            win_rate_last_5=0.8,
            key_absences=["Gavi", "Marc-André ter Stegen"]
        ),
        h2h=HeadToHeadStats(
            total_matches_analyzed=5,
            home_team_wins=3,
            draws=0,
            away_team_wins=2,
            avg_total_goals_h2h=3.4,
            avg_total_corners_h2h=10.2,
            avg_total_cards_h2h=4.8
        ),
        context_notes=[
            "El Clásico en el Santiago Bernabéu con ambos equipos en la parte alta de la tabla.",
            "Barcelona llega con promedio ofensivo superior a 2.5 goles por partido fuera de casa."
        ]
    )

def test_poisson_dixon_coles():
    print("--- TEST 1: POISSON DIXON-COLES BIVARIADO ---")
    raw = build_mock_real_match()
    res = poisson_model.predict(raw)

    assert "winner_probs" in res
    assert "goals" in res
    assert "corners" in res
    assert "cards" in res

    probs = res["winner_probs"]
    total_p = probs["home_win"] + probs["draw"] + probs["away_win"]
    print(f"Poisson Lambdas: Local={res['lambda_home']}, Visitante={res['mu_away']}")
    print(f"Probabilidades 1X2 Poisson: {probs} (Suma: {total_p:.1f}%)")
    print(f"Goles esperados: {res['goals']['expected_total']}, Marcador más probable: {res['goals']['most_likely_score']}")
    print(f"Córners esperados: {res['corners']['expected_total']}, Tarjetas esperadas: {res['cards']['expected_total']}")

    assert 98.0 <= total_p <= 102.0
    assert res["goals"]["expected_total"] > 1.5
    print("✅ Poisson Dixon-Coles funcionando correctamente.\n")

def test_tabular_xgboost():
    print("--- TEST 2: MACHINE LEARNING TABULAR (XGBOOST) ---")
    raw = build_mock_real_match()
    res = tabular_predictor.predict(raw)

    assert "winner_probs" in res
    assert "goals_expected" in res
    probs = res["winner_probs"]
    total_p = probs["home_win"] + probs["draw"] + probs["away_win"]
    print(f"Probabilidades 1X2 XGBoost: {probs} (Suma: {total_p:.1f}%)")
    print(f"Expectativa de goles tabulares: {res['goals_expected']}, Over 2.5: {res['over_2_5_pct']}%")

    assert 99.0 <= total_p <= 101.0
    assert os.path.exists("backend/weights/xgb_1x2.json")
    print("✅ XGBoost Tabular funcionando y pesos guardados en disco.\n")

def test_lstm_recurrent_net():
    print("--- TEST 3: RED NEURONAL RECURRENTE (PYTORCH LSTM) ---")
    raw = build_mock_real_match()
    res = lstm_predictor.predict(raw)

    assert "winner_probs" in res
    assert "momentum_goals" in res
    probs = res["winner_probs"]
    total_p = probs["home_win"] + probs["draw"] + probs["away_win"]
    print(f"Probabilidades 1X2 LSTM: {probs} (Suma: {total_p:.1f}%)")
    print(f"Momentum ofensivo estimado: {res['momentum_goals']}")

    assert 99.0 <= total_p <= 101.0
    assert os.path.exists("backend/weights/lstm_momentum.pt")
    print("✅ PyTorch LSTM secuencial ejecutando inferencia y pesos guardados.\n")

def test_meta_ensemble_and_human_translator():
    print("--- TEST 4: META-ENSAMBLE CALIBRADO Y TRADUCTOR HUMANO ---")
    raw = build_mock_real_match()
    final_output = ensemble_engine.predict(raw)

    pred = final_output.prediction
    w = pred.winner
    g = pred.goals
    c = pred.corners
    k = pred.cards

    sum_1x2 = round(w.home_win_pct + w.draw_pct + w.away_win_pct, 1)
    print(f"Resultado Ensamble 1X2: Local {w.home_win_pct}% | Empate {w.draw_pct}% | Visitante {w.away_win_pct}%")
    print(f"SUMA EXACTA 1X2: {sum_1x2}%")
    print(f"Veredicto Ganador: '{w.human_verdict}'")

    print(f"\nGoles esperados: {g.expected_total} | Más probable: '{g.most_likely_score}'")
    print(f"Over 1.5: {g.over_1_5_pct}% | Over 2.5: {g.over_2_5_pct}% | Over 3.5: {g.over_3_5_pct}% | Ambos Anotan: {g.both_teams_to_score_pct}%")
    print(f"Veredicto Goles: '{g.human_verdict}'")

    print(f"\nCórners esperados: {c.expected_total} | Over 8.5: {c.over_8_5_pct}% | Over 9.5: {c.over_9_5_pct}%")
    print(f"Veredicto Córners: '{c.human_verdict}'")

    print(f"\nTarjetas esperadas: {k.expected_total} | Riesgo Roja: {k.red_card_risk_pct}%")
    print(f"Veredicto Tarjetas: '{k.human_verdict}'")

    print("\nGráficas de Distribución generadas:")
    for dist in final_output.chart_data.goals_distribution:
        print(f"  - {dist.goals}: {dist.probability}%")

    print("\nTop Marcadores:")
    for score in final_output.chart_data.top_scores:
        print(f"  - {score.score}: {score.probability}%")

    print("\nFactores Clave Human-Readable:")
    for idx, factor in enumerate(final_output.key_factors, 1):
        print(f"  {idx}. {factor}")

    # Validaciones críticas de negocio
    assert sum_1x2 == 100.0, f"La suma de probabilidades 1X2 debe ser exactamente 100.0%, dio {sum_1x2}%"
    assert g.over_1_5_pct >= g.over_2_5_pct, "Over 1.5 debe ser >= Over 2.5"
    assert g.over_2_5_pct >= g.over_3_5_pct, "Over 2.5 debe ser >= Over 3.5"
    assert len(final_output.chart_data.goals_distribution) >= 5
    assert len(final_output.chart_data.top_scores) >= 5
    assert len(final_output.key_factors) >= 2
    assert len(w.human_verdict) > 5

    print("\n🏆 TODAS LAS VALIDACIONES DE LA FASE 3 PASARON SATISFACTORIAMENTE!")

if __name__ == "__main__":
    test_poisson_dixon_coles()
    test_tabular_xgboost()
    test_lstm_recurrent_net()
    test_meta_ensemble_and_human_translator()
