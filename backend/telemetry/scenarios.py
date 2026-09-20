"""
Scenario presets for the telemetry simulator.

Each scenario is a *preset + degradation profile*, not an independent
random generator — the simulator (simulator.py) owns the continuous
engine state and applies these presets/profiles to it every tick, so
transitions are smooth and physically-motivated rather than random noise.

IMPORTANT: all numeric relationships here are prototype assumptions for a
small aero-piston engine, chosen to be internally consistent and to
produce recognisable, documented fault signatures for the demo — they are
NOT sourced from a specific certified engine type. See docs/architecture.md.
"""
from __future__ import annotations

from dataclasses import dataclass

from schemas.telemetry import ScenarioName


@dataclass
class EnvironmentPreset:
    """Steady-state environment/operating targets a scenario asks the
    simulator to fly toward."""
    altitude_ft: float
    ambient_temperature_c: float
    throttle_pct: float


@dataclass
class DegradationProfile:
    """Describes how a fault scenario evolves over elapsed scenario-time
    (seconds). All rates are per-hour equivalents scaled down to whatever
    tick rate the simulator uses, so the demo can compress hours into
    minutes without changing the *shape* of the fault signature."""
    thermal_drift_rate_c_per_min: float = 0.0      # extra CHT/EGT bias growth
    vibration_drift_rate_mms_per_min: float = 0.0  # extra vibration growth
    sensor_drift_rate_c_per_min: float = 0.0       # CHT *sensor-only* bias (no true engine change)
    combustion_instability_amplitude: float = 0.0  # 0-1, irregular EGT/vibration oscillation strength


ENVIRONMENT_PRESETS: dict[ScenarioName, EnvironmentPreset] = {
    ScenarioName.NORMAL_CRUISE: EnvironmentPreset(altitude_ft=8000, ambient_temperature_c=15, throttle_pct=65),
    ScenarioName.HIGH_ALTITUDE: EnvironmentPreset(altitude_ft=22000, ambient_temperature_c=-5, throttle_pct=75),
    ScenarioName.HOT_WEATHER: EnvironmentPreset(altitude_ft=6000, ambient_temperature_c=42, throttle_pct=65),
    ScenarioName.THERMAL_DEGRADATION: EnvironmentPreset(altitude_ft=8000, ambient_temperature_c=15, throttle_pct=65),
    ScenarioName.VIBRATION_DEGRADATION: EnvironmentPreset(altitude_ft=8000, ambient_temperature_c=15, throttle_pct=65),
    ScenarioName.SENSOR_DRIFT: EnvironmentPreset(altitude_ft=8000, ambient_temperature_c=15, throttle_pct=65),
    ScenarioName.COMBUSTION_ANOMALY: EnvironmentPreset(altitude_ft=8000, ambient_temperature_c=15, throttle_pct=65),
    ScenarioName.COMBINED_DEGRADATION: EnvironmentPreset(altitude_ft=8000, ambient_temperature_c=15, throttle_pct=65),
}

DEGRADATION_PROFILES: dict[ScenarioName, DegradationProfile] = {
    ScenarioName.NORMAL_CRUISE: DegradationProfile(),
    ScenarioName.HIGH_ALTITUDE: DegradationProfile(),
    ScenarioName.HOT_WEATHER: DegradationProfile(),
    # Rates below are chosen so a live demo shows a clearly visible trend
    # within a few minutes of wall-clock time (compressing what would be
    # hours of real degradation), not a calibration against real failure
    # progression rates.
    ScenarioName.THERMAL_DEGRADATION: DegradationProfile(thermal_drift_rate_c_per_min=9.0),
    ScenarioName.VIBRATION_DEGRADATION: DegradationProfile(vibration_drift_rate_mms_per_min=0.9),
    ScenarioName.SENSOR_DRIFT: DegradationProfile(sensor_drift_rate_c_per_min=6.0),
    ScenarioName.COMBUSTION_ANOMALY: DegradationProfile(combustion_instability_amplitude=0.55),
    ScenarioName.COMBINED_DEGRADATION: DegradationProfile(
        thermal_drift_rate_c_per_min=6.0,
        vibration_drift_rate_mms_per_min=0.6,
    ),
}


def get_environment(scenario: ScenarioName) -> EnvironmentPreset:
    return ENVIRONMENT_PRESETS[scenario]


def get_degradation_profile(scenario: ScenarioName) -> DegradationProfile:
    return DEGRADATION_PROFILES[scenario]
