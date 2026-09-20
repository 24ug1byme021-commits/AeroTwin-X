"""
Natural-language mission input.

IMPORTANT: this module ONLY converts free text into structured
MissionInput parameters (and, on the way out, echoes back numbers the
physics/AI pipeline already computed). It must never itself invent an
engineering prediction — no health/RUL/risk numbers are produced here.

If config.settings.llm_enabled is False (no API key configured), this
falls back to a fully deterministic, offline, rule-based parser — the
app must work without any external LLM dependency. The LLM path is left
as a documented extension point rather than implemented, since no LLM
credentials are available in this environment; wiring one in later only
requires implementing `_parse_with_llm` and does not change the schema
or the deterministic fallback's behaviour.
"""
from __future__ import annotations

import re

from config import settings
from schemas.mission import MissionInput, MissionType, NaturalLanguageMissionParse

_DURATION_RE = re.compile(r"(\d+(?:\.\d+)?)\s*(?:h|hr|hrs|hour|hours)\b", re.IGNORECASE)

_ALTITUDE_KEYWORDS = {
    "high altitude": (22000.0, 24000.0),
    "high-altitude": (22000.0, 24000.0),
    "low altitude": (3000.0, 4000.0),
    "low-altitude": (3000.0, 4000.0),
}
_DEFAULT_CRUISE_ALT = 8000.0
_DEFAULT_MAX_ALT = 10000.0

_TEMPERATURE_KEYWORDS = {
    "hot weather": 42.0,
    "hot": 42.0,
    "cold weather": -15.0,
    "cold": -15.0,
}
_DEFAULT_AMBIENT_C = 15.0

_MISSION_TYPE_KEYWORDS = {
    "isr": MissionType.NORMAL_ISR,
    "surveillance": MissionType.NORMAL_ISR,
    "endurance": MissionType.HIGH_LOAD_ENDURANCE,
    "high load": MissionType.HIGH_LOAD_ENDURANCE,
    "high-load": MissionType.HIGH_LOAD_ENDURANCE,
}

_THROTTLE_BY_TYPE = {
    MissionType.NORMAL_ISR: 60.0,
    MissionType.HIGH_ALTITUDE: 70.0,
    MissionType.HOT_WEATHER: 60.0,
    MissionType.HIGH_LOAD_ENDURANCE: 85.0,
    MissionType.CUSTOM: 65.0,
}


def _rule_based_parse(text: str) -> tuple[MissionInput, list[str]]:
    notes: list[str] = []
    lowered = text.lower()

    duration_match = _DURATION_RE.search(lowered)
    if duration_match:
        duration_hours = float(duration_match.group(1))
    else:
        duration_hours = 4.0
        notes.append("No duration found in text; defaulted to 4 hours.")

    cruise_altitude_ft = _DEFAULT_CRUISE_ALT
    max_altitude_ft = _DEFAULT_MAX_ALT
    altitude_matched = False
    for kw, (cruise, mx) in _ALTITUDE_KEYWORDS.items():
        if kw in lowered:
            cruise_altitude_ft, max_altitude_ft = cruise, mx
            altitude_matched = True
            break
    if not altitude_matched:
        notes.append("No altitude keyword found; defaulted to normal altitude.")

    ambient_temperature_c = _DEFAULT_AMBIENT_C
    temp_matched = False
    for kw, temp in _TEMPERATURE_KEYWORDS.items():
        if kw in lowered:
            ambient_temperature_c = temp
            temp_matched = True
            break
    if not temp_matched:
        notes.append("No temperature keyword found; defaulted to standard temperature.")

    mission_type = MissionType.CUSTOM
    for kw, mtype in _MISSION_TYPE_KEYWORDS.items():
        if kw in lowered:
            mission_type = mtype
            break
    if mission_type == MissionType.CUSTOM and altitude_matched and max_altitude_ft >= 22000:
        mission_type = MissionType.HIGH_ALTITUDE
    if mission_type == MissionType.CUSTOM and temp_matched and ambient_temperature_c >= 35:
        mission_type = MissionType.HOT_WEATHER

    average_throttle_pct = _THROTTLE_BY_TYPE.get(mission_type, 65.0)

    mission_input = MissionInput(
        mission_type=mission_type,
        duration_hours=duration_hours,
        cruise_altitude_ft=cruise_altitude_ft,
        max_altitude_ft=max_altitude_ft,
        ambient_temperature_c=ambient_temperature_c,
        average_throttle_pct=average_throttle_pct,
    )
    return mission_input, notes


def parse_mission_text(text: str) -> NaturalLanguageMissionParse:
    if settings.llm_enabled and settings.llm_api_key:
        # Extension point: an LLM call would go here, but it must ONLY
        # extract structured fields (duration/altitude/temperature/type)
        # from `text` — never generate health/RUL/risk predictions itself.
        # Not implemented in this environment (no LLM credentials
        # available); falling back to the deterministic parser keeps the
        # app fully functional offline.
        pass

    mission_input, notes = _rule_based_parse(text)
    return NaturalLanguageMissionParse(
        raw_text=text,
        parsed=mission_input,
        parser_used="rule_based_fallback",
        parse_notes=notes,
    )
