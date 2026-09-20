"""
Tests for the white-box statistical anomaly detector and the
selectable detector mode. These back the claim that the system works
with zero ML-library involvement in the detection path.
"""
from health.statistical_anomaly import StatisticalAnomalyDetector
from telemetry.streaming import SimulationEngine
from schemas.telemetry import ScenarioName


def test_statistical_detector_quiet_on_healthy():
    """A healthy cruise frame should score near zero (no false alarm)."""
    det = StatisticalAnomalyDetector()
    # Zero residuals = perfectly healthy => score should be ~0.
    score, _ = det.score(cht_residual_c=0.0, egt_residual_c=0.0, vibration_mms=2.5,
                         fuel_flow_residual_lph=0.0, rpm=4200)
    assert score < 1.0


def test_statistical_detector_flags_thermal_excursion():
    """A large CHT residual must produce a clearly elevated score and name CHT."""
    det = StatisticalAnomalyDetector()
    score, feats = det.score(cht_residual_c=30.0, egt_residual_c=25.0, vibration_mms=3.0,
                            fuel_flow_residual_lph=0.0, rpm=4200)
    assert score > 2.0
    assert any("CHT" in f for f in feats)


def test_detector_mode_switch_is_respected():
    eng = SimulationEngine()
    assert eng.set_detector_mode("statistical") == "statistical"
    assert eng.set_detector_mode("ml") == "ml"
    assert eng.set_detector_mode("hybrid") == "hybrid"


def test_invalid_detector_mode_rejected():
    eng = SimulationEngine()
    try:
        eng.set_detector_mode("magic")
        assert False, "expected ValueError"
    except ValueError:
        pass


def test_statistical_mode_end_to_end_degrades_health():
    """With the ML path disabled entirely, thermal degradation must still
    drive the health index down — proving the system works without ML."""
    eng = SimulationEngine()
    eng.set_detector_mode("statistical")
    eng.set_scenario(ScenarioName.THERMAL_DEGRADATION)
    eng.start()
    health_end = 100.0
    for _ in range(150):
        msg = eng.tick()
        health_end = msg.health.health_index
    assert health_end < 80.0, "statistical-only path should detect thermal degradation"
