"""
Sensor Fault Isolation.

Reasoning pattern (mirrors the CHT example from the PS/architecture doc):

  CHT residual rises AND EGT residual / vibration / fuel-flow residual
  stay within their normal bands  -> POSSIBLE sensor fault (e.g. CHT
  probe drift), because a real thermal problem should show up in more
  than one correlated signal.

  CHT residual rises TOGETHER WITH EGT residual and/or vibration and/or
  fuel-flow changes -> POSSIBLE engine fault (e.g. thermal degradation),
  because multiple independent signals are moving together.

This module never claims certainty — output is always "possible" /
"suspected" with an explicit confidence and explanation, and falls back
to INSUFFICIENT_EVIDENCE until enough rolling history exists.
"""
from __future__ import annotations

from collections import deque
from datetime import datetime, timezone

from schemas.health import DiagnosisCategory, Severity, SensorFaultDiagnosis
from sensor_fault_isolation import rules


class SensorFaultIsolator:
    def __init__(self, window: int = 60):
        self._cht_residual: deque[float] = deque(maxlen=window)
        self._egt_residual: deque[float] = deque(maxlen=window)
        self._vibration: deque[float] = deque(maxlen=window)
        self._fuel_flow_residual: deque[float] = deque(maxlen=window)

    @staticmethod
    def _shift(history: deque[float]) -> tuple[float, float, float]:
        """Returns (baseline_mean, recent_mean, shift) using the oldest
        portion of the window as baseline and the last RECENT_WINDOW
        samples as 'recent'."""
        n = len(history)
        recent = list(history)[-rules.RECENT_WINDOW:]
        baseline_slice = list(history)[: max(0, n - rules.RECENT_WINDOW)]
        if not baseline_slice:
            baseline_slice = recent
        baseline_mean = sum(baseline_slice) / len(baseline_slice)
        recent_mean = sum(recent) / len(recent)
        return baseline_mean, recent_mean, recent_mean - baseline_mean

    def update(
        self,
        cht_residual_c: float,
        egt_residual_c: float,
        vibration_mms: float,
        fuel_flow_residual_lph: float,
        timestamp: datetime | None = None,
    ) -> SensorFaultDiagnosis:
        timestamp = timestamp or datetime.now(timezone.utc)

        self._cht_residual.append(cht_residual_c)
        self._egt_residual.append(egt_residual_c)
        self._vibration.append(vibration_mms)
        self._fuel_flow_residual.append(fuel_flow_residual_lph)

        if len(self._cht_residual) < rules.MIN_HISTORY_SAMPLES:
            return SensorFaultDiagnosis(
                timestamp=timestamp,
                category=DiagnosisCategory.INSUFFICIENT_EVIDENCE,
                severity=Severity.NONE,
                confidence_pct=0.0,
                affected_sensors=[],
                explanation=(
                    f"Only {len(self._cht_residual)} samples collected; "
                    f"need at least {rules.MIN_HISTORY_SAMPLES} before diagnosing."
                ),
            )

        _, _, cht_shift = self._shift(self._cht_residual)
        _, _, egt_shift = self._shift(self._egt_residual)
        _, vib_recent_mean, vib_shift = self._shift(self._vibration)
        _, _, fuel_shift = self._shift(self._fuel_flow_residual)

        cht_ratio = abs(cht_shift) / rules.CHT_SHIFT_THRESHOLD_C
        egt_ratio = abs(egt_shift) / rules.EGT_SHIFT_THRESHOLD_C
        vib_ratio = abs(vib_shift) / rules.VIBRATION_SHIFT_THRESHOLD_MMS
        fuel_ratio = abs(fuel_shift) / rules.FUEL_FLOW_SHIFT_THRESHOLD_LPH

        cht_moved = cht_ratio >= 1.0
        others_moved = egt_ratio >= 1.0 or vib_ratio >= 1.0 or fuel_ratio >= 1.0

        if cht_moved and not others_moved:
            confidence = min(95.0, 55.0 + 10.0 * cht_ratio)
            return SensorFaultDiagnosis(
                timestamp=timestamp,
                category=DiagnosisCategory.POSSIBLE_SENSOR_FAULT,
                severity=Severity(rules.severity_from_ratio(cht_ratio)),
                confidence_pct=confidence,
                affected_sensors=["CHT"],
                explanation=(
                    f"CHT residual shifted by {cht_shift:+.1f} C over the recent window while "
                    f"EGT residual ({egt_shift:+.1f} C), vibration ({vib_shift:+.2f} mm/s) and "
                    f"fuel-flow residual ({fuel_shift:+.2f} L/h) remained within normal bands. "
                    f"This pattern is consistent with a CHT sensor drift/fault rather than a real "
                    f"thermal change, since a genuine engine thermal issue would be expected to "
                    f"also affect EGT and/or vibration."
                ),
            )

        if cht_moved and others_moved:
            confidence = min(95.0, 50.0 + 8.0 * max(cht_ratio, egt_ratio, vib_ratio))
            affected = ["CHT"]
            if egt_ratio >= 1.0:
                affected.append("EGT")
            if vib_ratio >= 1.0:
                affected.append("Vibration")
            if fuel_ratio >= 1.0:
                affected.append("Fuel Flow")
            worst_ratio = max(cht_ratio, egt_ratio, vib_ratio, fuel_ratio)
            return SensorFaultDiagnosis(
                timestamp=timestamp,
                category=DiagnosisCategory.POSSIBLE_ENGINE_FAULT,
                severity=Severity(rules.severity_from_ratio(worst_ratio)),
                confidence_pct=confidence,
                affected_sensors=affected,
                explanation=(
                    f"CHT residual shifted by {cht_shift:+.1f} C together with correlated changes "
                    f"in {', '.join(affected[1:]) or 'other signals'}. Multiple independent signals "
                    f"moving together suggests a genuine engine thermal/mechanical change rather than "
                    f"an isolated sensor fault."
                ),
            )

        if not cht_moved and (vib_ratio >= 1.0 or egt_ratio >= 1.0):
            worst_ratio = max(egt_ratio, vib_ratio)
            affected = []
            if egt_ratio >= 1.0:
                affected.append("EGT")
            if vib_ratio >= 1.0:
                affected.append("Vibration")
            return SensorFaultDiagnosis(
                timestamp=timestamp,
                category=DiagnosisCategory.POSSIBLE_ENGINE_FAULT,
                severity=Severity(rules.severity_from_ratio(worst_ratio)),
                confidence_pct=min(90.0, 45.0 + 8.0 * worst_ratio),
                affected_sensors=affected,
                explanation=(
                    f"EGT residual ({egt_shift:+.1f} C) and/or vibration "
                    f"(mean {vib_recent_mean:.2f} mm/s, shift {vib_shift:+.2f} mm/s) moved "
                    f"significantly without a corresponding CHT shift — pattern consistent with a "
                    f"combustion-related or mechanical anomaly rather than a CHT sensor issue."
                ),
            )

        return SensorFaultDiagnosis(
            timestamp=timestamp,
            category=DiagnosisCategory.NONE,
            severity=Severity.NONE,
            confidence_pct=80.0,
            affected_sensors=[],
            explanation="All monitored signals within normal bands relative to recent baseline.",
        )
