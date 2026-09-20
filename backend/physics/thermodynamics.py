"""
Low-level atmospheric/thermodynamic helper functions shared by the
telemetry simulator's "healthy baseline" and the physics twin's
"expected value" predictor.

These are deliberately simple, documented approximations for a hackathon
prototype — not a certified engine performance model. Where a real
constant is used (e.g. the ISA temperature lapse rate) it is a genuine
published value; where a relationship is a simplification (e.g. cooling
efficiency vs. altitude) that is stated explicitly. See
docs/architecture.md "Physics Twin Assumptions" for the full list.
"""
from __future__ import annotations

import math

SEA_LEVEL_TEMP_C = 15.0
ISA_LAPSE_RATE_C_PER_FT = 1.98 / 1000.0  # standard atmosphere, ~1.98 C per 1000 ft


def isa_ambient_temperature_c(altitude_ft: float) -> float:
    """International Standard Atmosphere temperature at a given altitude,
    ignoring weather-driven deviation (the simulator can still override
    this with a scenario-specific ambient temperature, e.g. HOT_WEATHER)."""
    return SEA_LEVEL_TEMP_C - ISA_LAPSE_RATE_C_PER_FT * altitude_ft


def air_density_factor(altitude_ft: float) -> float:
    """Simplified relative air density (1.0 at sea level), using the
    standard barometric approximation. Used as a proxy for both cooling
    efficiency and mixture/fuel-flow effects at altitude — a real FADEC
    would use a full lookup/compensation table; we use one smooth
    approximation for both, which is a stated simplification."""
    return max(0.35, math.exp(-altitude_ft / 27000.0))


def cooling_efficiency_factor(altitude_ft: float) -> float:
    """Thinner air at altitude cools the engine less effectively for the
    same airspeed/cowl-flap setting. Modeled as monotonically decreasing
    with altitude, floored so it never reaches zero."""
    return max(0.55, air_density_factor(altitude_ft) ** 0.5)
