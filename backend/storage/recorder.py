"""
Telemetry persistence — SQLite (standard-library sqlite3, no ORM, no
external dependency, fully offline / air-gap friendly).

Every simulation run is recorded as a row in `runs`, and every processed
frame as a row in `frames`. This gives the system three things the
problem statement explicitly asks for:

  * a real datastore ("Cloud or local server-based analytics"),
  * post-flight analysis (query a completed run), and
  * mission replay (stream a stored run back).

The recorder is deliberately fail-safe: if the database is unavailable
for any reason, recording is skipped and a warning is logged — telemetry
streaming and health analysis never break because of a storage problem.
This mirrors how a real GCS must keep flying even if its logging disk
fills up.
"""
from __future__ import annotations

import logging
import sqlite3
import threading
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

logger = logging.getLogger("aerotwinx.storage")


def _resolve_sqlite_path(database_url: str) -> Path:
    """Turn a sqlite:///relative/or/absolute path URL into a Path."""
    prefix = "sqlite:///"
    raw = database_url[len(prefix):] if database_url.startswith(prefix) else database_url
    return Path(raw).resolve()


class TelemetryRecorder:
    def __init__(self, database_url: str):
        self._path = _resolve_sqlite_path(database_url)
        self._path.parent.mkdir(parents=True, exist_ok=True)
        # check_same_thread=False: the async tick loop and API handlers may
        # touch the connection from different threads; we serialise writes
        # with our own lock to keep it safe and simple.
        self._lock = threading.Lock()
        self._conn = sqlite3.connect(str(self._path), check_same_thread=False)
        self._conn.execute("PRAGMA journal_mode=WAL;")
        self._conn.row_factory = sqlite3.Row
        self._init_schema()
        self._active_run_id: int | None = None

    def _init_schema(self) -> None:
        with self._lock:
            self._conn.executescript(
                """
                CREATE TABLE IF NOT EXISTS runs (
                    run_id        INTEGER PRIMARY KEY AUTOINCREMENT,
                    started_at    TEXT NOT NULL,
                    ended_at      TEXT,
                    scenario      TEXT,
                    detector_mode TEXT,
                    frame_count   INTEGER DEFAULT 0
                );
                CREATE TABLE IF NOT EXISTS frames (
                    run_id            INTEGER NOT NULL,
                    ts                TEXT NOT NULL,
                    rpm               REAL, cht_c REAL, egt_c REAL,
                    oil_pressure_psi  REAL, oil_temperature_c REAL,
                    fuel_flow_lph     REAL, vibration_mms REAL,
                    battery_voltage_v REAL, alternator_load_pct REAL,
                    injection_timing_deg REAL, altitude_ft REAL,
                    cht_residual_c    REAL, egt_residual_c REAL,
                    health_index      REAL, status TEXT,
                    anomaly_score     REAL, degradation_index REAL,
                    rul_hours         REAL,
                    FOREIGN KEY(run_id) REFERENCES runs(run_id)
                );
                CREATE INDEX IF NOT EXISTS idx_frames_run ON frames(run_id);
                """
            )
            self._conn.commit()

    # -- run lifecycle -------------------------------------------------
    def start_run(self, scenario: str, detector_mode: str) -> int | None:
        try:
            now = datetime.now(timezone.utc).isoformat()
            with self._lock:
                cur = self._conn.execute(
                    "INSERT INTO runs (started_at, scenario, detector_mode) VALUES (?, ?, ?)",
                    (now, scenario, detector_mode),
                )
                self._conn.commit()
                self._active_run_id = int(cur.lastrowid)
            return self._active_run_id
        except Exception as exc:  # pragma: no cover - defensive
            logger.warning("start_run failed, continuing without persistence: %s", exc)
            self._active_run_id = None
            return None

    def update_scenario(self, scenario: str) -> None:
        """Reflect a mid-run scenario change on the active run row."""
        if self._active_run_id is None:
            return
        try:
            with self._lock:
                self._conn.execute(
                    "UPDATE runs SET scenario = ? WHERE run_id = ?",
                    (scenario, self._active_run_id),
                )
                self._conn.commit()
        except Exception as exc:  # pragma: no cover
            logger.warning("update_scenario failed: %s", exc)

    def end_run(self) -> None:
        if self._active_run_id is None:
            return
        try:
            now = datetime.now(timezone.utc).isoformat()
            with self._lock:
                self._conn.execute(
                    "UPDATE runs SET ended_at = ? WHERE run_id = ?",
                    (now, self._active_run_id),
                )
                self._conn.commit()
        except Exception as exc:  # pragma: no cover
            logger.warning("end_run failed: %s", exc)
        finally:
            self._active_run_id = None

    # -- per-frame recording ------------------------------------------
    def record(self, message: Any) -> None:
        if self._active_run_id is None:
            return
        try:
            t = message.telemetry
            r = message.residuals
            h = message.health
            d = message.degradation
            rul = message.rul
            row = (
                self._active_run_id,
                t.timestamp.isoformat() if hasattr(t.timestamp, "isoformat") else str(t.timestamp),
                t.rpm, t.cht_c, t.egt_c, t.oil_pressure_psi, t.oil_temperature_c,
                t.fuel_flow_lph, t.vibration_mms, t.battery_voltage_v,
                t.alternator_load_pct, t.injection_timing_deg, t.altitude_ft,
                getattr(r, "cht_residual_c", None) if r else None,
                getattr(r, "egt_residual_c", None) if r else None,
                getattr(h, "health_index", None) if h else None,
                getattr(h, "status", None).value if h and getattr(h, "status", None) else None,
                getattr(h, "anomaly_score", None) if h else None,
                getattr(d, "degradation_index", None) if d else None,
                getattr(rul, "rul_hours", None) if rul else None,
            )
            with self._lock:
                self._conn.execute(
                    """INSERT INTO frames (
                        run_id, ts, rpm, cht_c, egt_c, oil_pressure_psi, oil_temperature_c,
                        fuel_flow_lph, vibration_mms, battery_voltage_v, alternator_load_pct,
                        injection_timing_deg, altitude_ft, cht_residual_c, egt_residual_c,
                        health_index, status, anomaly_score, degradation_index, rul_hours
                    ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                    row,
                )
                self._conn.execute(
                    "UPDATE runs SET frame_count = frame_count + 1 WHERE run_id = ?",
                    (self._active_run_id,),
                )
                self._conn.commit()
        except Exception as exc:  # pragma: no cover
            logger.warning("frame record failed: %s", exc)

    # -- queries: post-flight analysis & replay -----------------------
    def list_runs(self, limit: int = 50) -> list[dict]:
        with self._lock:
            rows = self._conn.execute(
                "SELECT * FROM runs ORDER BY run_id DESC LIMIT ?", (limit,)
            ).fetchall()
        return [dict(r) for r in rows]

    def get_run(self, run_id: int) -> dict | None:
        with self._lock:
            row = self._conn.execute("SELECT * FROM runs WHERE run_id = ?", (run_id,)).fetchone()
        return dict(row) if row else None

    def get_frames(self, run_id: int, limit: int = 5000) -> list[dict]:
        with self._lock:
            rows = self._conn.execute(
                "SELECT * FROM frames WHERE run_id = ? ORDER BY rowid ASC LIMIT ?",
                (run_id, limit),
            ).fetchall()
        return [dict(r) for r in rows]

    def run_report(self, run_id: int) -> dict | None:
        """Aggregate a completed run into a post-flight summary."""
        with self._lock:
            run = self._conn.execute("SELECT * FROM runs WHERE run_id = ?", (run_id,)).fetchone()
            if run is None:
                return None
            agg = self._conn.execute(
                """SELECT
                     COUNT(*)          AS frames,
                     MIN(health_index) AS min_health,
                     AVG(health_index) AS avg_health,
                     MAX(cht_c)        AS peak_cht,
                     MAX(egt_c)        AS peak_egt,
                     MAX(vibration_mms) AS peak_vibration,
                     MAX(anomaly_score) AS peak_anomaly,
                     MAX(degradation_index) AS peak_degradation,
                     MIN(rul_hours)    AS min_rul
                   FROM frames WHERE run_id = ?""",
                (run_id,),
            ).fetchone()
        report = dict(run)
        report["summary"] = {k: (round(v, 2) if isinstance(v, float) else v) for k, v in dict(agg).items()}
        return report


_recorder: TelemetryRecorder | None = None


def get_recorder() -> TelemetryRecorder | None:
    """Lazily construct the shared recorder; returns None if it can't init."""
    global _recorder
    if _recorder is None:
        try:
            from config import settings
            _recorder = TelemetryRecorder(settings.database_url)
            logger.info("Telemetry recorder ready at %s", _recorder._path)
        except Exception as exc:  # pragma: no cover
            logger.warning("Recorder unavailable, running without persistence: %s", exc)
            _recorder = None
    return _recorder
