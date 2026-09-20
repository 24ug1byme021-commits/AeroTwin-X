"""
SimulationEngine: the single stateful object that owns one running
"engine session" — telemetry simulator + the full processing pipeline
(physics residuals -> sensor fault isolation -> AI health twin ->
degradation tracking -> RUL). Used by both the REST endpoints and the
/ws/telemetry WebSocket broadcaster, so they always see the same state.
"""
from __future__ import annotations

import time
from collections import deque

from config import settings
from health.anomaly_detector import AnomalyDetector
from health.statistical_anomaly import StatisticalAnomalyDetector
from storage.recorder import get_recorder
from health.fault_classifier import classify as classify_fault
from health.health_index import HealthIndexEngine
from physics.residuals import compute_residuals
from rul.degradation import DegradationTracker
from rul.estimator import RULEstimator
from schemas.prediction import SystemStatus, TelemetryStreamMessage
from schemas.telemetry import ScenarioName
from sensor_fault_isolation.detector import SensorFaultIsolator
from telemetry.simulator import EngineSimulator


class SimulationEngine:
    def __init__(self):
        self._start_time = time.time()
        self._frames_processed = 0
        self._running = False

        self.simulator = EngineSimulator(scenario=ScenarioName.NORMAL_CRUISE)
        self.sensor_fault_isolator = SensorFaultIsolator()
        self.health_index_engine = HealthIndexEngine()
        self.degradation_tracker = DegradationTracker()
        self.rul_estimator = RULEstimator()

        # Two interchangeable anomaly detectors, both trained once at
        # startup on simulated healthy data:
        #  - statistical: white-box Mahalanobis distance (pure NumPy math)
        #  - ml: IsolationForest (unsupervised pattern detection)
        # Mode selects which score drives the health pipeline. Default is the
        # fully-transparent statistical path; "ml" or "hybrid" can be enabled
        # live. This lets us demonstrate the system with zero ML dependency.
        self.statistical_detector = StatisticalAnomalyDetector()
        self.anomaly_detector = AnomalyDetector()
        self.detector_mode: str = "hybrid"  # "statistical" | "ml" | "hybrid"

        self._history: deque[TelemetryStreamMessage] = deque(maxlen=settings.telemetry_history_max_frames)

    # -- lifecycle -----------------------------------------------------
    def start(self) -> None:
        # A fresh run always begins from a clean baseline, so the dashboard
        # starts at zero/steady-state rather than continuing from wherever a
        # previous run left off.
        if not self._running:
            self._reset_state(preserve_scenario=True)
            # Open a persisted run so the whole session is stored for
            # post-flight analysis and mission replay.
            recorder = get_recorder()
            if recorder is not None:
                recorder.start_run(self.simulator.scenario.value, self.detector_mode)
        self._running = True

    def stop(self) -> None:
        # Stopping fully resets the session: degradation, RUL, health,
        # fault-isolation memory and telemetry history all return to
        # baseline so the next run starts clean and the UI drops to zero.
        self._running = False
        recorder = get_recorder()
        if recorder is not None:
            recorder.end_run()
        self._reset_state(preserve_scenario=True)

    def reset(self) -> None:
        """Explicit reset endpoint hook — clears all accumulated state."""
        was_running = self._running
        self._reset_state(preserve_scenario=True)
        self._running = was_running

    def _reset_state(self, preserve_scenario: bool = True) -> None:
        """Rebuild every stateful pipeline component from scratch.

        The trained IsolationForest (anomaly_detector) is intentionally
        preserved — it is trained once on healthy data at startup and is
        not part of per-run state, so retraining it here would be wasteful
        and would not change behaviour.
        """
        scenario = self.simulator.scenario if preserve_scenario else ScenarioName.NORMAL_CRUISE
        self.simulator = EngineSimulator(scenario=scenario)
        self.sensor_fault_isolator = SensorFaultIsolator()
        self.health_index_engine = HealthIndexEngine()
        self.degradation_tracker = DegradationTracker()
        self.rul_estimator = RULEstimator()
        self._history.clear()
        self._frames_processed = 0

    def set_scenario(self, scenario: ScenarioName) -> None:
        self.simulator.set_scenario(scenario)
        if self._running:
            recorder = get_recorder()
            if recorder is not None:
                recorder.update_scenario(scenario.value)

    def set_detector_mode(self, mode: str) -> str:
        """Switch the anomaly-detection backend live.

        'statistical' -> pure Mahalanobis math (no ML library in the path)
        'ml'          -> IsolationForest only
        'hybrid'      -> both run; the more conservative (higher) score wins
        """
        mode = mode.lower().strip()
        if mode not in ("statistical", "ml", "hybrid"):
            raise ValueError("mode must be 'statistical', 'ml' or 'hybrid'")
        self.detector_mode = mode
        return self.detector_mode

    def _score_anomaly(self, residuals, frame) -> tuple[float, list[str]]:
        """Dispatch to the selected detector(s)."""
        stat_score, stat_feats = self.statistical_detector.score(
            cht_residual_c=residuals.cht_residual_c,
            egt_residual_c=residuals.egt_residual_c,
            vibration_mms=frame.vibration_mms,
            fuel_flow_residual_lph=residuals.fuel_flow_residual_lph,
            rpm=frame.rpm,
        )
        if self.detector_mode == "statistical":
            return stat_score, stat_feats

        ml_score, ml_feats = self.anomaly_detector.score(
            cht_residual_c=residuals.cht_residual_c,
            egt_residual_c=residuals.egt_residual_c,
            vibration_mms=frame.vibration_mms,
            fuel_flow_residual_lph=residuals.fuel_flow_residual_lph,
            rpm=frame.rpm,
        )
        if self.detector_mode == "ml":
            return ml_score, ml_feats

        # hybrid: take the higher (more conservative) score, merge evidence
        if stat_score >= ml_score:
            merged = stat_feats or ml_feats
            return stat_score, merged
        merged = ml_feats or stat_feats
        return ml_score, merged

    @property
    def running(self) -> bool:
        return self._running

    def status(self) -> SystemStatus:
        return SystemStatus(
            simulation_running=self._running,
            active_scenario=self.simulator.scenario.value,
            frames_processed=self._frames_processed,
            uptime_seconds=round(time.time() - self._start_time, 1),
            detector_mode=self.detector_mode,
        )

    # -- core pipeline ---------------------------------------------------
    def tick(self, dt_seconds: float | None = None) -> TelemetryStreamMessage:
        dt_seconds = dt_seconds if dt_seconds is not None else settings.telemetry_tick_seconds

        frame = self.simulator.step(dt_seconds)
        residuals = compute_residuals(frame)

        sensor_fault = self.sensor_fault_isolator.update(
            cht_residual_c=residuals.cht_residual_c,
            egt_residual_c=residuals.egt_residual_c,
            vibration_mms=frame.vibration_mms,
            fuel_flow_residual_lph=residuals.fuel_flow_residual_lph,
            timestamp=frame.timestamp,
        )

        anomaly_score, contributing_features = self._score_anomaly(residuals, frame)

        fault = classify_fault(
            frame=frame,
            cht_residual_c=residuals.cht_residual_c,
            egt_residual_c=residuals.egt_residual_c,
            oil_temperature_residual_c=residuals.oil_temperature_residual_c,
            fuel_flow_residual_lph=residuals.fuel_flow_residual_lph,
            sensor_fault=sensor_fault,
        )

        health = self.health_index_engine.update(
            anomaly_score=anomaly_score,
            contributing_features=contributing_features,
            fault=fault,
            timestamp=frame.timestamp,
        )

        vibration_excess = frame.vibration_mms - (1.0 + 2.5 * max(0.0, min(1.0, (frame.rpm - 1700.0) / (5500.0 - 1700.0))))
        degradation = self.degradation_tracker.update(
            dt_seconds=dt_seconds,
            cht_residual_c=residuals.cht_residual_c,
            vibration_excess_mms=vibration_excess,
            anomaly_score=anomaly_score,
            timestamp=frame.timestamp,
        )

        rul = self.rul_estimator.update(
            operating_hours=degradation.accumulated_operating_hours,
            degradation_index=degradation.degradation_index,
            timestamp=frame.timestamp,
        )

        self._frames_processed += 1
        message = TelemetryStreamMessage(
            telemetry=frame,
            residuals=residuals,
            sensor_fault=sensor_fault,
            health=health,
            degradation=degradation,
            rul=rul,
        )
        self._history.append(message)

        # Persist the frame for post-flight analysis / replay (fail-safe:
        # a storage error never interrupts streaming).
        recorder = get_recorder()
        if recorder is not None:
            recorder.record(message)

        return message

    def history(self, n: int | None = None) -> list[TelemetryStreamMessage]:
        items = list(self._history)
        return items[-n:] if n else items

    def latest(self) -> TelemetryStreamMessage | None:
        return self._history[-1] if self._history else None


# Module-level singleton — one simulation session per backend process,
# shared by REST routes and the WebSocket. Building this trains the
# IsolationForest once at import time.
engine = SimulationEngine()
