from fastapi import APIRouter, HTTPException

from schemas.health import HealthIndexResult, SensorFaultDiagnosis
from telemetry.streaming import engine

router = APIRouter(prefix="/health", tags=["health"])


@router.get("/status", response_model=HealthIndexResult)
def get_health_status():
    latest = engine.latest()
    if latest is None or latest.health is None:
        raise HTTPException(status_code=404, detail="No health assessment yet — POST /api/simulation/start first.")
    return latest.health


@router.get("/sensor-fault", response_model=SensorFaultDiagnosis)
def get_sensor_fault_diagnosis():
    latest = engine.latest()
    if latest is None or latest.sensor_fault is None:
        raise HTTPException(status_code=404, detail="No sensor fault diagnosis yet — POST /api/simulation/start first.")
    return latest.sensor_fault
