# AeroTwin-X

**AI-Enabled Mission-Aware Digital Twin for Aero-Piston Engine Health & Mission Reliability**
Prototype for SIH 2026 Problem Statement **SIH26054** (DRDO — Robotics and Drones).

> ⚠️ **All telemetry in this prototype is simulated/synthetic.** No real DRDO or UAV
> engine data is used, referenced, or implied anywhere in this codebase. See
> [Limitations](#limitations) below.

## What's new in this build

- **Aerospace-grade dashboard.** Full visual overhaul: animated hero header,
  live **engine schematic** (spinning crank, moving pistons, sensor pickups that
  light up), **animated circular gauges**, an animated **Digital-Twin pipeline**
  diagram, and a status-driven health ring that pulses on critical.
- **Residual-driven fault visualization.** The schematic's sensor nodes colour by
  the *physics residual* (actual − expected for the current operating point), not
  the raw value — so a legitimately hot cylinder at high altitude stays green while
  a genuinely degrading one is flagged even before it reaches an absolute redline.
  The raw gauges independently show true instrument redlines.
- **Battery/Alternator health + Injection timing** added to the telemetry contract,
  simulator and dashboard (completes the PS health-monitoring parameter set).
- **Fixed Start/Stop reset.** Stopping now fully resets the simulator, degradation,
  RUL, health and fault-isolation state and clears history, so a new run always
  starts clean from zero instead of freezing on the last frame or resuming old
  degradation. Added a `POST /api/simulation/reset` endpoint and a Reset button.
- **Demo-tuned fault rates** so thermal/vibration/sensor degradation develops
  visibly within a couple of minutes of wall-clock time.

---

## 1. Problem

Conventional UAV piston-engine monitoring is threshold-based and reactive — it tells
an operator an abnormality has already occurred, not whether the engine can safely
complete an upcoming mission, how it is likely to degrade, or how much time remains
before maintenance is needed.

## 2. AeroTwin-X Solution

AeroTwin-X answers a different question than a normal health-monitoring dashboard:

> **"Given the current engine condition and the upcoming mission profile, can this
> engine reliably complete the mission, what risks are expected, and what action
> should the operator take?"**

It does this with three linked innovations:

1. **Physics-Residual AI** — a documented, simplified physics model predicts what a
   *healthy* engine should read at the current operating point; the AI layer reasons
   about the *residual* (actual − expected), not raw sensor values.
2. **Mission-Conditioned RUL** — Remaining Useful Life depends on the mission profile,
   not just elapsed time — the same engine can have very different RUL for a gentle
   cruise vs. a high-altitude, high-load mission.
3. **Sensor Fault Isolation** — the system distinguishes "this sensor is probably
   drifting" from "this engine is probably degrading," rather than raising one
   generic alarm for both.

## 3. Architecture

```
Engine Telemetry (simulated)
        │
        ▼
Sensor Validation / Sensor Fault Isolation   ← distinguishes sensor vs. engine fault
        │
        ▼
Physics-Based Engine Twin                    ← "what should a healthy engine show?"
        │
        ▼
Physics Residual Calculation                 ← actual − expected
        │
        ▼
AI Health Twin (IsolationForest + rules)     ← anomaly score, health index, fault type
        │
        ▼
Degradation Tracking                         ← leaky-integrator accumulated stress
        │
        ▼
Uncertainty-Aware RUL                        ← derived from fitted degradation rate
        │
        ▼
Mission Twin / What-If Simulation            ← projects health forward through a mission
        │
        ▼
Mission Readiness Assessment                 ← GREEN / YELLOW / RED + explicit reason
        │
        ▼
Actionable Recommendation
```

See [`docs/architecture.md`](docs/architecture.md) for full data flow, every physics
assumption, and the exact folder-to-pipeline-stage mapping.

## 4. Tech Stack

- **Backend:** Python 3.11+, FastAPI, Pydantic, NumPy, SciPy, scikit-learn, SQLite (WebSockets for live streaming)
- **Frontend:** React + TypeScript + Vite, Tailwind CSS, Recharts, Lucide icons, custom animated SVG instrumentation (gauges, live engine schematic, pipeline flow)
- **Testing:** pytest (41 backend tests, all passing)

### Monitored parameters

RPM, Cylinder Head Temperature (CHT), Exhaust Gas Temperature (EGT), Oil
Pressure & Temperature, Fuel Flow, Vibration, **Battery / bus voltage &
Alternator load**, and **Injection timing** — covering the full health-monitoring
parameter set called for in the problem statement.

## 5. Project Structure

```
AeroTwin-X/
├── backend/
│   ├── main.py                 FastAPI app, CORS, WebSocket, background tick loop
│   ├── config.py               Settings (pydantic-settings)
│   ├── api/                    REST routers (telemetry, physics, health, rul, mission, system)
│   ├── schemas/                Pydantic data contracts (telemetry, health, mission, prediction)
│   ├── telemetry/               Simulator + 8 scenario presets + streaming/session engine
│   ├── physics/                 Engine baseline model + residual calculation
│   ├── sensor_fault_isolation/  Sensor-vs-engine fault reasoning
│   ├── health/                  IsolationForest anomaly detector + fault classifier + health index
│   ├── rul/                     Degradation tracker + RUL estimator + uncertainty
│   ├── mission/                 Mission stress model + Mission Twin simulator + readiness engine + NL parser
│   └── tests/                   41 pytest tests covering every module above
├── frontend/
│   └── src/
│       ├── components/          Panel, StatusBadge, telemetry/health/mission UI panels
│       ├── pages/DashboardPage.tsx
│       ├── services/api.ts      REST client
│       ├── hooks/useTelemetryStream.ts   WebSocket hook
│       └── types/api.ts         TypeScript mirror of the backend schemas
├── data/                        (reserved for synthetic CSVs / recorded scenarios)
└── docs/architecture.md
```

## 6. Setup

### Backend
```bash
cd backend
python3 -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp ../.env.example .env         # optional — defaults work without it
```

### Frontend
```bash
cd frontend
npm install
```

## 7. Run

Two terminals:

```bash
# Terminal 1 — backend
cd backend && source venv/bin/activate && uvicorn main:app --reload --port 8000

# Terminal 2 — frontend
cd frontend && npm run dev
```

Open **http://localhost:5173**. The Vite dev server proxies `/api`, `/health` and
`/ws` to the backend on port 8000 (see `frontend/vite.config.ts`) — no separate CORS
configuration needed for local development.

## 8. Demo Instructions

1. Click **Start Simulation** (defaults to `NORMAL_CRUISE`).
2. Watch Live Telemetry, Physics Twin (actual vs. expected), and AI Health populate in
   real time over the WebSocket stream.
3. Switch to **Thermal Degradation** — watch CHT/EGT residuals and the degradation
   index climb over ~1-2 minutes, then RUL start to drop from its "no significant
   degradation" ceiling.
4. Switch to **Sensor Drift** — watch the Sensor Fault Isolation panel report
   `POSSIBLE_SENSOR_FAULT` (CHT only) rather than an engine-fault warning, since EGT/
   vibration/fuel-flow stay flat. Compare this against Thermal Degradation, where the
   same CHT rise is instead correctly classified `POSSIBLE_ENGINE_FAULT` because EGT
   moves with it.
5. In the **Mission Twin** panel, type a natural-language mission (e.g. *"Plan an 8
   hour ISR mission at high altitude in hot weather"*) and click **Parse & Run** —
   the deterministic parser extracts duration/altitude/temperature, then the Mission
   Twin projects the current engine's degradation state forward through that
   profile and returns a GREEN/YELLOW/RED verdict with a stated critical phase and
   contributing factors.

## 9. Testing

```bash
cd backend && source venv/bin/activate && python -m pytest -v
```
41/41 tests passing, covering: telemetry schema validation, all 8 simulator
scenarios (including that Sensor Drift moves only the CHT reading, not EGT/fuel
flow), the physics model, residual calculation, sensor fault isolation logic, the
anomaly detector/health index/degradation tracker/RUL estimator, mission simulation
+ readiness decisions, and the REST API end-to-end.

## 10. What's Implemented vs. Future Real-UAV Integration

| Component | Status |
|---|---|
| Telemetry schema, validation | ✅ Implemented (prototype ranges — see architecture.md) |
| Telemetry simulator (8 scenarios) | ✅ Implemented, fully synthetic |
| Physics Twin | ✅ Implemented, simplified/documented assumptions |
| Physics Residuals | ✅ Implemented |
| Sensor Fault Isolation | ✅ Implemented, rule-based, "possible/suspected" language throughout |
| AI Health Twin | ✅ Implemented — real scikit-learn IsolationForest trained on simulated healthy data |
| Degradation Tracking | ✅ Implemented — leaky-integrator, not random |
| RUL + Uncertainty | ✅ Implemented — derived from fitted degradation rate |
| Mission Twin / Mission-Conditioned RUL | ✅ Implemented |
| Mission Readiness Engine | ✅ Implemented |
| Natural-language mission input | ✅ Deterministic rule-based parser (offline). LLM path is a documented, unimplemented extension point — no LLM credentials available in this environment |
| Live dashboard (WebSocket) | ✅ Implemented |
| Demo Mode scripted sequence | ⏳ Manual via Scenario Controller today; a fully scripted auto-advancing sequence is the next increment |
| Real CAN/ECU/FADEC hardware integration | 🔭 Future — architecture is designed for it (see below), not built in this prototype |
| Federated learning across a UAV fleet | 🔭 Future roadmap item, not implemented |

## 11. Future Deployment Architecture

```
UAV ENGINE → ECU/Sensors → CAN/Telemetry → EDGE GATEWAY
    → Compressed Telemetry → Ground Control Station → AeroTwin-X Digital Twin
    → Mission Decision Support
```

The current prototype runs entirely locally (no physical hardware required) and is
built so `telemetry/simulator.py` can be swapped for a real CAN/SocketCAN telemetry
source without changing any downstream module — every module downstream of the
simulator only depends on the `TelemetryFrame` schema, not on how it was produced.

## 12. Limitations

- All telemetry is simulated. No real aero-piston engine or DRDO dataset was
  available, so the physics model's constants (documented in
  `docs/architecture.md`) are prototype assumptions, not values from a certified
  engine's operating manual.
- The AI Health Twin's IsolationForest is trained on simulated healthy data only —
  its anomaly scores are internally consistent within this prototype, not
  calibrated against real engine failure statistics.
- RUL is a prototype estimate derived from the simulated degradation trajectory. It
  is explicitly labeled as such in every API response (`RULEstimate.basis`) and is
  not a certified time-to-failure prediction.
- The natural-language mission parser is a deterministic, offline, rule-based
  fallback. No LLM is called in this environment.
