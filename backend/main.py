"""
AeroTwin-X backend entrypoint.

Wires the domain routers together, enables CORS for the Vite dev server,
runs a background tick loop that advances the simulation engine while
`engine.running` is True, and exposes /ws/telemetry for the live
dashboard.
"""
from __future__ import annotations

import asyncio
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware

from config import settings
from telemetry.streaming import engine
from api import telemetry, physics, health, rul, mission, system

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("aerotwinx")


@asynccontextmanager
async def lifespan(_app: FastAPI):
    logger.info("AeroTwin-X backend starting up (environment=%s)", settings.environment)
    task = asyncio.create_task(_tick_loop())
    yield
    task.cancel()


app = FastAPI(title=settings.app_name, version="0.1.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    # Browsers reject "*" combined with credentials, so only allow
    # credentials when a specific origin list is configured. This app
    # doesn't use cookies, so disabling credentials for a wildcard-origin
    # deployment (e.g. quick Render demo before a real frontend URL is
    # known) is safe.
    allow_credentials=settings.cors_origin_list != ["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(system.router)
app.include_router(telemetry.router, prefix="/api")
app.include_router(physics.router, prefix="/api")
app.include_router(health.router, prefix="/api")
app.include_router(rul.router, prefix="/api")
app.include_router(mission.router, prefix="/api")


class ConnectionManager:
    def __init__(self):
        self._connections: set[WebSocket] = set()

    async def connect(self, ws: WebSocket) -> None:
        await ws.accept()
        self._connections.add(ws)

    def disconnect(self, ws: WebSocket) -> None:
        self._connections.discard(ws)

    async def broadcast(self, payload: str) -> None:
        dead: list[WebSocket] = []
        for ws in self._connections:
            try:
                await ws.send_text(payload)
            except Exception:
                dead.append(ws)
        for ws in dead:
            self.disconnect(ws)


manager = ConnectionManager()


@app.websocket("/ws/telemetry")
async def telemetry_ws(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            # Keep the connection open; all data is pushed from the
            # background tick loop below. We still need to await
            # receive() so disconnects are detected promptly.
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket)


async def _tick_loop():
    while True:
        await asyncio.sleep(settings.telemetry_tick_seconds)
        if not engine.running:
            continue
        try:
            message = engine.tick()
            await manager.broadcast(message.model_dump_json())
        except Exception:
            logger.exception("Error while ticking simulation engine")
