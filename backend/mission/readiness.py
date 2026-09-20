"""
Mission Readiness Engine: turns a projected mission trajectory into a
GREEN / YELLOW / RED decision with an explicit reason, critical phase,
and recommendation — never a bare status with no explanation.
"""
from __future__ import annotations

import numpy as np

from schemas.mission import MissionInput, MissionResult, MissionTrajectoryPoint, RiskLevel
from rul.estimator import NO_DEGRADATION_CEILING_HOURS

CLIMB_PHASE_MAX_HOURS = 0.5
CLIMB_PHASE_FRACTION = 0.10


def _project_end_of_mission_rul(trajectory: list[MissionTrajectoryPoint]) -> tuple[float, float]:
    """Fits the SAME kind of degradation-rate-based RUL used live
    (rul/estimator.py), but over the projected mission trajectory, so the
    Mission Twin's RUL number is derived the same way, not a different
    ad-hoc formula."""
    t = np.array([p.t_hours for p in trajectory])
    d = np.array([p.degradation_index for p in trajectory])
    if np.ptp(t) < 1e-6 or len(t) < 3:
        return NO_DEGRADATION_CEILING_HOURS, NO_DEGRADATION_CEILING_HOURS * 0.5

    slope, intercept = np.polyfit(t, d, 1)
    if slope <= 1e-4:
        return NO_DEGRADATION_CEILING_HOURS, NO_DEGRADATION_CEILING_HOURS * 0.4

    remaining_capacity = max(0.0, 100.0 - d[-1])
    rul_hours = min(NO_DEGRADATION_CEILING_HOURS, remaining_capacity / slope)
    fitted = slope * t + intercept
    resid_std = float(np.std(d - fitted))
    uncertainty_hours = min(rul_hours, rul_hours * (0.15 + min(0.5, resid_std / 10.0)))
    return round(rul_hours, 1), round(uncertainty_hours, 1)


def assess(mission: MissionInput, trajectory: list[MissionTrajectoryPoint]) -> MissionResult:
    end_health = trajectory[-1].health_index
    min_point = min(trajectory, key=lambda p: p.health_index)

    climb_hours = min(CLIMB_PHASE_MAX_HOURS, mission.duration_hours * CLIMB_PHASE_FRACTION)
    critical_phase = "high-altitude climb" if min_point.t_hours <= climb_hours and climb_hours > 0 else "cruise"

    predicted_rul_hours, rul_uncertainty_hours = _project_end_of_mission_rul(trajectory)

    start = trajectory[0]
    end = trajectory[-1]
    thermal_growth_proxy = end.cht_c - start.cht_c
    vibration_growth_proxy = end.vibration_mms - start.vibration_mms

    contributors: list[str] = []
    if thermal_growth_proxy > 5:
        contributors.append("elevated thermal margin consumption (CHT/EGT)")
    if vibration_growth_proxy > 0.5:
        contributors.append("increasing vibration trend")
    if predicted_rul_hours < mission.duration_hours:
        contributors.append("projected RUL shorter than mission duration")
    if not contributors:
        contributors.append("no single dominant contributor — degradation within normal range")

    engine_cannot_complete = predicted_rul_hours < mission.duration_hours
    if engine_cannot_complete or end_health < 55 or min_point.health_index < 40:
        risk_level = RiskLevel.RED
        recommendation = "Inspect cooling/combustion and lubrication systems before deployment; do not fly this mission profile without inspection."
    elif end_health < 80 or min_point.health_index < 70:
        risk_level = RiskLevel.YELLOW
        recommendation = "Mission is achievable but with reduced margin — consider a post-mission inspection and monitor the flagged signals closely in flight."
    else:
        risk_level = RiskLevel.GREEN
        recommendation = "No elevated risk projected for this mission profile under current engine condition."

    return MissionResult(
        mission_input=mission,
        trajectory=trajectory,
        predicted_end_of_mission_health=end_health,
        predicted_rul_hours=predicted_rul_hours,
        rul_uncertainty_hours=rul_uncertainty_hours,
        risk_level=risk_level,
        critical_phase=critical_phase,
        main_contributors=contributors,
        recommendation=recommendation,
    )
