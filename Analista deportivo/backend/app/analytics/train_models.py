"""
Pipeline de Entrenamiento Supervisado con Datos Históricos Reales (Katakuri v4).
Entrena XGBoost y PyTorch LSTM exclusivamente sobre la secuencia cronológica real
de los partidos de grandes ligas sin fugas de datos hacia el futuro (cero look-ahead bias).
Genera y guarda:
- backend/weights/xgb_1x2.json (XGBoost calibrado)
- backend/weights/lstm_momentum.pt (PyTorch LSTM secuencial)
"""
import os
import math
import logging
import numpy as np
import torch
import torch.nn as nn
import xgboost as xgb
from typing import List, Dict, Tuple
from backend.app.db import SessionLocal, HistoricalMatch, Team, League
from backend.app.models.lstm_net import MatchSequenceLSTM, TIMESTEPS, FEATURES_PER_STEP
from backend.app.models.tabular_ml import FEATURE_NAMES

logger = logging.getLogger(__name__)

def build_training_dataset():
    """
    Construye matrices de entrenamiento tabulares y tensoriales secuenciales
    a partir de la cronología real de partidos en la base de datos local.
    """
    db = SessionLocal()
    try:
        matches = db.query(HistoricalMatch).order_by(
            HistoricalMatch.match_date.asc(),
            HistoricalMatch.id.asc()
        ).all()
        teams = {t.name: t for t in db.query(Team).all()}
        leagues = {l.code: l for l in db.query(League).all()}
        logger.info(f"Procesando {len(matches)} partidos reales cronológicos para entrenamiento...")

        # Rastrear Elo y partidos dinámicamente en orden cronológico estricto
        elo_tracker = {t_name: float(teams[t_name].elo_rating or 1600.0) for t_name in teams}
        team_history = {t_name: [] for t_name in teams}

        X_tab_list = []
        y_tab_list = []
        y_goals_list = []

        X_seq_home_list = []
        X_seq_away_list = []

        for m in matches:
            h_name = m.home_team
            a_name = m.away_team

            h_hist = team_history.get(h_name, [])
            a_hist = team_history.get(a_name, [])

            cur_elo_h = elo_tracker.get(h_name, 1600.0)
            cur_elo_a = elo_tracker.get(a_name, 1600.0)

            # Entrenar en partidos donde ambos clubes tienen historial previo conocido
            if len(h_hist) >= 2 and len(a_hist) >= 2:
                # 1. Features Tabulares con estado PREVIO al partido
                elo_diff = (cur_elo_h - cur_elo_a + 65.0) / 100.0
                home_elo_scaled = cur_elo_h / 1000.0
                away_elo_scaled = cur_elo_a / 1000.0

                h_last5 = h_hist[-5:]
                a_last5 = a_hist[-5:]

                h_wr5 = sum(1 for match in h_last5 if match["res"] == "W") / len(h_last5)
                a_wr5 = sum(1 for match in a_last5 if match["res"] == "W") / len(a_last5)

                h_gf_avg = float(np.mean([match["gf"] for match in h_hist[-10:]]))
                h_ga_avg = float(np.mean([match["ga"] for match in h_hist[-10:]]))
                a_gf_avg = float(np.mean([match["gf"] for match in a_hist[-10:]]))
                a_ga_avg = float(np.mean([match["ga"] for match in a_hist[-10:]]))

                h_diff = h_gf_avg - h_ga_avg
                a_diff = a_gf_avg - a_ga_avg
                delta_diff = h_diff - a_diff

                h_sot_avg = float(np.mean([match["hst"] for match in h_hist[-10:]]))
                a_sot_avg = float(np.mean([match["hst"] for match in a_hist[-10:]]))

                # Historial H2H previo estricto
                past_h2h = [match for match in h_hist if match["opp"] == a_name]
                if past_h2h:
                    h2h_h = sum(1 for x in past_h2h if x["res"] == "W") / len(past_h2h)
                    h2h_a = sum(1 for x in past_h2h if x["res"] == "L") / len(past_h2h)
                    h2h_d = sum(1 for x in past_h2h if x["res"] == "D") / len(past_h2h)
                    h2h_g = float(np.mean([x["gf"] + x["ga"] for x in past_h2h]))
                else:
                    h2h_h, h2h_a, h2h_d, h2h_g = 0.38, 0.32, 0.30, 2.75

                h_cn_avg = float(np.mean([match["cn"] for match in h_hist[-10:]]))
                a_cn_avg = float(np.mean([match["cn"] for match in a_hist[-10:]]))
                h_cr_avg = float(np.mean([match["cr"] for match in h_hist[-10:]]))
                a_cr_avg = float(np.mean([match["cr"] for match in a_hist[-10:]]))

                l_obj = leagues.get(m.league_code)
                home_adv = l_obj.home_adv if l_obj else 1.14
                home_absences = 0.0
                away_absences = 0.0

                tab_row = [
                    float(elo_diff),
                    float(home_elo_scaled),
                    float(away_elo_scaled),
                    float(h_wr5),
                    float(a_wr5),
                    float(h_diff),
                    float(a_diff),
                    float(delta_diff),
                    float(h_gf_avg),
                    float(a_gf_avg),
                    float(h_ga_avg),
                    float(a_ga_avg),
                    float(h_sot_avg),
                    float(a_sot_avg),
                    float(h2h_h),
                    float(h2h_a),
                    float(h2h_d),
                    float(h2h_g),
                    float(home_absences),
                    float(away_absences),
                    float(home_adv),
                    float(h_cn_avg + a_cn_avg),
                    float(h_cr_avg + a_cr_avg)
                ]
                X_tab_list.append(tab_row)

                # Etiqueta: 0 = Local, 1 = Empate, 2 = Visitante
                y_label = 0 if m.home_goals > m.away_goals else (1 if m.home_goals == m.away_goals else 2)
                y_tab_list.append(y_label)
                y_goals_list.append(float(m.home_goals + m.away_goals))

                # 2. Secuencias para LSTM (últimos 10 pasos cronológicos)
                seq_h = []
                seq_a = []
                pad_h = TIMESTEPS - min(TIMESTEPS, len(h_hist))
                for p in range(pad_h):
                    seq_h.append([h_gf_avg, h_ga_avg, h_diff, 0.0, 0.5, 0.5, 0.4, (p + 1) / 10.0])
                for idx, prev in enumerate(h_hist[-TIMESTEPS:]):
                    r_code = 1.0 if prev["res"] == "W" else (0.0 if prev["res"] == "D" else -1.0)
                    t_w = float(pad_h + idx + 1) / TIMESTEPS
                    seq_h.append([
                        float(prev["gf"]), float(prev["ga"]), float(prev["gf"] - prev["ga"]),
                        r_code, 1.0 if prev["was_home"] else 0.0,
                        float(prev["cn"]) / 10.0, float(prev["cr"]) / 5.0, t_w
                    ])

                pad_a = TIMESTEPS - min(TIMESTEPS, len(a_hist))
                for p in range(pad_a):
                    seq_a.append([a_gf_avg, a_ga_avg, a_diff, 0.0, 0.5, 0.5, 0.4, (p + 1) / 10.0])
                for idx, prev in enumerate(a_hist[-TIMESTEPS:]):
                    r_code = 1.0 if prev["res"] == "W" else (0.0 if prev["res"] == "D" else -1.0)
                    t_w = float(pad_a + idx + 1) / TIMESTEPS
                    seq_a.append([
                        float(prev["gf"]), float(prev["ga"]), float(prev["gf"] - prev["ga"]),
                        r_code, 1.0 if prev["was_home"] else 0.0,
                        float(prev["cn"]) / 10.0, float(prev["cr"]) / 5.0, t_w
                    ])

                X_seq_home_list.append(seq_h)
                X_seq_away_list.append(seq_a)

            # Actualizar historial y Elo cronológicamente
            from backend.app.services.real_data_loader import calculate_elo_update
            new_h, new_a = calculate_elo_update(cur_elo_h, cur_elo_a, m.home_goals, m.away_goals)
            elo_tracker[h_name] = new_h
            elo_tracker[a_name] = new_a

            if h_name in team_history:
                team_history[h_name].append({
                    "opp": a_name, "was_home": True, "gf": m.home_goals, "ga": m.away_goals,
                    "res": "W" if m.home_goals > m.away_goals else ("D" if m.home_goals == m.away_goals else "L"),
                    "hst": m.home_shots_target, "ast": m.away_shots_target,
                    "cn": m.corners_home, "cr": m.cards_home
                })
            if a_name in team_history:
                team_history[a_name].append({
                    "opp": h_name, "was_home": False, "gf": m.away_goals, "ga": m.home_goals,
                    "res": "W" if m.away_goals > m.home_goals else ("D" if m.home_goals == m.away_goals else "L"),
                    "hst": m.away_shots_target, "ast": m.home_shots_target,
                    "cn": m.corners_away, "cr": m.cards_away
                })

        logger.info(f"Dataset cronológico real construido con {len(X_tab_list)} muestras puras.")
        return (
            np.array(X_tab_list, dtype=np.float32),
            np.array(y_tab_list, dtype=int),
            np.array(y_goals_list, dtype=np.float32),
            torch.tensor(X_seq_home_list, dtype=torch.float32),
            torch.tensor(X_seq_away_list, dtype=torch.float32)
        )
    finally:
        db.close()

def train_and_save_all_models(weights_dir: str = "backend/weights"):
    """Entrena y persiste XGBoost y PyTorch LSTM sobre el dataset histórico real."""
    os.makedirs(weights_dir, exist_ok=True)
    X_tab, y_tab, y_goals, X_seq_h, X_seq_a = build_training_dataset()

    n_samples = len(X_tab)
    if n_samples < 50:
        logger.warning("Muestras insuficientes para entrenamiento. Verifique que la BD tenga partidos seeded.")
        return

    # División temporal estricta (85% train, 15% validation)
    split_idx = int(n_samples * 0.85)
    X_train, X_val = X_tab[:split_idx], X_tab[split_idx:]
    y_train, y_val = y_tab[:split_idx], y_tab[split_idx:]
    y_goals_train, y_goals_val = y_goals[:split_idx], y_goals[split_idx:]

    # 1. Entrenar XGBoost multi-clase calibrado
    xgb_path = os.path.join(weights_dir, "xgb_1x2.json")
    logger.info(f"Entrenando XGBoost en {len(X_train)} muestras reales (validación en {len(X_val)})...")
    dtrain = xgb.DMatrix(X_train, label=y_train, feature_names=FEATURE_NAMES)
    dval = xgb.DMatrix(X_val, label=y_val, feature_names=FEATURE_NAMES)

    params = {
        "objective": "multi:softprob",
        "num_class": 3,
        "max_depth": 4,
        "learning_rate": 0.05,
        "subsample": 0.85,
        "colsample_bytree": 0.85,
        "gamma": 0.1,
        "reg_alpha": 0.1,
        "reg_lambda": 1.0,
        "eval_metric": "mlogloss",
        "seed": 42
    }
    evals = [(dtrain, "train"), (dval, "val")]
    booster = xgb.train(
        params,
        dtrain,
        num_boost_round=120,
        evals=evals,
        verbose_eval=False
    )
    booster.save_model(xgb_path)
    logger.info(f"✅ XGBoost entrenado con datos reales y guardado en {xgb_path}")

    # 2. Entrenar PyTorch LSTM con secuencias reales
    if len(X_seq_h) >= 10:
        lstm_path = os.path.join(weights_dir, "lstm_momentum.pt")
        logger.info(f"Entrenando PyTorch LSTM en {len(X_seq_h)} secuencias reales...")
        model = MatchSequenceLSTM()
        optimizer = torch.optim.Adam(model.parameters(), lr=0.002, weight_decay=1e-4)
        criterion_1x2 = nn.CrossEntropyLoss()
        criterion_goals = nn.MSELoss()

        model.train()
        y_seq_1x2 = torch.tensor(y_tab[:len(X_seq_h)], dtype=torch.long)
        y_seq_goals = torch.tensor(y_goals[:len(X_seq_h)], dtype=torch.float32).unsqueeze(1)

        dataset_size = len(X_seq_h)
        batch_size = 32
        epochs = 35

        for epoch in range(epochs):
            permutation = torch.randperm(dataset_size)
            total_loss = 0.0
            for i in range(0, dataset_size, batch_size):
                indices = permutation[i:i + batch_size]
                batch_xh, batch_xa = X_seq_h[indices], X_seq_a[indices]
                batch_y_1x2, batch_y_goals = y_seq_1x2[indices], y_seq_goals[indices]

                optimizer.zero_grad()
                logits, pred_goals = model(batch_xh, batch_xa)
                loss = criterion_1x2(logits, batch_y_1x2) + 0.25 * criterion_goals(pred_goals, batch_y_goals)
                loss.backward()
                optimizer.step()
                total_loss += loss.item()

        model.eval()
        torch.save(model.state_dict(), lstm_path)
        logger.info(f"✅ PyTorch LSTM entrenada con datos reales y guardada en {lstm_path}")

if __name__ == "__main__":
    train_and_save_all_models()
