from health.anomaly_detector import AnomalyDetector
from health.health_index import HealthIndexEngine
from health.fault_classifier import FaultClassification
from rul.degradation import DegradationTracker
from rul.estimator import RULEstimator, NO_DEGRADATION_CEILING_HOURS


def test_anomaly_detector_scores_healthy_point_low():
    detector = AnomalyDetector(n_training_samples=300)
    score, _ = detector.score(cht_residual_c=0.0, egt_residual_c=0.0, vibration_mms=2.0, fuel_flow_residual_lph=0.0, rpm=3000)
    assert score < 5.0


def test_anomaly_detector_scores_extreme_point_higher_than_healthy():
    detector = AnomalyDetector(n_training_samples=300)
    healthy_score, _ = detector.score(cht_residual_c=0.0, egt_residual_c=0.0, vibration_mms=2.0, fuel_flow_residual_lph=0.0, rpm=3000)
    extreme_score, features = detector.score(cht_residual_c=80.0, egt_residual_c=150.0, vibration_mms=10.0, fuel_flow_residual_lph=-5.0, rpm=3000)
    assert extreme_score > healthy_score
    assert len(features) > 0


def test_health_index_engine_normal_status_for_low_anomaly():
    engine = HealthIndexEngine()
    result = None
    for _ in range(20):
        result = engine.update(anomaly_score=0.2, contributing_features=[], fault=FaultClassification(None, []))
    assert result.status.value == "NORMAL"
    assert result.health_index > 80


def test_health_index_engine_critical_status_for_high_anomaly_and_fault():
    engine = HealthIndexEngine()
    result = None
    for _ in range(20):
        result = engine.update(
            anomaly_score=9.0,
            contributing_features=["CHT residual"],
            fault=FaultClassification("possible overheating / thermal degradation trend", ["CHT residual"]),
        )
    assert result.status.value in ("WARNING", "CRITICAL")
    assert result.suspected_fault is not None


def test_degradation_tracker_increases_under_sustained_stress():
    tracker = DegradationTracker()
    state = None
    for _ in range(600):  # 10 simulated minutes at 1s steps
        state = tracker.update(dt_seconds=1.0, cht_residual_c=20.0, vibration_excess_mms=2.0, anomaly_score=5.0)
    assert state.degradation_index > 0


def test_degradation_tracker_decays_when_healthy():
    tracker = DegradationTracker()
    for _ in range(300):
        tracker.update(dt_seconds=1.0, cht_residual_c=20.0, vibration_excess_mms=2.0, anomaly_score=5.0)
    stressed_index = tracker.thermal_component
    for _ in range(600):
        tracker.update(dt_seconds=1.0, cht_residual_c=0.0, vibration_excess_mms=0.0, anomaly_score=0.0)
    assert tracker.thermal_component < stressed_index


def test_rul_estimator_returns_ceiling_with_no_trend():
    estimator = RULEstimator()
    result = None
    for i in range(60):
        result = estimator.update(operating_hours=i / 60.0, degradation_index=0.0)
    assert result.rul_hours == NO_DEGRADATION_CEILING_HOURS


def test_rul_estimator_decreases_as_degradation_accumulates():
    estimator = RULEstimator()
    result = None
    for i in range(60):
        result = estimator.update(operating_hours=i * 0.1, degradation_index=min(90.0, i * 1.5))
    assert result.rul_hours < NO_DEGRADATION_CEILING_HOURS
    assert result.uncertainty_hours >= 0
