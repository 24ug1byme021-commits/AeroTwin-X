"""
Mission stress model.

Reuses the SAME physics engine model (physics/engine_model.py) used for
live telemetry residuals, so a mission's projected EGT/CHT come from the
identical assumptions as the rest of the system — not a separate,
inconsistent "mission math". This module adds the mapping from those
expected thermal values to a degradation STRESS RATE, which is a
prototype approximation documented here and in docs/architecture.md.
"""
from __future__ import annotations

from dataclasses import dataclass

from physics.engine_model import expected_values, expected_rpm

CHT_COMFORT_C = 150.0     # above this, thermal stress accrues
CHT_STRESS_SCALE_C = 18.0
VIBRATION_BASELINE_REF_RPM_FRAC_SCALE = 2.5


@dataclass
class MissionPointPhysics:
    expected_egt_c: float
    expected_cht_c: float
    expected_vibration_mms: float
    thermal_stress: float  # unitless, ~0 at comfortable CHT, grows above it


def evaluate_operating_point(throttle_pct: float, altitude_ft: float, ambient_temperature_c: float) -> MissionPointPhysics:
    ev = expected_values(throttle_pct=throttle_pct, altitude_ft=altitude_ft, ambient_temperature_c=ambient_temperature_c)
    rpm = expected_rpm(throttle_pct)
    rpm_frac = max(0.0, min(1.0, (rpm - 1700.0) / (5500.0 - 1700.0)))
    expected_vibration_mms = 1.0 + VIBRATION_BASELINE_REF_RPM_FRAC_SCALE * rpm_frac

    thermal_stress = max(0.0, (ev.expected_cht_c - CHT_COMFORT_C) / CHT_STRESS_SCALE_C)

    return MissionPointPhysics(
        expected_egt_c=ev.expected_egt_c,
        expected_cht_c=ev.expected_cht_c,
        expected_vibration_mms=expected_vibration_mms,
        thermal_stress=thermal_stress,
    )
