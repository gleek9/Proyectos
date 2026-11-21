"""
Módulo de Machine Learning Tabular: XGBoost / LightGBM.
Procesa el vector de características avanzadas y genera probabilidades 1X2 y líneas Over/Under.
"""
import os
import logging
import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Tuple
import xgboost as xgb
try:
    import lightgbm as lgb
    _HAS_LGB = True
except ImportError:
    _HAS_LGB = False
from sklearn.preprocessing import StandardScaler
from backend.app.schemas.match import MatchRawFeatures
from backend.app.models.dixon_coles_mle import dixon_coles_mle
from backend.app.models.poisson import (
    parse_elapsed_minute, calculate_remaining_goal_ratio, get_competition_parameters,
    parse_live_score, condition_1x2_on_live_state, poisson_model, get_competition_rho,
)

logger = logging.getLogger(__name__)

# Definición de nombres de características tabulares enriquecidas (Katakuri v5: 44 features)
FEATURE_NAMES = [
    "elo_diff",
    "home_elo",
    "away_elo",
    "home_win_rate_5",
    "away_win_rate_5",
    "home_goal_diff",
    "away_goal_diff",
    "delta_goal_diff",
    "home_goals_scored",
    "away_goals_scored",
    "home_goals_conceded",
    "away_goals_conceded",
    "home_split_scored",
    "home_split_conceded",
    "away_split_scored",
    "away_split_conceded",
    "home_sot_avg",
    "away_sot_avg",
    "home_sot_against",
    "away_sot_against",
    "h2h_home_win_ratio",
    "h2h_away_win_ratio",
    "h2h_draw_ratio",
    "h2h_avg_goals",
    "home_advantage",
    "expected_corners_sum",
    "corners_conceded_sum",
    "expected_cards_sum",
    "rest_diff",
    "poisson_lambda_h",
    "poisson_mu_a",
    "poisson_p_home",
    "poisson_p_draw",
    "poisson_p_away",
    "home_shots_avg",
    "away_shots_avg",
    "home_shots_against",
    "away_shots_against",
    "shot_efficiency_diff",
    "fouls_sum",
    "ht_goal_diff_delta",
    "referee_cards_factor",
    "dc_mle_lambda_h",
    "dc_mle_mu_a",
]

class TabularPredictor:
    def __init__(self, weights_dir: str = "backend/weights"):
        self.weights_dir = weights_dir
        self.xgb_model_path = os.path.join(self.weights_dir, "xgb_1x2.json")
        self.lgb_model_path = os.path.join(self.weights_dir, "lgb_1x2.txt")
        self.model = None
        self.lgb_model = None
        self._ensure_model_ready()

    def _ensure_model_ready(self):
        """Carga XGBoost + LightGBM guardados o inicializa el modelo base calibrado."""
        os.makedirs(self.weights_dir, exist_ok=True)
        if _HAS_LGB and os.path.exists(self.lgb_model_path):
            try:
                booster_lgb = lgb.Booster(model_file=self.lgb_model_path)
                if booster_lgb.num_feature() == len(FEATURE_NAMES):
                    self.lgb_model = booster_lgb
            except Exception as e:
                logger.warning(f"No se pudo cargar LightGBM: {e}")

        if os.path.exists(self.xgb_model_path):
            try:
                booster = xgb.Booster()
                booster.load_model(self.xgb_model_path)
                # Verificar compatibilidad exacta de dimensión de features v5
                if booster.num_features() == len(FEATURE_NAMES):
                    self.model = booster
                    logger.info("Modelo tabular XGBoost (+LightGBM si disponible) cargado exitosamente desde disco.")
                    return
                logger.info(
                    f"Pesos XGBoost en disco ({booster.num_features()}F) desactualizados frente a {len(FEATURE_NAMES)}F. Reentrenando..."
                )
            except Exception as e:
                logger.warning(f"No se pudo cargar el modelo existente: {e}. Reentrenando base...")

        self._train_and_save_baseline_model()
        if _HAS_LGB and os.path.exists(self.lgb_model_path) and self.lgb_model is None:
            try:
                booster_lgb = lgb.Booster(model_file=self.lgb_model_path)
                if booster_lgb.num_feature() == len(FEATURE_NAMES):
                    self.lgb_model = booster_lgb
            except Exception:
                pass

    def _train_and_save_baseline_model(self):
        """
        Entrena un modelo XGBoost multi-clase calibrado sobre el historial real de partidos
        o fallback de regularización si la BD está en inicialización.
        """
        try:
            from backend.app.analytics.train_models import train_and_save_all_models
            train_and_save_all_models(self.weights_dir)
            if os.path.exists(self.xgb_model_path):
                self.model = xgb.Booster()
                self.model.load_model(self.xgb_model_path)
                logger.info("Modelo XGBoost entrenado exitosamente con datos históricos reales.")
                return
        except Exception as e:
            logger.warning(f"Entrenamiento con dataset histórico derivó a contingencia: {e}")

        logger.info("Entrenando modelo tabular XGBoost base calibrado de contingencia...")
        np.random.seed(42)
        n_samples = 4000

        # Simular features representativas (23 features completas)
        elo_h_sim = np.random.normal(1680.0, 110.0, n_samples)
        elo_a_sim = np.random.normal(1680.0, 110.0, n_samples)
        elo_diff_sim = (elo_h_sim - elo_a_sim + 65.0) / 100.0
        home_elo_sc = elo_h_sim / 1000.0
        away_elo_sc = elo_a_sim / 1000.0

        home_win_rates = np.random.uniform(0.1, 0.9, n_samples)
        away_win_rates = np.random.uniform(0.1, 0.9, n_samples)
        home_scored = np.random.uniform(0.8, 3.2, n_samples)
        away_scored = np.random.uniform(0.6, 2.8, n_samples)
        home_conceded = np.random.uniform(0.6, 2.5, n_samples)
        away_conceded = np.random.uniform(0.8, 2.9, n_samples)

        home_diff = home_scored - home_conceded
        away_diff = away_scored - away_conceded
        delta_diff = home_diff - away_diff

        home_sot = home_scored * 2.8 + np.random.normal(0.5, 0.6, n_samples)
        away_sot = away_scored * 2.6 + np.random.normal(0.4, 0.6, n_samples)

        h2h_home = np.random.uniform(0.1, 0.6, n_samples)
        h2h_away = np.random.uniform(0.1, 0.5, n_samples)
        h2h_draw = 1.0 - h2h_home - h2h_away
        h2h_goals = np.random.uniform(1.8, 3.8, n_samples)

        home_absences = np.random.poisson(1.2, n_samples)
        away_absences = np.random.poisson(1.3, n_samples)
        home_adv = np.ones(n_samples) * 1.15

        corners = home_scored * 2.2 + away_scored * 2.0 + np.random.normal(0, 1.0, n_samples)
        cards = np.random.uniform(2.5, 6.5, n_samples)

        X_sim = np.column_stack([
            elo_diff_sim, home_elo_sc, away_elo_sc,
            home_win_rates, away_win_rates, home_diff, away_diff, delta_diff,
            home_scored, away_scored, home_conceded, away_conceded,
            home_scored * 1.08, home_conceded * 0.92, away_scored * 0.92, away_conceded * 1.08,
            home_sot, away_sot, away_sot * 0.95, home_sot * 0.95,
            h2h_home, h2h_away, h2h_draw, h2h_goals,
            home_adv,
            corners, corners * 0.95, cards,
            np.zeros(n_samples),
            np.clip(home_scored * 1.05, 0.6, 3.0), np.clip(away_scored * 0.95, 0.5, 2.8),
            np.full(n_samples, 0.44), np.full(n_samples, 0.25), np.full(n_samples, 0.31),
            home_sot * 2.6, away_sot * 2.6, away_sot * 2.5, home_sot * 2.5,
            np.zeros(n_samples), np.full(n_samples, 22.5), np.zeros(n_samples), np.ones(n_samples),
            np.clip(home_scored * 1.05, 0.6, 3.0), np.clip(away_scored * 0.95, 0.5, 2.8),
        ])

        # Generar etiquetas 0: Home Win, 1: Draw, 2: Away Win basadas en física de partidos
        # Score latent
        score_diff = delta_diff * 0.8 + (home_win_rates - away_win_rates) * 1.2 + 0.35  # ventaja localía
        score_diff -= (home_absences * 0.12 - away_absences * 0.12)

        p_home = 1.0 / (1.0 + np.exp(-1.3 * (score_diff - 0.15)))
        p_away = 1.0 / (1.0 + np.exp(1.3 * (score_diff + 0.15)))
        p_draw = np.maximum(0.18, 1.0 - p_home - p_away)

        # Normalizar
        prob_sum = p_home + p_draw + p_away
        p_home /= prob_sum
        p_draw /= prob_sum
        p_away /= prob_sum

        y_sim = np.zeros(n_samples, dtype=int)
        for i in range(n_samples):
            y_sim[i] = np.random.choice([0, 1, 2], p=[p_home[i], p_draw[i], p_away[i]])

        dtrain = xgb.DMatrix(X_sim, label=y_sim, feature_names=FEATURE_NAMES)
        params = {
            "objective": "multi:softprob",
            "num_class": 3,
            "max_depth": 4,
            "learning_rate": 0.08,
            "subsample": 0.85,
            "colsample_bytree": 0.85,
            "eval_metric": "mlogloss",
            "seed": 42
        }

        self.model = xgb.train(params, dtrain, num_boost_round=120)
        self.model.save_model(self.xgb_model_path)
        logger.info(f"Modelo XGBoost entrenado y guardado en {self.xgb_model_path}")

    def extract_features(self, raw: MatchRawFeatures) -> np.ndarray:
        """Convierte MatchRawFeatures en el vector numérico 1D exacto requerido."""
        h = raw.home_stats
        a = raw.away_stats
        h2h = raw.h2h

        home_diff = h.avg_goals_scored - h.avg_goals_conceded
        away_diff = a.avg_goals_scored - a.avg_goals_conceded
        delta_diff = home_diff - away_diff

        # Suavizado Bayesiano de H2H (evita extremos 0%/100% con 1-2 partidos previos)
        tot_h2h = int(getattr(h2h, "total_matches_analyzed", 0) or 0)
        prior_n = 4.0
        h2h_h_ratio = (float(h2h.home_team_wins) + prior_n * 0.44) / (tot_h2h + prior_n)
        h2h_d_ratio = (float(h2h.draws) + prior_n * 0.25) / (tot_h2h + prior_n)
        h2h_a_ratio = (float(h2h.away_team_wins) + prior_n * 0.31) / (tot_h2h + prior_n)
        if tot_h2h > 0:
            h2h_avg_goals = h2h.avg_total_goals_h2h
        else:
            league_avg_g, _, _ = get_competition_parameters(getattr(raw, "competition", "General"))
            h2h_avg_goals = league_avg_g * 2.0

        # Normalización defensiva de win_rate_last_5 (fracciones vs porcentajes)
        h_wr = float(h.win_rate_last_5)
        if h_wr > 1.0:
            h_wr /= 100.0
        h_wr = float(np.clip(h_wr, 0.0, 1.0))

        a_wr = float(a.win_rate_last_5)
        if a_wr > 1.0:
            a_wr /= 100.0
        a_wr = float(np.clip(a_wr, 0.0, 1.0))

        # Ratings Elo
        elo_h = getattr(h, "elo_rating", None)
        elo_a = getattr(a, "elo_rating", None)
        if elo_h is None or elo_a is None:
            try:
                from backend.app.services.league_database import league_db
                if elo_h is None:
                    t_h = league_db.normalize_team(raw.home_team)
                    if t_h and t_h.elo_rating:
                        elo_h = t_h.elo_rating
                if elo_a is None:
                    t_a = league_db.normalize_team(raw.away_team)
                    if t_a and t_a.elo_rating:
                        elo_a = t_a.elo_rating
            except Exception:
                pass
        elo_h = float(elo_h or 1600.0)
        elo_a = float(elo_a or 1600.0)
        elo_diff = (elo_h - elo_a + 50.0) / 100.0
        home_elo_scaled = elo_h / 1000.0
        away_elo_scaled = elo_a / 1000.0

        home_sot = float(getattr(h, "avg_shots_target_for", None) or 5.0)
        away_sot = float(getattr(a, "avg_shots_target_for", None) or 4.5)
        home_sot_against = float(getattr(h, "avg_shots_target_against", None) or 4.5)
        away_sot_against = float(getattr(a, "avg_shots_target_against", None) or 4.5)

        h_split_sc = float(getattr(h, "home_goals_scored", None) or h.avg_goals_scored)
        h_split_co = float(getattr(h, "home_goals_conceded", None) or h.avg_goals_conceded)
        a_split_sc = float(getattr(a, "away_goals_scored", None) or a.avg_goals_scored)
        a_split_co = float(getattr(a, "away_goals_conceded", None) or a.avg_goals_conceded)

        h_cn_conc = float(getattr(h, "avg_corners_conceded", None) or 4.5)
        a_cn_conc = float(getattr(a, "avg_corners_conceded", None) or 4.8)

        h_rest = float(getattr(h, "rest_days", None) or 7.0)
        a_rest = float(getattr(a, "rest_days", None) or 7.0)
        rest_diff = h_rest - a_rest

        # Señal estructural de Poisson Dixon-Coles y parámetros v5 (tiros, faltas, HT, árbitro, MLE)
        comp_name = getattr(raw, "competition", "General")
        _, comp_home_adv, _ = get_competition_parameters(comp_name)
        lam_h, mu_a = poisson_model._calculate_lambdas(raw)
        rho = get_competition_rho(comp_name)
        p_mat = poisson_model.evaluate_matrix_goals(lam_h, mu_a, rho=rho)
        p_w = p_mat["winner_probs"]

        h_shots_for = float(getattr(h, "avg_shots_for", None) or (home_sot * 2.65))
        a_shots_for = float(getattr(a, "avg_shots_for", None) or (away_sot * 2.65))
        h_shots_ag = float(getattr(h, "avg_shots_against", None) or (home_sot_against * 2.65))
        a_shots_ag = float(getattr(a, "avg_shots_against", None) or (away_sot_against * 2.65))
        eff_h = home_sot / max(1.0, h_shots_for)
        eff_a = away_sot / max(1.0, a_shots_for)
        shot_eff_diff = float(eff_h - eff_a)

        h_fouls = float(getattr(h, "avg_fouls_for", None) or 11.2)
        a_fouls = float(getattr(a, "avg_fouls_for", None) or 11.3)
        fouls_sum = float(h_fouls + a_fouls)

        ht_h = float(getattr(h, "ht_goal_diff_avg", None) or (home_diff * 0.45))
        ht_a = float(getattr(a, "ht_goal_diff_avg", None) or (away_diff * 0.45))
        ht_diff_delta = float(ht_h - ht_a)

        ref_cards = getattr(raw, "referee_avg_cards", None)
        ref_factor = float(ref_cards) / 4.30 if (ref_cards is not None and float(ref_cards) > 0) else 1.0

        mle_res = dixon_coles_mle.get_match_lambdas(comp_name, raw.home_team, raw.away_team)
        mle_lh, mle_ma = (mle_res[0], mle_res[1]) if mle_res is not None else (float(lam_h), float(mu_a))

        feat = [
            float(elo_diff),
            float(home_elo_scaled),
            float(away_elo_scaled),
            h_wr,
            a_wr,
            float(home_diff),
            float(away_diff),
            float(delta_diff),
            float(h.avg_goals_scored),
            float(a.avg_goals_scored),
            float(h.avg_goals_conceded),
            float(a.avg_goals_conceded),
            h_split_sc,
            h_split_co,
            a_split_sc,
            a_split_co,
            float(home_sot),
            float(away_sot),
            home_sot_against,
            away_sot_against,
            float(h2h_h_ratio),
            float(h2h_a_ratio),
            float(h2h_d_ratio),
            float(h2h_avg_goals),
            float(comp_home_adv),
            float(h.avg_corners + a.avg_corners),
            float(h_cn_conc + a_cn_conc),
            float(h.avg_cards + a.avg_cards),
            float(rest_diff),
            float(lam_h),
            float(mu_a),
            float(p_w["home_win"]) / 100.0,
            float(p_w["draw"]) / 100.0,
            float(p_w["away_win"]) / 100.0,
            h_shots_for,
            a_shots_for,
            h_shots_ag,
            a_shots_ag,
            shot_eff_diff,
            fouls_sum,
            ht_diff_delta,
            ref_factor,
            float(mle_lh),
            float(mle_ma),
        ]
        return np.array([feat], dtype=np.float32)

    def predict(self, raw: MatchRawFeatures) -> Dict:
        """Inferencia tabular híbrida (XGBoost + LightGBM si está entrenado)."""
        features_vec = self.extract_features(raw)
        dmatrix = xgb.DMatrix(features_vec, feature_names=FEATURE_NAMES)
        preds = self.model.predict(dmatrix)[0]  # Array de longitud 3: [P(Home), P(Draw), P(Away)]

        if self.lgb_model is not None:
            try:
                lgb_preds = self.lgb_model.predict(features_vec)[0]
                if len(lgb_preds) == 3 and float(np.sum(lgb_preds)) > 0:
                    preds = 0.55 * preds + 0.45 * lgb_preds
            except Exception as e:
                logger.debug(f"Fallback solo XGBoost en inferencia LightGBM: {e}")

        p_home = float(preds[0])
        p_draw = float(preds[1])
        p_away = float(preds[2])

        # Expectativas agregadas de soporte tabular con shrinkage Bayesiano ancladas al torneo (volumen de 90')
        comp_name = getattr(raw, "competition", "General")
        league_avg_g, home_adv, _ = get_competition_parameters(comp_name)
        w_tab = 0.65
        tot_h = w_tab * ((raw.home_stats.avg_goals_scored + raw.away_stats.avg_goals_conceded) / 2.0) + (1.0 - w_tab) * league_avg_g
        tot_a = w_tab * ((raw.away_stats.avg_goals_scored + raw.home_stats.avg_goals_conceded) / 2.0) + (1.0 - w_tab) * league_avg_g
        tot_goals_est = float(tot_h * 1.03 + tot_a * 0.97)  # Ajuste por localía
        tot_goals_est = float(np.clip(tot_goals_est, 1.80, league_avg_g * 2.0 * 1.20))

        is_live = getattr(raw, "is_live", False)
        rem_goals_tabular = None
        no_more_p_tab = None
        more_p_tab = None

        if is_live:
            # Condicionamiento temporal in-play: el 1X2 converge al marcador real a medida que se agota el tiempo
            elapsed_min = parse_elapsed_minute(getattr(raw, "live_minute", None))
            time_rem_ratio = calculate_remaining_goal_ratio(elapsed_min)
            gh, ga = parse_live_score(getattr(raw, "live_score", None))
            reds_h = int(getattr(raw, "live_red_cards_home", 0) or 0)
            reds_a = int(getattr(raw, "live_red_cards_away", 0) or 0)

            p_home, p_draw, p_away = condition_1x2_on_live_state(
                p_home, p_draw, p_away,
                total_goals_90=tot_goals_est,
                curr_gh=gh, curr_ga=ga,
                time_rem_ratio=time_rem_ratio,
                reds_h=reds_h, reds_a=reds_a,
            )

            current_total = gh + ga
            rem_goals_tabular = float(tot_goals_est * time_rem_ratio * 0.90)
            tot_goals_est = max(float(current_total), current_total + rem_goals_tabular)
            if time_rem_ratio > 0:
                no_more_p_tab = float(np.clip(np.exp(-rem_goals_tabular), 0.02, 0.99))
            else:
                no_more_p_tab = 1.0  # Partido finalizado
            more_p_tab = float(1.0 - no_more_p_tab)

        # Asegurar suma = 1.0
        tot = p_home + p_draw + p_away
        p_home /= tot
        p_draw /= tot
        p_away /= tot

        if not is_live:
            # Calibración de temperatura equilibrada post-regularización (Katakuri v4.1: T=1.02)
            T = 1.02
            log_p = np.log(np.clip([p_home, p_draw, p_away], 1e-6, 1.0)) / T
            e_p = np.exp(log_p - np.max(log_p))
            e_sum = np.sum(e_p)
            p_home, p_draw, p_away = float(e_p[0] / e_sum), float(e_p[1] / e_sum), float(e_p[2] / e_sum)
            if p_draw < 0.10:
                deficit = 0.10 - p_draw
                p_draw = 0.10
                if p_home >= p_away:
                    p_home = max(0.04, p_home - deficit)
                else:
                    p_away = max(0.04, p_away - deficit)
                tot = p_home + p_draw + p_away
                p_home /= tot
                p_draw /= tot
                p_away /= tot

        # Probabilidad de Over 2.5 calculada mediante función logística sigmoide calibrada al volumen real
        over_2_5_pct = float(1.0 / (1.0 + np.exp(-1.60 * (tot_goals_est - 2.50))) * 100.0)
        over_2_5_pct = float(np.clip(over_2_5_pct, 15.0, 92.0))

        return {
            "model_name": "xgboost_tabular",
            "winner_probs": {
                "home_win": round(p_home * 100, 2),
                "draw": round(p_draw * 100, 2),
                "away_win": round(p_away * 100, 2)
            },
            "goals_expected": round(tot_goals_est, 2),
            "over_2_5_pct": round(over_2_5_pct, 2),
            "live_expected_remaining_goals": round(rem_goals_tabular, 2) if rem_goals_tabular is not None else None,
            "live_no_more_goals_pct": round(no_more_p_tab * 100, 1) if no_more_p_tab is not None else None,
            "live_more_goals_pct": round(more_p_tab * 100, 1) if more_p_tab is not None else None
        }

tabular_predictor = TabularPredictor()
