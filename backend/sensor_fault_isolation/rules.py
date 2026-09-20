"""
Threshold rules used by the Sensor Fault Isolation detector.

These are prototype thresholds chosen to make the demo scenarios
(SENSOR_DRIFT vs THERMAL_DEGRADATION vs COMBUSTION_ANOMALY) clearly
distinguishable — they are illustrative, not calibrated against a real
engine's failure statistics. See docs/architecture.md.
"""
from __future__ import annotations

# Minimum rolling-window samples before we trust a diagnosis at all.
MIN_HISTORY_SAMPLES = 20

# "Recent" window used to detect a shift vs. the longer-run baseline.
RECENT_WINDOW = 5

# Shift thresholds: how far the recent mean must move from the baseline
# mean before we consider a signal to have "changed" at all.
CHT_SHIFT_THRESHOLD_C = 6.0
EGT_SHIFT_THRESHOLD_C = 15.0
VIBRATION_SHIFT_THRESHOLD_MMS = 0.8
FUEL_FLOW_SHIFT_THRESHOLD_LPH = 1.0

# Severity bands, expressed as a multiple of the relevant shift threshold.
SEVERITY_MEDIUM_MULTIPLIER = 1.6
SEVERITY_HIGH_MULTIPLIER = 3.0


def severity_from_ratio(ratio: float) -> str:
    if ratio >= SEVERITY_HIGH_MULTIPLIER:
        return "HIGH"
    if ratio >= SEVERITY_MEDIUM_MULTIPLIER:
        return "MEDIUM"
    if ratio >= 1.0:
        return "LOW"
    return "NONE"
