"""
Combines the IsolationForest anomaly score and the rule-based fault
classification into a single 0-100 health index, status band, and a
degradation TREND description (not the long-run degradation index itself
— that lives in rul/degradation.py and consumes this module's output,
matching the pipeline order Physics Residual -> AI Health Twin ->
Degradation Tracking -> RUL).
"""
from __future__ import annotations

from collections import deque
from datetime import datetime, timezone

import numpy as np

from schemas.health import HealthIndexResult, HealthStatus
from health.fault_classifier import FaultClassification

MIN_HISTORY_FOR_TREND = 15
TREND_WINDOW = 40


def _trend_label(slope_per_sample: float) -> str:
    # slope is in anomaly-score units per sample (~1 sample/sec in the demo)
    if abs(slope_per_sample) < 0.01:
        return "stable"
    if slope_per_sample > 0:
        return "rapidly increasing" if slope_per_sample > 0.05 else "slowly increasing"
    return "rapidly decreasing" if slope_per_sample < -0.05 else "slowly decreasing"


class HealthIndexEngine:
    def __init__(self):
        self._anomaly_history: deque[float] = deque(maxlen=TREND_WINDOW)

    def update(
        self,
        anomaly_score: float,
        contributing_features: list[str],
        fault: FaultClassification,
        timestamp: datetime | None = None,
    ) -> HealthIndexResult:
        timestamp = timestamp or datetime.now(timezone.utc)
        self._anomaly_history.append(anomaly_score)

        # Don't surface "contributing signals" when the anomaly score
        # itself rounds down to ~0 — otherwise a NORMAL/healthy reading can
        # misleadingly list signals that didn't actually drive any concern.
        if anomaly_score < 0.05:
            contributing_features = []

        # Base health index purely from anomaly score.
        health_index = 100.0 - min(100.0, anomaly_score * 9.0)

        # Named-fault severity nudges the index down further, since a
        # classified fault is more actionable than a raw anomaly score.
        if fault.suspected_fault is not None:
            health_index = min(health_index, 70.0) if "sensor" not in fault.suspected_fault else health_index
            if "overheating" in fault.suspected_fault or "thermal" in fault.suspected_fault:
                health_index = min(health_index, 60.0)
            if "lubrication" in fault.suspected_fault:
                health_index = min(health_index, 55.0)
            if "combustion" in fault.suspected_fault:
                health_index = min(health_index, 58.0)
            if "vibration" in fault.suspected_fault:
                health_index = min(health_index, 65.0)
        health_index = max(0.0, min(100.0, health_index))

        if health_index >= 80:
            status = HealthStatus.NORMAL
        elif health_index >= 50:
            status = HealthStatus.WARNING
        else:
            status = HealthStatus.CRITICAL

        # Trend: simple linear regression slope over recent anomaly-score history.
        if len(self._anomaly_history) >= MIN_HISTORY_FOR_TREND:
            y = np.array(self._anomaly_history)
            x = np.arange(len(y))
            slope = float(np.polyfit(x, y, 1)[0])
            trend = _trend_label(slope)
        else:
            trend = "insufficient history"

        # Confidence: grows with history depth, shrinks when the current
        # reading is far out of the training distribution (large anomaly
        # score) — an operator should trust a wildly novel reading less,
        # not more.
        history_confidence = min(1.0, len(self._anomaly_history) / MIN_HISTORY_FOR_TREND) * 90.0
        novelty_penalty = min(25.0, anomaly_score * 2.5)
        confidence_pct = max(30.0, history_confidence - novelty_penalty)

        return HealthIndexResult(
            timestamp=timestamp,
            health_index=round(health_index, 1),
            status=status,
            anomaly_score=round(anomaly_score, 3),
            suspected_fault=fault.suspected_fault,
            degradation_trend=trend,
            confidence_pct=round(confidence_pct, 1),
            contributing_signals=list(dict.fromkeys(contributing_features + fault.contributing_signals)),
        )
