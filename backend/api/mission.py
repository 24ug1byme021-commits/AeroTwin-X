from datetime import datetime, timezone

from fastapi import APIRouter

from schemas.health import DegradationState
from schemas.mission import MissionInput, MissionResult, NaturalLanguageMissionRequest, NaturalLanguageMissionParse
from mission.simulator import simulate_mission
from mission.readiness import assess
from mission.nl_parser import parse_mission_text
from telemetry.streaming import engine

router = APIRouter(prefix="/mission", tags=["mission"])


def _current_or_default_degradation() -> DegradationState:
    latest = engine.latest()
    if latest is not None and latest.degradation is not None:
        return latest.degradation
    # No simulation has run yet — start the Mission Twin from a clean,
    # explicitly-labelled healthy baseline rather than erroring out, so
    # the Mission Twin can be demoed independently of the live stream.
    return DegradationState(
        timestamp=datetime.now(timezone.utc),
        degradation_index=0.0,
        thermal_component=0.0,
        vibration_component=0.0,
        residual_component=0.0,
        accumulated_operating_hours=0.0,
    )


@router.post("/simulate", response_model=MissionResult)
def simulate(mission: MissionInput):
    start_degradation = _current_or_default_degradation()
    trajectory = simulate_mission(mission, start_degradation)
    return assess(mission, trajectory)


@router.post("/parse", response_model=NaturalLanguageMissionParse)
def parse(request: NaturalLanguageMissionRequest):
    return parse_mission_text(request.text)
