from fastapi.testclient import TestClient

from main import app

client = TestClient(app)


def test_liveness_health_endpoint():
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"


def test_system_status_endpoint():
    resp = client.get("/api/system/status")
    assert resp.status_code == 200
    body = resp.json()
    assert "simulation_running" in body


def test_simulation_start_and_telemetry_current():
    start = client.post("/api/simulation/start")
    assert start.status_code == 200

    # Manually tick the shared engine once so there's data to fetch —
    # the background loop also ticks it, but we don't want this test to
    # depend on wall-clock timing.
    from telemetry.streaming import engine
    engine.tick()

    resp = client.get("/api/telemetry/current")
    assert resp.status_code == 200
    body = resp.json()
    assert "rpm" in body
    assert body["source"] == "simulated"


def test_scenario_switch_endpoint():
    resp = client.post("/api/simulation/scenario", json={"scenario": "THERMAL_DEGRADATION"})
    assert resp.status_code == 200
    assert resp.json()["scenario"] == "THERMAL_DEGRADATION"


def test_engine_state_endpoint_after_tick():
    from telemetry.streaming import engine
    engine.tick()
    resp = client.get("/api/engine/state")
    assert resp.status_code == 200
    body = resp.json()
    assert "health" in body and "rul" in body and "degradation" in body


def test_mission_parse_endpoint():
    resp = client.post("/api/mission/parse", json={"text": "Plan an 8 hour ISR mission at high altitude in hot weather."})
    assert resp.status_code == 200
    body = resp.json()
    assert body["parsed"]["duration_hours"] == 8.0
    assert body["parser_used"] == "rule_based_fallback"


def test_mission_simulate_endpoint():
    payload = {
        "mission_type": "HIGH_ALTITUDE",
        "duration_hours": 6,
        "cruise_altitude_ft": 8000,
        "max_altitude_ft": 22000,
        "ambient_temperature_c": 40,
        "average_throttle_pct": 80,
    }
    resp = client.post("/api/mission/simulate", json=payload)
    assert resp.status_code == 200
    body = resp.json()
    assert body["risk_level"] in ("GREEN", "YELLOW", "RED")
    assert len(body["trajectory"]) > 0
