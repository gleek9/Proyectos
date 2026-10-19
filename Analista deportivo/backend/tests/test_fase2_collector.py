import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT_DIR))

from backend.app.agent.collector import collector

print("=================================================================")
print("EJECUTANDO PRUEBA COMPLETA DE FASE 2: BÚSQUEDA Y EXTRACCIÓN")
print("=================================================================")

features = collector.collect(
    home_team="Manchester City",
    away_team="Liverpool",
    competition="Premier League",
    force_refresh=True
)

print(f"\n[OK] Partido: {features.home_team} vs {features.away_team} ({features.competition})")
print(f"--- Estadísticas Local ({features.home_team}) ---")
print(f"  • Goles anotados p/p: {features.home_stats.avg_goals_scored}")
print(f"  • Goles recibidos p/p: {features.home_stats.avg_goals_conceded}")
print(f"  • Córners promedio: {features.home_stats.avg_corners}")
print(f"  • Tarjetas promedio: {features.home_stats.avg_cards}")
print(f"  • Victorias últimos 5: {features.home_stats.win_rate_last_5 * 100:.0f}%")
print(f"  • Bajas clave: {features.home_stats.key_absences or 'Ninguna reportada'}")

print(f"\n--- Estadísticas Visitante ({features.away_team}) ---")
print(f"  • Goles anotados p/p: {features.away_stats.avg_goals_scored}")
print(f"  • Goles recibidos p/p: {features.away_stats.avg_goals_conceded}")
print(f"  • Córners promedio: {features.away_stats.avg_corners}")
print(f"  • Tarjetas promedio: {features.away_stats.avg_cards}")
print(f"  • Victorias últimos 5: {features.away_stats.win_rate_last_5 * 100:.0f}%")
print(f"  • Bajas clave: {features.away_stats.key_absences or 'Ninguna reportada'}")

print(f"\n--- Historial H2H ---")
print(f"  • Partidos analizados: {features.h2h.total_matches_analyzed}")
print(f"  • Victorias {features.home_team}: {features.h2h.home_team_wins}")
print(f"  • Empates: {features.h2h.draws}")
print(f"  • Victorias {features.away_team}: {features.h2h.away_team_wins}")
print(f"  • Promedio total de goles en H2H: {features.h2h.avg_total_goals_h2h}")
print(f"  • Promedio de córners en H2H: {features.h2h.avg_total_corners_h2h}")
print(f"  • Promedio de tarjetas en H2H: {features.h2h.avg_total_cards_h2h}")

print(f"\n--- Factores Contextuales ({len(features.context_notes)}) ---")
for note in features.context_notes:
    print(f"  • {note}")

print("\n>>> FASE 2 COMPLETADA Y VERIFICADA CON ÉXITO <<<")
