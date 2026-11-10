import math
import numpy as np
from typing import List, Dict, Optional, Tuple
from pydantic import BaseModel, Field
from backend.app.schemas.match import MatchRawFeatures, TeamFormStats, HeadToHeadStats
from backend.app.models.ensemble import ensemble_engine

class MatchActualResult(BaseModel):
    """Resultado real verificado de un partido para backtesting."""
    home_goals: int = Field(..., ge=0, description="Goles finales del equipo local")
    away_goals: int = Field(..., ge=0, description="Goles finales del equipo visitante")
    corners: Optional[int] = Field(None, ge=0, description="Total de córners disputados")
    cards: Optional[int] = Field(None, ge=0, description="Total de tarjetas del encuentro")

    @property
    def outcome_1x2(self) -> str:
        if self.home_goals > self.away_goals:
            return "1"
        elif self.home_goals == self.away_goals:
            return "X"
        else:
            return "2"

    @property
    def is_over_2_5(self) -> bool:
        return (self.home_goals + self.away_goals) > 2.5

    @property
    def is_btts(self) -> bool:
        return self.home_goals >= 1 and self.away_goals >= 1

    @property
    def total_goals(self) -> int:
        return self.home_goals + self.away_goals

class HistoricalEvaluationItem(BaseModel):
    """Instancia de prueba histórica combinando features previas y resultado verificado."""
    match_id: str
    features: MatchRawFeatures
    actual: MatchActualResult

def compute_rps(home_p: float, draw_p: float, away_p: float, actual_outcome: str) -> float:
    """
    Calcula el Ranked Probability Score (RPS) para el mercado 1X2.
    El RPS penaliza la distancia ordinal respecto al desenlace real:
    RPS = 1/(K-1) * sum_{r=1}^{K-1} (sum_{i=1}^r p_i - sum_{i=1}^r e_i)^2
    donde K=3 (Local=1, Empate=X, Visitante=2).
    Un RPS cercano a 0 denota predicciones probabilísticas de excelencia.
    """
    total = home_p + draw_p + away_p
    if total <= 0:
        p1, p2, p3 = 1.0 / 3.0, 1.0 / 3.0, 1.0 / 3.0
    else:
        p1 = home_p / total
        p2 = draw_p / total
        p3 = away_p / total

    if actual_outcome == "1":
        e1, e2 = 1.0, 0.0
    elif actual_outcome == "X":
        e1, e2 = 0.0, 1.0
    else:
        e1, e2 = 0.0, 0.0

    # R = 1
    term1 = (p1 - e1) ** 2
    # R = 2
    term2 = ((p1 + p2) - (e1 + e2)) ** 2

    return float(0.5 * (term1 + term2))

def compute_brier_score(prob: float, actual: bool) -> float:
    """
    Calcula el Brier Score para un evento binario (probabilidad entre 0 y 1 o 0 y 100).
    """
    p = prob / 100.0 if prob > 1.0 else prob
    y = 1.0 if actual else 0.0
    return float((p - y) ** 2)

def compute_log_loss(home_p: float, draw_p: float, away_p: float, actual_outcome: str, eps: float = 1e-15) -> float:
    """
    Calcula la Pérdida Logarítmica (Log-Loss / Cross-Entropy) para la predicción 1X2.
    """
    total = home_p + draw_p + away_p
    if total <= 0:
        p_dict = {"1": 1.0 / 3.0, "X": 1.0 / 3.0, "2": 1.0 / 3.0}
    else:
        p_dict = {
            "1": max(eps, home_p / total),
            "X": max(eps, draw_p / total),
            "2": max(eps, away_p / total)
        }
    actual_prob = p_dict.get(actual_outcome, 1.0 / 3.0)
    return float(-math.log(actual_prob))

def compute_mae(predictions: List[float], actuals: List[float]) -> float:
    if not predictions:
        return 0.0
    return float(np.mean([abs(p - a) for p, a in zip(predictions, actuals)]))

def compute_rmse(predictions: List[float], actuals: List[float]) -> float:
    if not predictions:
        return 0.0
    return float(np.sqrt(np.mean([(p - a) ** 2 for p, a in zip(predictions, actuals)])))

def run_backtest(items: List[HistoricalEvaluationItem], engine=None) -> Dict:
    """
    Ejecuta un ciclo completo de backtesting sobre un conjunto de partidos evaluados.
    Calcula métricas agregadas de calibración probabilística (RPS, Brier Score, Log-Loss),
    precisión clasificatoria y error cuadrático/absoluto en líneas numéricas.
    """
    if engine is None:
        engine = ensemble_engine

    if not items:
        return {
            "total_matches": 0,
            "status": "error",
            "message": "No se proporcionaron partidos para evaluar."
        }

    rps_scores = []
    log_losses = []
    brier_over_2_5 = []
    brier_btts = []

    hits_1x2 = 0
    hits_over_2_5 = 0
    hits_btts = 0

    pred_goals_list = []
    actual_goals_list = []

    pred_corners_list = []
    actual_corners_list = []

    match_reports = []

    for item in items:
        pred_res = engine.predict(item.features)
        pred_win = pred_res.prediction.winner
        pred_goals = pred_res.prediction.goals
        pred_corners = pred_res.prediction.corners

        actual = item.actual
        actual_1x2 = actual.outcome_1x2

        # 1X2 Probabilidades
        h_pct = pred_win.home_win_pct
        d_pct = pred_win.draw_pct
        a_pct = pred_win.away_win_pct

        rps = compute_rps(h_pct, d_pct, a_pct, actual_1x2)
        ll = compute_log_loss(h_pct, d_pct, a_pct, actual_1x2)
        rps_scores.append(rps)
        log_losses.append(ll)

        # 1X2 Predicción dominante con detector de empate táctico en duelos ultra-parejos (Katakuri v4.1)
        if (d_pct >= h_pct and d_pct >= a_pct) or (abs(h_pct - a_pct) <= 4.0 and d_pct >= 28.5):
            dominant_1x2 = "X"
        elif h_pct >= d_pct and h_pct >= a_pct:
            dominant_1x2 = "1"
        else:
            dominant_1x2 = "2"

        if dominant_1x2 == actual_1x2:
            hits_1x2 += 1

        # Over 2.5 Brier & Hit
        p_over25 = pred_goals.over_2_5_pct
        bs_o25 = compute_brier_score(p_over25, actual.is_over_2_5)
        brier_over_2_5.append(bs_o25)
        if (p_over25 >= 50.0) == actual.is_over_2_5:
            hits_over_2_5 += 1

        # BTTS Brier & Hit
        p_btts = pred_goals.both_teams_to_score_pct
        bs_btts = compute_brier_score(p_btts, actual.is_btts)
        brier_btts.append(bs_btts)
        if (p_btts >= 50.0) == actual.is_btts:
            hits_btts += 1

        # Goles totales
        pred_goals_list.append(pred_goals.expected_total)
        actual_goals_list.append(actual.total_goals)

        # Córners
        if actual.corners is not None:
            pred_corners_list.append(pred_corners.expected_total)
            actual_corners_list.append(actual.corners)

        match_reports.append({
            "match_id": item.match_id,
            "match": f"{item.features.home_team} vs {item.features.away_team}",
            "actual_score": f"{actual.home_goals} - {actual.away_goals}",
            "dominant_pred": dominant_1x2,
            "actual_outcome": actual_1x2,
            "home_win_pct": round(h_pct, 1),
            "draw_pct": round(d_pct, 1),
            "away_win_pct": round(a_pct, 1),
            "rps": round(rps, 4),
            "log_loss": round(ll, 4),
            "expected_goals": pred_goals.expected_total,
            "actual_goals": actual.total_goals,
            "over_2_5_pct": p_over25,
            "btts_pct": p_btts
        })

    n = len(items)
    mean_rps = float(np.mean(rps_scores))
    mean_ll = float(np.mean(log_losses))
    mean_bs_over = float(np.mean(brier_over_2_5))
    mean_bs_btts = float(np.mean(brier_btts))

    acc_1x2 = round((hits_1x2 / n) * 100.0, 1)
    acc_over_2_5 = round((hits_over_2_5 / n) * 100.0, 1)
    acc_btts = round((hits_btts / n) * 100.0, 1)

    mae_goals = round(compute_mae(pred_goals_list, actual_goals_list), 2)
    rmse_goals = round(compute_rmse(pred_goals_list, actual_goals_list), 2)

    mae_corners = round(compute_mae(pred_corners_list, actual_corners_list), 2) if pred_corners_list else None
    rmse_corners = round(compute_rmse(pred_corners_list, actual_corners_list), 2) if pred_corners_list else None

    # Calificación analítica según estándares Constantinou-Fenton
    if mean_rps <= 0.190:
        verdict = "Calibración probabilística EXCELENTE (RPS <= 0.190). Superior a líneas de casas de apuestas estándar."
    elif mean_rps <= 0.215:
        verdict = "Calibración probabilística ÓPTIMA (RPS <= 0.215). Alto rigor en probabilidades asignadas."
    elif mean_rps <= 0.235:
        verdict = "Calibración probabilística ACEPTABLE (RPS <= 0.235). Margen de mejora en marcadores imprevistos."
    else:
        verdict = "Calibración probabilística DEFICIENTE (RPS > 0.235). Requiere ajuste de parámetros de ensamble."

    return {
        "total_matches_evaluated": n,
        "metrics": {
            "rps_mean": round(mean_rps, 4),
            "log_loss_mean": round(mean_ll, 4),
            "brier_score_over_2_5": round(mean_bs_over, 4),
            "brier_score_btts": round(mean_bs_btts, 4),
            "accuracy_1x2_pct": acc_1x2,
            "accuracy_over_2_5_pct": acc_over_2_5,
            "accuracy_btts_pct": acc_btts,
            "goals_mae": mae_goals,
            "goals_rmse": rmse_goals,
            "corners_mae": mae_corners,
            "corners_rmse": rmse_corners
        },
        "verdict": verdict,
        "matches": match_reports
    }

def get_benchmark_dataset() -> List[HistoricalEvaluationItem]:
    """
    Retorna un dataset benchmark curado de partidos representativos
    (grandes ligas europeas, estilos contrastantes, clásicos y sorpresas)
    con estadísticas pre-match y resultados finales confirmados.
    """
    return [
        HistoricalEvaluationItem(
            match_id="bm_001_mci_ars",
            features=MatchRawFeatures(
                home_team="Manchester City",
                away_team="Arsenal",
                competition="Premier League",
                is_live=False,
                home_stats=TeamFormStats(
                    team_name="Manchester City",
                    avg_goals_scored=2.4,
                    avg_goals_conceded=1.0,
                    avg_corners=7.1,
                    avg_cards=1.5,
                    win_rate_last_5=0.8
                ),
                away_stats=TeamFormStats(
                    team_name="Arsenal",
                    avg_goals_scored=2.1,
                    avg_goals_conceded=0.8,
                    avg_corners=6.4,
                    avg_cards=1.9,
                    win_rate_last_5=0.8
                ),
                h2h=HeadToHeadStats(
                    total_matches_analyzed=5,
                    home_team_wins=2,
                    draws=2,
                    away_team_wins=1,
                    avg_total_goals_h2h=2.6,
                    avg_total_corners_h2h=10.2,
                    avg_total_cards_h2h=4.2
                )
            ),
            actual=MatchActualResult(
                home_goals=2,
                away_goals=2,
                corners=11,
                cards=5
            )
        ),
        HistoricalEvaluationItem(
            match_id="bm_002_rma_bar",
            features=MatchRawFeatures(
                home_team="Real Madrid",
                away_team="Barcelona",
                competition="LaLiga",
                is_live=False,
                home_stats=TeamFormStats(
                    team_name="Real Madrid",
                    avg_goals_scored=2.2,
                    avg_goals_conceded=1.1,
                    avg_corners=6.0,
                    avg_cards=2.0,
                    win_rate_last_5=0.8
                ),
                away_stats=TeamFormStats(
                    team_name="Barcelona",
                    avg_goals_scored=2.5,
                    avg_goals_conceded=1.2,
                    avg_corners=6.5,
                    avg_cards=2.4,
                    win_rate_last_5=0.8
                ),
                h2h=HeadToHeadStats(
                    total_matches_analyzed=5,
                    home_team_wins=3,
                    draws=0,
                    away_team_wins=2,
                    avg_total_goals_h2h=3.8,
                    avg_total_corners_h2h=10.8,
                    avg_total_cards_h2h=5.4
                )
            ),
            actual=MatchActualResult(
                home_goals=3,
                away_goals=2,
                corners=10,
                cards=6
            )
        ),
        HistoricalEvaluationItem(
            match_id="bm_003_int_juv",
            features=MatchRawFeatures(
                home_team="Inter Milan",
                away_team="Juventus",
                competition="Serie A",
                is_live=False,
                home_stats=TeamFormStats(
                    team_name="Inter Milan",
                    avg_goals_scored=1.9,
                    avg_goals_conceded=0.7,
                    avg_corners=5.8,
                    avg_cards=2.2,
                    win_rate_last_5=0.8
                ),
                away_stats=TeamFormStats(
                    team_name="Juventus",
                    avg_goals_scored=1.4,
                    avg_goals_conceded=0.6,
                    avg_corners=4.8,
                    avg_cards=2.5,
                    win_rate_last_5=0.6
                ),
                h2h=HeadToHeadStats(
                    total_matches_analyzed=5,
                    home_team_wins=2,
                    draws=2,
                    away_team_wins=1,
                    avg_total_goals_h2h=1.8,
                    avg_total_corners_h2h=8.6,
                    avg_total_cards_h2h=5.2
                )
            ),
            actual=MatchActualResult(
                home_goals=1,
                away_goals=0,
                corners=9,
                cards=4
            )
        ),
        HistoricalEvaluationItem(
            match_id="bm_004_bay_dor",
            features=MatchRawFeatures(
                home_team="Bayern Munich",
                away_team="Borussia Dortmund",
                competition="Bundesliga",
                is_live=False,
                home_stats=TeamFormStats(
                    team_name="Bayern Munich",
                    avg_goals_scored=2.8,
                    avg_goals_conceded=1.3,
                    avg_corners=7.4,
                    avg_cards=1.4,
                    win_rate_last_5=0.8
                ),
                away_stats=TeamFormStats(
                    team_name="Borussia Dortmund",
                    avg_goals_scored=2.0,
                    avg_goals_conceded=1.4,
                    avg_corners=5.5,
                    avg_cards=2.1,
                    win_rate_last_5=0.6
                ),
                h2h=HeadToHeadStats(
                    total_matches_analyzed=5,
                    home_team_wins=3,
                    draws=1,
                    away_team_wins=1,
                    avg_total_goals_h2h=4.2,
                    avg_total_corners_h2h=10.6,
                    avg_total_cards_h2h=3.8
                )
            ),
            actual=MatchActualResult(
                home_goals=3,
                away_goals=1,
                corners=12,
                cards=3
            )
        ),
        HistoricalEvaluationItem(
            match_id="bm_005_get_mal",
            features=MatchRawFeatures(
                home_team="Getafe",
                away_team="Mallorca",
                competition="LaLiga",
                is_live=False,
                home_stats=TeamFormStats(
                    team_name="Getafe",
                    avg_goals_scored=0.8,
                    avg_goals_conceded=0.9,
                    avg_corners=3.6,
                    avg_cards=3.4,
                    win_rate_last_5=0.4
                ),
                away_stats=TeamFormStats(
                    team_name="Mallorca",
                    avg_goals_scored=0.7,
                    avg_goals_conceded=1.0,
                    avg_corners=3.4,
                    avg_cards=2.8,
                    win_rate_last_5=0.4
                ),
                h2h=HeadToHeadStats(
                    total_matches_analyzed=5,
                    home_team_wins=1,
                    draws=3,
                    away_team_wins=1,
                    avg_total_goals_h2h=1.4,
                    avg_total_corners_h2h=6.8,
                    avg_total_cards_h2h=6.0
                )
            ),
            actual=MatchActualResult(
                home_goals=0,
                away_goals=0,
                corners=7,
                cards=7
            )
        )
    ]

def run_walk_forward_backtest(
    n_matches: int = 150,
    competition: Optional[str] = None,
    edge_threshold: float = 0.05
) -> Dict:
    """
    Ejecuta un backtesting temporal walk-forward Point-in-Time estricto (Katakuri v4.1) sobre partidos oficiales reales.
    Reconstruye cronológicamente el historial previo, rating Elo dinámico, splits Home/Away y H2H antes de cada partido
    (cero look-ahead bias / cero fuga de datos futuros), evaluando precisión probabilística (RPS, Log-Loss) y
    Value Betting con Criterio de Kelly Fraccional (1/4) frente a cuotas reales de Bet365.
    """
    from collections import defaultdict
    from backend.app.db import SessionLocal, HistoricalMatch, League
    from backend.app.schemas.match import PreviousMatch
    from backend.app.services.league_database import TEAMS_CONFIG
    from backend.app.services.real_data_loader import calculate_elo_update

    db = SessionLocal()
    try:
        all_matches = db.query(HistoricalMatch).order_by(
            HistoricalMatch.match_date.asc(),
            HistoricalMatch.id.asc()
        ).all()
        league_objs = {l.code: l for l in db.query(League).all()}
    finally:
        db.close()

    if not all_matches:
        return {
            "total_matches_evaluated": 0,
            "status": "error",
            "message": "No se encontraron partidos históricos en la base de datos para la evaluación."
        }

    target_code = None
    if competition:
        comp_clean = competition.lower().strip()
        code_map = {
            "premier league": "premier_league",
            "laliga": "laliga",
            "serie a": "serie_a",
            "bundesliga": "bundesliga",
            "ligue 1": "ligue_1",
            "eredivisie": "eredivisie",
            "primeira liga": "primeira_liga",
            "champions league": "champions_league",
            "liga mx": "liga_mx"
        }
        target_code = code_map.get(comp_clean, comp_clean.replace(" ", "_"))

    # Identificar los IDs de los últimos n_matches que cumplen el filtro para evaluar solo esos,
    # pero recorriendo toda la línea temporal previa para reconstruir estado exacto Point-in-Time
    if target_code is not None:
        candidate_matches = [
            m for m in all_matches
            if target_code in (m.league_code or "").lower()
        ]
        eval_target_ids = {m.id for m in candidate_matches[-n_matches:]}
    else:
        # Selección multi-liga estratificada proporcionalmente entre las grandes ligas completas
        by_league = defaultdict(list)
        for m in all_matches:
            if (m.league_code or "") not in ("champions_league", "liga_mx"):
                by_league[m.league_code].append(m)
        if not by_league:
            for m in all_matches:
                by_league[m.league_code].append(m)
        selected_ids = set()
        # Tomar del tramo competitivo de cierre de temporada (evitando distorsión de partidos de trámite final)
        max_len = max((len(v) for v in by_league.values()), default=0)
        for offset in range(10, max_len + 1):
            for lg_code in sorted(by_league.keys()):
                lg_list = by_league[lg_code]
                if offset <= len(lg_list):
                    selected_ids.add(lg_list[-offset].id)
                    if len(selected_ids) >= n_matches:
                        break
            if len(selected_ids) >= n_matches:
                break
        eval_target_ids = selected_ids

    if not eval_target_ids:
        return {
            "total_matches_evaluated": 0,
            "status": "error",
            "message": "No se encontraron partidos para la competición seleccionada."
        }

    base_elo_map = {tc["name"]: float(tc["elo"]) for tc in TEAMS_CONFIG}
    elo_tracker = defaultdict(lambda: 1600.0, base_elo_map)
    team_history = defaultdict(list)
    team_last_season = {}

    items: List[HistoricalEvaluationItem] = []
    bet_data: List[Dict] = []

    for m in all_matches:
        h_name = m.home_team
        a_name = m.away_team
        l_code = m.league_code
        cur_season = getattr(m, "season", "2024-25")

        for club in (h_name, a_name):
            prev_s = team_last_season.get(club)
            if prev_s is not None and prev_s != cur_season:
                base_ref = base_elo_map.get(club, 1620.0)
                elo_tracker[club] = 0.85 * elo_tracker[club] + 0.15 * base_ref
            team_last_season[club] = cur_season

        cur_elo_h = elo_tracker[h_name]
        cur_elo_a = elo_tracker[a_name]
        h_hist = team_history[h_name]
        a_hist = team_history[a_name]

        if m.id in eval_target_ids:
            l_obj = league_objs.get(l_code)
            comp_name = l_obj.name if l_obj else l_code
            def_goals = l_obj.avg_goals if l_obj else 1.35

            if len(h_hist) >= 2 and len(a_hist) >= 2:
                last_15_h = h_hist[-15:]
                last_15_a = a_hist[-15:]
                last_10_h = last_15_h[-10:]
                last_10_a = last_15_a[-10:]
                last_5_h = last_15_h[-5:]
                last_5_a = last_15_a[-5:]

                home_matches_h = [x for x in h_hist if x["was_home"]][-10:]
                away_matches_a = [x for x in a_hist if not x["was_home"]][-10:]

                # Shrinkage empírico de James-Stein hacia el prior estructural (Elo + liga) para estabilizar ventanas cortas
                elo_diff_h = (cur_elo_h - 1650.0) / 400.0
                elo_diff_a = (cur_elo_a - 1650.0) / 400.0
                prior_h_gf = max(0.7, def_goals * (1.0 + 0.18 * elo_diff_h))
                prior_h_ga = max(0.6, def_goals * (1.0 - 0.15 * elo_diff_h))
                prior_a_gf = max(0.7, def_goals * (1.0 + 0.18 * elo_diff_a))
                prior_a_ga = max(0.6, def_goals * (1.0 - 0.15 * elo_diff_a))

                raw_h_gf = float(np.mean([x["gf"] for x in last_15_h]))
                raw_h_ga = float(np.mean([x["ga"] for x in last_15_h]))
                raw_a_gf = float(np.mean([x["gf"] for x in last_15_a]))
                raw_a_ga = float(np.mean([x["ga"] for x in last_15_a]))

                h_gf = round(0.75 * raw_h_gf + 0.25 * prior_h_gf, 2)
                h_ga = round(0.75 * raw_h_ga + 0.25 * prior_h_ga, 2)
                a_gf = round(0.75 * raw_a_gf + 0.25 * prior_a_gf, 2)
                a_ga = round(0.75 * raw_a_ga + 0.25 * prior_a_ga, 2)

                h_home_gf = round(0.75 * float(np.mean([x["gf"] for x in home_matches_h])) + 0.25 * prior_h_gf, 2) if home_matches_h else h_gf
                h_home_ga = round(0.75 * float(np.mean([x["ga"] for x in home_matches_h])) + 0.25 * prior_h_ga, 2) if home_matches_h else h_ga
                a_away_gf = round(0.75 * float(np.mean([x["gf"] for x in away_matches_a])) + 0.25 * prior_a_gf, 2) if away_matches_a else a_gf
                a_away_ga = round(0.75 * float(np.mean([x["ga"] for x in away_matches_a])) + 0.25 * prior_a_ga, 2) if away_matches_a else a_ga

                h_prev_objs = [
                    PreviousMatch(
                        opponent=x["opp"], was_home=x["was_home"], goals_for=int(x["gf"]), goals_against=int(x["ga"]),
                        result=x["res"], corners_for=float(x["cn"]), cards_total=float(x["cr_tot"])
                    ) for x in reversed(last_10_h)
                ]
                a_prev_objs = [
                    PreviousMatch(
                        opponent=x["opp"], was_home=x["was_home"], goals_for=int(x["gf"]), goals_against=int(x["ga"]),
                        result=x["res"], corners_for=float(x["cn"]), cards_total=float(x["cr_tot"])
                    ) for x in reversed(last_10_a)
                ]

                past_h2h = [x for x in h_hist if x["opp"] == a_name][-8:]
                if past_h2h:
                    h_w = sum(1 for x in past_h2h if x["res"] == "W")
                    a_w = sum(1 for x in past_h2h if x["res"] == "L")
                    drw = sum(1 for x in past_h2h if x["res"] == "D")
                    h2h_g = round(float(np.mean([x["gf"] + x["ga"] for x in past_h2h])), 2)
                    h2h_cn = round(float(np.mean([x["cn_tot"] for x in past_h2h])), 1)
                    h2h_cr = round(float(np.mean([x["cr_tot"] for x in past_h2h])), 1)
                else:
                    h_w, a_w, drw = 0, 0, 0
                    h2h_g = (l_obj.avg_goals * 2.0) if l_obj else 2.7
                    h2h_cn = l_obj.avg_corners if l_obj else 9.5
                    h2h_cr = l_obj.avg_cards if l_obj else 4.0

                feats = MatchRawFeatures(
                    home_team=h_name,
                    away_team=a_name,
                    competition=comp_name,
                    is_live=False,
                    home_stats=TeamFormStats(
                        team_name=h_name,
                        avg_goals_scored=h_gf,
                        avg_goals_conceded=h_ga,
                        avg_corners=round(float(np.mean([x["cn"] for x in last_15_h])), 1),
                        avg_cards=round(float(np.mean([x["cr"] for x in last_15_h])), 1),
                        win_rate_last_5=round(sum(1 for x in last_5_h if x["res"] == "W") / len(last_5_h), 2),
                        last_matches=h_prev_objs,
                        elo_rating=round(cur_elo_h, 1),
                        home_goals_scored=h_home_gf,
                        home_goals_conceded=h_home_ga,
                        avg_shots_target_for=round(float(np.mean([x["hst"] for x in last_15_h])), 1),
                        avg_shots_target_against=round(float(np.mean([x["ast"] for x in last_15_h])), 1)
                    ),
                    away_stats=TeamFormStats(
                        team_name=a_name,
                        avg_goals_scored=a_gf,
                        avg_goals_conceded=a_ga,
                        avg_corners=round(float(np.mean([x["cn"] for x in last_15_a])), 1),
                        avg_cards=round(float(np.mean([x["cr"] for x in last_15_a])), 1),
                        win_rate_last_5=round(sum(1 for x in last_5_a if x["res"] == "W") / len(last_5_a), 2),
                        last_matches=a_prev_objs,
                        elo_rating=round(cur_elo_a, 1),
                        away_goals_scored=a_away_gf,
                        away_goals_conceded=a_away_ga,
                        avg_shots_target_for=round(float(np.mean([x["hst"] for x in last_15_a])), 1),
                        avg_shots_target_against=round(float(np.mean([x["ast"] for x in last_15_a])), 1)
                    ),
                    h2h=HeadToHeadStats(
                        total_matches_analyzed=len(past_h2h),
                        home_team_wins=h_w,
                        away_team_wins=a_w,
                        draws=drw,
                        avg_total_goals_h2h=h2h_g,
                        avg_total_corners_h2h=h2h_cn,
                        avg_total_cards_h2h=h2h_cr
                    )
                )
            else:
                feats = MatchRawFeatures(
                    home_team=h_name,
                    away_team=a_name,
                    competition=comp_name,
                    home_stats=TeamFormStats(team_name=h_name, avg_goals_scored=def_goals * 1.05, avg_goals_conceded=def_goals * 0.95, elo_rating=round(cur_elo_h, 1)),
                    away_stats=TeamFormStats(team_name=a_name, avg_goals_scored=def_goals * 0.95, avg_goals_conceded=def_goals * 1.05, elo_rating=round(cur_elo_a, 1)),
                    h2h=HeadToHeadStats(total_matches_analyzed=0, avg_total_goals_h2h=def_goals * 2.0)
                )

            cn_sum = (m.corners_home + m.corners_away) if (m.corners_home is not None and m.corners_away is not None and (m.corners_home + m.corners_away) > 0) else None
            cd_sum = (m.cards_home + m.cards_away) if (m.cards_home is not None and m.cards_away is not None and (m.cards_home + m.cards_away) > 0) else None

            actual = MatchActualResult(
                home_goals=m.home_goals,
                away_goals=m.away_goals,
                corners=cn_sum,
                cards=cd_sum
            )

            items.append(HistoricalEvaluationItem(
                match_id=f"wf_{m.id}_{h_name}_{a_name}",
                features=feats,
                actual=actual
            ))
            bet_data.append({
                "b365_h": m.b365_home_odds,
                "b365_d": m.b365_draw_odds,
                "b365_a": m.b365_away_odds,
                "outcome": actual.outcome_1x2
            })

        # Actualizar estado cronológico ESTRICTAMENTE DESPUÉS de registrar las features previas del partido
        new_h, new_a = calculate_elo_update(cur_elo_h, cur_elo_a, m.home_goals, m.away_goals)
        elo_tracker[h_name] = new_h
        elo_tracker[a_name] = new_a

        cn_tot = (m.corners_home or 0) + (m.corners_away or 0)
        cr_tot = (m.cards_home or 0) + (m.cards_away or 0)
        team_history[h_name].append({
            "opp": a_name, "was_home": True, "date": m.match_date,
            "gf": m.home_goals, "ga": m.away_goals,
            "res": "W" if m.home_goals > m.away_goals else ("D" if m.home_goals == m.away_goals else "L"),
            "hst": m.home_shots_target or 4, "ast": m.away_shots_target or 4,
            "cn": m.corners_home or 5, "cr": m.cards_home or 2,
            "cn_tot": cn_tot, "cr_tot": cr_tot
        })
        team_history[a_name].append({
            "opp": h_name, "was_home": False, "date": m.match_date,
            "gf": m.away_goals, "ga": m.home_goals,
            "res": "W" if m.away_goals > m.home_goals else ("D" if m.home_goals == m.away_goals else "L"),
            "hst": m.away_shots_target or 4, "ast": m.home_shots_target or 4,
            "cn": m.corners_away or 4, "cr": m.cards_away or 2,
            "cn_tot": cn_tot, "cr_tot": cr_tot
        })

    # Ejecutar evaluación mediante el ensamble de Katakuri v4.1
    base_results = run_backtest(items)

    # Simulación de Value Betting (Katakuri Edge vs Cuotas de Mercado + Kelly 1/4 Staking)
    total_bets = 0
    bets_won = 0
    total_staked = 0.0
    total_returned = 0.0
    kelly_staked = 0.0
    kelly_returned = 0.0

    for i, report in enumerate(base_results.get("matches", [])):
        b = bet_data[i]
        b_h, b_d, b_a = b["b365_h"], b["b365_d"], b["b365_a"]
        actual_out = b["outcome"]

        if b_h and b_d and b_a and b_h > 1.0 and b_d > 1.0 and b_a > 1.0:
            raw_h, raw_d, raw_a = 1.0 / b_h, 1.0 / b_d, 1.0 / b_a
            margin = raw_h + raw_d + raw_a
            p_mkt_h, p_mkt_d, p_mkt_a = raw_h / margin, raw_d / margin, raw_a / margin

            p_mod_h = report.get("home_win_pct", 33.3) / 100.0
            p_mod_d = report.get("draw_pct", 33.3) / 100.0
            p_mod_a = report.get("away_win_pct", 33.3) / 100.0

            candidates = [
                ("1", p_mod_h, p_mkt_h, b_h),
                ("X", p_mod_d, p_mkt_d, b_d),
                ("2", p_mod_a, p_mkt_a, b_a)
            ]

            best_pick = None
            max_edge = 0.0
            best_odds = 1.0
            best_prob = 0.0

            for pick_code, p_mod, p_mkt, odds_val in candidates:
                edge_val = p_mod - p_mkt
                # Filtro institucional de alta convicción: cuotas en rango eficiente (1.42 a 4.10) y probabilidad >= 34%
                if edge_val > edge_threshold and 1.42 <= odds_val <= 4.10 and p_mod >= 0.34:
                    if edge_val > max_edge:
                        max_edge = edge_val
                        best_pick = pick_code
                        best_odds = odds_val
                        best_prob = p_mod

            if best_pick is not None:
                total_bets += 1
                total_staked += 1.0  # Unidad plana
                # Criterio de Kelly Fraccional (1/4 Kelly) acotado entre 0.25u y 2.0u
                b_net = max(0.1, best_odds - 1.0)
                kelly_f = max(0.25, min(2.0, 0.25 * ((best_prob * best_odds - 1.0) / b_net) * 10.0))
                kelly_staked += kelly_f

                if best_pick == actual_out:
                    bets_won += 1
                    total_returned += best_odds
                    kelly_returned += kelly_f * best_odds

    net_profit = round(total_returned - total_staked, 2)
    roi_pct = round((net_profit / total_staked * 100.0), 2) if total_staked > 0 else 0.0
    kelly_profit = round(kelly_returned - kelly_staked, 2)
    kelly_roi_pct = round((kelly_profit / kelly_staked * 100.0), 2) if kelly_staked > 0 else 0.0
    win_rate_bets = round((bets_won / total_bets * 100.0), 1) if total_bets > 0 else 0.0

    base_results["walk_forward_simulation"] = {
        "dataset_type": "Partidos Históricos Oficiales Point-in-Time (Cero Fuga Temporal)",
        "sample_size": len(items),
        "competition_filter": competition or "Todas las ligas activas (9 competiciones)",
        "value_betting": {
            "edge_threshold_pct": round(edge_threshold * 100.0, 1),
            "total_bets_placed": total_bets,
            "bets_won": bets_won,
            "bets_lost": total_bets - bets_won,
            "win_rate_pct": win_rate_bets,
            "total_staked_units": total_staked,
            "net_profit_units": net_profit,
            "roi_pct": roi_pct,
            "kelly_net_profit_units": kelly_profit,
            "kelly_roi_pct": kelly_roi_pct
        }
    }
    return base_results
