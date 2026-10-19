"""
Test suite de validación integral para la Fase 4: Endpoint API en FastAPI y Caché SQLite.
"""
import sys
import os
from fastapi.testclient import TestClient

# Asegurar path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from backend.app.main import app
from backend.app.db import SessionLocal, MatchPrediction

client = TestClient(app)

def test_health_endpoint():
    print("--- TEST 1: GET /api/health ---")
    response = client.get("/api/health")
    assert response.status_code == 200, f"Health check falló con status {response.status_code}"
    data = response.json()
    print("Health response:", data)
    assert data["status"] == "online"
    assert "models_local" in data
    print("✅ Endpoint /api/health responde 200 OK.\n")

def test_validation_same_teams():
    print("--- TEST 2: Validación de equipos idénticos ---")
    response = client.post("/api/predict", json={
        "home_team": "Real Madrid",
        "away_team": "Real Madrid",
        "competition": "LaLiga"
    })
    assert response.status_code == 400, "Debería retornar 400 cuando los equipos son idénticos"
    print("Respuesta de error 400:", response.json())
    print("✅ Validación de error 400 superada.\n")

def test_predict_and_cache_flow():
    print("--- TEST 3: POST /api/predict y Sistema de Caché SQLite ---")
    payload = {
        "home_team": "Arsenal",
        "away_team": "Chelsea",
        "competition": "Premier League",
        "force_refresh": False
    }

    # 1. Primera consulta: Puede consultar web o caché existente
    print(f"Enviando solicitud POST /api/predict para {payload['home_team']} vs {payload['away_team']}...")
    res1 = client.post("/api/predict", json=payload)
    assert res1.status_code == 200, f"Error en endpoint /api/predict: {res1.text}"
    data1 = res1.json()

    print("\n--- Respuesta del Motor Predictivo (Katakuri) ---")
    print(f"Partido: {data1['match']['home_team']} vs {data1['match']['away_team']} ({data1['match']['competition']})")
    
    winner = data1['prediction']['winner']
    print(f"1X2: Local {winner['home_win_pct']}% | Empate {winner['draw_pct']}% | Visitante {winner['away_win_pct']}%")
    print(f"Veredicto Ganador: {winner['human_verdict']}")

    goals = data1['prediction']['goals']
    print(f"Goles: Esperados {goals['expected_total']} | Marcador probable: {goals['most_likely_score']} | Over 2.5: {goals['over_2_5_pct']}%")
    print(f"Veredicto Goles: {goals['human_verdict']}")

    corners = data1['prediction']['corners']
    print(f"Córners: Esperados {corners['expected_total']} | Over 9.5: {corners['over_9_5_pct']}% | Veredicto: {corners['human_verdict']}")

    cards = data1['prediction']['cards']
    print(f"Tarjetas: Esperadas {cards['expected_total']} | Riesgo Roja: {cards['red_card_risk_pct']}% | Veredicto: {cards['human_verdict']}")

    # Verificación de suma 100%
    total_1x2 = round(winner['home_win_pct'] + winner['draw_pct'] + winner['away_win_pct'], 1)
    assert total_1x2 == 100.0, f"La suma de 1X2 debe ser 100.0%, dio {total_1x2}"

    # Verificación de persistencia en SQLite
    db = SessionLocal()
    saved = db.query(MatchPrediction).filter(
        MatchPrediction.home_team.ilike("Arsenal"),
        MatchPrediction.away_team.ilike("Chelsea")
    ).first()
    db.close()
    assert saved is not None, "El registro no fue guardado en la base de datos SQLite"
    print("✅ Registro verificado en SQLite analista.db con ID:", saved.id)

    # 2. Segunda consulta: debe ser un Cache HIT instantáneo
    print("\nEnviando segunda consulta para verificar CACHÉ HIT instantáneo...")
    res2 = client.post("/api/predict", json=payload)
    assert res2.status_code == 200
    data2 = res2.json()
    assert data2['prediction']['winner']['home_win_pct'] == winner['home_win_pct'], "La caché debe retornar datos idénticos"
    print("✅ Caché HIT verificado con éxito.\n")

def test_recent_predictions_endpoint():
    print("--- TEST 4: GET /api/predictions/recent ---")
    response = client.get("/api/predictions/recent?limit=5")
    assert response.status_code == 200
    data = response.json()
    print("Recent predictions data:", data)
    assert "predictions" in data
    assert len(data["predictions"]) >= 1
    print("✅ Endpoint /api/predictions/recent verificado con éxito.\n")

if __name__ == "__main__":
    test_health_endpoint()
    test_validation_same_teams()
    test_predict_and_cache_flow()
    test_recent_predictions_endpoint()
    print("🏆 TODOS LOS TESTS DE LA FASE 4 PASARON EXITOSAMENTE!")
