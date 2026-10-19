"""
Módulo de Modelado Matemático: Poisson Bivariado Dinámico con corrección Dixon-Coles.
Calcula probabilidades exactas de marcadores, 1X2, goles Over/Under, córners y tarjetas.
"""
import math
import numpy as np
import re
from typing import Dict, Tuple, List, Optional
from scipy.stats import poisson
from backend.app.schemas.match import MatchRawFeatures

def parse_elapsed_minute(minute_str: Optional[str]) -> int:
    """
    Parsea de forma robusta cualquier representación de tiempo en vivo ('34'', '2T 68'', 'HT', 'MT', 'Descanso', '1T')
    y retorna el minuto transcurrido acotado entre 1 y 89.
    """
    if not minute_str:
        return 45
    min_clean = str(minute_str).upper().strip()
    if "MT" in min_clean or "DESCANSO" in min_clean or "HT" in min_clean or "ENTRETIEMPO" in min_clean:
        return 45
    elif "2T" in min_clean or "ST" in min_clean:
        num_match = re.search(r"\d+", min_clean)
        if num_match:
            val = int(num_match.group(0))
            return int(np.clip(val if val >= 45 else 45 + val, 1, 89))
        return 65
    elif "1T" in min_clean or "PT" in min_clean:
        num_match = re.search(r"\d+", min_clean)
        return int(np.clip(int(num_match.group(0)) if num_match else 25, 1, 45))
    else:
        num_match = re.search(r"\d+", min_clean)
        if num_match:
            return int(np.clip(int(num_match.group(0)), 1, 89))
    return 45

def calculate_remaining_goal_ratio(elapsed_minutes: int) -> float:
    """
    Calcula la fracción de expectativa de gol restante en función del minuto actual,
    basándose en la curva empírica no homogénea de llegada de goles en el fútbol profesional.
    Distribución acumulada representativa:
    0'-15': 13.0%, 16'-30': 15.5%, 31'-45': 17.5% (Total 1T: 46.0%)
    46'-60': 16.5%, 61'-75': 18.5%, 76'-90+': 22.5% (Total 2T: 54.0%)
    """
    minute_anchors = [0.0, 15.0, 30.0, 45.0, 60.0, 75.0, 90.0]
    cumulative_dist = [0.0, 0.130, 0.285, 0.460, 0.625, 0.775, 1.000]
    m_clamped = float(np.clip(elapsed_minutes, 0, 90))
    passed_ratio = float(np.interp(m_clamped, minute_anchors, cumulative_dist))
    return max(0.04, 1.0 - passed_ratio)

def calculate_remaining_corner_ratio(elapsed_minutes: int) -> float:
    """
    Fracción de tiempo restante para saques de esquina considerando mayor frecuencia en el 2T.
    """
    minute_anchors = [0.0, 45.0, 75.0, 90.0]
    cumulative_dist = [0.0, 0.470, 0.790, 1.000]
    m_clamped = float(np.clip(elapsed_minutes, 0, 90))
    passed_ratio = float(np.interp(m_clamped, minute_anchors, cumulative_dist))
    return max(0.04, 1.0 - passed_ratio)

COMPETITION_BASELINES = {
    "bundesliga": {"avg_goals_team": 1.58, "home_adv": 1.12},       # ~3.16 goles totales
    "premier league": {"avg_goals_team": 1.43, "home_adv": 1.13},   # ~2.86 goles totales
    "premier": {"avg_goals_team": 1.43, "home_adv": 1.13},
    "laliga 2": {"avg_goals_team": 1.12, "home_adv": 1.18},         # ~2.24 goles totales
    "hypermotion": {"avg_goals_team": 1.12, "home_adv": 1.18},
    "segunda": {"avg_goals_team": 1.12, "home_adv": 1.18},
    "laliga": {"avg_goals_team": 1.28, "home_adv": 1.16},           # ~2.56 goles totales
    "serie a": {"avg_goals_team": 1.31, "home_adv": 1.15},          # ~2.62 goles totales
    "ligue 1": {"avg_goals_team": 1.30, "home_adv": 1.14},          # ~2.60 goles totales
    "champions league": {"avg_goals_team": 1.50, "home_adv": 1.12}, # ~3.00 goles totales
    "champions": {"avg_goals_team": 1.50, "home_adv": 1.12},
    "europa league": {"avg_goals_team": 1.45, "home_adv": 1.14},    # ~2.90 goles totales
    "eredivisie": {"avg_goals_team": 1.55, "home_adv": 1.15},       # ~3.10 goles totales
    "liga mx": {"avg_goals_team": 1.38, "home_adv": 1.18},          # ~2.76 goles totales
    "brasileirao": {"avg_goals_team": 1.25, "home_adv": 1.20},      # ~2.50 goles totales
    "copa libertadores": {"avg_goals_team": 1.30, "home_adv": 1.22},# ~2.60 goles totales
    "mls": {"avg_goals_team": 1.48, "home_adv": 1.16},              # ~2.96 goles totales
}

def get_competition_parameters(competition_name: Optional[str]) -> Tuple[float, float]:
    """
    Retorna (league_avg_goals_per_team, home_advantage) adaptado al torneo solicitado.
    Si no coincide con ninguna liga indexada, recurre al estándar global (1.35, 1.15).
    Las claves más largas y específicas se priorizan para evitar colisiones (ej: 'laliga hypermotion' antes de 'laliga').
    """
    if not competition_name:
        return 1.35, 1.15
    comp_clean = competition_name.lower().strip()
    for key in sorted(COMPETITION_BASELINES.keys(), key=len, reverse=True):
        if key in comp_clean:
            return COMPETITION_BASELINES[key]["avg_goals_team"], COMPETITION_BASELINES[key]["home_adv"]
    return 1.35, 1.15

class DixonColesPoissonModel:
    def __init__(self, rho: float = -0.10, max_goals: int = 7):
        """
        :param rho: Parámetro de correlación Dixon-Coles para marcadores bajos (0-0, 1-0, 0-1, 1-1).
        :param max_goals: Máximo de goles a simular por equipo en la matriz conjunta.
        """
        self.rho = rho
        self.max_goals = max_goals
        self.league_avg_goals = 1.35  # Promedio estándar global de goles por equipo por partido

    def _evaluate_absences_impact(self, absences: List[str]) -> Tuple[float, float]:
        """
        Pondera las ausencias según posición y relevancia:
        - Bajas defensivas (portero, defensas) aumentan la expectativa de goles concedidos.
        - Bajas ofensivas (delanteros, extremos, goleadores) reducen el poder de ataque.
        Retorna (attack_multiplier, defense_conceded_multiplier).
        """
        att_multiplier = 1.0
        def_multiplier = 1.0
        defensive_kw = ["portero", "arquero", "goalkeeper", "gk", "defensa", "central", "lateral", "cb", "lb", "rb"]
        offensive_kw = ["delantero", "goleador", "striker", "extremo", "forward", "fw", "winger", "atacante"]

        for player in absences:
            p_low = player.lower()
            if any(k in p_low for k in defensive_kw):
                def_multiplier *= 1.06  # Concede ~6% más por baja defensiva
            elif any(k in p_low for k in offensive_kw):
                att_multiplier *= 0.93  # Pierde ~7% de gol por ausencia de goleador
            else:
                att_multiplier *= 0.96  # Ausencia genérica (~4%)

        return max(0.70, att_multiplier), min(1.30, def_multiplier)

    def _calculate_lambdas(self, features: MatchRawFeatures) -> Tuple[float, float]:
        """
        Calcula las expectativas de gol esperadas (lambda_home, mu_away)
        considerando fuerza ofensiva, debilidad defensiva, ventaja de localía por competición,
        datos H2H y ausencias clasificadas por posición.
        """
        home = features.home_stats
        away = features.away_stats
        h2h = features.h2h

        # 1. Parámetros basales adaptados a la liga
        comp_name = getattr(features, "competition", "General")
        league_avg_goals, home_advantage = get_competition_parameters(comp_name)

        # 2. Shrinkage Bayesiano hacia el estándar general (atenúa la varianza y rachas extremas)
        global_ref = self.league_avg_goals
        w_shrink = 0.72
        h_att_shrunk = w_shrink * home.avg_goals_scored + (1.0 - w_shrink) * global_ref
        a_def_shrunk = w_shrink * away.avg_goals_conceded + (1.0 - w_shrink) * global_ref
        a_att_shrunk = w_shrink * away.avg_goals_scored + (1.0 - w_shrink) * global_ref
        h_def_shrunk = w_shrink * home.avg_goals_conceded + (1.0 - w_shrink) * global_ref

        # 3. Ratios de fuerza relativa adimensional con amortiguamiento elástico (gamma = 0.65)
        # Previene la sobreestimación cuadrática multiplicativa de Dixon-Coles en extremos
        gamma = 0.65
        att_ratio_h = (max(0.40, h_att_shrunk) / global_ref) ** gamma
        def_ratio_a = (max(0.40, a_def_shrunk) / global_ref) ** gamma
        att_ratio_a = (max(0.40, a_att_shrunk) / global_ref) ** gamma
        def_ratio_h = (max(0.40, h_def_shrunk) / global_ref) ** gamma

        # 4. Ponderación posicional de ausencias clave
        h_att_mult, h_def_mult = self._evaluate_absences_impact(home.key_absences)
        a_att_mult, a_def_mult = self._evaluate_absences_impact(away.key_absences)

        # 5. Expectativa base modulada por el promedio real de la competición y localía
        lambda_home = league_avg_goals * home_advantage * att_ratio_h * def_ratio_a * h_att_mult * a_def_mult
        mu_away = league_avg_goals * att_ratio_a * def_ratio_h * a_att_mult * h_def_mult

        # 6. Ajuste por histórico H2H con shrinkage proporcional a la muestra
        if h2h.total_matches_analyzed > 0:
            w_h2h = min(0.15, h2h.total_matches_analyzed * 0.03)
            h2h_shrunk_rate = (0.60 * h2h.avg_total_goals_h2h + 0.40 * (league_avg_goals * 2.0)) / 2.0
            lambda_home = (1.0 - w_h2h) * lambda_home + w_h2h * (h2h_shrunk_rate * 1.05)
            mu_away = (1.0 - w_h2h) * mu_away + w_h2h * (h2h_shrunk_rate * 0.95)

        # Rango seguro y realista de lambdas en fútbol profesional (máximo 3.20 en localía extrema)
        lambda_home = float(np.clip(lambda_home, 0.35, 3.20))
        mu_away = float(np.clip(mu_away, 0.30, 2.70))

        return lambda_home, mu_away

    def _dixon_coles_tau(self, x: int, y: int, lambda_val: float, mu_val: float) -> float:
        """
        Función de corrección tau de Dixon & Coles (1997) para baja anotación.
        """
        rho = self.rho
        if x == 0 and y == 0:
            return 1.0 - (lambda_val * mu_val * rho)
        elif x == 0 and y == 1:
            return 1.0 + (lambda_val * rho)
        elif x == 1 and y == 0:
            return 1.0 + (mu_val * rho)
        elif x == 1 and y == 1:
            return 1.0 - rho
        else:
            return 1.0

    def compute_bivariate_matrix(self, lambda_home: float, mu_away: float, apply_dixon_coles: bool = True) -> np.ndarray:
        """
        Calcula la matriz de probabilidad conjunta (max_goals x max_goals)
        con ajuste Dixon-Coles y normalización.
        En partidos en vivo, apply_dixon_coles=False para no distorsionar goles adicionales con tau.
        """
        matrix = np.zeros((self.max_goals + 1, self.max_goals + 1), dtype=float)

        for x in range(self.max_goals + 1):
            prob_x = poisson.pmf(x, lambda_home)
            for y in range(self.max_goals + 1):
                prob_y = poisson.pmf(y, mu_away)
                tau = self._dixon_coles_tau(x, y, lambda_home, mu_away) if apply_dixon_coles else 1.0
                matrix[x, y] = max(0.0, prob_x * prob_y * tau)

        # Normalizar para que la suma total sea exactamente 1.0
        total_sum = matrix.sum()
        if total_sum > 0:
            matrix /= total_sum

        return matrix

    def _parse_live_info(self, features: MatchRawFeatures) -> Tuple[int, int, int]:
        """
        Extrae los goles actuales (home, away) y el minuto aproximado transcurrido de un partido en vivo.
        Retorna (current_home_goals, current_away_goals, elapsed_minutes).
        """
        if not getattr(features, "is_live", False):
            return 0, 0, 0

        score_str = getattr(features, "live_score", "") or ""
        minute_str = getattr(features, "live_minute", "") or ""

        # Parsear goles (ej: "2 - 1", "1-0", "0:0")
        goals_h, goals_a = 0, 0
        score_match = re.search(r"(\d+)\s*[-:]\s*(\d+)", score_str)
        if score_match:
            goals_h = int(score_match.group(1))
            goals_a = int(score_match.group(2))

        elapsed_min = parse_elapsed_minute(minute_str)
        return goals_h, goals_a, elapsed_min

    def predict(self, features: MatchRawFeatures) -> Dict:
        """
        Ejecuta la inferencia de Poisson Bivariado y devuelve todas las métricas
        probabilísticas de 1X2, goles, córners y tarjetas.
        Si el partido es EN VIVO, da prioridad absoluta al marcador parcial y tiempo restante.
        """
        is_live = getattr(features, "is_live", False)
        curr_gh, curr_ga, elapsed_min = self._parse_live_info(features)

        lambda_base_h, mu_base_a = self._calculate_lambdas(features)

        if is_live:
            # Fracción de tiempo restante de juego calculada con la curva de intensidad real no lineal
            time_remaining_ratio = calculate_remaining_goal_ratio(elapsed_min)

            # -------------------------------------------------------------
            # Factor 1: Ventaja Numérica por Tarjetas Rojas en Vivo
            # Cada expulsión reduce el ataque en ~32% y aumenta la concesión en ~38%
            # -------------------------------------------------------------
            reds_h = int(getattr(features, "live_red_cards_home", 0) or 0)
            reds_a = int(getattr(features, "live_red_cards_away", 0) or 0)

            att_mod_h = max(0.35, 1.0 - (0.32 * reds_h))
            def_mod_h = 1.0 + (0.38 * reds_a)

            att_mod_a = max(0.35, 1.0 - (0.32 * reds_a))
            def_mod_a = 1.0 + (0.38 * reds_h)

            # -------------------------------------------------------------
            # Factor 2: Presión Ofensiva In-Play (Tiros a Puerta en Directo)
            # Modula suavemente la expectativa ofensiva restante según el asedio real
            # -------------------------------------------------------------
            sot_h = getattr(features, "live_shots_on_target_home", None)
            sot_a = getattr(features, "live_shots_on_target_away", None)
            pressure_h = 1.0
            pressure_a = 1.0
            if sot_h is not None and sot_a is not None and elapsed_min >= 20:
                sot_diff = int(sot_h) - int(sot_a)
                pressure_h = float(np.clip(1.0 + (sot_diff * 0.04), 0.75, 1.30))
                pressure_a = float(np.clip(1.0 - (sot_diff * 0.04), 0.75, 1.30))

            # Escalar lambdas al tiempo restante modulados por ventaja numérica y asedio
            lambda_home = lambda_base_h * time_remaining_ratio * att_mod_h * def_mod_h * pressure_h
            mu_away = mu_base_a * time_remaining_ratio * att_mod_a * def_mod_a * pressure_a
        else:
            lambda_home = lambda_base_h
            mu_away = mu_base_a

        # En vivo: apply_dixon_coles=False porque los goles adicionales no son el marcador global 0-0
        matrix = self.compute_bivariate_matrix(lambda_home, mu_away, apply_dixon_coles=not is_live)

        # -------------------------------------------------------------
        # Cálculo Condicional 1X2 y Goles
        # -------------------------------------------------------------
        home_win_p = 0.0
        draw_p = 0.0
        away_win_p = 0.0

        over_1_5 = 0.0
        over_2_5 = 0.0
        over_3_5 = 0.0
        btts = 0.0

        total_goals_dist = {0: 0.0, 1: 0.0, 2: 0.0, 3: 0.0, 4: 0.0, 5: 0.0}
        score_probabilities = []

        for add_x in range(self.max_goals + 1):
            for add_y in range(self.max_goals + 1):
                p = float(matrix[add_x, add_y])
                final_gh = curr_gh + add_x
                final_ga = curr_ga + add_y
                tot_goals = final_gh + final_ga

                # 1X2
                if final_gh > final_ga:
                    home_win_p += p
                elif final_gh == final_ga:
                    draw_p += p
                else:
                    away_win_p += p

                # Líneas de goles
                if tot_goals > 1.5:
                    over_1_5 += p
                if tot_goals > 2.5:
                    over_2_5 += p
                if tot_goals > 3.5:
                    over_3_5 += p
                if final_gh >= 1 and final_ga >= 1:
                    btts += p

                bucket = min(tot_goals, 5)
                total_goals_dist[bucket] += p

                score_probabilities.append((f"{final_gh} - {final_ga}", p * 100))

        # Sumar duplicados de marcadores si se alcanzaron por distintas combinaciones
        consolidated_scores = {}
        for sc, prob in score_probabilities:
            consolidated_scores[sc] = consolidated_scores.get(sc, 0.0) + prob

        sorted_scores = sorted(consolidated_scores.items(), key=lambda x: x[1], reverse=True)
        top_scores = sorted_scores[:6]
        most_likely_score = top_scores[0][0] if top_scores else f"{curr_gh} - {curr_ga}"

        expected_total_goals = float(curr_gh + curr_ga + lambda_home + mu_away)

        # -------------------------------------------------------------
        # Cálculo de Probabilidades Dinámicas en Vivo (Goles y Córners)
        # -------------------------------------------------------------
        curr_total_goals = curr_gh + curr_ga if is_live else 0
        no_more_goals_p = float(matrix[0, 0]) if is_live else 0.0
        more_goals_p = float(1.0 - no_more_goals_p) if is_live else 0.0
        
        plus_2_goals_p = float(sum(matrix[x, y] for x in range(self.max_goals + 1) for y in range(self.max_goals + 1) if (x + y) >= 2)) if is_live else 0.0
        plus_3_goals_p = float(sum(matrix[x, y] for x in range(self.max_goals + 1) for y in range(self.max_goals + 1) if (x + y) >= 3)) if is_live else 0.0

        live_goal_lines = []
        if is_live:
            live_goal_lines = [
                {
                    "line": f"Sin más goles (+0) [Marcador final {curr_gh} - {curr_ga}]",
                    "over_threshold": float(curr_total_goals),
                    "probability": round(no_more_goals_p * 100, 1)
                },
                {
                    "line": f"+1 gol adicional [Más de {curr_total_goals}.5 goles]",
                    "over_threshold": float(curr_total_goals + 0.5),
                    "probability": round(more_goals_p * 100, 1)
                },
                {
                    "line": f"+2 goles adicionales [Más de {curr_total_goals + 1}.5 goles]",
                    "over_threshold": float(curr_total_goals + 1.5),
                    "probability": round(plus_2_goals_p * 100, 1)
                },
                {
                    "line": f"+3 goles adicionales [Más de {curr_total_goals + 2}.5 goles]",
                    "over_threshold": float(curr_total_goals + 2.5),
                    "probability": round(plus_3_goals_p * 100, 1)
                }
            ]

        # -------------------------------------------------------------
        # Proyección de Córners (Dinámica, No Sesgada y Calibrada)
        # -------------------------------------------------------------
        home_corners_rate = features.home_stats.avg_corners
        away_corners_rate = features.away_stats.avg_corners

        # Ajuste dinámico de córners por presión ofensiva relativa y control territorial local (+10% home / -10% away)
        lambda_ratio_h = max(0.5, lambda_base_h / self.league_avg_goals)
        mu_ratio_a = max(0.5, mu_base_a / self.league_avg_goals)

        exp_corners_home = home_corners_rate * (0.65 + 0.35 * lambda_ratio_h) * 1.10
        exp_corners_away = away_corners_rate * (0.65 + 0.35 * mu_ratio_a) * 0.90
        corners_combined = exp_corners_home + exp_corners_away

        # Integrar H2H solo si hay historial con partidos analizados reales
        if features.h2h.total_matches_analyzed > 0 and features.h2h.avg_total_corners_h2h > 0:
            expected_corners_base = round(corners_combined * 0.75 + features.h2h.avg_total_corners_h2h * 0.25, 1)
        else:
            expected_corners_base = round(corners_combined, 1)

        curr_corners = None
        expected_corners_rem = 0.0
        no_more_corners_p = 0.0
        more_corners_p = 0.0
        live_corner_lines = []

        if is_live:
            # Proyección para el tiempo restante usando curva acumulada de saques de esquina
            time_rem_ratio = calculate_remaining_corner_ratio(elapsed_min)
            expected_corners_rem = round(expected_corners_base * time_rem_ratio, 1)

            # Si el scraper o el usuario detectaron córners actuales en directo, usarlos condicionadamente
            # NUNCA inventar un 5 por defecto si no hay datos en directo
            if getattr(features, "live_corners", None) is not None:
                curr_corners = int(features.live_corners)
                # Total proyectado acumulado = córners ya ocurridos + córners esperados en tiempo restante
                expected_corners = round(curr_corners + expected_corners_rem, 1)

                # Probabilidades Over 8.5, 9.5, 10.5 condicionadas estrictamente a los córners ya disputados
                needed_8_5 = 9 - curr_corners
                if needed_8_5 <= 0:
                    over_8_5_corners = 100.0
                else:
                    over_8_5_corners = float(1.0 - poisson.cdf(needed_8_5 - 1, max(0.05, expected_corners_rem))) * 100

                needed_9_5 = 10 - curr_corners
                if needed_9_5 <= 0:
                    over_9_5_corners = 100.0
                else:
                    over_9_5_corners = float(1.0 - poisson.cdf(needed_9_5 - 1, max(0.05, expected_corners_rem))) * 100

                needed_10_5 = 11 - curr_corners
                if needed_10_5 <= 0:
                    over_10_5_corners = 100.0
                else:
                    over_10_5_corners = float(1.0 - poisson.cdf(needed_10_5 - 1, max(0.05, expected_corners_rem))) * 100
            else:
                # Si no se detectaron córners en directo, proyectar la expectativa base sin inventar 5
                curr_corners = None
                expected_corners = round(expected_corners_base, 1)
                over_8_5_corners = float(1.0 - poisson.cdf(8, expected_corners)) * 100
                over_9_5_corners = float(1.0 - poisson.cdf(9, expected_corners)) * 100
                over_10_5_corners = float(1.0 - poisson.cdf(10, expected_corners)) * 100

            no_more_corners_p = float(poisson.pmf(0, max(0.2, expected_corners_rem)))
            more_corners_p = float(1.0 - no_more_corners_p)
            live_corner_lines = [
                {"line": "Sin córners adicionales en tiempo restante", "probability": round(no_more_corners_p * 100, 1)},
                {"line": "+1 córner o más en tiempo restante", "probability": round(more_corners_p * 100, 1)},
                {"line": "+2 córners o más en tiempo restante", "probability": round(float(1.0 - poisson.cdf(1, max(0.05, expected_corners_rem))) * 100, 1)},
                {"line": "+3 córners o más en tiempo restante", "probability": round(float(1.0 - poisson.cdf(2, max(0.05, expected_corners_rem))) * 100, 1)}
            ]

            # Garantizar monotonía
            over_8_5_corners = min(100.0, max(0.0, over_8_5_corners))
            over_9_5_corners = min(over_8_5_corners, max(0.0, over_9_5_corners))
            over_10_5_corners = min(over_9_5_corners, max(0.0, over_10_5_corners))
        else:
            expected_corners = round(expected_corners_base, 1)
            over_8_5_corners = float(1.0 - poisson.cdf(8, expected_corners)) * 100
            over_9_5_corners = float(1.0 - poisson.cdf(9, expected_corners)) * 100
            over_10_5_corners = float(1.0 - poisson.cdf(10, expected_corners)) * 100

        # -------------------------------------------------------------
        # Proyección de Tarjetas
        # -------------------------------------------------------------
        home_cards = features.home_stats.avg_cards
        away_cards = features.away_stats.avg_cards
        if features.h2h.avg_total_cards_h2h > 0:
            expected_cards = (home_cards + away_cards) * 0.65 + (features.h2h.avg_total_cards_h2h) * 0.35
        else:
            expected_cards = home_cards + away_cards

        over_3_5_cards = float(1.0 - poisson.cdf(3, expected_cards)) * 100
        over_4_5_cards = float(1.0 - poisson.cdf(4, expected_cards)) * 100
        red_card_risk = float(np.clip((expected_cards / 5.0) * 18.0, 8.0, 35.0))

        return {
            "model_name": "poisson_dixon_coles",
            "is_live": is_live,
            "lambda_home": round(lambda_home, 2),
            "mu_away": round(mu_away, 2),
            "winner_probs": {
                "home_win": round(home_win_p * 100, 2),
                "draw": round(draw_p * 100, 2),
                "away_win": round(away_win_p * 100, 2),
            },
            "goals": {
                "expected_total": round(expected_total_goals, 2),
                "most_likely_score": most_likely_score,
                "over_1_5_pct": round(over_1_5 * 100, 2),
                "over_2_5_pct": round(over_2_5 * 100, 2),
                "over_3_5_pct": round(over_3_5 * 100, 2),
                "both_teams_to_score_pct": round(btts * 100, 2),
                "is_live": is_live,
                "current_goals": curr_total_goals if is_live else None,
                "no_more_goals_pct": round(no_more_goals_p * 100, 1) if is_live else None,
                "more_goals_pct": round(more_goals_p * 100, 1) if is_live else None,
                "plus_1_goal_pct": round(more_goals_p * 100, 1) if is_live else None,
                "plus_2_goals_pct": round(plus_2_goals_p * 100, 1) if is_live else None,
                "plus_3_goals_pct": round(plus_3_goals_p * 100, 1) if is_live else None,
                "live_lines": live_goal_lines,
                "goals_distribution": [
                    {"goals": f"{k} Gol{'es' if k != 1 else ''}" if k < 5 else "5+ Goles", "probability": round(v * 100, 1)}
                    for k, v in total_goals_dist.items()
                ],
                "top_scores": [
                    {"score": s[0], "probability": round(s[1], 1)} for s in top_scores
                ]
            },
            "corners": {
                "expected_total": round(expected_corners, 1),
                "current_corners": curr_corners if is_live else None,
                "over_8_5_pct": round(over_8_5_corners, 1),
                "over_9_5_pct": round(over_9_5_corners, 1),
                "over_10_5_pct": round(over_10_5_corners, 1),
                "is_live": is_live,
                "expected_remaining_corners": expected_corners_rem if is_live else None,
                "no_more_corners_pct": round(no_more_corners_p * 100, 1) if is_live else None,
                "more_corners_pct": round(more_corners_p * 100, 1) if is_live else None,
                "live_corners_lines": live_corner_lines
            },
            "cards": {
                "expected_total": round(expected_cards, 1),
                "over_3_5_pct": round(over_3_5_cards, 1),
                "over_4_5_pct": round(over_4_5_cards, 1),
                "red_card_risk_pct": round(red_card_risk, 1)
            }
        }

poisson_model = DixonColesPoissonModel()
