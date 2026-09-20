"""
Degradation tracking.

Per the engineering rules for this prototype, degradation is NOT a random
number — it is a leaky-integrator state that accumulates when stress
indicators (thermal residual, vibration excess, general anomaly score)
are elevated, and slowly decays when the engine returns to normal
operation. This gives RUL something real to be derived from, and makes
the "gradual degradation begins" phase of the demo an actual computed
trajectory rather than a scripted number.
"""
from __future__ import annotations

from datetime import datetime, timezone

from schemas.health import DegradationState

# Prototype accumulation/decay rates — tuned so the demo scenarios show a
# clearly visible trend over a few simulated minutes, not calibrated
# against real engine wear data.
THERMAL_ACCUMULATION_RATE = 1.6   # index points per minute at full stress input
VIBRATION_ACCUMULATION_RATE = 1.3
RESIDUAL_ACCUMULATION_RATE = 1.0
DECAY_RATE_PER_MINUTE = 0.35      # recovery per minute when stress input is ~0


class DegradationTracker:
    def __init__(self):
        self.thermal_component = 0.0
        self.vibration_component = 0.0
        self.residual_component = 0.0
        self.accumulated_operating_hours = 0.0

    def update(
        self,
        dt_seconds: float,
        cht_residual_c: float,
        vibration_excess_mms: float,
        anomaly_score: float,
        timestamp: datetime | None = None,
    ) -> DegradationState:
        timestamp = timestamp or datetime.now(timezone.utc)
        dt_min = dt_seconds / 60.0
        self.accumulated_operating_hours += dt_seconds / 3600.0

        thermal_stress = max(0.0, cht_residual_c) / 10.0          # ~1.0 at 10C residual
        vibration_stress = max(0.0, vibration_excess_mms) / 2.0    # ~1.0 at 2mm/s excess
        residual_stress = anomaly_score / 10.0                     # ~1.0 at anomaly_score=10

        self.thermal_component = max(0.0, min(100.0,
            self.thermal_component + thermal_stress * THERMAL_ACCUMULATION_RATE * dt_min
            - DECAY_RATE_PER_MINUTE * dt_min
        ))
        self.vibration_component = max(0.0, min(100.0,
            self.vibration_component + vibration_stress * VIBRATION_ACCUMULATION_RATE * dt_min
            - DECAY_RATE_PER_MINUTE * dt_min
        ))
        self.residual_component = max(0.0, min(100.0,
            self.residual_component + residual_stress * RESIDUAL_ACCUMULATION_RATE * dt_min
            - DECAY_RATE_PER_MINUTE * dt_min
        ))

        degradation_index = (
            0.4 * self.thermal_component
            + 0.3 * self.vibration_component
            + 0.3 * self.residual_component
        )

        return DegradationState(
            timestamp=timestamp,
            degradation_index=round(min(100.0, degradation_index), 2),
            thermal_component=round(self.thermal_component, 2),
            vibration_component=round(self.vibration_component, 2),
            residual_component=round(self.residual_component, 2),
            accumulated_operating_hours=round(self.accumulated_operating_hours, 4),
        )
