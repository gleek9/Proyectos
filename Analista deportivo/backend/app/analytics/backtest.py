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

        # 1X2 Predicción dominante
        if h_pct >= d_pct and h_pct >= a_pct:
            dominant_1x2 = "1"
        elif a_pct >= d_pct and a_pct >= h_pct:
            dominant_1x2 = "2"
        else:
            dominant_1x2 = "X"

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
