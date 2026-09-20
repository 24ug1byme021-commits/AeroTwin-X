from sensor_fault_isolation.detector import SensorFaultIsolator
from schemas.health import DiagnosisCategory


def test_insufficient_evidence_with_short_history():
    isolator = SensorFaultIsolator()
    diagnosis = isolator.update(cht_residual_c=0, egt_residual_c=0, vibration_mms=2.0, fuel_flow_residual_lph=0)
    assert diagnosis.category == DiagnosisCategory.INSUFFICIENT_EVIDENCE


def _feed_baseline(isolator, n=25, cht=0.0, egt=0.0, vib=2.0, fuel=0.0):
    last = None
    for _ in range(n):
        last = isolator.update(cht_residual_c=cht, egt_residual_c=egt, vibration_mms=vib, fuel_flow_residual_lph=fuel)
    return last


def test_cht_only_shift_flags_possible_sensor_fault():
    isolator = SensorFaultIsolator()
    _feed_baseline(isolator, n=25, cht=0.0, egt=0.0, vib=2.0, fuel=0.0)
    # Now shift ONLY CHT residual, keep everything else flat.
    diagnosis = None
    for _ in range(6):
        diagnosis = isolator.update(cht_residual_c=15.0, egt_residual_c=0.0, vibration_mms=2.0, fuel_flow_residual_lph=0.0)
    assert diagnosis.category == DiagnosisCategory.POSSIBLE_SENSOR_FAULT
    assert "CHT" in diagnosis.affected_sensors


def test_cht_and_egt_shift_together_flags_possible_engine_fault():
    isolator = SensorFaultIsolator()
    _feed_baseline(isolator, n=25, cht=0.0, egt=0.0, vib=2.0, fuel=0.0)
    diagnosis = None
    for _ in range(6):
        diagnosis = isolator.update(cht_residual_c=15.0, egt_residual_c=25.0, vibration_mms=2.0, fuel_flow_residual_lph=0.0)
    assert diagnosis.category == DiagnosisCategory.POSSIBLE_ENGINE_FAULT


def test_no_shift_returns_none_category():
    isolator = SensorFaultIsolator()
    diagnosis = _feed_baseline(isolator, n=30, cht=0.0, egt=0.0, vib=2.0, fuel=0.0)
    assert diagnosis.category == DiagnosisCategory.NONE


def test_diagnosis_never_claims_certainty_in_wording():
    isolator = SensorFaultIsolator()
    _feed_baseline(isolator, n=25)
    diagnosis = None
    for _ in range(6):
        diagnosis = isolator.update(cht_residual_c=15.0, egt_residual_c=0.0, vibration_mms=2.0, fuel_flow_residual_lph=0.0)
    banned_words = ["definitely", "certainly", "confirmed engine failure"]
    for w in banned_words:
        assert w not in diagnosis.explanation.lower()
