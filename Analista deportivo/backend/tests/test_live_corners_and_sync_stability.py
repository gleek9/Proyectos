"""
Test Suite de Verificación para Katakuri:
1. Búsqueda y Extracción por igual de 'tiros de esquina' y 'corners'.
2. Eliminación definitiva del valor por defecto de 5 en tiros de esquina/córners en vivo.
3. Estabilidad y consistencia tras actualizaciones de 5 minutos (continuidad de temporada y monotonía).
"""
import sys
import os

# Añadir raíz al sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from backend.app.schemas.match import MatchRawFeatures, TeamFormStats, HeadToHeadStats, PreviousMatch
from backend.app.models.poisson import poisson_model
from backend.app.models.ensemble import ensemble_engine
from backend.app.agent.parser import parser

def test_no_default_5_corners_when_none():
    """Verifica que si no hay datos de córners en vivo, current_corners sea None y NO 5."""
    features = MatchRawFeatures(
        home_team="Arsenal",
        away_team="Chelsea",
        competition="Premier League",
        is_live=True,
        live_minute="45'",
        live_score="1 - 0",
        live_corners=None,  # No se detectaron córners en directo
        home_stats=TeamFormStats(
            team_name="Arsenal",
            avg_goals_scored=1.8,
            avg_goals_conceded=1.0,
            avg_corners=5.5,
            avg_cards=1.9,
            win_rate_last_5=0.7,
            last_matches=[]
        ),
        away_stats=TeamFormStats(
            team_name="Chelsea",
            avg_goals_scored=1.4,
            avg_goals_conceded=1.2,
            avg_corners=4.5,
            avg_cards=2.2,
            win_rate_last_5=0.5,
            last_matches=[]
        ),
        h2h=HeadToHeadStats(
            total_matches_analyzed=5,
            home_team_wins=2,
            draws=2,
            away_team_wins=1,
            avg_total_goals_h2h=2.8,
            avg_total_corners_h2h=10.0,
            avg_total_cards_h2h=4.1
        )
    )

    p_res = poisson_model.predict(features)
    print("\n--- TEST: CÓRNERS EN VIVO SIN DATOS (live_corners=None) ---")
    print(f"Current corners in Poisson: {p_res['corners']['current_corners']}")
    assert p_res["corners"]["current_corners"] is None, f"Se esperaba None, pero se obtuvo {p_res['corners']['current_corners']}"
    assert p_res["corners"]["current_corners"] != 5, "ERROR CRÍTICO: El modelo sigue asignando 5 por defecto!"

    res = ensemble_engine.predict(features)
    print(f"Current corners in Ensamble: {res.prediction.corners.current_corners}")
    print(f"Human verdict corners: {res.prediction.corners.human_verdict}")
    assert res.prediction.corners.current_corners is None
    assert "5 córners actuales" not in res.prediction.corners.human_verdict
    print("✅ Prueba superada: Ningún valor por defecto de 5 asignado cuando no hay datos.")

def test_exact_live_corners_when_present():
    """Verifica que cuando hay córners reales (ej: 2, 7), se usen con precisión matemática."""
    for corners_val in [2, 7]:
        features = MatchRawFeatures(
            home_team="Real Madrid",
            away_team="Barcelona",
            competition="LaLiga",
            is_live=True,
            live_minute="60'",
            live_score="2 - 1",
            live_corners=corners_val,
            home_stats=TeamFormStats(
                team_name="Real Madrid",
                avg_goals_scored=2.1,
                avg_goals_conceded=0.9,
                avg_corners=6.0,
                avg_cards=2.0,
                win_rate_last_5=0.8,
                last_matches=[]
            ),
            away_stats=TeamFormStats(
                team_name="Barcelona",
                avg_goals_scored=2.0,
                avg_goals_conceded=1.1,
                avg_corners=5.5,
                avg_cards=2.4,
                win_rate_last_5=0.7,
                last_matches=[]
            ),
            h2h=HeadToHeadStats(
                total_matches_analyzed=5,
                home_team_wins=2,
                draws=1,
                away_team_wins=2,
                avg_total_goals_h2h=3.2,
                avg_total_corners_h2h=10.5,
                avg_total_cards_h2h=4.5
            )
        )

        res = ensemble_engine.predict(features)
        assert res.prediction.corners.current_corners == corners_val
        assert f"{corners_val} córners actuales" in res.prediction.corners.human_verdict
        print(f"✅ Prueba superada: Se respetan con exactitud {corners_val} córners en vivo.")

def test_dual_search_heuristic_corners_and_tiros_de_esquina():
    """Verifica que el extractor reconozca indistintamente 'tiros de esquina' y 'corners'."""
    # Caso 1: Con 'tiros de esquina'
    text_tiros = "Minuto 55. El partido está en juego. Marcador Real Madrid 1 - 0 Barcelona. Tiros de esquina: 4 - 2. Faltas cometidas 12."
    features_tiros = parser._fallback_local_heuristic_parse("Real Madrid", "Barcelona", "LaLiga", text_tiros)
    assert features_tiros.is_live is True
    assert features_tiros.live_score == "1 - 0"
    assert features_tiros.live_corners == 6, f"Esperado 6 tiros de esquina, obtenido: {features_tiros.live_corners}"

    # Caso 2: Con 'corners'
    text_corners = "Minuto 70. Partido en curso. Marcador Real Madrid 2 - 1 Barcelona. Corners: 5 - 3. 8 corners en total."
    features_corners = parser._fallback_local_heuristic_parse("Real Madrid", "Barcelona", "LaLiga", text_corners)
    assert features_corners.is_live is True
    assert features_corners.live_score == "2 - 1"
    assert features_corners.live_corners == 8, f"Esperado 8 corners, obtenido: {features_corners.live_corners}"

    # Caso 3: Con 'saques de esquina'
    text_saques = "Minuto 38. Jugándose en directo. Marcador Liverpool 1 - 1 Chelsea. 7 saques de esquina."
    features_saques = parser._fallback_local_heuristic_parse("Liverpool", "Chelsea", "Premier League", text_saques)
    assert features_saques.is_live is True
    assert features_saques.live_corners == 7, f"Esperado 7 saques de esquina, obtenido: {features_saques.live_corners}"

    print("✅ Prueba superada: Extracción bilingüe idéntica para tiros de esquina, corners y saques de esquina.")

def test_stability_after_5_minutes_refresh():
    """Verifica que una actualización tras 5 minutos no cambie bruscamente los datos de fondo ni retroceda goles/córners."""
    prev_features = MatchRawFeatures(
        home_team="Arsenal",
        away_team="Chelsea",
        competition="Premier League",
        is_live=True,
        live_minute="35'",
        live_score="1 - 0",
        live_corners=4,
        home_stats=TeamFormStats(
            team_name="Arsenal",
            avg_goals_scored=1.85,
            avg_goals_conceded=1.05,
            avg_corners=6.2,
            avg_cards=2.0,
            win_rate_last_5=0.6,
            last_matches=[]
        ),
        away_stats=TeamFormStats(
            team_name="Chelsea",
            avg_goals_scored=1.40,
            avg_goals_conceded=1.20,
            avg_corners=4.8,
            avg_cards=2.2,
            win_rate_last_5=0.4,
            last_matches=[]
        ),
        h2h=HeadToHeadStats(
            total_matches_analyzed=5,
            home_team_wins=2,
            draws=2,
            away_team_wins=1,
            avg_total_goals_h2h=2.8,
            avg_total_corners_h2h=10.2,
            avg_total_cards_h2h=4.2
        )
    )

    # Simular una búsqueda 5 minutos después donde DuckDuckGo devuelve un texto breve sin mencionar goles nuevos
    subsequent_text = "Minuto 40'. Partido en directo en el Emirates Stadium. Arsenal y Chelsea disputan un juego intenso en mediocampo."
    updated_features = parser.parse_match(
        home_team="Arsenal",
        away_team="Chelsea",
        competition="Premier League",
        search_context=subsequent_text,
        previous_features=prev_features,
        is_live=True
    )

    # 1. No debe retroceder el marcador (1 - 0 no debe convertirse en 0 - 0)
    assert updated_features.live_score == "1 - 0", f"El marcador retrocedió: {updated_features.live_score}"
    # 2. No deben desaparecer los 4 córners acumulados
    assert updated_features.live_corners >= 4, f"Los córners disminuyeron: {updated_features.live_corners}"
    # 3. No debe invertir los equipos
    assert updated_features.home_team == "Arsenal"
    assert updated_features.away_team == "Chelsea"
    # 4. Las estadísticas base de temporada deben permanecer ancladas y estables
    assert updated_features.home_stats.avg_corners == 6.2
    assert updated_features.away_stats.avg_corners == 4.8
    assert updated_features.home_stats.avg_goals_scored == 1.85

    print("✅ Prueba superada: Estabilidad, continuidad y monotonía garantizadas tras actualización de 5 minutos.")

if __name__ == "__main__":
    test_no_default_5_corners_when_none()
    test_exact_live_corners_when_present()
    test_dual_search_heuristic_corners_and_tiros_de_esquina()
    test_stability_after_5_minutes_refresh()
    print("\n🎉 TODAS LAS PRUEBAS DE EN VIVO Y CÓRNERS PASARON EXITOSAMENTE.")
