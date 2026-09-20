"""
AeroTwin-X telemetry simulator.

Generates smooth, physically-motivated, CLEARLY SYNTHETIC time-series
telemetry for an aero-piston engine. This is not random-per-tick noise —
the simulator owns continuous engine state (RPM, CHT, oil temperature,
degradation accumulators) and steps it forward each tick using
exponential-lag dynamics toward scenario-driven targets, so faults have
recognisable temporal signatures rather than looking like sensor noise.

Healthy-engine relationships are shared with the Physics Twin
(physics/engine_model.py) — see that module's docstring for why. Fault
scenarios add deltas ON TOP of that shared healthy baseline.
"""
from __future__ import annotations

import math
import random
from dataclasses import dataclass, field

from physics.engine_model import expected_values, expected_rpm
from schemas.telemetry import TelemetryFrame, DataSource, ScenarioName
from telemetry.scenarios import get_environment, get_degradation_profile


def _lag_step(current: float, target: float, dt: float, tau: float) -> float:
    """One step of first-order exponential lag toward `target`."""
    if tau <= 0:
        return target
    alpha = 1.0 - math.exp(-dt / tau)
    return current + (target - current) * alpha


@dataclass
class _EngineState:
    rpm: float = 1700.0
    throttle_pct: float = 65.0
    cht_true_c: float = 95.0
    egt_true_c: float = 620.0
    oil_temperature_c: float = 60.0

    accumulated_operating_hours: float = 0.0
    elapsed_scenario_seconds: float = 0.0

    thermal_bias_c: float = 0.0
    vibration_bias_mms: float = 0.0
    sensor_drift_bias_c: float = 0.0  # CHT SENSOR-ONLY bias; does not affect true engine state

    combustion_phase: float = 0.0


class EngineSimulator:
    """Owns one engine's continuous simulated state. Not thread-safe by
    design — one simulator instance per active demo session."""

    def __init__(self, scenario: ScenarioName = ScenarioName.NORMAL_CRUISE, seed: int | None = 42):
        self._rng = random.Random(seed)
        self.scenario = scenario
        env = get_environment(scenario)
        self._altitude_ft = env.altitude_ft
        self._ambient_temperature_c = env.ambient_temperature_c

        # Start already AT the scenario's operating point (representing an
        # aircraft already in cruise when the operator selects/switches a
        # scenario) rather than idling from a cold-start default — a
        # demo/test that samples "the first few seconds" should see
        # steady-state behaviour, not an engine spool-up transient.
        baseline = expected_values(
            throttle_pct=env.throttle_pct,
            altitude_ft=env.altitude_ft,
            ambient_temperature_c=env.ambient_temperature_c,
        )
        self.state = _EngineState(
            rpm=expected_rpm(env.throttle_pct),
            throttle_pct=env.throttle_pct,
            cht_true_c=baseline.expected_cht_c,
            egt_true_c=baseline.expected_egt_c,
            oil_temperature_c=baseline.expected_oil_temperature_c,
        )

    def set_scenario(self, scenario: ScenarioName) -> None:
        """Switch scenario mid-demo. Engine physical state (RPM/CHT/etc.)
        carries over smoothly; fault-growth timers reset so each fault
        demonstration starts from a clean ramp."""
        self.scenario = scenario
        env = get_environment(scenario)
        self._altitude_ft = env.altitude_ft
        self._ambient_temperature_c = env.ambient_temperature_c
        self.state.throttle_pct_target = env.throttle_pct  # type: ignore[attr-defined]
        self.state.elapsed_scenario_seconds = 0.0

    def step(self, dt_seconds: float = 1.0) -> TelemetryFrame:
        s = self.state
        env = get_environment(self.scenario)
        profile = get_degradation_profile(self.scenario)
        dt_min = dt_seconds / 60.0
        s.elapsed_scenario_seconds += dt_seconds
        s.accumulated_operating_hours += dt_seconds / 3600.0

        # --- throttle & rpm: slow lag toward the scenario's target, plus tiny noise
        s.throttle_pct = _lag_step(s.throttle_pct, env.throttle_pct, dt_seconds, tau=2.0)
        s.throttle_pct += self._rng.gauss(0, 0.3)
        s.throttle_pct = max(0.0, min(100.0, s.throttle_pct))

        target_rpm = expected_rpm(s.throttle_pct)
        s.rpm = _lag_step(s.rpm, target_rpm, dt_seconds, tau=3.0)
        s.rpm += self._rng.gauss(0, 8.0)

        # --- healthy baseline from the shared physics model
        baseline = expected_values(
            throttle_pct=s.throttle_pct,
            altitude_ft=self._altitude_ft,
            ambient_temperature_c=self._ambient_temperature_c,
        )

        # --- degradation accumulators
        s.thermal_bias_c += profile.thermal_drift_rate_c_per_min * dt_min
        s.vibration_bias_mms += profile.vibration_drift_rate_mms_per_min * dt_min
        s.sensor_drift_bias_c += profile.sensor_drift_rate_c_per_min * dt_min

        # --- combustion instability: irregular EGT/vibration pulses (misfire-like)
        combustion_amp = profile.combustion_instability_amplitude
        combustion_pulse_egt = 0.0
        combustion_pulse_vibration = 0.0
        fuel_flow_dropout = 0.0
        if combustion_amp > 0:
            s.combustion_phase += dt_seconds
            if self._rng.random() < 0.12 * combustion_amp:
                combustion_pulse_egt = self._rng.uniform(-1, 1) * 40.0 * combustion_amp
                combustion_pulse_vibration = abs(self._rng.uniform(0, 1)) * 3.0 * combustion_amp
                fuel_flow_dropout = self._rng.uniform(0, 1) * 1.5 * combustion_amp

        # --- true (fault-affected) CHT / EGT, lagged for thermal mass
        target_cht_true = baseline.expected_cht_c + s.thermal_bias_c
        target_egt_true = baseline.expected_egt_c + s.thermal_bias_c * 0.8 + combustion_pulse_egt
        s.cht_true_c = _lag_step(s.cht_true_c, target_cht_true, dt_seconds, tau=45.0)
        s.egt_true_c = _lag_step(s.egt_true_c, target_egt_true, dt_seconds, tau=5.0)

        target_oil_temp = baseline.expected_oil_temperature_c + 0.3 * s.thermal_bias_c
        s.oil_temperature_c = _lag_step(s.oil_temperature_c, target_oil_temp, dt_seconds, tau=60.0)

        # --- reported CHT includes the *sensor-only* drift (true engine state above is unaffected)
        reported_cht_c = s.cht_true_c + s.sensor_drift_bias_c + self._rng.gauss(0, 0.4)
        reported_egt_c = s.egt_true_c + self._rng.gauss(0, 1.5)

        # --- fuel flow: correlates with load/rpm; combustion anomaly causes irregular dropouts
        rpm_frac = max(0.0, min(1.0, (s.rpm - 1700.0) / (5500.0 - 1700.0)))
        fuel_flow_lph = baseline.expected_fuel_flow_lph - fuel_flow_dropout + self._rng.gauss(0, 0.15)
        fuel_flow_lph = max(0.0, fuel_flow_lph)

        # --- oil pressure: from baseline + noise
        oil_pressure_psi = baseline.expected_oil_pressure_psi + self._rng.gauss(0, 0.8)

        # --- vibration: baseline rises with RPM, plus degradation + combustion pulses + noise
        baseline_vibration = 1.0 + 2.5 * rpm_frac
        vibration_mms = (
            baseline_vibration
            + s.vibration_bias_mms
            + combustion_pulse_vibration
            + abs(self._rng.gauss(0, 0.15))
        )

        # --- electrical system: 28V bus. Alternator load tracks engine load;
        # bus voltage sags slightly as electrical load rises and dips a touch
        # with accumulated degradation (representing a tiring alternator).
        alternator_load_pct = max(0.0, min(120.0, 35.0 + 45.0 * rpm_frac + self._rng.gauss(0, 1.2)))
        battery_voltage_v = (
            28.2
            - 0.9 * max(0.0, (alternator_load_pct - 60.0) / 60.0)
            - 0.15 * min(4.0, s.vibration_bias_mms)
            + self._rng.gauss(0, 0.05)
        )
        battery_voltage_v = max(0.0, min(32.0, battery_voltage_v))

        # --- injection timing: nominal advance, retards slightly under thermal
        # stress / combustion instability (a real ECU pulls timing when knock
        # or high CHT is sensed).
        injection_timing_deg = (
            12.0
            - 0.05 * max(0.0, s.thermal_bias_c)
            - 1.5 * combustion_amp
            + self._rng.gauss(0, 0.2)
        )
        injection_timing_deg = max(-10.0, min(45.0, injection_timing_deg))

        frame = TelemetryFrame(
            source=DataSource.SIMULATED,
            rpm=max(0.0, s.rpm),
            cht_c=reported_cht_c,
            egt_c=reported_egt_c,
            oil_pressure_psi=max(0.0, oil_pressure_psi),
            oil_temperature_c=s.oil_temperature_c,
            fuel_flow_lph=fuel_flow_lph,
            vibration_mms=max(0.0, vibration_mms),
            battery_voltage_v=battery_voltage_v,
            alternator_load_pct=alternator_load_pct,
            injection_timing_deg=injection_timing_deg,
            altitude_ft=self._altitude_ft,
            ambient_temperature_c=self._ambient_temperature_c,
            throttle_pct=s.throttle_pct,
            engine_load_pct=rpm_frac * 100.0,
            scenario=self.scenario.value,
        )
        return frame
