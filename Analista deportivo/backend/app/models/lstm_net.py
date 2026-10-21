"""
Módulo de Deep Learning Secuencial: Red Neuronal Recurrente LSTM (PyTorch).
Captura el momentum, la inercia temporal y las rachas recientes de los últimos partidos.
"""
import os
import logging
import torch
import torch.nn as nn
import torch.nn.functional as F
import numpy as np
from typing import Dict, List
from backend.app.schemas.match import MatchRawFeatures, PreviousMatch
from backend.app.models.poisson import (
    parse_elapsed_minute, calculate_remaining_goal_ratio,
    parse_live_score, condition_1x2_on_live_state,
)

logger = logging.getLogger(__name__)

TIMESTEPS = 10
FEATURES_PER_STEP = 8

class MatchSequenceLSTM(nn.Module):
    def __init__(self, input_dim: int = FEATURES_PER_STEP, hidden_dim: int = 32, num_layers: int = 2):
        super(MatchSequenceLSTM, self).__init__()
        self.lstm = nn.LSTM(
            input_size=input_dim,
            hidden_size=hidden_dim,
            num_layers=num_layers,
            batch_first=True,
            dropout=0.15 if num_layers > 1 else 0.0
        )
        # Capa densa que fusiona el vector latente de ambos equipos (hidden_dim * 2 = 64)
        self.fc1 = nn.Linear(hidden_dim * 2, 32)
        self.relu = nn.ReLU()
        self.dropout = nn.Dropout(0.1)
        # 1X2 Logits (Home, Draw, Away)
        self.head_1x2 = nn.Linear(32, 3)
        # Estimador auxiliar de momentum ofensivo
        self.head_goals = nn.Linear(32, 1)

    def forward(self, x_home: torch.Tensor, x_away: torch.Tensor):
        # x_home, x_away: [batch_size, timesteps, input_dim]
        _, (h_home, _) = self.lstm(x_home)  # h_home[-1]: [batch_size, hidden_dim]
        _, (h_away, _) = self.lstm(x_away)

        # Concatenar representaciones latentes de ambos equipos
        combined = torch.cat((h_home[-1], h_away[-1]), dim=-1)  # [batch_size, hidden_dim * 2]
        x = self.dropout(self.relu(self.fc1(combined)))

        logits_1x2 = self.head_1x2(x)
        goal_momentum = self.head_goals(x)
        return logits_1x2, goal_momentum

class LSTMPredictor:
    def __init__(self, weights_dir: str = "backend/weights"):
        self.weights_dir = weights_dir
        self.model_path = os.path.join(self.weights_dir, "lstm_momentum.pt")
        self.device = torch.device("cpu")
        self.model = MatchSequenceLSTM().to(self.device)
        self._ensure_model_ready()

    def _ensure_model_ready(self):
        """Carga los pesos locales de la red o crea un checkpoint base preentrenado."""
        os.makedirs(self.weights_dir, exist_ok=True)
        if os.path.exists(self.model_path):
            try:
                state_dict = torch.load(self.model_path, map_location=self.device)
                self.model.load_state_dict(state_dict)
                self.model.eval()
                logger.info("Modelo LSTM cargado exitosamente desde disco.")
                return
            except Exception as e:
                logger.warning(f"Error cargando pesos LSTM: {e}. Reentrenando base...")

        self._train_and_save_baseline()

    def _train_and_save_baseline(self):
        """
        Entrena el modelo LSTM con secuencias de momentum sintéticas que reflejan
        la dinámica de rachas consecutivas y decaimiento temporal en el fútbol.
        """
        logger.info("Inicializando y preentrenando red LSTM secuencial...")
        torch.manual_seed(42)
        np.random.seed(42)

        optimizer = torch.optim.Adam(self.model.parameters(), lr=0.003, weight_decay=1e-4)
        criterion_1x2 = nn.CrossEntropyLoss()
        criterion_goals = nn.MSELoss()

        self.model.train()
        n_batches = 300
        batch_size = 32

        for _ in range(n_batches):
            # Generar batch sintético de secuencias
            x_h = torch.randn(batch_size, TIMESTEPS, FEATURES_PER_STEP)
            x_a = torch.randn(batch_size, TIMESTEPS, FEATURES_PER_STEP)

            # Señal de tendencia: si los últimos 3 partidos tienen mayor diferencial de goles
            recent_momentum_h = x_h[:, -3:, 2].mean(dim=1)
            recent_momentum_a = x_a[:, -3:, 2].mean(dim=1)
            diff = recent_momentum_h - recent_momentum_a + 0.3  # ventaja localía

            # Etiquetas
            probs_h = torch.sigmoid(diff * 1.5)
            y_1x2 = torch.where(diff > 0.35, 0, torch.where(diff < -0.35, 2, 1))
            y_goals = torch.clamp(2.5 + diff * 0.4, 1.0, 5.0).unsqueeze(1)

            optimizer.zero_grad()
            logits, pred_goals = self.model(x_h, x_a)
            loss = criterion_1x2(logits, y_1x2) + 0.3 * criterion_goals(pred_goals, y_goals)
            loss.backward()
            optimizer.step()

        self.model.eval()
        torch.save(self.model.state_dict(), self.model_path)
        logger.info(f"Pesos de red LSTM guardados exitosamente en {self.model_path}")

    def _build_sequence_tensor(self, matches: List[PreviousMatch], default_scored: float, default_conceded: float) -> torch.Tensor:
        """
        Construye una matriz de tamaño [1, TIMESTEPS=10, FEATURES_PER_STEP=8]
        con orden cronológico (índice 0 = más antiguo, índice 9 = más reciente).
        Si hay menos de 10 partidos, rellena con la media del equipo.
        """
        features_list = []
        n_available = len(matches)

        # Si no hay partidos disponibles, rellenar con valores medios
        if n_available == 0:
            for step in range(TIMESTEPS):
                features_list.append([
                    default_scored, default_conceded, default_scored - default_conceded,
                    0.2, 0.5, 5.0 / 10.0, 2.0 / 5.0, (step + 1) / 10.0
                ])
        else:
            # Revertir para orden cronológico si vienen ordenados del más reciente al más antiguo
            ordered_matches = list(reversed(matches[:TIMESTEPS]))

            # Padding si hay menos de 10
            pad_needed = TIMESTEPS - len(ordered_matches)
            for p in range(pad_needed):
                features_list.append([
                    default_scored, default_conceded, default_scored - default_conceded,
                    0.2, 0.5, 5.0 / 10.0, 2.0 / 5.0, (p + 1) / 10.0
                ])

            for idx, m in enumerate(ordered_matches):
                # Codificar resultado
                res_code = 1.0 if m.result == "W" else (0.0 if m.result == "D" else -1.0)
                diff = float(m.goals_for - m.goals_against)
                is_home = 1.0 if m.was_home else 0.0
                corners = float(m.corners_for if m.corners_for is not None else 5.0) / 10.0
                cards = float(m.cards_total if m.cards_total is not None else 2.5) / 5.0
                # Decaimiento temporal lineal ascendente (el partido más reciente tiene peso 1.0)
                time_weight = float(pad_needed + idx + 1) / TIMESTEPS

                features_list.append([
                    float(m.goals_for),
                    float(m.goals_against),
                    diff,
                    res_code,
                    is_home,
                    corners,
                    cards,
                    time_weight
                ])

        tensor = torch.tensor([features_list], dtype=torch.float32)
        return tensor

    def predict(self, raw: MatchRawFeatures) -> Dict:
        """
        Ejecuta la inferencia temporal secuencial con la red LSTM.
        """
        self.model.eval()
        with torch.no_grad():
            x_h = self._build_sequence_tensor(
                raw.home_stats.last_matches,
                raw.home_stats.avg_goals_scored,
                raw.home_stats.avg_goals_conceded
            ).to(self.device)

            x_a = self._build_sequence_tensor(
                raw.away_stats.last_matches,
                raw.away_stats.avg_goals_scored,
                raw.away_stats.avg_goals_conceded
            ).to(self.device)

            logits_1x2, goal_momentum = self.model(x_h, x_a)
            # Calibración de temperatura para evitar sobre-polarización extrema en rachas asimétricas
            temperature = 1.45
            calibrated_logits = logits_1x2 / temperature
            probs = F.softmax(calibrated_logits, dim=-1).squeeze(0).cpu().numpy()

            p_home = float(probs[0])
            p_draw = float(probs[1])
            p_away = float(probs[2])

            momentum_factor = float(goal_momentum.squeeze().item())

            # -------------------------------------------------------------
            # Análisis de Dinámica en Vivo con Red Neuronal LSTM
            # -------------------------------------------------------------
            is_live = getattr(raw, "is_live", False)
            live_rem_goals = None
            live_no_more_p = None
            live_more_p = None

            if not is_live:
                # En pre-partido, asegurar suelo competitivo de empate para evitar colapso a 0%
                if p_draw < 0.12:
                    deficit = 0.12 - p_draw
                    p_draw = 0.12
                    if p_home >= p_away:
                        p_home = max(0.04, p_home - deficit)
                    else:
                        p_away = max(0.04, p_away - deficit)
                    tot_p = p_home + p_draw + p_away
                    p_home /= tot_p
                    p_draw /= tot_p
                    p_away /= tot_p

            if is_live:
                elapsed_min = parse_elapsed_minute(getattr(raw, "live_minute", None))
                time_rem_ratio = calculate_remaining_goal_ratio(elapsed_min)
                gh, ga = parse_live_score(getattr(raw, "live_score", None))
                reds_h = int(getattr(raw, "live_red_cards_home", 0) or 0)
                reds_a = int(getattr(raw, "live_red_cards_away", 0) or 0)

                # Condicionamiento temporal del 1X2 secuencial al estado real del partido
                p_home, p_draw, p_away = condition_1x2_on_live_state(
                    p_home, p_draw, p_away,
                    total_goals_90=float(np.clip(momentum_factor, 1.6, 4.0)),
                    curr_gh=gh, curr_ga=ga,
                    time_rem_ratio=time_rem_ratio,
                    reds_h=reds_h, reds_a=reds_a,
                )

                # Calcular tensión o urgencia de gol según marcador actual
                urgency = 1.0
                diff = abs(gh - ga)
                if diff == 1 and elapsed_min >= 60:
                    urgency = 1.25  # Partido cerrado con remontada en disputa
                elif diff >= 3:
                    urgency = 0.85  # Partido sentenciado

                # Goles adicionales proyectados por el momentum de la red neuronal
                base_momentum = max(0.4, min(4.5, momentum_factor))
                live_rem_goals = float(base_momentum * time_rem_ratio * urgency)
                
                # Probabilidad de que no haya más goles según la tasa de llegada de la red
                if time_rem_ratio > 0:
                    live_no_more_p = float(np.clip(np.exp(-live_rem_goals), 0.02, 0.95))
                else:
                    live_no_more_p = 1.0  # Partido finalizado
                live_more_p = float(1.0 - live_no_more_p)

        return {
            "model_name": "lstm_recurrent_net",
            "winner_probs": {
                "home_win": round(p_home * 100, 2),
                "draw": round(p_draw * 100, 2),
                "away_win": round(p_away * 100, 2)
            },
            "momentum_goals": round(momentum_factor, 2),
            "live_expected_remaining_goals": round(live_rem_goals, 2) if live_rem_goals is not None else None,
            "live_no_more_goals_pct": round(live_no_more_p * 100, 1) if live_no_more_p is not None else None,
            "live_more_goals_pct": round(live_more_p * 100, 1) if live_more_p is not None else None
        }

lstm_predictor = LSTMPredictor()
