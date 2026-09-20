"""
TelemetryFrame is the ONE data contract every AeroTwin-X module consumes.

No module should pass raw dicts between layers — telemetry simulator,
physics twin, sensor fault isolation, AI health twin, RUL and mission twin
all read/write TelemetryFrame (or models built directly on top of it).

Sensor ranges below are prototype assumptions for a small aero-piston
engine broadly in the class used on MALE UAVs (~90-130 hp four-stroke).
They are NOT sourced from a specific certified engine's operating manual —
see docs/architecture.md "Assumptions" section. They exist so we can reject
physically impossible values (e.g. negative RPM, EGT of 5000C), not to
certify real operating limits.
"""
from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum

from pydantic import BaseModel, Field, field_validator


class DataSource(str, Enum):
    """Every frame must declare its provenance. Never allow ambiguity
    between simulated and real telemetry."""
    SIMULATED = "simulated"
    REPLAY = "replay"          # replayed from a recorded synthetic CSV
    REAL_HARDWARE = "real_hardware"  # reserved for future real UAV integration


class TelemetryFrame(BaseModel):
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    source: DataSource = DataSource.SIMULATED

    rpm: float = Field(..., ge=0, le=6500, description="Engine RPM")
    cht_c: float = Field(..., ge=-40, le=350, description="Cylinder Head Temperature, deg C")
    egt_c: float = Field(..., ge=-40, le=1100, description="Exhaust Gas Temperature, deg C")
    oil_pressure_psi: float = Field(..., ge=0, le=150, description="Oil pressure, psi")
    oil_temperature_c: float = Field(..., ge=-40, le=180, description="Oil temperature, deg C")
    fuel_flow_lph: float = Field(..., ge=0, le=60, description="Fuel flow, litres/hour")
    vibration_mms: float = Field(..., ge=0, le=50, description="Vibration RMS, mm/s")

    # --- Electrical system health (PS-required: "Battery/Alternator health") ---
    # Defaults keep every existing TelemetryFrame(...) construction valid; the
    # simulator always populates these explicitly.
    battery_voltage_v: float = Field(default=28.0, ge=0, le=32, description="Main bus / battery voltage, V")
    alternator_load_pct: float = Field(default=45.0, ge=0, le=120, description="Alternator load, %")

    # --- Injection timing (PS-required: "Injection timing parameters") ---
    injection_timing_deg: float = Field(default=12.0, ge=-10, le=45, description="Injection timing advance, deg BTDC")

    altitude_ft: float = Field(..., ge=0, le=35000, description="Altitude, feet")
    ambient_temperature_c: float = Field(..., ge=-60, le=60, description="Ambient temperature, deg C")
    throttle_pct: float = Field(..., ge=0, le=100, description="Throttle position, %")
    engine_load_pct: float = Field(..., ge=0, le=100, description="Engine load, %")

    scenario: str | None = Field(default=None, description="Active simulator scenario label, if any")

    @field_validator("timestamp")
    @classmethod
    def _timestamp_not_absurd(cls, v: datetime) -> datetime:
        # Reject obviously broken clocks (e.g. epoch-zero or far future),
        # which in real telemetry usually indicates a clock/sync fault.
        if v.year < 2000 or v.year > 2100:
            raise ValueError("timestamp outside plausible range")
        return v

    def is_physically_plausible(self) -> bool:
        """Coarse sanity check beyond individual field ranges — catches
        combinations that are individually in-range but jointly impossible.
        This is intentionally simple; it is NOT a substitute for the
        Sensor Fault Isolation layer, which reasons about *patterns* over
        time rather than a single frame."""
        if self.rpm < 200 and self.egt_c > 300:
            return False  # engine essentially stopped but EGT very high
        if self.oil_pressure_psi < 5 and self.rpm > 1000:
            return False  # running engine with near-zero oil pressure
        return True


class TelemetryHistoryResponse(BaseModel):
    frames: list[TelemetryFrame]
    count: int


class ScenarioName(str, Enum):
    NORMAL_CRUISE = "NORMAL_CRUISE"
    HIGH_ALTITUDE = "HIGH_ALTITUDE"
    HOT_WEATHER = "HOT_WEATHER"
    THERMAL_DEGRADATION = "THERMAL_DEGRADATION"
    VIBRATION_DEGRADATION = "VIBRATION_DEGRADATION"
    SENSOR_DRIFT = "SENSOR_DRIFT"
    COMBUSTION_ANOMALY = "COMBUSTION_ANOMALY"
    COMBINED_DEGRADATION = "COMBINED_DEGRADATION"


class ScenarioRequest(BaseModel):
    scenario: ScenarioName
