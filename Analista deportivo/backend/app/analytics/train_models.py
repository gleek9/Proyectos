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
import os
import logging
import numpy as np
import torch
import torch.nn as nn
import xgboost as xgb
from collections import defaultdict
from backend.app.db import SessionLocal, HistoricalMatch, League
from backend.app.models.lstm_net import MatchSequenceLSTM, LSTMPredictor, TIMESTEPS, FEATURES_PER_STEP
from backend.app.models.tabular_ml import FEATURE_NAMES, TabularPredictor
from backend.app.services.real_data_loader import (
    get_honest_initial_elo_map,
    build_point_in_time_match_features,
    calculate_elo_update,
)

logger = logging.getLogger(__name__)

# Corte temporal estricto: todo partido >= TRAIN_CUTOFF_DATE queda reservado 100% fuera de muestra (Out-of-Sample)
TRAIN_CUTOFF_DATE = "2025-01-01"


def build_training_dataset(cutoff_date: str = TRAIN_CUTOFF_DATE):
    """
    Construye matrices de entrenamiento tabulares y tensoriales secuenciales
    a partir de la cronología real de partidos en la base de datos local,
    utilizando exactamente el mismo pipeline Point-in-Time de producción.
    """
    db = SessionLocal()
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

        X_tab_list = []
        y_tab_list = []
        y_goals_list = []

        X_seq_home_list = []
        X_seq_away_list = []

        for m in matches:
            # Detener recolección de muestras de entrenamiento al llegar al corte Out-of-Sample
            if cutoff_date and (m.match_date or "") >= cutoff_date:
                break

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
                )

                # 1. Vector tabular exacto de producción (23 features con shrinkage de James-Stein)
                tab_row = TabularPredictor.extract_features(None, feats)[0]
                X_tab_list.append(tab_row)

                # Etiqueta: 0 = Local, 1 = Empate, 2 = Visitante
                y_label = 0 if m.home_goals > m.away_goals else (1 if m.home_goals == m.away_goals else 2)
                y_tab_list.append(y_label)
                y_goals_list.append(float(m.home_goals + m.away_goals))

                # 2. Secuencias exactas de producción para LSTM (TIMESTEPS=10, FEATURES_PER_STEP=8)
                seq_h = LSTMPredictor._build_sequence_tensor(
                    None,
                    feats.home_stats.last_matches,
                    feats.home_stats.avg_goals_scored,
                    feats.home_stats.avg_goals_conceded,
                ).squeeze(0).numpy()
                seq_a = LSTMPredictor._build_sequence_tensor(
                    None,
                    feats.away_stats.last_matches,
                    feats.away_stats.avg_goals_scored,
                    feats.away_stats.avg_goals_conceded,
                ).squeeze(0).numpy()

                X_seq_home_list.append(seq_h)
                X_seq_away_list.append(seq_a)

            # Actualizar historial y Elo cronológicamente ESTRICTAMENTE DESPUÉS del partido
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
                "cn": m.corners_home or 5, "cn_opp": m.corners_away or 4,
                "cr": m.cards_home or 2, "cn_tot": cn_tot, "cr_tot": cr_tot
            })
            team_history[a_name].append({
                "opp": h_name, "was_home": False, "date": m.match_date,
                "gf": m.away_goals, "ga": m.home_goals,
                "res": "W" if m.away_goals > m.home_goals else ("D" if m.home_goals == m.away_goals else "L"),
                "hst": m.away_shots_target or 4, "ast": m.home_shots_target or 4,
                "cn": m.corners_away or 4, "cn_opp": m.corners_home or 5,
                "cr": m.cards_away or 2, "cn_tot": cn_tot, "cr_tot": cr_tot
            })

        logger.info(f"Dataset cronológico pre-{cutoff_date} construido con {len(X_tab_list)} muestras puras.")
        return (
            np.array(X_tab_list, dtype=np.float32),
            np.array(y_tab_list, dtype=int),
            np.array(y_goals_list, dtype=np.float32),
            torch.tensor(np.array(X_seq_home_list, dtype=np.float32), dtype=torch.float32),
            torch.tensor(np.array(X_seq_away_list, dtype=np.float32), dtype=torch.float32)
        )
    finally:
        db.close()


def train_and_save_all_models(weights_dir: str = "backend/weights", cutoff_date: str = TRAIN_CUTOFF_DATE):
    """Entrena y persiste XGBoost y PyTorch LSTM con validación temporal y Early Stopping."""
    os.makedirs(weights_dir, exist_ok=True)
    X_tab, y_tab, y_goals, X_seq_h, X_seq_a = build_training_dataset(cutoff_date=cutoff_date)

    n_samples = len(X_tab)
    if n_samples < 50:
        logger.warning("Muestras insuficientes para entrenamiento. Verifique que la BD tenga partidos seeded.")
        return

    # División temporal estricta dentro del bloque de entrenamiento (85% train, 15% validation)
    split_idx = int(n_samples * 0.85)
    X_train, X_val = X_tab[:split_idx], X_tab[split_idx:]
    y_train, y_val = y_tab[:split_idx], y_tab[split_idx:]

    # 1. Entrenar XGBoost multi-clase regularizado con Early Stopping en validación
    xgb_path = os.path.join(weights_dir, "xgb_1x2.json")
    logger.info(f"Entrenando XGBoost en {len(X_train)} muestras reales (validación en {len(X_val)})...")
    dtrain = xgb.DMatrix(X_train, label=y_train, feature_names=FEATURE_NAMES)
    dval = xgb.DMatrix(X_val, label=y_val, feature_names=FEATURE_NAMES)

    params = {
        "objective": "multi:softprob",
        "num_class": 3,
        "max_depth": 3,
        "min_child_weight": 10,
        "learning_rate": 0.03,
        "subsample": 0.80,
        "colsample_bytree": 0.80,
        "gamma": 0.25,
        "reg_alpha": 0.5,
        "reg_lambda": 2.5,
        "eval_metric": "mlogloss",
        "seed": 42
    }
    evals = [(dtrain, "train"), (dval, "val")]
    booster = xgb.train(
        params,
        dtrain,
        num_boost_round=220,
        evals=evals,
        early_stopping_rounds=25,
        verbose_eval=False
    )
    booster.save_model(xgb_path)
    logger.info(f"✅ XGBoost entrenado con Early Stopping (best_iteration={getattr(booster, 'best_iteration', 'N/A')}) y guardado en {xgb_path}")

    # 2. Entrenar PyTorch LSTM con secuencias reales exclusivamente en el split de entrenamiento
    #    y seleccionar el mejor checkpoint según pérdida en el split de validación
    if len(X_seq_h) >= 50:
        lstm_path = os.path.join(weights_dir, "lstm_momentum.pt")
        torch.manual_seed(42)
        np.random.seed(42)

        Xh_train, Xh_val = X_seq_h[:split_idx], X_seq_h[split_idx:]
        Xa_train, Xa_val = X_seq_a[:split_idx], X_seq_a[split_idx:]
        y_seq_train = torch.tensor(y_tab[:split_idx], dtype=torch.long)
        y_seq_val = torch.tensor(y_tab[split_idx:], dtype=torch.long)
        y_goals_train_t = torch.tensor(y_goals[:split_idx], dtype=torch.float32).unsqueeze(1)
        y_goals_val_t = torch.tensor(y_goals[split_idx:], dtype=torch.float32).unsqueeze(1)

        logger.info(f"Entrenando PyTorch LSTM en {len(Xh_train)} secuencias reales (validación en {len(Xh_val)})...")
        model = MatchSequenceLSTM()
        optimizer = torch.optim.Adam(model.parameters(), lr=0.0015, weight_decay=5e-4)
        criterion_1x2 = nn.CrossEntropyLoss()
        criterion_goals = nn.MSELoss()

        train_size = len(Xh_train)
        batch_size = 64
        epochs = 30
        best_val_loss = float("inf")
        best_state = copy.deepcopy(model.state_dict())

        for epoch in range(epochs):
            model.train()
            permutation = torch.randperm(train_size)
            for i in range(0, train_size, batch_size):
                indices = permutation[i:i + batch_size]
                batch_xh, batch_xa = Xh_train[indices], Xa_train[indices]
                batch_y_1x2, batch_y_goals = y_seq_train[indices], y_goals_train_t[indices]

                optimizer.zero_grad()
                logits, pred_goals = model(batch_xh, batch_xa)
                loss = criterion_1x2(logits, batch_y_1x2) + 0.15 * criterion_goals(pred_goals, batch_y_goals)
                loss.backward()
                optimizer.step()

            model.eval()
            with torch.no_grad():
                val_logits, val_goals = model(Xh_val, Xa_val)
                val_loss = (
                    criterion_1x2(val_logits, y_seq_val) + 0.15 * criterion_goals(val_goals, y_goals_val_t)
                ).item()
                if val_loss < best_val_loss:
                    best_val_loss = val_loss
                    best_state = copy.deepcopy(model.state_dict())

        model.load_state_dict(best_state)
        model.eval()
        torch.save(model.state_dict(), lstm_path)
        logger.info(f"✅ PyTorch LSTM entrenada con Early Stopping (best_val_loss={best_val_loss:.4f}) y guardada en {lstm_path}")


if __name__ == "__main__":
    train_and_save_all_models()
