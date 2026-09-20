"""
Rule-based fault classifier.

Deliberately NOT a black-box model: DRDO's PS explicitly asks for
explainable diagnostics, and the physics-residual approach already gives
us clean, interpretable signals. A transparent rule layer on top of those
signals is more trustworthy for a safety-critical prototype than an
opaque classifier would be, and is easy to extend later.

Every result states "possible X" / "suspected X" — never a bare diagnosis
— and lists exactly which signals triggered it.
"""
from __future__ import annotations

from dataclasses import dataclass

from physics.engine_model import expected_values
from schemas.health import DiagnosisCategory, SensorFaultDiagnosis
from schemas.telemetry import TelemetryFrame

OVERHEAT_CHT_RESIDUAL_C = 12.0
OVERHEAT_EGT_RESIDUAL_C = 20.0
ABNORMAL_VIBRATION_EXCESS_MMS = 1.2
LOW_OIL_PRESSURE_RESIDUAL_PSI = -8.0
LUBRICATION_OIL_TEMP_RESIDUAL_C = 8.0
COMBUSTION_FUEL_FLOW_RESIDUAL_LPH = -1.2


@dataclass
class FaultClassification:
    suspected_fault: str | None
    contributing_signals: list[str]


def _healthy_baseline_vibration(rpm: float) -> float:
    rpm_frac = max(0.0, min(1.0, (rpm - 1700.0) / (5500.0 - 1700.0)))
    return 1.0 + 2.5 * rpm_frac


def classify(
    frame: TelemetryFrame,
    cht_residual_c: float,
    egt_residual_c: float,
    oil_temperature_residual_c: float,
    fuel_flow_residual_lph: float,
    sensor_fault: SensorFaultDiagnosis,
) -> FaultClassification:
    vib_excess = frame.vibration_mms - _healthy_baseline_vibration(frame.rpm)

    expected = expected_values(
        throttle_pct=frame.throttle_pct,
        altitude_ft=frame.altitude_ft,
        ambient_temperature_c=frame.ambient_temperature_c,
    )
    oil_pressure_residual = frame.oil_pressure_psi - expected.expected_oil_pressure_psi

    # Sensor faults take priority in the narrative: if the fault isolation
    # layer already suspects a sensor problem, don't also claim an engine
    # fault off the same reading.
    if sensor_fault.category == DiagnosisCategory.POSSIBLE_SENSOR_FAULT:
        return FaultClassification(
            suspected_fault=f"possible sensor drift/fault ({', '.join(sensor_fault.affected_sensors)})",
            contributing_signals=sensor_fault.affected_sensors,
        )

    signals: list[str] = []

    if cht_residual_c >= OVERHEAT_CHT_RESIDUAL_C and egt_residual_c >= OVERHEAT_EGT_RESIDUAL_C * 0.5:
        signals += ["CHT residual", "EGT residual"]
        return FaultClassification("possible overheating / thermal degradation trend", signals)

    if oil_pressure_residual <= LOW_OIL_PRESSURE_RESIDUAL_PSI and oil_temperature_residual_c >= LUBRICATION_OIL_TEMP_RESIDUAL_C:
        signals += ["Oil pressure residual", "Oil temperature residual"]
        return FaultClassification("possible lubrication issue", signals)

    if fuel_flow_residual_lph <= COMBUSTION_FUEL_FLOW_RESIDUAL_LPH and vib_excess >= ABNORMAL_VIBRATION_EXCESS_MMS * 0.5:
        signals += ["Fuel flow residual", "Vibration"]
        return FaultClassification("possible combustion anomaly (misfire-like pattern)", signals)

    if vib_excess >= ABNORMAL_VIBRATION_EXCESS_MMS:
        signals += ["Vibration"]
        return FaultClassification("possible abnormal vibration (mechanical wear)", signals)

    if egt_residual_c >= OVERHEAT_EGT_RESIDUAL_C:
        signals += ["EGT residual"]
        return FaultClassification("possible abnormal thermal behaviour", signals)

    return FaultClassification(suspected_fault=None, contributing_signals=[])
