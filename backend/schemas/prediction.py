"""
Top-level response/streaming envelopes that combine telemetry with the
processed engine state. Used by the WebSocket stream and by
/api/engine/state. Kept separate from health.py so that "one frame of
everything" has a single, obvious home.
"""
from __future__ import annotations

from datetime import datetime, timezone

from pydantic import BaseModel, Field

from schemas.telemetry import TelemetryFrame
from schemas.health import (
    ResidualFrame,
    SensorFaultDiagnosis,
    HealthIndexResult,
    DegradationState,
    RULEstimate,
)


class SystemStatus(BaseModel):
    """Response for GET /api/system/status — is the simulation running,
    which scenario is active, how many frames processed, etc."""
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    simulation_running: bool
    active_scenario: str | None
    frames_processed: int
    uptime_seconds: float
    detector_mode: str = "hybrid"


class TelemetryStreamMessage(BaseModel):
    """One message pushed over /ws/telemetry. Everything the frontend
    needs to update the live dashboard for a single tick, in one payload
    so the UI never has to reconcile partial updates from separate calls."""
    telemetry: TelemetryFrame
    residuals: ResidualFrame | None = None
    sensor_fault: SensorFaultDiagnosis | None = None
    health: HealthIndexResult | None = None
    degradation: DegradationState | None = None
    rul: RULEstimate | None = None
