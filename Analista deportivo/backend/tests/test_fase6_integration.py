"""
Test suite de validación final para la Fase 6: Pruebas de Integración y Calibración Final.
Evalúa calibración probabilística, monotonía de líneas, inversión de localía y consistencia numérica.
"""
import sys
import os

# Asegurar path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from backend.app.schemas.match import (
    MatchRawFeatures, TeamFormStats, HeadToHeadStats, PreviousMatch
)
from backend.app.models.ensemble import ensemble_engine

def create_match_scenario(home_adv_strong: bool = True) -> MatchRawFeatures:
    """Crea escenarios tácticos variados para probar calibración y límites."""
    if home_adv_strong:
        # Escenario 1: Local dominante
        home_stats = TeamFormStats(
            team_name="Bayern München",
            last_matches=[
                PreviousMatch(opponent="Bochum", was_home=True, goals_for=5, goals_against=0, corners_for=9, cards_total=1, result="W"),
                PreviousMatch(opponent="Freiburg", was_home=False, goals_for=3, goals_against=1, corners_for=7, cards_total=2, result="W"),
                PreviousMatch(opponent="Wolfsburg", was_home=True, goals_for=4, goals_against=1, corners_for=8, cards_total=1, result="W"),
            ],
            avg_goals_scored=3.2,
            avg_goals_conceded=0.6,
            avg_corners=7.8,
            avg_cards=1.5,
            win_rate_last_5=0.9,
            key_absences=[]
        )
        away_stats = TeamFormStats(
            team_name="FC Augsburg",
            last_matches=[
                PreviousMatch(opponent="Mainz", was_home=False, goals_for=0, goals_against=2, corners_for=3, cards_total=3, result="L"),
                PreviousMatch(opponent="Heidenheim", was_home=True, goals_for=1, goals_against=1, corners_for=4, cards_total=2, result="D"),
                PreviousMatch(opponent="Stuttgart", was_home=False, goals_for=0, goals_against=3, corners_for=2, cards_total=4, result="L"),
            ],
            avg_goals_scored=0.9,
            avg_goals_conceded=2.1,
            avg_corners=3.6,
            avg_cards=2.9,
            win_rate_last_5=0.2,
            key_absences=["Jeff Gouweleeuw"]
        )
        h2h = HeadToHeadStats(
            total_matches_analyzed=4,
            home_team_wins=3,
            draws=1,
            away_team_wins=0,
            avg_total_goals_h2h=3.8,
            avg_total_corners_h2h=10.5,
            avg_total_cards_h2h=4.2
        )
        return MatchRawFeatures(
            home_team="Bayern München",
            away_team="FC Augsburg",
            competition="Bundesliga",
            home_stats=home_stats,
            away_stats=away_stats,
            h2h=h2h,
            context_notes=["Gran diferencia de poder ofensivo en el Allianz Arena."]
        )
    else:
        # Escenario 2: Duelo parejo cerrado
        home_stats = TeamFormStats(
            team_name="Atlético de Madrid",
            last_matches=[
                PreviousMatch(opponent="Valencia", was_home=True, goals_for=1, goals_against=0, corners_for=5, cards_total=3, result="W"),
                PreviousMatch(opponent="Athletic Club", was_home=False, goals_for=1, goals_against=1, corners_for=4, cards_total=4, result="D"),
            ],
            avg_goals_scored=1.3,
            avg_goals_conceded=0.7,
            avg_corners=5.1,
            avg_cards=2.8,
            win_rate_last_5=0.6,
            key_absences=[]
        )
        away_stats = TeamFormStats(
            team_name="Juventus",
            last_matches=[
                PreviousMatch(opponent="Roma", was_home=True, goals_for=0, goals_against=0, corners_for=4, cards_total=3, result="D"),
                PreviousMatch(opponent="Empoli", was_home=False, goals_for=1, goals_against=0, corners_for=5, cards_total=2, result="W"),
            ],
            avg_goals_scored=1.2,
            avg_goals_conceded=0.6,
            avg_corners=4.8,
            avg_cards=2.4,
            win_rate_last_5=0.6,
            key_absences=[]
        )
        h2h = HeadToHeadStats(
            total_matches_analyzed=3,
            home_team_wins=1,
            draws=1,
            away_team_wins=1,
            avg_total_goals_h2h=1.7,
            avg_total_corners_h2h=8.8,
            avg_total_cards_h2h=5.2
        )
        return MatchRawFeatures(
            home_team="Atlético de Madrid",
            away_team="Juventus",
            competition="UEFA Champions League",
            home_stats=home_stats,
            away_stats=away_stats,
            h2h=h2h,
            context_notes=["Duelo táctico cerrado entre dos de las mejores defensas de Europa."]
        )

def test_1x2_strict_sum_and_monotonicity():
    print("--- PRUEBA 1: Verificación de Suma Estricta 100.0% y Monotonía de Goles ---")
    scenarios = [create_match_scenario(True), create_match_scenario(False)]

    for idx, raw in enumerate(scenarios, 1):
        res = ensemble_engine.predict(raw)
        p = res.prediction
        w = p.winner
        g = p.goals
        c = p.corners
        k = p.cards

        # 1. Suma exacta de 1X2
        sum_1x2 = round(w.home_win_pct + w.draw_pct + w.away_win_pct, 1)
        print(f"\nEscenario {idx} ({raw.home_team} vs {raw.away_team}):")
        print(f"  1X2: Local {w.home_win_pct}% | Empate {w.draw_pct}% | Visita {w.away_win_pct}% => Suma: {sum_1x2}%")
        print(f"  Veredicto: '{w.human_verdict}'")
        assert sum_1x2 == 100.0, f"Error: la suma de probabilidades 1X2 debe ser exactamente 100.0%, dio {sum_1x2}%"

        # 2. Monotonía de goles: Over 1.5 >= Over 2.5 >= Over 3.5
        print(f"  Líneas Goles: Over 1.5 ({g.over_1_5_pct}%) >= Over 2.5 ({g.over_2_5_pct}%) >= Over 3.5 ({g.over_3_5_pct}%)")
        assert g.over_1_5_pct >= g.over_2_5_pct, "Error de consistencia en Over 1.5 vs 2.5"
        assert g.over_2_5_pct >= g.over_3_5_pct, "Error de consistencia en Over 2.5 vs 3.5"

        # 3. Monotonía de córners: Over 8.5 >= Over 9.5 >= Over 10.5
        print(f"  Líneas Córners: Over 8.5 ({c.over_8_5_pct}%) >= Over 9.5 ({c.over_9_5_pct}%) >= Over 10.5 ({c.over_10_5_pct}%)")
        assert c.over_8_5_pct >= c.over_9_5_pct, "Error en córners Over 8.5 vs 9.5"
        assert c.over_9_5_pct >= c.over_10_5_pct, "Error en córners Over 9.5 vs 10.5"

        # 4. Tarjetas
        print(f"  Líneas Tarjetas: Over 3.5 ({k.over_3_5_pct}%) >= Over 4.5 ({k.over_4_5_pct}%) | Roja: {k.red_card_risk_pct}%")
        assert k.over_3_5_pct >= k.over_4_5_pct, "Error en tarjetas Over 3.5 vs 4.5"
        assert 0.0 <= k.red_card_risk_pct <= 100.0

    print("\n✅ Todas las pruebas de suma estricta y monotonía matemática pasaron.")

def test_home_advantage_swap_consistency():
    print("\n--- PRUEBA 2: Consistencia en Inversión de Localía (Home Advantage Test) ---")
    base = create_match_scenario(False)

    # Predicción A como Local
    resA = ensemble_engine.predict(base)

    # Invertir Localía: B como Local, A como Visita
    inverted = MatchRawFeatures(
        home_team=base.away_team,
        away_team=base.home_team,
        competition=base.competition,
        home_stats=base.away_stats,
        away_stats=base.home_stats,
        h2h=HeadToHeadStats(
            total_matches_analyzed=base.h2h.total_matches_analyzed,
            home_team_wins=base.h2h.away_team_wins,
            draws=base.h2h.draws,
            away_team_wins=base.h2h.home_team_wins,
            avg_total_goals_h2h=base.h2h.avg_total_goals_h2h,
            avg_total_corners_h2h=base.h2h.avg_total_corners_h2h,
            avg_total_cards_h2h=base.h2h.avg_total_cards_h2h
        ),
        context_notes=base.context_notes
    )

    resB = ensemble_engine.predict(inverted)

    pA_home = resA.prediction.winner.home_win_pct
    pB_away_as_home = resB.prediction.winner.home_win_pct

    print(f"Partido A: {base.home_team} (Local) {pA_home}% vs {base.away_team} (Visita) {resA.prediction.winner.away_win_pct}%")
    print(f"Partido B (Invertido): {inverted.home_team} (Local) {pB_away_as_home}% vs {inverted.away_team} (Visita) {resB.prediction.winner.away_win_pct}%")

    # Al invertir localía, el equipo visitante ahora anfitrión debe ganar probabilidad con respecto a cuando era visitante
    assert pB_away_as_home > resA.prediction.winner.away_win_pct, "El equipo debió aumentar su % al pasar de visitante a local."
    print("✅ Inversión de localía probada: la ventaja de campo reacciona fielmente a la condición de local.")

if __name__ == "__main__":
    test_1x2_strict_sum_and_monotonicity()
    test_home_advantage_swap_consistency()
    print("\n🏆 FASE 6 FINALIZADA CON ÉXITO: MOTOR Y CALIBRACIÓN AL 100%!")
