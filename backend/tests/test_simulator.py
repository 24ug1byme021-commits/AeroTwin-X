from schemas.telemetry import ScenarioName
from telemetry.simulator import EngineSimulator


def _run(scenario: ScenarioName, steps: int = 120, seed: int = 1):
    sim = EngineSimulator(scenario=scenario, seed=seed)
    frames = [sim.step(1.0) for _ in range(steps)]
    return frames


def test_normal_cruise_produces_valid_frames():
    frames = _run(ScenarioName.NORMAL_CRUISE)
    assert len(frames) == 120
    for f in frames:
        assert f.rpm > 0
        assert f.scenario == ScenarioName.NORMAL_CRUISE.value


def test_all_scenarios_run_without_error():
    for scenario in ScenarioName:
        frames = _run(scenario, steps=30)
        assert len(frames) == 30


def test_thermal_degradation_increases_cht_over_time():
    frames = _run(ScenarioName.THERMAL_DEGRADATION, steps=300)
    early_avg = sum(f.cht_c for f in frames[:20]) / 20
    late_avg = sum(f.cht_c for f in frames[-20:]) / 20
    assert late_avg > early_avg + 5, "CHT should trend upward under thermal degradation"


def test_vibration_degradation_increases_vibration_over_time():
    frames = _run(ScenarioName.VIBRATION_DEGRADATION, steps=300)
    early_avg = sum(f.vibration_mms for f in frames[:20]) / 20
    late_avg = sum(f.vibration_mms for f in frames[-20:]) / 20
    assert late_avg > early_avg + 0.5, "Vibration should trend upward under vibration degradation"


def test_sensor_drift_does_not_move_egt_or_fuel_flow():
    frames = _run(ScenarioName.SENSOR_DRIFT, steps=300)
    early_egt = sum(f.egt_c for f in frames[:20]) / 20
    late_egt = sum(f.egt_c for f in frames[-20:]) / 20
    early_fuel = sum(f.fuel_flow_lph for f in frames[:20]) / 20
    late_fuel = sum(f.fuel_flow_lph for f in frames[-20:]) / 20
    # EGT/fuel flow should stay roughly flat — only the CHT *sensor
    # reading* should drift in this scenario, not the true engine state.
    assert abs(late_egt - early_egt) < 15
    assert abs(late_fuel - early_fuel) < 2

    early_cht = sum(f.cht_c for f in frames[:20]) / 20
    late_cht = sum(f.cht_c for f in frames[-20:]) / 20
    assert late_cht > early_cht + 5, "Reported CHT should drift due to sensor bias"


def test_scenario_switch_carries_state_forward():
    sim = EngineSimulator(scenario=ScenarioName.NORMAL_CRUISE, seed=3)
    for _ in range(30):
        sim.step(1.0)
    rpm_before = sim.state.rpm
    sim.set_scenario(ScenarioName.THERMAL_DEGRADATION)
    frame = sim.step(1.0)
    # RPM shouldn't jump discontinuously just from switching scenario.
    assert abs(frame.rpm - rpm_before) < 200
