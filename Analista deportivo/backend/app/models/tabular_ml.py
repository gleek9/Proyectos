"""
Módulo de Machine Learning Tabular: XGBoost / LightGBM.
Procesa el vector de características avanzadas y genera probabilidades 1X2 y líneas Over/Under.
"""
import os
import logging
import numpy as np
import pandas as pd
from typing import Dict, List, Tuple
import xgboost as xgb
from sklearn.preprocessing import StandardScaler
from backend.app.schemas.match import MatchRawFeatures
from backend.app.models.poisson import (
    parse_elapsed_minute, calculate_remaining_goal_ratio, get_competition_parameters,
    parse_live_score, condition_1x2_on_live_state,
)

logger = logging.getLogger(__name__)

# Definición de nombres de características tabulares
FEATURE_NAMES = [
    "home_win_rate_5",
    "away_win_rate_5",
    "home_goal_diff",
    "away_goal_diff",
    "delta_goal_diff",
    "home_goals_scored",
    "away_goals_scored",
    "home_goals_conceded",
    "away_goals_conceded",
    "h2h_home_win_ratio",
    "h2h_away_win_ratio",
    "h2h_draw_ratio",
    "h2h_avg_goals",
    "home_absences",
    "away_absences",
    "home_advantage",
    "expected_corners_sum",
    "expected_cards_sum"
]

class TabularPredictor:
    def __init__(self, weights_dir: str = "backend/weights"):
        self.weights_dir = weights_dir
        self.xgb_model_path = os.path.join(self.weights_dir, "xgb_1x2.json")
        self.model = None
        self._ensure_model_ready()

    def _ensure_model_ready(self):
        """Carga el modelo guardado o inicializa y entrena el modelo base calibrado."""
        os.makedirs(self.weights_dir, exist_ok=True)
        if os.path.exists(self.xgb_model_path):
            try:
                self.model = xgb.Booster()
                self.model.load_model(self.xgb_model_path)
                logger.info("Modelo XGBoost cargado exitosamente desde disco.")
                return
            except Exception as e:
                logger.warning(f"No se pudo cargar el modelo existente: {e}. Reentrenando base...")

        self._train_and_save_baseline_model()

    def _train_and_save_baseline_model(self):
        """
        Entrena un modelo XGBoost multi-clase calibrado sobre distribuciones de dominio
        futbolístico representativas (fuerza de ataque/defensa, H2H y localía).
        """
        logger.info("Entrenando modelo tabular XGBoost base calibrado...")
        np.random.seed(42)
        n_samples = 4000

        # Simular features representativas
        home_win_rates = np.random.uniform(0.1, 0.9, n_samples)
        away_win_rates = np.random.uniform(0.1, 0.9, n_samples)
        home_scored = np.random.uniform(0.8, 3.2, n_samples)
        away_scored = np.random.uniform(0.6, 2.8, n_samples)
        home_conceded = np.random.uniform(0.6, 2.5, n_samples)
        away_conceded = np.random.uniform(0.8, 2.9, n_samples)

        home_diff = home_scored - home_conceded
        away_diff = away_scored - away_conceded
        delta_diff = home_diff - away_diff

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
            home_win_rates, away_win_rates, home_diff, away_diff, delta_diff,
            home_scored, away_scored, home_conceded, away_conceded,
            h2h_home, h2h_away, h2h_draw, h2h_goals,
            home_absences, away_absences, home_adv,
            corners, cards
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

        if h2h.total_matches_analyzed > 0:
            tot_h2h = h2h.total_matches_analyzed
            h2h_h_ratio = h2h.home_team_wins / tot_h2h
            h2h_a_ratio = h2h.away_team_wins / tot_h2h
            h2h_d_ratio = h2h.draws / tot_h2h
            h2h_avg_goals = h2h.avg_total_goals_h2h
        else:
            # Sin H2H real: valores neutros (medias de la distribución de entrenamiento y media goleadora de la liga)
            h2h_h_ratio, h2h_a_ratio, h2h_d_ratio = 0.35, 0.35, 0.30
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

        # Ventaja de localía calibrada al torneo específico
        _, comp_home_adv, _ = get_competition_parameters(getattr(raw, "competition", "General"))

        feat = [
            h_wr,
            a_wr,
            float(home_diff),
            float(away_diff),
            float(delta_diff),
            float(h.avg_goals_scored),
            float(a.avg_goals_scored),
            float(h.avg_goals_conceded),
            float(a.avg_goals_conceded),
            float(h2h_h_ratio),
            float(h2h_a_ratio),
            float(h2h_d_ratio),
            float(h2h_avg_goals),
            float(len(h.key_absences)),
            float(len(a.key_absences)),
            float(comp_home_adv),  # Ventaja de localía por torneo
            float(h.avg_corners + a.avg_corners),
            float(h.avg_cards + a.avg_cards)
        ]
        return np.array([feat], dtype=np.float32)

    def predict(self, raw: MatchRawFeatures) -> Dict:
        """Inferencia con XGBoost."""
        features_vec = self.extract_features(raw)
        dmatrix = xgb.DMatrix(features_vec, feature_names=FEATURE_NAMES)
        preds = self.model.predict(dmatrix)[0]  # Array de longitud 3: [P(Home), P(Draw), P(Away)]

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
            rem_goals_tabular = float(tot_goals_est * time_rem_ratio * 0.95)
            tot_goals_est = max(float(current_total), current_total + rem_goals_tabular)
            if time_rem_ratio > 0:
                no_more_p_tab = float(np.clip(np.exp(-rem_goals_tabular), 0.02, 0.95))
            else:
                no_more_p_tab = 1.0  # Partido finalizado
            more_p_tab = float(1.0 - no_more_p_tab)

        # Asegurar suma = 1.0
        tot = p_home + p_draw + p_away
        p_home /= tot
        p_draw /= tot
        p_away /= tot

        if not is_live:
            # Calibración de temperatura para regularizar polarización excesiva en rachas asimétricas
            T = 1.35
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
