"""
Schemas for the physics twin, residuals, sensor fault isolation,
AI health twin, degradation and RUL. These are the shapes every
downstream module (and the frontend) can rely on.
"""
from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Physics Twin + Residuals
# ---------------------------------------------------------------------------

class PhysicsExpected(BaseModel):
    """Expected values from the simplified physics-informed engine model,
    for the same instant as a TelemetryFrame. See physics/engine_model.py
    for the documented assumptions behind these equations."""
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    expected_egt_c: float
    expected_cht_c: float
    expected_oil_temperature_c: float
    expected_fuel_flow_lph: float


class ResidualFrame(BaseModel):
    """Actual - Expected, per parameter, at one instant."""
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    egt_residual_c: float
    cht_residual_c: float
    oil_temperature_residual_c: float
    fuel_flow_residual_lph: float


# ---------------------------------------------------------------------------
# Sensor Fault Isolation
# ---------------------------------------------------------------------------

class DiagnosisCategory(str, Enum):
    NONE = "NONE"
    POSSIBLE_SENSOR_FAULT = "POSSIBLE_SENSOR_FAULT"
    POSSIBLE_ENGINE_FAULT = "POSSIBLE_ENGINE_FAULT"
    INSUFFICIENT_EVIDENCE = "INSUFFICIENT_EVIDENCE"


class Severity(str, Enum):
    NONE = "NONE"
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"


class SensorFaultDiagnosis(BaseModel):
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    category: DiagnosisCategory
    severity: Severity
    confidence_pct: float = Field(..., ge=0, le=100)
    affected_sensors: list[str] = Field(default_factory=list)
    explanation: str


# ---------------------------------------------------------------------------
# AI Health Twin
# ---------------------------------------------------------------------------

class HealthStatus(str, Enum):
    NORMAL = "NORMAL"
    WARNING = "WARNING"
    CRITICAL = "CRITICAL"


class HealthIndexResult(BaseModel):
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    health_index: float = Field(..., ge=0, le=100)
    status: HealthStatus
    anomaly_score: float = Field(..., description="Higher = more anomalous. Not a calibrated probability.")
    suspected_fault: str | None = None
    degradation_trend: str = Field(..., description="e.g. 'stable', 'slowly increasing', 'rapidly increasing'")
    confidence_pct: float = Field(..., ge=0, le=100)
    contributing_signals: list[str] = Field(default_factory=list)


# ---------------------------------------------------------------------------
# Degradation + RUL
# ---------------------------------------------------------------------------

class DegradationState(BaseModel):
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    degradation_index: float = Field(..., ge=0, le=100, description="0 = no accumulated degradation, 100 = end of life")
    thermal_component: float = Field(..., ge=0, le=100)
    vibration_component: float = Field(..., ge=0, le=100)
    residual_component: float = Field(..., ge=0, le=100)
    accumulated_operating_hours: float = Field(..., ge=0)


class RULEstimate(BaseModel):
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    rul_hours: float = Field(..., ge=0)
    uncertainty_hours: float = Field(..., ge=0)
    confidence_pct: float = Field(..., ge=0, le=100)
    basis: str = Field(
        default="Prototype estimate derived from simulated degradation state. "
                "Not calibrated against real engine failure data."
    )


class EngineStateSnapshot(BaseModel):
    """Aggregated snapshot used by /api/engine/state and the dashboard."""
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    telemetry_source: str
    residuals: ResidualFrame | None = None
    sensor_fault: SensorFaultDiagnosis | None = None
    health: HealthIndexResult | None = None
    degradation: DegradationState | None = None
    rul: RULEstimate | None = None
