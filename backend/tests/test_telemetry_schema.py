import pytest
from pydantic import ValidationError

from schemas.telemetry import TelemetryFrame, DataSource


def _valid_kwargs(**overrides):
    base = dict(
        rpm=3000, cht_c=150, egt_c=700, oil_pressure_psi=60,
        oil_temperature_c=80, fuel_flow_lph=15, vibration_mms=2.0,
        altitude_ft=8000, ambient_temperature_c=15, throttle_pct=65,
        engine_load_pct=60,
    )
    base.update(overrides)
    return base


def test_valid_frame_constructs():
    frame = TelemetryFrame(**_valid_kwargs())
    assert frame.source == DataSource.SIMULATED
    assert frame.is_physically_plausible()


def test_negative_rpm_rejected():
    with pytest.raises(ValidationError):
        TelemetryFrame(**_valid_kwargs(rpm=-10))


def test_impossible_egt_rejected():
    with pytest.raises(ValidationError):
        TelemetryFrame(**_valid_kwargs(egt_c=5000))


def test_missing_required_field_rejected():
    kwargs = _valid_kwargs()
    del kwargs["rpm"]
    with pytest.raises(ValidationError):
        TelemetryFrame(**kwargs)


def test_plausibility_check_catches_stopped_engine_high_egt():
    frame = TelemetryFrame(**_valid_kwargs(rpm=0, egt_c=500))
    assert not frame.is_physically_plausible()


def test_plausibility_check_catches_zero_oil_pressure_running_engine():
    frame = TelemetryFrame(**_valid_kwargs(rpm=3000, oil_pressure_psi=0))
    assert not frame.is_physically_plausible()
