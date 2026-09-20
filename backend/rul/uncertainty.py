"""
Uncertainty quantification for the RUL estimate.

Kept deliberately simple for the prototype: uncertainty widens when we
have little history to estimate a degradation rate from, and when the
degradation rate itself is volatile (noisy slope estimate). This is a
heuristic, not a calibrated statistical model — labeled as such wherever
it is surfaced.
"""
from __future__ import annotations


def estimate_uncertainty_hours(rul_hours: float, history_length: int, min_history: int, rate_volatility: float) -> float:
    history_factor = max(0.15, 1.0 - min(1.0, history_length / (min_history * 3)))
    base_uncertainty = rul_hours * (0.12 + 0.35 * history_factor)
    volatility_penalty = rul_hours * min(0.5, rate_volatility)
    return round(min(rul_hours, base_uncertainty + volatility_penalty), 1)


def estimate_confidence_pct(history_length: int, min_history: int, rate_volatility: float) -> float:
    history_confidence = min(1.0, history_length / (min_history * 3)) * 90.0
    volatility_penalty = min(40.0, rate_volatility * 100.0)
    return round(max(20.0, history_confidence - volatility_penalty), 1)
