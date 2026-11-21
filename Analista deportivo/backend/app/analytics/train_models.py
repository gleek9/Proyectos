"""
Pipeline de Entrenamiento Supervisado con Datos Históricos Reales (Katakuri v4.1).
Entrena XGBoost y PyTorch LSTM exclusivamente sobre la secuencia cronológica real
de los partidos previos al corte temporal (TRAIN_CUTOFF_DATE = '2025-01-01'),
reservando todos los partidos >= 2025-01-01 como conjunto Out-of-Sample puro
para la validación Walk-Forward (cero look-ahead bias, cero fuga de datos).
Genera y guarda:
- backend/weights/xgb_1x2.json (XGBoost regularizado con Early Stopping)
- backend/weights/lstm_momentum.pt (PyTorch LSTM secuencial con Early Stopping en validación)
"""
import copy
import json
import os
import logging
import numpy as np
import torch
import torch.nn as nn
import xgboost as xgb
try:
    import lightgbm as lgb
    _HAS_LGB = True
except ImportError:
    _HAS_LGB = False
from collections import defaultdict
from scipy.optimize import minimize
from backend.app.db import SessionLocal, HistoricalMatch, League
from backend.app.models.dixon_coles_mle import dixon_coles_mle
from backend.app.models.lstm_net import MatchSequenceLSTM, LSTMPredictor, TIMESTEPS, FEATURES_PER_STEP
from backend.app.models.poisson import poisson_model
from backend.app.models.tabular_ml import FEATURE_NAMES, TabularPredictor
from backend.app.services.real_data_loader import (
    get_honest_initial_elo_map,
    build_point_in_time_match_features,
    calculate_elo_update,
)

logger = logging.getLogger(__name__)

# Corte temporal estricto: todo partido >= TRAIN_CUTOFF_DATE queda reservado 100% fuera de muestra (Out-of-Sample)
TRAIN_CUTOFF_DATE = "2025-01-01"


def _rps_batch(probs: np.ndarray, targets: np.ndarray) -> float:
    """Calcula el Ranked Probability Score medio sobre probabilidades [N, 3] y targets {0, 1, 2}."""
    p = np.clip(np.asarray(probs, dtype=np.float64), 1e-6, 1.0)
    p = p / p.sum(axis=1, keepdims=True)
    y_oh = np.eye(3, dtype=np.float64)[targets]
    cum_p = np.cumsum(p[:, :2], axis=1)
    cum_y = np.cumsum(y_oh[:, :2], axis=1)
    return float(np.mean(0.5 * np.sum((cum_p - cum_y) ** 2, axis=1)))


def build_training_dataset(cutoff_date: str = TRAIN_CUTOFF_DATE):
    """
    Construye matrices de entrenamiento tabulares (44 features) y tensoriales secuenciales (10x14)
    a partir de la cronología real de partidos en la base de datos local,
    utilizando exactamente el mismo pipeline Point-in-Time de producción (cero fugas de datos).
    """
    db = SessionLocal()
    saved_mle_leagues = copy.deepcopy(dixon_coles_mle.leagues)
    saved_mle_cutoff = dixon_coles_mle.cutoff_date
    try:
        matches = db.query(HistoricalMatch).order_by(
            HistoricalMatch.match_date.asc(),
            HistoricalMatch.id.asc()
        ).all()
        leagues = {l.code: l for l in db.query(League).all()}
        logger.info(f"Procesando {len(matches)} partidos reales cronológicos (corte entrenamiento < {cutoff_date})...")

        base_elo_map = get_honest_initial_elo_map()
        elo_tracker = defaultdict(lambda: 1600.0, base_elo_map)
        team_history = defaultdict(list)
        team_last_season = {}
        ref_history = defaultdict(list)
        past_matches_by_league = defaultdict(list)

        # Snapshots causales de Dixon-Coles MLE para evitar look-ahead en features GBDT
        dixon_coles_mle.leagues = {}
        mle_stages = [s for s in ("2023-07-01", "2024-07-01") if not cutoff_date or s < cutoff_date]
        stage_idx = 0

        X_tab_list = []
        y_tab_list = []
        y_goals_list = []
        p_poisson_list = []

        X_seq_home_list = []
        X_seq_away_list = []

        for m in matches:
            m_date = m.match_date or ""
            # Detener recolección de muestras de entrenamiento al llegar al corte Out-of-Sample
            if cutoff_date and m_date >= cutoff_date:
                break

            while stage_idx < len(mle_stages) and m_date >= mle_stages[stage_idx]:
                stage_label = mle_stages[stage_idx]
                fitted_stage = {}
                for l_code, lg_rows in past_matches_by_league.items():
                    res = dixon_coles_mle.fit_league(lg_rows)
                    if res is not None:
                        fitted_stage[l_code] = res
                dixon_coles_mle.leagues = fitted_stage
                dixon_coles_mle.cutoff_date = stage_label
                logger.info(f"Snapshot MLE causal pre-{stage_label} ajustado en {len(fitted_stage)} ligas.")
                stage_idx += 1

            h_name = m.home_team
            a_name = m.away_team
            cur_season = getattr(m, "season", "2024-25")

            # Regresión inter-temporada honesta hacia la media neutral de liga (1650.0)
            for club in (h_name, a_name):
                prev_s = team_last_season.get(club)
                if prev_s is not None and prev_s != cur_season:
                    elo_tracker[club] = 0.85 * elo_tracker[club] + 0.15 * 1650.0
                team_last_season[club] = cur_season

            h_hist = team_history[h_name]
            a_hist = team_history[a_name]

            cur_elo_h = elo_tracker[h_name]
            cur_elo_a = elo_tracker[a_name]

            ref_name = getattr(m, "referee", None)
            ref_avg = None
            if ref_name and len(ref_history[ref_name]) >= 3:
                recent_ref = ref_history[ref_name][-15:]
                ref_avg = round(sum(recent_ref) / len(recent_ref), 2)

            # Entrenar en partidos donde ambos clubes tienen historial previo conocido
            if len(h_hist) >= 3 and len(a_hist) >= 3:
                l_obj = leagues.get(m.league_code)
                comp_name = l_obj.name if l_obj else m.league_code
                def_goals = l_obj.avg_goals if l_obj else 1.35
                def_corners = l_obj.avg_corners if l_obj else 9.5
                def_cards = l_obj.avg_cards if l_obj else 4.0

                feats = build_point_in_time_match_features(
                    h_name=h_name,
                    a_name=a_name,
                    comp_name=comp_name,
                    cur_elo_h=cur_elo_h,
                    cur_elo_a=cur_elo_a,
                    h_hist=h_hist,
                    a_hist=a_hist,
                    def_goals=def_goals,
                    def_corners=def_corners,
                    def_cards=def_cards,
                    match_date=m.match_date,
                    referee_name=ref_name,
                    referee_avg_cards=ref_avg,
                )

                # 1. Vector tabular exacto de producción (44 features enriquecidas)
                tab_row = TabularPredictor.extract_features(None, feats)[0]
                X_tab_list.append(tab_row)
                p_pois = np.clip(tab_row[31:34].astype(np.float64), 1e-4, 1.0)
                p_pois = p_pois / p_pois.sum()
                p_poisson_list.append(p_pois)

                # Etiqueta: 0 = Local, 1 = Empate, 2 = Visitante
                y_label = 0 if m.home_goals > m.away_goals else (1 if m.home_goals == m.away_goals else 2)
                y_tab_list.append(y_label)
                y_goals_list.append(float(m.home_goals + m.away_goals))

                # 2. Secuencias exactas de producción para RichLSTM (TIMESTEPS=10, FEATURES_PER_STEP=11)
                seq_h = LSTMPredictor._build_sequence_tensor(
                    None,
                    feats.home_stats.last_matches,
                    feats.home_stats.avg_goals_scored,
                    feats.home_stats.avg_goals_conceded,
                    team_elo=cur_elo_h,
                    opp_matchup_elo=cur_elo_a,
                ).squeeze(0).numpy()
                seq_a = LSTMPredictor._build_sequence_tensor(
                    None,
                    feats.away_stats.last_matches,
                    feats.away_stats.avg_goals_scored,
                    feats.away_stats.avg_goals_conceded,
                    team_elo=cur_elo_a,
                    opp_matchup_elo=cur_elo_h,
                ).squeeze(0).numpy()

                X_seq_home_list.append(seq_h)
                X_seq_away_list.append(seq_a)

            # Actualizar historial y Elo cronológicamente ESTRICTAMENTE DESPUÉS del partido
            new_h, new_a = calculate_elo_update(cur_elo_h, cur_elo_a, m.home_goals, m.away_goals)
            elo_tracker[h_name] = new_h
            elo_tracker[a_name] = new_a

            cn_tot = (m.corners_home or 0) + (m.corners_away or 0)
            cr_tot = (m.cards_home or 0) + (m.cards_away or 0)
            ht_h = getattr(m, "ht_home_goals", None)
            ht_a = getattr(m, "ht_away_goals", None)
            ht_diff_h = float(ht_h - ht_a) if (ht_h is not None and ht_a is not None) else None
            ht_diff_a = (-ht_diff_h) if ht_diff_h is not None else None
            hs_val = getattr(m, "home_shots", None)
            as_val = getattr(m, "away_shots", None)
            hf_val = getattr(m, "home_fouls", None)
            af_val = getattr(m, "away_fouls", None)

            team_history[h_name].append({
                "opp": a_name, "opp_elo": cur_elo_a, "was_home": True, "date": m.match_date,
                "gf": m.home_goals, "ga": m.away_goals,
                "res": "W" if m.home_goals > m.away_goals else ("D" if m.home_goals == m.away_goals else "L"),
                "hst": m.home_shots_target or 4, "ast": m.away_shots_target or 4,
                "hs": hs_val, "hf": hf_val, "ht_diff": ht_diff_h,
                "cn": m.corners_home or 5, "cn_opp": m.corners_away or 4,
                "cr": m.cards_home or 2, "cn_tot": cn_tot, "cr_tot": cr_tot
            })
            team_history[a_name].append({
                "opp": h_name, "opp_elo": cur_elo_h, "was_home": False, "date": m.match_date,
                "gf": m.away_goals, "ga": m.home_goals,
                "res": "W" if m.away_goals > m.home_goals else ("D" if m.away_goals == m.home_goals else "L"),
                "hst": m.away_shots_target or 4, "ast": m.home_shots_target or 4,
                "hs": as_val, "hf": af_val, "ht_diff": ht_diff_a,
                "cn": m.corners_away or 4, "cn_opp": m.corners_home or 5,
                "cr": m.cards_away or 2, "cn_tot": cn_tot, "cr_tot": cr_tot
            })
            if ref_name:
                ref_history[ref_name].append(float(cr_tot))
            past_matches_by_league[m.league_code].append({
                "home": h_name, "away": a_name,
                "hg": m.home_goals, "ag": m.away_goals,
                "date": m.match_date,
            })

        logger.info(f"Dataset cronológico pre-{cutoff_date} construido con {len(X_tab_list)} muestras puras.")
        return (
            np.array(X_tab_list, dtype=np.float32),
            np.array(y_tab_list, dtype=int),
            np.array(y_goals_list, dtype=np.float32),
            torch.tensor(np.array(X_seq_home_list, dtype=np.float32), dtype=torch.float32),
            torch.tensor(np.array(X_seq_away_list, dtype=np.float32), dtype=torch.float32),
            np.array(p_poisson_list, dtype=np.float32),
        )
    finally:
        dixon_coles_mle.leagues = saved_mle_leagues
        dixon_coles_mle.cutoff_date = saved_mle_cutoff
        db.close()


def train_and_save_all_models(weights_dir: str = "backend/weights", cutoff_date: str = TRAIN_CUTOFF_DATE):
    """Entrena y persiste XGBoost, LightGBM, PyTorch LSTM, Dixon-Coles MLE y Meta-Calibración."""
    os.makedirs(weights_dir, exist_ok=True)
    X_tab, y_tab, y_goals, X_seq_h, X_seq_a, p_pois_all = build_training_dataset(cutoff_date=cutoff_date)

    n_samples = len(X_tab)
    if n_samples < 50:
        logger.warning("Muestras insuficientes para entrenamiento. Verifique que la BD tenga partidos seeded.")
        return

    # División temporal estricta dentro del bloque de entrenamiento (85% train, 15% validation)
    split_idx = int(n_samples * 0.85)
    X_train, X_val = X_tab[:split_idx], X_tab[split_idx:]
    y_train, y_val = y_tab[:split_idx], y_tab[split_idx:]
    p_pois_val = p_pois_all[split_idx:]

    # 1. Entrenar XGBoost multi-clase regularizado con Early Stopping en validación
    xgb_path = os.path.join(weights_dir, "xgb_1x2.json")
    logger.info(f"Entrenando XGBoost (44F) en {len(X_train)} muestras reales (validación en {len(X_val)})...")
    dtrain = xgb.DMatrix(X_train, label=y_train, feature_names=FEATURE_NAMES)
    dval = xgb.DMatrix(X_val, label=y_val, feature_names=FEATURE_NAMES)

    params = {
        "objective": "multi:softprob",
        "num_class": 3,
        "max_depth": 2,
        "min_child_weight": 25,
        "learning_rate": 0.015,
        "subsample": 0.80,
        "colsample_bytree": 0.80,
        "gamma": 0.25,
        "reg_alpha": 0.8,
        "reg_lambda": 5.0,
        "eval_metric": "mlogloss",
        "seed": 42
    }
    evals = [(dtrain, "train"), (dval, "val")]
    booster = xgb.train(
        params,
        dtrain,
        num_boost_round=600,
        evals=evals,
        early_stopping_rounds=35,
        verbose_eval=False
    )
    booster.save_model(xgb_path)
    p_xgb_val = booster.predict(dval)
    logger.info(f"✅ XGBoost entrenado con Early Stopping (best_iteration={getattr(booster, 'best_iteration', 'N/A')}) y guardado en {xgb_path}")

    # 1b. Entrenar LightGBM multi-clase regularizado (44F) si está instalado
    p_tab_val = p_xgb_val
    if _HAS_LGB:
        lgb_path = os.path.join(weights_dir, "lgb_1x2.txt")
        lgb_train = lgb.Dataset(X_train, label=y_train, feature_name=FEATURE_NAMES)
        lgb_val = lgb.Dataset(X_val, label=y_val, feature_name=FEATURE_NAMES, reference=lgb_train)
        lgb_params = {
            "objective": "multiclass",
            "num_class": 3,
            "metric": "multi_logloss",
            "max_depth": 3,
            "num_leaves": 6,
            "min_child_samples": 40,
            "learning_rate": 0.015,
            "subsample": 0.80,
            "subsample_freq": 1,
            "colsample_bytree": 0.80,
            "reg_alpha": 1.0,
            "reg_lambda": 5.0,
            "verbose": -1,
            "seed": 42,
        }
        lgb_booster = lgb.train(
            lgb_params,
            lgb_train,
            num_boost_round=600,
            valid_sets=[lgb_val],
            callbacks=[lgb.early_stopping(35, verbose=False)],
        )
        lgb_booster.save_model(lgb_path)
        p_lgb_val = lgb_booster.predict(X_val)
        p_tab_val = 0.55 * p_xgb_val + 0.45 * p_lgb_val
        logger.info(f"✅ LightGBM entrenado (best_iteration={lgb_booster.best_iteration}) y guardado en {lgb_path}")

    p_tab_val = np.power(np.clip(p_tab_val, 1e-6, 1.0), 1.0 / 1.02)
    p_tab_val = p_tab_val / p_tab_val.sum(axis=1, keepdims=True)

    # 2. Entrenar PyTorch RichLSTM (14F) con secuencias reales exclusivamente en el split de entrenamiento
    p_lstm_val = np.full_like(p_tab_val, 1.0 / 3.0)
    if len(X_seq_h) >= 50:
        lstm_path = os.path.join(weights_dir, "lstm_momentum.pt")
        torch.manual_seed(42)
        np.random.seed(42)

        Xh_train, Xh_val = X_seq_h[:split_idx], X_seq_h[split_idx:]
        Xa_train, Xa_val = X_seq_a[:split_idx], X_seq_a[split_idx:]
        y_seq_train = torch.tensor(y_tab[:split_idx], dtype=torch.long)
        y_seq_val = torch.tensor(y_tab[split_idx:], dtype=torch.long)

        logger.info(f"Entrenando PyTorch RichLSTM (14F) en {len(Xh_train)} secuencias reales (validación en {len(Xh_val)})...")
        model = MatchSequenceLSTM()
        optimizer = torch.optim.AdamW(model.parameters(), lr=0.0005, weight_decay=2e-3)
        epochs = 50
        scheduler = torch.optim.lr_scheduler.CosineAnnealingLR(optimizer, T_max=epochs, eta_min=1e-5)
        criterion_1x2 = nn.CrossEntropyLoss()

        train_size = len(Xh_train)
        batch_size = 64
        best_val_loss = float("inf")
        best_state = copy.deepcopy(model.state_dict())

        for epoch in range(epochs):
            model.train()
            permutation = torch.randperm(train_size)
            for i in range(0, train_size, batch_size):
                indices = permutation[i:i + batch_size]
                batch_xh, batch_xa = Xh_train[indices], Xa_train[indices]
                batch_y_1x2 = y_seq_train[indices]

                optimizer.zero_grad()
                logits, _ = model(batch_xh, batch_xa)
                loss = criterion_1x2(logits, batch_y_1x2)
                loss.backward()
                torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
                optimizer.step()

            scheduler.step()
            model.eval()
            with torch.no_grad():
                val_logits, _ = model(Xh_val, Xa_val)
                val_loss = criterion_1x2(val_logits, y_seq_val).item()
                if val_loss < best_val_loss:
                    best_val_loss = val_loss
                    best_state = copy.deepcopy(model.state_dict())

        model.load_state_dict(best_state)
        model.eval()
        torch.save(model.state_dict(), lstm_path)
        with torch.no_grad():
            val_logits, _ = model(Xh_val, Xa_val)
            p_lstm_val = torch.softmax(val_logits, dim=1).numpy()
        logger.info(f"✅ PyTorch LSTM entrenada con Early Stopping (best_val_loss={best_val_loss:.4f}) y guardada en {lstm_path}")

    # 3. Meta-Calibración de pesos del Ensemble sobre validación temporal pre-corte
    rps_pois = _rps_batch(p_pois_val, y_val)
    rps_tab = _rps_batch(p_tab_val, y_val)
    rps_lstm = _rps_batch(p_lstm_val, y_val)

    def _ens_obj(w):
        w_n = np.asarray(w, dtype=np.float64)
        w_n = w_n / w_n.sum()
        blend = w_n[0] * p_pois_val + w_n[1] * p_tab_val + w_n[2] * p_lstm_val
        return _rps_batch(blend, y_val)

    opt = minimize(
        _ens_obj,
        x0=np.array([0.50, 0.35, 0.15]),
        bounds=[(0.30, 0.75), (0.15, 0.55), (0.05, 0.35)],
        constraints={"type": "eq", "fun": lambda w: float(np.sum(w) - 1.0)},
        method="SLSQP",
    )
    w_opt = np.asarray(opt.x if opt.success else [0.50, 0.38, 0.12], dtype=np.float64)
    w_opt = w_opt / w_opt.sum()
    rps_ens = _ens_obj(w_opt)

    calib_path = os.path.join(weights_dir, "ensemble_calibration.json")
    calib_payload = {
        "cutoff_date": cutoff_date,
        "n_train": len(X_train),
        "n_val": len(X_val),
        "weight_poisson": round(float(w_opt[0]), 4),
        "weight_xgboost": round(float(w_opt[1]), 4),
        "weight_lstm": round(float(w_opt[2]), 4),
        "val_rps_poisson": round(rps_pois, 5),
        "val_rps_tabular": round(rps_tab, 5),
        "val_rps_lstm": round(rps_lstm, 5),
        "val_rps_ensemble": round(rps_ens, 5),
    }
    with open(calib_path, "w", encoding="utf-8") as f:
        json.dump(calib_payload, f, indent=2, ensure_ascii=False)
    logger.info(
        f"✅ Meta-Calibración pre-{cutoff_date}: w=(Poisson={w_opt[0]:.3f}, Tabular={w_opt[1]:.3f}, LSTM={w_opt[2]:.3f}) | "
        f"RPS val: Poisson={rps_pois:.4f}, Tabular={rps_tab:.4f}, LSTM={rps_lstm:.4f} -> Ensemble={rps_ens:.4f}"
    )

    # 4. Ajustar y persistir Dixon-Coles MLE final con todo el historial < cutoff_date para inferencia 2025+
    dixon_coles_mle.weights_dir = weights_dir
    dixon_coles_mle.model_path = os.path.join(weights_dir, "dixon_coles_mle.json")
    dixon_coles_mle.fit_all_leagues_from_db(cutoff_date=cutoff_date)


if __name__ == "__main__":
    train_and_save_all_models()
