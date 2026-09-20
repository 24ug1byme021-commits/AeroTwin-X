"""
Tests for the SQLite persistence layer — proves runs are recorded and
can be summarised (post-flight analysis) and replayed.
"""
import tempfile
from pathlib import Path

from storage.recorder import TelemetryRecorder
from telemetry.streaming import SimulationEngine
from schemas.telemetry import ScenarioName


def _temp_recorder() -> TelemetryRecorder:
    tmp = Path(tempfile.mkdtemp()) / "test.db"
    return TelemetryRecorder(f"sqlite:///{tmp}")


def test_recorder_creates_and_lists_runs():
    rec = _temp_recorder()
    assert rec.list_runs() == []
    run_id = rec.start_run("NORMAL_CRUISE", "hybrid")
    assert run_id is not None
    rec.end_run()
    runs = rec.list_runs()
    assert len(runs) == 1
    assert runs[0]["scenario"] == "NORMAL_CRUISE"
    assert runs[0]["ended_at"] is not None


def test_recorder_records_frames_and_reports():
    """Drive a real engine through a recorder and confirm frames + report."""
    rec = _temp_recorder()
    run_id = rec.start_run("THERMAL_DEGRADATION", "statistical")

    eng = SimulationEngine()
    eng.set_scenario(ScenarioName.THERMAL_DEGRADATION)
    eng.start()
    for _ in range(30):
        rec.record(eng.tick())
    rec.end_run()

    frames = rec.get_frames(run_id)
    assert len(frames) == 30
    assert frames[0]["cht_c"] is not None

    report = rec.run_report(run_id)
    assert report is not None
    assert report["summary"]["frames"] == 30
    assert report["summary"]["peak_cht"] is not None


def test_report_missing_run_returns_none():
    rec = _temp_recorder()
    assert rec.run_report(9999) is None
