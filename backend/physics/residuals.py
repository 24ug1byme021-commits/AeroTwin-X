"""
Physics Residual Engine: Residual = Actual telemetry - Physics Twin expected.

This is one of AeroTwin-X's main technical differentiators: rather than
feeding raw sensor values straight into an anomaly detector, we first
subtract out what a *healthy* engine at this operating point should look
like, so the AI layer reasons about deviations, not absolute values that
naturally vary with throttle/altitude/temperature.
"""
from __future__ import annotations

from physics.engine_model import expected_values
from schemas.health import PhysicsExpected, ResidualFrame
from schemas.telemetry import TelemetryFrame


def compute_physics_expected(frame: TelemetryFrame) -> PhysicsExpected:
    ev = expected_values(
        throttle_pct=frame.throttle_pct,
        altitude_ft=frame.altitude_ft,
        ambient_temperature_c=frame.ambient_temperature_c,
    )
    return PhysicsExpected(
        timestamp=frame.timestamp,
        expected_egt_c=ev.expected_egt_c,
        expected_cht_c=ev.expected_cht_c,
        expected_oil_temperature_c=ev.expected_oil_temperature_c,
        expected_fuel_flow_lph=ev.expected_fuel_flow_lph,
    )


def compute_residuals(frame: TelemetryFrame, expected: PhysicsExpected | None = None) -> ResidualFrame:
    expected = expected or compute_physics_expected(frame)
    return ResidualFrame(
        timestamp=frame.timestamp,
        egt_residual_c=frame.egt_c - expected.expected_egt_c,
        cht_residual_c=frame.cht_c - expected.expected_cht_c,
        oil_temperature_residual_c=frame.oil_temperature_c - expected.expected_oil_temperature_c,
        fuel_flow_residual_lph=frame.fuel_flow_lph - expected.expected_fuel_flow_lph,
    )
