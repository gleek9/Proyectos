"""
Módulo Dixon-Coles MLE (Maximum Likelihood Estimation) con Decaimiento Exponencial Temporal.
Estima parámetros latentes por club (ataque alpha_i, defensa beta_i), ventaja local por liga (gamma_L)
y correlación de marcadores bajos (rho_L) estrictamente antes del corte temporal Out-of-Sample.
"""
import json
import logging
import math
import os
from datetime import datetime
from typing import Dict, List, Optional, Tuple

import numpy as np
from scipy.optimize import minimize

logger = logging.getLogger(__name__)


def resolve_league_code_from_name(competition: Optional[str]) -> Optional[str]:
    comp = (competition or "").lower().strip()
    if not comp:
        return None
    mapping = [
        ("premier", "premier_league"),
        ("laliga 2", "laliga2"),
        ("hypermotion", "laliga2"),
        ("laliga", "laliga"),
        ("serie a", "serie_a"),
        ("bundesliga", "bundesliga"),
        ("ligue 1", "ligue_1"),
        ("eredivisie", "eredivisie"),
        ("primeira", "primeira_liga"),
        ("champions femen", "uwcl"),
        ("uwcl", "uwcl"),
        ("champions", "champions_league"),
        ("liga f", "liga_f"),
        ("wsl", "wsl"),
        ("liga mx femen", "liga_mx_femenil"),
        ("liga mx", "liga_mx"),
    ]
    for needle, code in mapping:
        if needle in comp:
            return code
    return comp.replace(" ", "_")


def _tau_array(hg: np.ndarray, ag: np.ndarray, lam: np.ndarray, mu: np.ndarray, rho: float) -> np.ndarray:
    tau = np.ones_like(lam, dtype=np.float64)
    m00 = (hg == 0) & (ag == 0)
    m01 = (hg == 0) & (ag == 1)
    m10 = (hg == 1) & (ag == 0)
    m11 = (hg == 1) & (ag == 1)
    tau[m00] = 1.0 - lam[m00] * mu[m00] * rho
    tau[m01] = 1.0 + lam[m01] * rho
    tau[m10] = 1.0 + mu[m10] * rho
    tau[m11] = 1.0 - rho
    return np.clip(tau, 1e-4, 2.5)


class DixonColesMLEModel:
    def __init__(self, weights_dir: str = "backend/weights"):
        self.weights_dir = weights_dir
        self.model_path = os.path.join(self.weights_dir, "dixon_coles_mle.json")
        self.leagues: Dict[str, Dict] = {}
        self.cutoff_date: str = "2025-01-01"
        self.load()

    def load(self) -> bool:
        if not os.path.exists(self.model_path):
            return False
        try:
            with open(self.model_path, "r", encoding="utf-8") as f:
                payload = json.load(f)
            self.leagues = payload.get("leagues", {})
            self.cutoff_date = payload.get("cutoff_date", "2025-01-01")
            return bool(self.leagues)
        except Exception as e:
            logger.warning(f"No se pudo cargar Dixon-Coles MLE desde disco: {e}")
            return False

    def save(self) -> None:
        os.makedirs(self.weights_dir, exist_ok=True)
        payload = {
            "cutoff_date": self.cutoff_date,
            "updated_at": datetime.utcnow().isoformat(),
            "leagues": self.leagues,
        }
        with open(self.model_path, "w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2, ensure_ascii=False)

    def fit_league(
        self,
        matches: List[Dict],
        xi_per_day: float = 0.0020,
        l2_reg: float = 3.5,
    ) -> Optional[Dict]:
        """
        Ajusta alpha (ataque), beta (defensa), home_adv y rho para una liga mediante L-BFGS-B.
        """
        if len(matches) < 100:
            return None

        teams = sorted({m["home"] for m in matches} | {m["away"] for m in matches})
        n_teams = len(teams)
        if n_teams < 6:
            return None

        team_idx = {t: i for i, t in enumerate(teams)}
        h_idx = np.array([team_idx[m["home"]] for m in matches], dtype=np.int64)
        a_idx = np.array([team_idx[m["away"]] for m in matches], dtype=np.int64)
        hg = np.array([int(m["hg"]) for m in matches], dtype=np.int64)
        ag = np.array([int(m["ag"]) for m in matches], dtype=np.int64)

        dates = []
        for m in matches:
            try:
                dates.append(datetime.strptime(str(m["date"])[:10], "%Y-%m-%d"))
            except Exception:
                dates.append(datetime(2024, 1, 1))
        max_date = max(dates)
        days_ago = np.array([(max_date - d).days for d in dates], dtype=np.float64)
        weights = np.exp(-xi_per_day * np.maximum(0.0, days_ago))

        # Vector inicial: alpha=0, beta=0, intercept=log(1.3), home_adv=0.22, rho=-0.06
        x0 = np.zeros(2 * n_teams + 3, dtype=np.float64)
        x0[-3] = math.log(1.30)
        x0[-2] = 0.22
        x0[-1] = -0.06

        bounds = [(-1.8, 1.8)] * (2 * n_teams) + [(-0.5, 1.2), (-0.1, 0.7), (-0.22, 0.08)]

        def neg_log_likelihood(params: np.ndarray) -> float:
            alphas = params[:n_teams]
            betas = params[n_teams:2 * n_teams]
            mu0 = params[-3]
            gamma = params[-2]
            rho = params[-1]

            # Centrado suave para identificabilidad (sum alpha = 0, sum beta = 0)
            alpha_mean = np.mean(alphas)
            beta_mean = np.mean(betas)
            a_c = alphas - alpha_mean
            b_c = betas - beta_mean

            log_lam = np.clip(mu0 + gamma + a_c[h_idx] + b_c[a_idx], -3.0, 2.2)
            log_mu = np.clip(mu0 + a_c[a_idx] + b_c[h_idx], -3.0, 2.2)
            lam = np.exp(log_lam)
            mu = np.exp(log_mu)

            tau = _tau_array(hg, ag, lam, mu, rho)
            ll = weights * (
                hg * log_lam - lam
                + ag * log_mu - mu
                + np.log(tau)
            )
            penalty = l2_reg * float(np.sum(a_c ** 2) + np.sum(b_c ** 2))
            ident_pen = 0.5 * float(alpha_mean ** 2 + beta_mean ** 2)
            return -float(np.sum(ll)) + penalty + ident_pen

        res = minimize(neg_log_likelihood, x0, method="L-BFGS-B", bounds=bounds, options={"maxiter": 250})
        params = res.x
        alphas = params[:n_teams] - np.mean(params[:n_teams])
        betas = params[n_teams:2 * n_teams] - np.mean(params[n_teams:2 * n_teams])
        mu0 = float(params[-3])
        gamma = float(params[-2])
        rho = float(params[-1])

        teams_dict = {
            t: {"alpha": round(float(alphas[i]), 5), "beta": round(float(betas[i]), 5)}
            for i, t in enumerate(teams)
        }
        return {
            "mu0": round(mu0, 5),
            "home_adv": round(gamma, 5),
            "rho": round(rho, 5),
            "n_matches": len(matches),
            "teams": teams_dict,
        }

    def fit_all_leagues_from_db(self, cutoff_date: str = "2025-01-01", xi_per_day: float = 0.0020) -> Dict[str, Dict]:
        """Entrena los parámetros MLE por liga usando exclusivamente partidos < cutoff_date."""
        from backend.app.db import HistoricalMatch, SessionLocal

        self.cutoff_date = cutoff_date
        db = SessionLocal()
        try:
            rows = (
                db.query(HistoricalMatch)
                .filter(HistoricalMatch.match_date < cutoff_date)
                .order_by(HistoricalMatch.match_date.asc(), HistoricalMatch.id.asc())
                .all()
            )
        finally:
            db.close()

        by_league: Dict[str, List[Dict]] = {}
        for m in rows:
            by_league.setdefault(m.league_code, []).append({
                "home": m.home_team,
                "away": m.away_team,
                "hg": m.home_goals,
                "ag": m.away_goals,
                "date": m.match_date,
            })

        fitted: Dict[str, Dict] = {}
        for l_code, lg_matches in by_league.items():
            res = self.fit_league(lg_matches, xi_per_day=xi_per_day)
            if res is not None:
                fitted[l_code] = res
                logger.info(
                    f"Dixon-Coles MLE [{l_code}]: {res['n_matches']} partidos | "
                    f"gamma={res['home_adv']:.3f} | rho={res['rho']:.3f} | clubes={len(res['teams'])}"
                )

        self.leagues = fitted
        self.save()
        return fitted

    def get_match_lambdas(
        self,
        competition: Optional[str],
        home_team: str,
        away_team: str,
    ) -> Optional[Tuple[float, float, float]]:
        """Retorna (lambda_home_mle, mu_away_mle, rho_mle) si ambos clubes están en la liga MLE."""
        if not self.leagues:
            return None

        l_code = resolve_league_code_from_name(competition)
        candidate_leagues = [self.leagues[l_code]] if (l_code and l_code in self.leagues) else []
        if not candidate_leagues:
            # Búsqueda fallback por presencia directa de ambos clubes en una misma liga MLE
            for lg_data in self.leagues.values():
                teams = lg_data.get("teams", {})
                if home_team in teams and away_team in teams:
                    candidate_leagues.append(lg_data)
                    break

        for lg in candidate_leagues:
            teams = lg.get("teams", {})
            h_p = teams.get(home_team)
            a_p = teams.get(away_team)
            if h_p and a_p:
                mu0 = float(lg["mu0"])
                gamma = float(lg["home_adv"])
                rho = float(lg["rho"])
                lam_h = float(np.clip(math.exp(mu0 + gamma + h_p["alpha"] + a_p["beta"]), 0.35, 3.40))
                mu_a = float(np.clip(math.exp(mu0 + a_p["alpha"] + h_p["beta"]), 0.25, 2.90))
                return lam_h, mu_a, rho
        return None


dixon_coles_mle = DixonColesMLEModel()

