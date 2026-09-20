"""
Remaining Useful Life estimator.

RUL is derived from the ACTUAL degradation trajectory (rate of change of
degradation_index vs. operating hours), not hard-coded or randomly
generated. When degradation is flat/negligible, RUL saturates at a large
"no significant degradation detected" ceiling rather than reporting a
fake precise number — this is called out explicitly in `basis`.
"""
from __future__ import annotations

from collections import deque
from datetime import datetime, timezone

import numpy as np

from rul import uncertainty
from schemas.health import RULEstimate

MIN_HISTORY = 20
MAX_HISTORY = 200
END_OF_LIFE_INDEX = 100.0
NO_DEGRADATION_CEILING_HOURS = 500.0  # "no meaningful trend yet" placeholder ceiling, stated in basis


class RULEstimator:
    def __init__(self):
        self._hours_history: deque[float] = deque(maxlen=MAX_HISTORY)
        self._degradation_history: deque[float] = deque(maxlen=MAX_HISTORY)

    def update(self, operating_hours: float, degradation_index: float, timestamp: datetime | None = None) -> RULEstimate:
        timestamp = timestamp or datetime.now(timezone.utc)
        self._hours_history.append(operating_hours)
        self._degradation_history.append(degradation_index)

        n = len(self._hours_history)
        if n < MIN_HISTORY:
            return RULEstimate(
                timestamp=timestamp,
                rul_hours=NO_DEGRADATION_CEILING_HOURS,
                uncertainty_hours=NO_DEGRADATION_CEILING_HOURS * 0.5,
                confidence_pct=20.0,
                basis=(
                    "Insufficient operating history to estimate a degradation rate yet "
                    f"({n}/{MIN_HISTORY} samples). Reporting a placeholder ceiling, not a "
                    "measured estimate."
                ),
            )

        x = np.array(self._hours_history)
        y = np.array(self._degradation_history)

        # Guard against a degenerate (near-zero variance) x-range early on.
        if np.ptp(x) < 1e-6:
            rate_per_hour = 0.0
            rate_volatility = 1.0
        else:
            # Fit over the whole retained window; residual scatter around
            # the fit is used as a crude "volatility" signal for uncertainty.
            slope, intercept = np.polyfit(x, y, 1)
            rate_per_hour = float(slope)
            fitted = slope * x + intercept
            resid_std = float(np.std(y - fitted))
            rate_volatility = min(1.0, resid_std / 10.0)

        current_degradation = float(y[-1])
        remaining_capacity = max(0.0, END_OF_LIFE_INDEX - current_degradation)

        if rate_per_hour <= 1e-4:
            rul_hours = NO_DEGRADATION_CEILING_HOURS
            basis = (
                "No significant upward degradation trend detected in the current window; "
                f"reporting the prototype's planning-horizon ceiling ({NO_DEGRADATION_CEILING_HOURS:.0f}h), "
                "not a measured time-to-failure."
            )
        else:
            rul_hours = min(NO_DEGRADATION_CEILING_HOURS, remaining_capacity / rate_per_hour)
            basis = (
                f"Derived from fitted degradation rate of {rate_per_hour:.3f} index-points/hour "
                f"over {n} samples spanning {np.ptp(x):.3f} operating hours. Prototype estimate, "
                "not calibrated against real engine failure data."
            )

        uncertainty_hours = uncertainty.estimate_uncertainty_hours(
            rul_hours, history_length=n, min_history=MIN_HISTORY, rate_volatility=rate_volatility
        )
        confidence_pct = uncertainty.estimate_confidence_pct(
            history_length=n, min_history=MIN_HISTORY, rate_volatility=rate_volatility
        )

        return RULEstimate(
            timestamp=timestamp,
            rul_hours=round(rul_hours, 1),
            uncertainty_hours=uncertainty_hours,
            confidence_pct=confidence_pct,
            basis=basis,
        )
