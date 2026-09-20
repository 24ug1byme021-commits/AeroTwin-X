from fastapi import APIRouter, HTTPException, Query

from schemas.telemetry import TelemetryFrame, TelemetryHistoryResponse, ScenarioRequest
from telemetry.streaming import engine
from storage.recorder import get_recorder

router = APIRouter(tags=["telemetry"])


@router.get("/runs")
def list_runs(limit: int = Query(default=50, ge=1, le=200)):
    """List recorded simulation runs (post-flight analysis index)."""
    recorder = get_recorder()
    if recorder is None:
        return {"runs": [], "persistence": "unavailable"}
    return {"runs": recorder.list_runs(limit), "persistence": "sqlite"}


@router.get("/runs/{run_id}/report")
def get_run_report(run_id: int):
    """Post-flight summary report for a completed run."""
    recorder = get_recorder()
    if recorder is None:
        raise HTTPException(status_code=503, detail="Persistence unavailable")
    report = recorder.run_report(run_id)
    if report is None:
        raise HTTPException(status_code=404, detail=f"Run {run_id} not found")
    return report


@router.get("/runs/{run_id}/frames")
def get_run_frames(run_id: int, limit: int = Query(default=5000, ge=1, le=20000)):
    """Stored frames for a run — used for mission replay."""
    recorder = get_recorder()
    if recorder is None:
        raise HTTPException(status_code=503, detail="Persistence unavailable")
    frames = recorder.get_frames(run_id, limit)
    if not frames and recorder.get_run(run_id) is None:
        raise HTTPException(status_code=404, detail=f"Run {run_id} not found")
    return {"run_id": run_id, "frame_count": len(frames), "frames": frames}


@router.get("/telemetry/current", response_model=TelemetryFrame)
def get_current_telemetry():
    latest = engine.latest()
    if latest is None:
        raise HTTPException(status_code=404, detail="No telemetry yet — POST /api/simulation/start first.")
    return latest.telemetry


@router.get("/telemetry/history", response_model=TelemetryHistoryResponse)
def get_telemetry_history(n: int = Query(default=100, ge=1, le=3600)):
    messages = engine.history(n)
    frames = [m.telemetry for m in messages]
    return TelemetryHistoryResponse(frames=frames, count=len(frames))


@router.post("/simulation/start")
def start_simulation():
    engine.start()
    return {"status": "started", "scenario": engine.simulator.scenario.value}


@router.post("/simulation/stop")
def stop_simulation():
    engine.stop()
    return {"status": "stopped"}


@router.post("/simulation/reset")
def reset_simulation():
    engine.reset()
    return {"status": "reset", "scenario": engine.simulator.scenario.value}


@router.post("/detector/mode")
def set_detector_mode(payload: dict):
    """Switch anomaly-detection backend: 'statistical' | 'ml' | 'hybrid'."""
    mode = payload.get("mode", "")
    try:
        applied = engine.set_detector_mode(mode)
    except ValueError as exc:
        return {"status": "error", "detail": str(exc)}
    return {"status": "ok", "detector_mode": applied}


@router.post("/simulation/scenario")
def set_scenario(request: ScenarioRequest):
    engine.set_scenario(request.scenario)
    return {"status": "ok", "scenario": request.scenario.value}
