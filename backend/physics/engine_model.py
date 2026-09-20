"""
Simplified physics-informed engine baseline ("Physics Twin").

Given the *commanded/observed operating point* (RPM, throttle, altitude,
ambient temperature) — signals that are largely independent of engine
health — this model predicts what a HEALTHY engine's dependent
parameters (EGT, CHT, oil temperature, fuel flow) should look like.

This is the same baseline the telemetry simulator uses to generate
"healthy" ground truth. Fault scenarios in the simulator add deltas on
TOP of this baseline that this model does not know about — that gap is
exactly the residual the AI Health Twin consumes. This is intentional:
it is what makes residuals meaningful in a prototype without real
engine data, rather than being circular.

IMPORTANT: This is a prototype model with documented, simplified
assumptions — not a certified aero-engine performance model. See
docs/architecture.md "Physics Twin Assumptions".
"""
from __future__ import annotations

from dataclasses import dataclass

from physics.thermodynamics import air_density_factor, cooling_efficiency_factor

# --- Documented baseline assumptions (prototype constants) -----------------
IDLE_RPM = 1700.0
MAX_RPM = 5500.0

EGT_BASE_C = 620.0          # EGT at idle, sea level, standard temperature
EGT_LOAD_GAIN_C = 190.0     # additional EGT at 100% load (before altitude effects)

CHT_BASE_C = 95.0           # CHT at idle, sea level, standard temperature
CHT_LOAD_GAIN_C = 95.0      # additional CHT at 100% load, before cooling-efficiency correction

OIL_TEMP_BASE_C = 60.0
OIL_TEMP_CHT_COUPLING = 0.35  # oil temperature tracks a fraction of CHT above baseline

FUEL_FLOW_IDLE_LPH = 4.0
FUEL_FLOW_MAX_LPH = 32.0

OIL_PRESSURE_BASE_PSI = 55.0
OIL_PRESSURE_RPM_GAIN_PSI = 12.0       # more RPM -> modestly higher pressure, saturating
OIL_PRESSURE_HIGH_TEMP_LOSS_PSI = 10.0  # hot oil is thinner -> modest pressure loss


@dataclass
class PhysicsExpectedValues:
    expected_egt_c: float
    expected_cht_c: float
    expected_oil_temperature_c: float
    expected_fuel_flow_lph: float
    expected_oil_pressure_psi: float


def load_fraction_from_throttle(throttle_pct: float) -> float:
    """Engine load lags throttle slightly in reality (turbo/prop response);
    the simulator applies its own lag dynamics on top of this. Here we
    treat load as a direct (saturating) function of throttle for the
    purpose of computing *expected* steady-state values."""
    return max(0.0, min(1.0, throttle_pct / 100.0))


def expected_rpm(throttle_pct: float) -> float:
    load = load_fraction_from_throttle(throttle_pct)
    return IDLE_RPM + (MAX_RPM - IDLE_RPM) * load


def expected_values(
    throttle_pct: float,
    altitude_ft: float,
    ambient_temperature_c: float,
) -> PhysicsExpectedValues:
    load = load_fraction_from_throttle(throttle_pct)
    density = air_density_factor(altitude_ft)
    cooling = cooling_efficiency_factor(altitude_ft)

    # Ambient temperature shifts every thermal parameter roughly 1:1 away
    # from the ISA baseline used inside cooling/density approximations.
    ambient_delta_from_isa = ambient_temperature_c - (15.0 - 1.98 * altitude_ft / 1000.0)

    expected_egt_c = (
        EGT_BASE_C
        + EGT_LOAD_GAIN_C * load
        + 25.0 * (1.0 - density)   # leaner mixture at altitude raises EGT somewhat
        + 0.4 * ambient_delta_from_isa
    )

    expected_cht_c = (
        CHT_BASE_C
        + (CHT_LOAD_GAIN_C * load) / cooling
        + 0.5 * ambient_delta_from_isa
    )

    expected_oil_temperature_c = (
        OIL_TEMP_BASE_C
        + OIL_TEMP_CHT_COUPLING * (expected_cht_c - CHT_BASE_C)
        + 0.3 * ambient_delta_from_isa
    )

    expected_fuel_flow_lph = (
        FUEL_FLOW_IDLE_LPH
        + (FUEL_FLOW_MAX_LPH - FUEL_FLOW_IDLE_LPH) * load / max(density, 0.4)
    )

    rpm = expected_rpm(throttle_pct)
    rpm_frac = (rpm - IDLE_RPM) / (MAX_RPM - IDLE_RPM)
    expected_oil_pressure_psi = (
        OIL_PRESSURE_BASE_PSI
        + OIL_PRESSURE_RPM_GAIN_PSI * min(1.0, rpm_frac)
        - OIL_PRESSURE_HIGH_TEMP_LOSS_PSI * max(0.0, (expected_oil_temperature_c - 90.0) / 40.0)
    )

    return PhysicsExpectedValues(
        expected_egt_c=expected_egt_c,
        expected_cht_c=expected_cht_c,
        expected_oil_temperature_c=expected_oil_temperature_c,
        expected_fuel_flow_lph=expected_fuel_flow_lph,
        expected_oil_pressure_psi=expected_oil_pressure_psi,
    )
