"""
Mission Twin: projects how CURRENT engine degradation state evolves over
a proposed mission, using the same physics/stress relationships as the
live pipeline, applied deterministically (no sensor noise — this is a
forward projection, not a telemetry replay).

Mission profile is modelled as two phases so a genuine "critical phase"
emerges from the model rather than being hard-coded:
  - CLIMB phase: first portion of the mission at max_altitude_ft and
    slightly elevated throttle (representing the climb to altitude).
  - CRUISE phase: remainder of the mission at cruise_altitude_ft and the
    requested average throttle.
"""
from __future__ import annotations

from schemas.health import DegradationState
from schemas.mission import MissionInput, MissionTrajectoryPoint
from mission.mission_model import evaluate_operating_point

CLIMB_PHASE_FRACTION = 0.10
CLIMB_PHASE_MAX_HOURS = 0.5
CLIMB_THROTTLE_BOOST_PCT = 15.0

THERMAL_ACCUMULATION_RATE = 1.6   # matches rul/degradation.py's constant, by design
VIBRATION_ACCUMULATION_RATE = 1.3
DECAY_RATE_PER_HOUR = 0.35 * 60.0 / 60.0  # per-hour equivalent of the live tracker's per-minute decay


def _phase_for_time(t_hours: float, duration_hours: float, mission: MissionInput) -> tuple[float, float, str]:
    climb_hours = min(CLIMB_PHASE_MAX_HOURS, duration_hours * CLIMB_PHASE_FRACTION)
    if t_hours <= climb_hours and climb_hours > 0:
        throttle = min(100.0, mission.average_throttle_pct + CLIMB_THROTTLE_BOOST_PCT)
        altitude = mission.max_altitude_ft
        return throttle, altitude, "climb to mission altitude"
    return mission.average_throttle_pct, mission.cruise_altitude_ft, "cruise"


def simulate_mission(
    mission: MissionInput,
    start_degradation: DegradationState,
    step_hours: float = 0.1,
) -> list[MissionTrajectoryPoint]:
    thermal = start_degradation.thermal_component
    vibration = start_degradation.vibration_component
    residual = start_degradation.residual_component

    trajectory: list[MissionTrajectoryPoint] = []
    t = 0.0
    while t <= mission.duration_hours + 1e-9:
        throttle, altitude, _phase = _phase_for_time(t, mission.duration_hours, mission)
        physics = evaluate_operating_point(
            throttle_pct=throttle,
            altitude_ft=altitude,
            ambient_temperature_c=mission.ambient_temperature_c,
        )

        vibration_stress = max(0.0, physics.expected_vibration_mms - 2.0) / 2.0

        thermal = max(0.0, min(100.0, thermal + physics.thermal_stress * THERMAL_ACCUMULATION_RATE * step_hours - DECAY_RATE_PER_HOUR * step_hours))
        vibration = max(0.0, min(100.0, vibration + vibration_stress * VIBRATION_ACCUMULATION_RATE * step_hours - DECAY_RATE_PER_HOUR * step_hours))
        # residual component decays toward 0 during a forward projection —
        # we have no future sensor anomalies to feed it, only the current
        # carried-over value fading out.
        residual = max(0.0, residual - DECAY_RATE_PER_HOUR * step_hours)

        degradation_index = min(100.0, 0.4 * thermal + 0.3 * vibration + 0.3 * residual)
        health_index = max(0.0, 100.0 - degradation_index)

        trajectory.append(MissionTrajectoryPoint(
            t_hours=round(t, 3),
            health_index=round(health_index, 1),
            egt_c=round(physics.expected_egt_c, 1),
            cht_c=round(physics.expected_cht_c, 1),
            vibration_mms=round(physics.expected_vibration_mms, 2),
            degradation_index=round(degradation_index, 2),
        ))
        t += step_hours

    return trajectory
