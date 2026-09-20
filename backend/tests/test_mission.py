from datetime import datetime, timezone

from schemas.health import DegradationState
from schemas.mission import MissionInput, MissionType
from mission.simulator import simulate_mission
from mission.readiness import assess


def _healthy_start():
    return DegradationState(
        timestamp=datetime.now(timezone.utc),
        degradation_index=0.0, thermal_component=0.0,
        vibration_component=0.0, residual_component=0.0,
        accumulated_operating_hours=100.0,
    )


def _degraded_start():
    return DegradationState(
        timestamp=datetime.now(timezone.utc),
        degradation_index=70.0, thermal_component=80.0,
        vibration_component=50.0, residual_component=40.0,
        accumulated_operating_hours=500.0,
    )


def test_mission_simulation_produces_trajectory_covering_full_duration():
    mission = MissionInput(
        mission_type=MissionType.NORMAL_ISR, duration_hours=8, cruise_altitude_ft=8000,
        max_altitude_ft=10000, ambient_temperature_c=15, average_throttle_pct=60,
    )
    trajectory = simulate_mission(mission, _healthy_start(), step_hours=0.5)
    assert trajectory[0].t_hours == 0.0
    assert trajectory[-1].t_hours >= 7.5
    assert len(trajectory) > 10


def test_healthy_engine_normal_mission_is_green_or_yellow():
    mission = MissionInput(
        mission_type=MissionType.NORMAL_ISR, duration_hours=4, cruise_altitude_ft=8000,
        max_altitude_ft=9000, ambient_temperature_c=15, average_throttle_pct=55,
    )
    trajectory = simulate_mission(mission, _healthy_start())
    result = assess(mission, trajectory)
    assert result.risk_level.value in ("GREEN", "YELLOW")
    assert result.recommendation


def test_degraded_engine_harsh_mission_is_more_risky_than_healthy_easy_mission():
    easy_mission = MissionInput(
        mission_type=MissionType.NORMAL_ISR, duration_hours=2, cruise_altitude_ft=5000,
        max_altitude_ft=6000, ambient_temperature_c=15, average_throttle_pct=50,
    )
    harsh_mission = MissionInput(
        mission_type=MissionType.HIGH_LOAD_ENDURANCE, duration_hours=10, cruise_altitude_ft=23000,
        max_altitude_ft=24000, ambient_temperature_c=42, average_throttle_pct=90,
    )
    easy_trajectory = simulate_mission(easy_mission, _healthy_start())
    harsh_trajectory = simulate_mission(harsh_mission, _degraded_start())

    easy_result = assess(easy_mission, easy_trajectory)
    harsh_result = assess(harsh_mission, harsh_trajectory)

    risk_rank = {"GREEN": 0, "YELLOW": 1, "RED": 2}
    assert risk_rank[harsh_result.risk_level.value] >= risk_rank[easy_result.risk_level.value]
    assert harsh_result.predicted_end_of_mission_health <= easy_result.predicted_end_of_mission_health


def test_critical_phase_is_labelled():
    mission = MissionInput(
        mission_type=MissionType.HIGH_ALTITUDE, duration_hours=6, cruise_altitude_ft=8000,
        max_altitude_ft=24000, ambient_temperature_c=-5, average_throttle_pct=80,
    )
    trajectory = simulate_mission(mission, _degraded_start())
    result = assess(mission, trajectory)
    assert result.critical_phase in ("high-altitude climb", "cruise")
    assert len(result.main_contributors) >= 1
