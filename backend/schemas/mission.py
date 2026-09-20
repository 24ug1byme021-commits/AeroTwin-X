"""
Schemas for the Mission Twin / what-if simulator and the Mission
Readiness decision layer.
"""
from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, Field


class MissionType(str, Enum):
    NORMAL_ISR = "NORMAL_ISR"
    HIGH_ALTITUDE = "HIGH_ALTITUDE"
    HOT_WEATHER = "HOT_WEATHER"
    HIGH_LOAD_ENDURANCE = "HIGH_LOAD_ENDURANCE"
    CUSTOM = "CUSTOM"


class MissionInput(BaseModel):
    mission_type: MissionType = MissionType.CUSTOM
    duration_hours: float = Field(..., gt=0, le=48)
    cruise_altitude_ft: float = Field(..., ge=0, le=35000)
    max_altitude_ft: float = Field(..., ge=0, le=35000)
    ambient_temperature_c: float = Field(..., ge=-60, le=60)
    average_throttle_pct: float = Field(..., ge=0, le=100)
    endurance_requirement_hours: float | None = Field(
        default=None, description="Minimum hours the mission requires the engine to keep running"
    )


class RiskLevel(str, Enum):
    GREEN = "GREEN"
    YELLOW = "YELLOW"
    RED = "RED"


class MissionTrajectoryPoint(BaseModel):
    t_hours: float
    health_index: float
    egt_c: float
    cht_c: float
    vibration_mms: float
    degradation_index: float


class MissionResult(BaseModel):
    mission_input: MissionInput
    trajectory: list[MissionTrajectoryPoint]
    predicted_end_of_mission_health: float = Field(..., ge=0, le=100)
    predicted_rul_hours: float
    rul_uncertainty_hours: float
    risk_level: RiskLevel
    critical_phase: str
    main_contributors: list[str]
    recommendation: str


class NaturalLanguageMissionRequest(BaseModel):
    text: str = Field(..., min_length=3, max_length=500)


class NaturalLanguageMissionParse(BaseModel):
    raw_text: str
    parsed: MissionInput
    parser_used: str = Field(..., description="'llm' or 'rule_based_fallback'")
    parse_notes: list[str] = Field(default_factory=list)
