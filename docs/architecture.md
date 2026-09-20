# AeroTwin-X Architecture

## 1. Data Flow

```
telemetry/simulator.py  (EngineSimulator.step)
        │  produces TelemetryFrame (schemas/telemetry.py)
        ▼
physics/residuals.py    (compute_residuals)
        │  uses physics/engine_model.py to get "expected" values
        │  produces ResidualFrame (schemas/health.py)
        ▼
sensor_fault_isolation/detector.py   (SensorFaultIsolator.update)
        │  produces SensorFaultDiagnosis
        ▼
health/anomaly_detector.py   (AnomalyDetector.score)
        │  IsolationForest → anomaly_score
        ▼
health/fault_classifier.py   (classify)
        │  rule-based → suspected_fault + contributing signals
        ▼
health/health_index.py       (HealthIndexEngine.update)
        │  produces HealthIndexResult (0-100, status, trend, confidence)
        ▼
rul/degradation.py            (DegradationTracker.update)
        │  produces DegradationState (leaky-integrator accumulation)
        ▼
rul/estimator.py              (RULEstimator.update)
        │  produces RULEstimate (fitted degradation rate → hours remaining)
        ▼
telemetry/streaming.py (SimulationEngine.tick) ties all of the above together
into one TelemetryStreamMessage per tick, broadcast over /ws/telemetry and
also served by the REST endpoints (each reads the same in-memory history).

mission/simulator.py + mission/readiness.py are a SEPARATE, on-demand forward
projection — triggered by POST /api/mission/simulate, starting from whatever
degradation state the live pipeline above currently has (or a healthy default
if the simulation hasn't been started yet).
```

## 2. Why Residuals Instead of Raw Values

The AI layer never sees raw EGT/CHT/etc. directly — it sees `actual − expected`,
where `expected` comes from `physics/engine_model.py`. This means:

- The **same** healthy-baseline math is used by (a) the simulator to generate
  ground truth, and (b) the physics twin to predict what it *should* see. When the
  engine is healthy, actual ≈ expected and residuals hover near zero. When a fault
  scenario injects a delta the physics twin doesn't know about, a genuine residual
  appears — this is not circular, because the fault deltas are injected
  independently of the shared baseline (see `telemetry/scenarios.py`).
- The anomaly detector and rule-based classifier reason about deviations that are
  already normalized for operating point (throttle/altitude/ambient), so a healthy
  engine at high power doesn't look anomalous just because its absolute EGT is high.

## 3. Physics Twin Assumptions (`physics/engine_model.py`, `physics/thermodynamics.py`)

These are prototype constants for a small aero-piston engine broadly in the class
used on MALE UAVs (~90-130 hp four-stroke). **They are not sourced from a specific
certified engine's operating manual** — they were chosen to be internally consistent
(monotonic in load/altitude/temperature the way a real engine is) and to produce
clearly demo-able, recognizable fault signatures.

| Assumption | Value | Real/simplified? |
|---|---|---|
| ISA temperature lapse rate | 1.98°C / 1000 ft | Real published constant |
| Idle RPM / Max RPM | 1700 / 5500 | Prototype assumption |
| EGT at idle (sea level, 15°C) | 620°C | Prototype assumption |
| EGT gain at full load | +190°C | Prototype assumption |
| CHT at idle (sea level, 15°C) | 95°C | Prototype assumption |
| CHT gain at full load | +95°C (before cooling-efficiency correction) | Prototype assumption |
| Air density factor | `exp(-altitude_ft / 27000)` | Simplified barometric approximation |
| Cooling efficiency vs. altitude | `density_factor ** 0.5`, floored at 0.55 | Stated simplification, not a CFD-derived cooling curve |
| Oil temperature | Base 60°C + 35% of (CHT − baseline) | Prototype coupling assumption |
| Fuel flow | 4 L/h idle → 32 L/h max, divided by density factor at altitude | Prototype assumption (represents richer mixture demand at altitude if uncompensated) |
| Oil pressure | Base 55 psi + RPM-dependent gain − high-oil-temperature penalty | Prototype assumption |

**What this model deliberately does NOT claim:** it is not a certified aero-engine
performance model, it does not model transient combustion chemistry, and its
altitude/cooling relationship is a single smooth approximation used for both EGT and
CHT rather than the more detailed cooling-drag/airspeed-dependent models a real OEM
performance map would use.

## 4. Fault Scenario Signatures (`telemetry/scenarios.py`)

Each of the 8 scenarios is an **environment preset + degradation profile** applied on
top of the shared healthy baseline — not independent random generators:

| Scenario | Mechanism |
|---|---|
| NORMAL_CRUISE / HIGH_ALTITUDE / HOT_WEATHER | Environment preset only, no injected fault |
| THERMAL_DEGRADATION | CHT/EGT true engine state biased upward over time (both signals move together) |
| VIBRATION_DEGRADATION | Vibration biased upward over time, thermal signals unaffected |
| SENSOR_DRIFT | Bias applied **only to the reported CHT sensor value** — true engine state (and therefore EGT/vibration/fuel flow) is unaffected. This is what lets Sensor Fault Isolation correctly say "possible sensor fault" rather than "possible engine fault." |
| COMBUSTION_ANOMALY | Irregular EGT/vibration pulses + fuel-flow dropouts, misfire-like |
| COMBINED_DEGRADATION | Simultaneous thermal + vibration degradation |

Degradation/drift rates (e.g. "2.2°C/min" for thermal degradation) are chosen so a
live demo shows a clearly visible trend within a few minutes of wall-clock time —
they compress what would be a much longer real degradation timeline and are **not**
a calibration against real engine wear rates.

## 5. Sensor Fault Isolation Logic (`sensor_fault_isolation/`)

Rolling-window comparison of a recent mean vs. an older baseline mean, per signal.
If CHT residual shifts significantly while EGT/vibration/fuel-flow residuals do not
→ `POSSIBLE_SENSOR_FAULT`. If CHT shifts together with one or more of those →
`POSSIBLE_ENGINE_FAULT`. Below `MIN_HISTORY_SAMPLES` (20), the result is always
`INSUFFICIENT_EVIDENCE`. Every result carries a `confidence_pct` and a plain-English
`explanation` citing the actual numbers — never a bare label.

## 6. AI Health Twin (`health/anomaly_detector.py`, `health/fault_classifier.py`, `health/health_index.py`)

- **Anomaly score:** a real `sklearn.ensemble.IsolationForest`, trained once at
  process startup on ~900 samples of simulated NORMAL_CRUISE residuals/vibration
  (i.e. "what healthy looks like"). This is genuine unsupervised anomaly detection —
  but trained on synthetic data, which is why its scores are only internally
  meaningful within this prototype.
- **Fault classification:** deliberately rule-based, not a second black-box model —
  DRDO's PS explicitly asks for explainability, and clean physics residuals make
  transparent rules both accurate enough for a prototype and much easier to justify
  to a judge than an opaque classifier.
- **Health index / status / confidence:** combines the anomaly score and any
  classified fault into a 0-100 index and NORMAL/WARNING/CRITICAL band; confidence
  is reduced both when there isn't much history yet AND when the current reading is
  far outside the training distribution (a genuinely novel reading should be
  trusted less, not more).

## 7. Degradation & RUL (`rul/degradation.py`, `rul/estimator.py`, `rul/uncertainty.py`)

`DegradationTracker` is a **leaky integrator**: three components (thermal,
vibration, residual) accumulate when their respective stress inputs are elevated
and decay slowly back toward zero when the engine returns to normal — so
degradation is a real computed trajectory, not a random number.

`RULEstimator` fits a line through (operating_hours, degradation_index) history and
projects forward to `degradation_index = 100`. When the fitted rate is ~0 (no
meaningful trend yet), it reports a stated placeholder ceiling
(`NO_DEGRADATION_CEILING_HOURS = 500`) rather than a fabricated precise number —
this is explicit in `RULEstimate.basis` every time it happens.

## 8. Mission Twin (`mission/mission_model.py`, `mission/simulator.py`, `mission/readiness.py`)

Reuses the *same* `physics/engine_model.py` used for live telemetry, applied
deterministically (no sensor noise — this is a forward projection). A mission is
modeled as two phases so a genuine "critical phase" can emerge from the model:

- **Climb phase:** first ~10% of mission duration (capped at 0.5h), flown at
  `max_altitude_ft` and slightly boosted throttle.
- **Cruise phase:** remainder, at `cruise_altitude_ft` and the requested average
  throttle.

`mission/readiness.py` fits the same kind of degradation-rate-based RUL projection
used live, over the mission trajectory, and combines projected end-of-mission
health, minimum health point, and whether projected RUL is shorter than the mission
duration into a GREEN/YELLOW/RED decision with an explicit reason, critical phase,
and recommendation — never a bare status.

## 9. Natural-Language Mission Parser (`mission/nl_parser.py`)

Deterministic, offline, regex/keyword-based extraction of duration, altitude
category, temperature category, and mission type. **Never generates an engineering
prediction itself** — it only produces a `MissionInput`, which is then run through
the same Mission Twin as manually-entered parameters. An LLM-backed path is a
documented extension point (`_parse_with_llm`, not implemented) for when API
credentials are available; the app is fully functional offline without it.

## 10. Testing Strategy

41 pytest tests span every module above: schema validation (including deliberately
invalid/impossible values), all 8 simulator scenarios (including an explicit check
that SENSOR_DRIFT moves only the reported CHT value and not EGT/fuel flow), the
physics model's monotonicity properties, residual correctness, sensor fault
isolation's three-way classification, the anomaly detector's relative ordering
(not an arbitrary absolute threshold — IsolationForest's decision_function has a
data-dependent scale), degradation accumulation and decay, RUL's ceiling-vs-trend
behavior, mission simulation/readiness, and full API integration tests via
FastAPI's `TestClient`.
