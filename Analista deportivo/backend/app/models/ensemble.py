"""
Módulo Meta-Ensamble Calibrado y Traductor a Lenguaje Humano.
Combina Poisson Bivariado Dixon-Coles (40%), XGBoost (35%) y LSTM Secuencial (25%).
Garantiza coherencia probabilística (suma 100%) y genera veredictos legibles para personas.
"""
import logging
from typing import Dict, List
import numpy as np
from datetime import datetime, timezone

from backend.app.schemas.match import MatchRawFeatures
from backend.app.schemas.prediction import (
    PredictionResponse, MatchMeta, MatchPredictionDetails,
    WinnerPrediction, GoalsPrediction, CornersPrediction, CardsPrediction,
    ChartData, GoalDistributionItem, TopScoreItem,
    LiveGoalLine, LiveCornerLine,
    DoubleChancePrediction, DrawNoBetPrediction
)
from backend.app.models.poisson import poisson_model, parse_elapsed_minute
from backend.app.models.tabular_ml import tabular_predictor
from backend.app.models.lstm_net import lstm_predictor

logger = logging.getLogger(__name__)

def _coalesce(value, fallback):
    """Devuelve `value` salvo que sea None. A diferencia de `value or fallback`, conserva probabilidades 0.0 legítimas."""
    return fallback if value is None else value

class MetaEnsembleEngine:
    def __init__(
        self,
        weight_poisson: float = 0.40,
        weight_xgboost: float = 0.35,
        weight_lstm: float = 0.25
    ):
        self.w_poisson = weight_poisson
        self.w_xgb = weight_xgboost
        self.w_lstm = weight_lstm

    def _get_dynamic_weights(self, is_live: bool, elapsed_min: int = 0) -> tuple[float, float, float]:
        """
        Calcula las ponderaciones del ensamble. En partidos en vivo, ajusta los pesos dinámicamente
        según el minuto: a medida que el tiempo se agota, el modelo de probabilidad condicional matemática
        (Poisson con marcador actual y tiempo restante) gana peso frente a las expectativas pre-match.
        """
        if not is_live:
            return self.w_poisson, self.w_xgb, self.w_lstm

        m = float(np.clip(elapsed_min, 0, 90))
        # Anchors: 0' (inicio), 45' (descanso), 70' (recta final), 85' (cierre)
        min_anchors = [0.0, 45.0, 70.0, 85.0, 90.0]
        w_p_anchors = [0.45, 0.55, 0.68, 0.78, 0.82]
        w_x_anchors = [0.33, 0.28, 0.20, 0.14, 0.11]
        w_l_anchors = [0.22, 0.17, 0.12, 0.08, 0.07]

        wp = float(np.interp(m, min_anchors, w_p_anchors))
        wx = float(np.interp(m, min_anchors, w_x_anchors))
        wl = float(np.interp(m, min_anchors, w_l_anchors))

        tot = wp + wx + wl
        return wp / tot, wx / tot, wl / tot

    def _normalize_probs(self, home_p: float, draw_p: float, away_p: float) -> tuple[float, float, float]:
        """Normaliza las probabilidades 1X2 para que sumen exactamente 100.0% con 1 decimal."""
        tot = home_p + draw_p + away_p
        if tot <= 0:
            return 33.3, 33.4, 33.3

        h = round((home_p / tot) * 100, 1)
        d = round((draw_p / tot) * 100, 1)
        a = round(100.0 - h - d, 1)  # Garantizar cierre matemático exacto en 100.0%
        return h, d, a

    def _generate_human_verdicts(
        self,
        home_team: str,
        away_team: str,
        home_pct: float,
        draw_pct: float,
        away_pct: float,
        exp_goals: float,
        over_2_5_pct: float,
        exp_corners: float,
        exp_cards: float,
        red_card_risk: float,
        is_live: bool = False,
        live_minute: str = None,
        live_score: str = None,
        live_no_more_goals_pct: float = None,
        live_more_goals_pct: float = None,
        current_goals: int = None,
        current_corners: int = None
    ) -> Dict[str, str]:
        """Genera veredictos simples y directos sin jerga técnica con prioridad en vivo."""
        # 1. Ganador y coberturas recomendadas
        diff = home_pct - away_pct

        if home_pct >= 55.0:
            winner_verdict = f"Favorito claro: {home_team} ({home_pct}% de probabilidad)"
        elif away_pct >= 55.0:
            winner_verdict = f"Favorito claro: {away_team} ({away_pct}% de probabilidad)"
        elif diff >= 10.0:
            winner_verdict = f"Ligera ventaja para {home_team} ({home_pct}%). Sugerencia: 1X o DNB para cobertura."
        elif diff <= -10.0:
            winner_verdict = f"Ligera ventaja para {away_team} ({away_pct}%). Sugerencia: X2 o DNB para cobertura."
        elif draw_pct >= 31.0 or abs(diff) < 8.0:
            winner_verdict = f"Partido muy parejo con alta tendencia al empate ({draw_pct}%). Cobertura recomendada: Doble Oportunidad."
        else:
            winner_verdict = f"Duelo equilibrado con leve inclinación local."

        # 2. Goles
        if is_live and live_score:
            cg = current_goals if current_goals is not None else 0
            no_more_str = f"{live_no_more_goals_pct}%" if live_no_more_goals_pct is not None else "40%"
            more_str = f"{live_more_goals_pct}%" if live_more_goals_pct is not None else "60%"
            goals_verdict = (
                f"Marcador en directo {live_score} ({cg} goles actuales). La red neuronal y modelos estiman un "
                f"{no_more_str} de probabilidad de NO haber más goles y un {more_str} de marcar más goles ({cg + 1}+ totales)."
            )
        elif over_2_5_pct >= 62.0:
            goals_verdict = f"Partido abierto con alta probabilidad de más de 2 goles ({round(exp_goals, 1)} proyectados)"
        elif over_2_5_pct <= 40.0:
            goals_verdict = f"Duelo cerrado y táctico; tendencia a menos de 2.5 goles ({round(exp_goals, 1)} proyectados)"
        else:
            goals_verdict = f"Expectativa equilibrada de {round(exp_goals, 1)} goles en total"

        # 3. Córners
        corners_rounded = round(exp_corners)
        if is_live:
            if current_corners is not None:
                corners_verdict = f"En vivo: {current_corners} córners actuales; ritmo proyectado hacia {corners_rounded} córners totales acumulados al final del encuentro"
            else:
                corners_verdict = f"En vivo: Ritmo proyectado hacia {corners_rounded} tiros de esquina/córners totales al final del encuentro"
        elif exp_corners >= 10.0:
            corners_verdict = f"Frecuencia alta de tiros de esquina ({corners_rounded} proyectados)"
        elif exp_corners <= 8.0:
            corners_verdict = f"Frecuencia baja de tiros de esquina ({corners_rounded} proyectados)"
        else:
            corners_verdict = f"Ritmo estándar de {corners_rounded} córners en el encuentro"

        # 4. Tarjetas
        cards_rounded = round(exp_cards)
        if exp_cards >= 5.0 or red_card_risk >= 22.0:
            cards_verdict = f"Alta intensidad y fricción ({cards_rounded} tarjetas esperadas, riesgo de roja {round(red_card_risk)}%)"
        else:
            cards_verdict = f"Intensidad media ({cards_rounded} tarjetas esperadas, juego dentro del límite reglamentario)"

        return {
            "winner": winner_verdict,
            "goals": goals_verdict,
            "corners": corners_verdict,
            "cards": cards_verdict
        }

    def _extract_key_factors(self, raw: MatchRawFeatures, exp_goals: float) -> List[str]:
        """Extrae los 3 a 5 factores futbolísticos más determinantes, priorizando datos en vivo."""
        factors = []
        is_live = getattr(raw, "is_live", False)
        live_minute = getattr(raw, "live_minute", None)
        live_score = getattr(raw, "live_score", None)

        if is_live:
            min_txt = f" (Minuto {live_minute})" if live_minute else ""
            score_txt = f" Marcador en directo: {live_score}." if live_score else ""
            factors.append(f"🔴 PARTIDO EN VIVO{min_txt}:{score_txt} Prioridad absoluta a estadísticas y dinámica del encuentro en curso.")

            # Factores de expulsiones en directo
            reds_h = int(getattr(raw, "live_red_cards_home", 0) or 0)
            reds_a = int(getattr(raw, "live_red_cards_away", 0) or 0)
            if reds_h > 0:
                factors.append(f"🔴 INFERIORIDAD NUMÉRICA: {raw.home_team} juega con {reds_h} tarjeta{'s' if reds_h > 1 else ''} roja{'s' if reds_h > 1 else ''} en directo.")
            if reds_a > 0:
                factors.append(f"🔴 INFERIORIDAD NUMÉRICA: {raw.away_team} juega con {reds_a} tarjeta{'s' if reds_a > 1 else ''} roja{'s' if reds_a > 1 else ''} en directo.")

            # Telemetría de asedio en directo (tiros a puerta)
            sot_h = getattr(raw, "live_shots_on_target_home", None)
            sot_a = getattr(raw, "live_shots_on_target_away", None)
            if sot_h is not None and sot_a is not None and (int(sot_h) + int(sot_a) >= 4):
                factors.append(f"⚽ TELEMETRÍA EN DIRECTO: {raw.home_team} registra {sot_h} tiros a puerta frente a {sot_a} de {raw.away_team}.")

        h = raw.home_stats
        a = raw.away_stats
        h2h = raw.h2h

        # Factor ofensivo local
        if h.avg_goals_scored >= 2.0:
            factors.append(f"{raw.home_team} promedia {h.avg_goals_scored:.1f} goles anotados por partido en sus juegos recientes.")
        elif h.avg_goals_conceded <= 0.8:
            factors.append(f"{raw.home_team} mantiene una defensa sólida con solo {h.avg_goals_conceded:.1f} goles recibidos en promedio.")

        # Factor visitante
        if a.avg_goals_conceded >= 1.7:
            factors.append(f"{raw.away_team} muestra fragilidad defensiva concediendo {a.avg_goals_conceded:.1f} goles en promedio.")
        elif a.win_rate_last_5 >= 0.6:
            factors.append(f"{raw.away_team} llega en gran momento con un {int(a.win_rate_last_5 * 100)}% de victorias en sus últimos partidos.")

        # Factor H2H
        if h2h.total_matches_analyzed >= 2:
            if h2h.avg_total_goals_h2h >= 2.5:
                factors.append(f"Los enfrentamientos directos previos promedian {h2h.avg_total_goals_h2h:.1f} goles totales.")
            if h2h.home_team_wins > h2h.away_team_wins:
                factors.append(f"El historial directo favorece a {raw.home_team} con {h2h.home_team_wins} triunfos en {h2h.total_matches_analyzed} cruces.")
            elif h2h.away_team_wins > h2h.home_team_wins:
                factors.append(f"{raw.away_team} domina los antecedentes recientes con {h2h.away_team_wins} victorias sobre {raw.home_team}.")

        # Ausencias clave
        if h.key_absences:
            absences_str = ", ".join(h.key_absences[:2])
            factors.append(f"Bajas sensibles en {raw.home_team}: {absences_str}.")
        if a.key_absences:
            absences_str = ", ".join(a.key_absences[:2])
            factors.append(f"Bajas sensibles en {raw.away_team}: {absences_str}.")

        # Notas contextuales recogidas por Gemini
        if raw.context_notes:
            for note in raw.context_notes[:2]:
                if note and len(note) > 10 and note not in factors:
                    factors.append(note.strip())

        # Si hay menos de 3 factores, agregar resumen
        if len(factors) < 3:
            factors.append(f"Se proyecta un total combinado de {round(exp_goals, 1)} goles esperados en el encuentro.")

        return factors[:4]

    def predict(self, raw: MatchRawFeatures) -> PredictionResponse:
        """
        Ejecuta los tres modelos locales, realiza el ensamble ponderado,
        calibra porcentajes y genera el contrato final tipado.
        """
        logger.info(f"Iniciando Ensamble Predictivo Local para {raw.home_team} vs {raw.away_team}...")

        # 1. Ejecutar Poisson Dixon-Coles
        p_res = poisson_model.predict(raw)

        # 2. Ejecutar XGBoost Tabular
        xgb_res = tabular_predictor.predict(raw)

        # 3. Ejecutar PyTorch LSTM Secuencial
        lstm_res = lstm_predictor.predict(raw)

        # -------------------------------------------------------------
        # Combinación de Probabilidades 1X2 (Meta-Ensamble Dinámico)
        # -------------------------------------------------------------
        is_live = getattr(raw, "is_live", False)
        elapsed_min = parse_elapsed_minute(getattr(raw, "live_minute", None)) if is_live else 0
        wp, wx, wl = self._get_dynamic_weights(is_live, elapsed_min)

        raw_home_p = (
            p_res["winner_probs"]["home_win"] * wp +
            xgb_res["winner_probs"]["home_win"] * wx +
            lstm_res["winner_probs"]["home_win"] * wl
        )
        raw_draw_p = (
            p_res["winner_probs"]["draw"] * wp +
            xgb_res["winner_probs"]["draw"] * wx +
            lstm_res["winner_probs"]["draw"] * wl
        )
        raw_away_p = (
            p_res["winner_probs"]["away_win"] * wp +
            xgb_res["winner_probs"]["away_win"] * wx +
            lstm_res["winner_probs"]["away_win"] * wl
        )

        final_home_p, final_draw_p, final_away_p = self._normalize_probs(raw_home_p, raw_draw_p, raw_away_p)

        # -------------------------------------------------------------
        # Consenso de Goles
        # -------------------------------------------------------------
        # -------------------------------------------------------------
        # Consenso de Goles y Matriz Bivariada Unificada
        # -------------------------------------------------------------
        import re
        curr_gh, curr_ga = 0, 0
        if getattr(raw, "live_score", None):
            sc_m = re.search(r"(\d+)\s*[-:]\s*(\d+)", str(raw.live_score))
            if sc_m:
                curr_gh, curr_ga = int(sc_m.group(1)), int(sc_m.group(2))

        curr_tot_goals = curr_gh + curr_ga if is_live else 0

        poisson_goals = p_res["goals"]["expected_total"]
        tabular_goals = xgb_res["goals_expected"]
        lstm_momentum = lstm_res["momentum_goals"]

        # Expectativa ponderada dinámica del total de goles
        if is_live:
            lstm_live_tot = curr_tot_goals + (lstm_res.get("live_expected_remaining_goals") or 0.0)
            exp_goals_combined = round(poisson_goals * wp + tabular_goals * wx + lstm_live_tot * wl, 2)
            exp_goals_combined = max(float(curr_tot_goals), exp_goals_combined)
        else:
            lstm_mom = lstm_res.get("momentum_goals", 2.5)
            mom_ratio = float(np.clip(1.0 + (lstm_mom - 2.5) * 0.025, 0.95, 1.05))
            base_exp_goals = poisson_goals * 0.65 + tabular_goals * 0.35
            exp_goals_combined = round(base_exp_goals * mom_ratio, 2)

        # Reparto consensual de goles restantes entre local y visitante
        rem_goals_combined = max(0.08, exp_goals_combined - curr_tot_goals)
        p_lambda_h = float(p_res.get("lambda_home", 1.30))
        p_mu_a = float(p_res.get("mu_away", 1.15))
        tot_p_lambdas = max(0.1, p_lambda_h + p_mu_a)

        h_share_base = p_lambda_h / tot_p_lambdas
        ens_win_diff = (final_home_p - final_away_p) / 100.0
        pois_win_diff = (p_res["winner_probs"]["home_win"] - p_res["winner_probs"]["away_win"]) / 100.0
        h_share = float(np.clip(h_share_base + 0.12 * (ens_win_diff - pois_win_diff), 0.20, 0.80))

        cons_lambda_h = rem_goals_combined * h_share
        cons_mu_a = rem_goals_combined * (1.0 - h_share)

        # Matriz Bivariada de Consenso Unificado: garantiza coherencia total
        cons_goals = poisson_model.evaluate_matrix_goals(
            lambda_home=cons_lambda_h,
            mu_away=cons_mu_a,
            curr_gh=curr_gh,
            curr_ga=curr_ga,
            is_live=is_live
        )

        over_1_5 = round(cons_goals["over_1_5_pct"], 1)
        over_2_5_combined = round(cons_goals["over_2_5_pct"], 1)
        over_3_5 = round(cons_goals["over_3_5_pct"], 1)
        btts = round(cons_goals["both_teams_to_score_pct"], 1)

        # Selección de Marcador Más Probable Concordante a partir del ranking real de la matriz
        top_scores_list = cons_goals.get("top_scores", [])
        most_likely_score = cons_goals["most_likely_score"]

        try:
            if final_home_p >= 50.0 or (final_home_p - final_away_p >= 12.0):
                home_wins_scores = [
                    s["score"] for s in top_scores_list
                    if (int(s["score"].split("-")[0].strip()) > int(s["score"].split("-")[1].strip()))
                ]
                if home_wins_scores:
                    most_likely_score = home_wins_scores[0]
            elif final_away_p >= 50.0 or (final_away_p - final_home_p >= 12.0):
                away_wins_scores = [
                    s["score"] for s in top_scores_list
                    if (int(s["score"].split("-")[1].strip()) > int(s["score"].split("-")[0].strip()))
                ]
                if away_wins_scores:
                    most_likely_score = away_wins_scores[0]
            elif final_draw_p >= 30.0 or abs(final_home_p - final_away_p) <= 8.0:
                draw_scores = [
                    s["score"] for s in top_scores_list
                    if (int(s["score"].split("-")[0].strip()) == int(s["score"].split("-")[1].strip()))
                ]
                if draw_scores:
                    most_likely_score = draw_scores[0]
        except Exception:
            most_likely_score = cons_goals["most_likely_score"]

        # Córners en vivo: calibración y prevención estricta de sesgos
        exp_corners_final = p_res["corners"]["expected_total"]
        over_8_5_cn = p_res["corners"]["over_8_5_pct"]
        over_9_5_cn = p_res["corners"]["over_9_5_pct"]
        over_10_5_cn = p_res["corners"]["over_10_5_pct"]

        curr_cn = p_res["corners"].get("current_corners")
        if is_live and curr_cn is not None:
            exp_corners_final = max(float(curr_cn), exp_corners_final)
            if curr_cn >= 9:
                over_8_5_cn = 100.0
            if curr_cn >= 10:
                over_9_5_cn = 100.0
            if curr_cn >= 11:
                over_10_5_cn = 100.0

        # -------------------------------------------------------------
        # Consenso de Probabilidades Dinámicas en Vivo (Red Neuronal + Algoritmos)
        # -------------------------------------------------------------
        is_live = getattr(raw, "is_live", False)
        curr_goals = p_res["goals"].get("current_goals")
        final_no_more_p = None
        final_more_p = None
        final_plus_2_p = None
        final_plus_3_p = None
        live_goal_lines = []
        live_corner_lines = []

        if is_live:
            p_pois_no_more = _coalesce(p_res["goals"].get("no_more_goals_pct"), 45.0)
            p_xgb_no_more = _coalesce(xgb_res.get("live_no_more_goals_pct"), p_pois_no_more)
            p_lstm_no_more = _coalesce(lstm_res.get("live_no_more_goals_pct"), p_pois_no_more)

            # Ensamble ponderado dinámico de "Sin más goles" según minuto de juego
            final_no_more_p = round(p_pois_no_more * wp + p_xgb_no_more * wx + p_lstm_no_more * wl, 1)
            final_no_more_p = float(np.clip(final_no_more_p, 1.0, 99.0))
            final_more_p = round(100.0 - final_no_more_p, 1)

            pois_p2 = _coalesce(p_res["goals"].get("plus_2_goals_pct"), final_more_p * 0.65)
            final_plus_2_p = round(min(final_more_p * 0.72, pois_p2), 1)
            pois_p3 = _coalesce(p_res["goals"].get("plus_3_goals_pct"), final_plus_2_p * 0.55)
            final_plus_3_p = round(min(final_plus_2_p * 0.60, pois_p3), 1)

            import re
            curr_gh, curr_ga = 0, 0
            if getattr(raw, "live_score", None):
                sc_m = re.search(r"(\d+)\s*[-:]\s*(\d+)", str(raw.live_score))
                if sc_m:
                    curr_gh, curr_ga = int(sc_m.group(1)), int(sc_m.group(2))

            cg = curr_goals if curr_goals is not None else (curr_gh + curr_ga)
            live_goal_lines = [
                LiveGoalLine(
                    line=f"Sin más goles (+0) [Marcador final {curr_gh} - {curr_ga}]",
                    over_threshold=float(cg),
                    probability=final_no_more_p
                ),
                LiveGoalLine(
                    line=f"+1 gol adicional o más [Más de {cg}.5 goles totales]",
                    over_threshold=float(cg + 0.5),
                    probability=final_more_p
                ),
                LiveGoalLine(
                    line=f"+2 goles adicionales o más [Más de {cg + 1}.5 goles totales]",
                    over_threshold=float(cg + 1.5),
                    probability=final_plus_2_p
                ),
                LiveGoalLine(
                    line=f"+3 goles adicionales o más [Más de {cg + 2}.5 goles totales]",
                    over_threshold=float(cg + 2.5),
                    probability=final_plus_3_p
                )
            ]

            live_corner_lines = [
                LiveCornerLine(line=item["line"], probability=item["probability"])
                for item in p_res["corners"].get("live_corners_lines", [])
            ]

        # -------------------------------------------------------------
        # Veredictos Humanos y Factores Clave
        # -------------------------------------------------------------
        verdicts = self._generate_human_verdicts(
            home_team=raw.home_team,
            away_team=raw.away_team,
            home_pct=final_home_p,
            draw_pct=final_draw_p,
            away_pct=final_away_p,
            exp_goals=exp_goals_combined,
            over_2_5_pct=over_2_5_combined,
            exp_corners=exp_corners_final,
            exp_cards=p_res["cards"]["expected_total"],
            red_card_risk=p_res["cards"]["red_card_risk_pct"],
            is_live=is_live,
            live_minute=getattr(raw, "live_minute", None),
            live_score=getattr(raw, "live_score", None),
            live_no_more_goals_pct=final_no_more_p,
            live_more_goals_pct=final_more_p,
            current_goals=curr_goals,
            current_corners=p_res["corners"].get("current_corners")
        )

        key_factors = self._extract_key_factors(raw, exp_goals_combined)

        # -------------------------------------------------------------
        # Mercados Derivados: Doble Oportunidad (1X, X2, 12) y DNB
        # -------------------------------------------------------------
        dc_1x = round(min(99.0, final_home_p + final_draw_p), 1)
        dc_x2 = round(min(99.0, final_draw_p + final_away_p), 1)
        dc_12 = round(min(99.0, final_home_p + final_away_p), 1)
        double_chance = DoubleChancePrediction(
            home_or_draw_pct=dc_1x,
            draw_or_away_pct=dc_x2,
            home_or_away_pct=dc_12
        )

        denom_dnb = final_home_p + final_away_p
        if denom_dnb > 0:
            h_dnb = round((final_home_p / denom_dnb) * 100.0, 1)
            a_dnb = round(100.0 - h_dnb, 1)
        else:
            h_dnb = 50.0
            a_dnb = 50.0

        draw_no_bet = DrawNoBetPrediction(
            home_dnb_pct=h_dnb,
            away_dnb_pct=a_dnb
        )

        # -------------------------------------------------------------
        # Construcción de la Respuesta Final Tipada
        # -------------------------------------------------------------
        response = PredictionResponse(
            match=MatchMeta(
                home_team=raw.home_team,
                away_team=raw.away_team,
                competition=raw.competition,
                is_live=is_live,
                match_url=getattr(raw, "match_url", None),
                live_minute=getattr(raw, "live_minute", None),
                live_score=getattr(raw, "live_score", None),
                live_corners=p_res["corners"].get("current_corners"),
                live_red_cards_home=int(getattr(raw, "live_red_cards_home", 0) or 0),
                live_red_cards_away=int(getattr(raw, "live_red_cards_away", 0) or 0),
                live_shots_on_target_home=getattr(raw, "live_shots_on_target_home", None),
                live_shots_on_target_away=getattr(raw, "live_shots_on_target_away", None),
                live_possession_home=getattr(raw, "live_possession_home", None),
                live_possession_away=getattr(raw, "live_possession_away", None),
                analyzed_at=datetime.now(timezone.utc)
            ),
            prediction=MatchPredictionDetails(
                winner=WinnerPrediction(
                    home_win_pct=final_home_p,
                    draw_pct=final_draw_p,
                    away_win_pct=final_away_p,
                    human_verdict=verdicts["winner"],
                    double_chance=double_chance,
                    draw_no_bet=draw_no_bet
                ),
                goals=GoalsPrediction(
                    expected_total=exp_goals_combined,
                    most_likely_score=most_likely_score,
                    over_1_5_pct=over_1_5,
                    over_2_5_pct=over_2_5_combined,
                    over_3_5_pct=over_3_5,
                    both_teams_to_score_pct=btts,
                    human_verdict=verdicts["goals"],
                    is_live=is_live,
                    current_goals=curr_goals if is_live else None,
                    no_more_goals_pct=final_no_more_p if is_live else None,
                    more_goals_pct=final_more_p if is_live else None,
                    plus_1_goal_pct=final_more_p if is_live else None,
                    plus_2_goals_pct=final_plus_2_p if is_live else None,
                    plus_3_goals_pct=final_plus_3_p if is_live else None,
                    live_lines=live_goal_lines if is_live else []
                ),
                corners=CornersPrediction(
                    expected_total=exp_corners_final,
                    over_8_5_pct=over_8_5_cn,
                    over_9_5_pct=over_9_5_cn,
                    over_10_5_pct=over_10_5_cn,
                    human_verdict=verdicts["corners"],
                    is_live=is_live,
                    current_corners=p_res["corners"].get("current_corners") if is_live else None,
                    expected_remaining_corners=p_res["corners"].get("expected_remaining_corners") if is_live else None,
                    no_more_corners_pct=p_res["corners"].get("no_more_corners_pct") if is_live else None,
                    more_corners_pct=p_res["corners"].get("more_corners_pct") if is_live else None,
                    live_corners_lines=live_corner_lines if is_live else []
                ),
                cards=CardsPrediction(
                    expected_total=p_res["cards"]["expected_total"],
                    over_3_5_pct=p_res["cards"]["over_3_5_pct"],
                    over_4_5_pct=p_res["cards"]["over_4_5_pct"],
                    red_card_risk_pct=p_res["cards"]["red_card_risk_pct"],
                    human_verdict=verdicts["cards"]
                )
            ),
            chart_data=ChartData(
                goals_distribution=[
                    GoalDistributionItem(goals=item["goals"], probability=item["probability"])
                    for item in cons_goals["goals_distribution"]
                ],
                top_scores=[
                    TopScoreItem(score=s["score"], probability=s["probability"])
                    for s in cons_goals["top_scores"]
                ]
            ),
            key_factors=key_factors
        )

        return response

ensemble_engine = MetaEnsembleEngine()
