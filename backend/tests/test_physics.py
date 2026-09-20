from physics.engine_model import expected_values, expected_rpm
from physics.residuals import compute_physics_expected, compute_residuals
from schemas.telemetry import TelemetryFrame, DataSource


def test_expected_values_increase_with_load():
    low = expected_values(throttle_pct=20, altitude_ft=5000, ambient_temperature_c=15)
    high = expected_values(throttle_pct=90, altitude_ft=5000, ambient_temperature_c=15)
    assert high.expected_egt_c > low.expected_egt_c
    assert high.expected_cht_c > low.expected_cht_c
    assert high.expected_fuel_flow_lph > low.expected_fuel_flow_lph


def test_expected_rpm_monotonic_with_throttle():
    assert expected_rpm(0) < expected_rpm(50) < expected_rpm(100)


def test_higher_altitude_increases_cht_all_else_equal():
    low_alt = expected_values(throttle_pct=65, altitude_ft=2000, ambient_temperature_c=15)
    high_alt = expected_values(throttle_pct=65, altitude_ft=25000, ambient_temperature_c=15)
    assert high_alt.expected_cht_c > low_alt.expected_cht_c, "Thinner air should reduce cooling efficiency"


def test_residual_zero_when_actual_matches_expected():
    expected = expected_values(throttle_pct=65, altitude_ft=8000, ambient_temperature_c=15)
    frame = TelemetryFrame(
        source=DataSource.SIMULATED,
        rpm=expected_rpm(65), cht_c=expected.expected_cht_c, egt_c=expected.expected_egt_c,
        oil_pressure_psi=60, oil_temperature_c=expected.expected_oil_temperature_c,
        fuel_flow_lph=expected.expected_fuel_flow_lph, vibration_mms=2.0,
        altitude_ft=8000, ambient_temperature_c=15, throttle_pct=65, engine_load_pct=60,
    )
    residuals = compute_residuals(frame)
    assert abs(residuals.egt_residual_c) < 1e-6
    assert abs(residuals.cht_residual_c) < 1e-6


def test_residual_nonzero_when_actual_deviates():
    frame = TelemetryFrame(
        source=DataSource.SIMULATED,
        rpm=3000, cht_c=250, egt_c=700, oil_pressure_psi=60, oil_temperature_c=80,
        fuel_flow_lph=15, vibration_mms=2.0, altitude_ft=8000, ambient_temperature_c=15,
        throttle_pct=65, engine_load_pct=60,
    )
    expected = compute_physics_expected(frame)
    residuals = compute_residuals(frame, expected)
    assert residuals.cht_residual_c == frame.cht_c - expected.expected_cht_c
    assert residuals.cht_residual_c > 20, "CHT of 250C should be well above the healthy expected baseline"
