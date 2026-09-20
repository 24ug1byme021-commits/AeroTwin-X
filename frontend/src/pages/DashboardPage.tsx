import type { ScenarioName, RiskLevel, TelemetryStreamMessage } from "../types/api";
import { PipelineFlow } from "../components/PipelineFlow";
import { ScenarioControls } from "../components/ScenarioControls";
import { EngineStatusPanel } from "../components/EngineStatusPanel";
import { LiveTelemetryPanel } from "../components/LiveTelemetryPanel";
import { PhysicsTwinPanel } from "../components/PhysicsTwinPanel";
import { AIHealthPanel } from "../components/AIHealthPanel";
import { MissionTwinPanel } from "../components/MissionTwinPanel";
import { AlertsPanel } from "../components/AlertsPanel";
import { PostFlightLogPanel } from "../components/PostFlightLogPanel";

export function DashboardPage({
  running,
  activeScenario,
  latest,
  history,
  missionRisk,
  setMissionRisk,
  detectorMode,
  onSetDetectorMode,
  onStart,
  onStop,
  onReset,
  onScenarioChange,
}: {
  running: boolean;
  activeScenario: string | null;
  latest: TelemetryStreamMessage | null;
  history: TelemetryStreamMessage[];
  missionRisk: RiskLevel | null;
  setMissionRisk: (r: RiskLevel) => void;
  detectorMode: "statistical" | "ml" | "hybrid";
  onSetDetectorMode: (m: "statistical" | "ml" | "hybrid") => void;
  onStart: () => void;
  onStop: () => void;
  onReset: () => void;
  onScenarioChange: (scenario: ScenarioName) => void;
}) {
  return (
    <main className="mx-auto flex max-w-[1440px] flex-col gap-4 p-6">
      <PipelineFlow running={running} />

      <ScenarioControls
        running={running}
        activeScenario={activeScenario}
        onStart={onStart}
        onStop={onStop}
        onReset={onReset}
        onScenarioChange={onScenarioChange}
      />

      <EngineStatusPanel
        health={latest?.health ?? null}
        rul={latest?.rul ?? null}
        telemetry={latest?.telemetry ?? null}
        residuals={latest?.residuals ?? null}
        operatingMode={activeScenario}
        missionRisk={missionRisk}
        running={running}
      />

      <div className="grid grid-cols-1 gap-4 xl:grid-cols-3">
        <div className="xl:col-span-2">
          <LiveTelemetryPanel telemetry={latest?.telemetry ?? null} />
        </div>
        <AlertsPanel history={history} />
      </div>

      <PhysicsTwinPanel history={history} />
      <AIHealthPanel history={history} detectorMode={detectorMode} onSetDetectorMode={onSetDetectorMode} />
      <MissionTwinPanel onResult={(r) => setMissionRisk(r.risk_level)} />
      <PostFlightLogPanel running={running} />

      <footer className="pb-6 pt-2 text-center text-[11px] text-[var(--color-text-muted)]">
        AeroTwin-X prototype · all telemetry is simulated/synthetic · no real DRDO/UAV data is used or claimed · SIH26054
      </footer>
    </main>
  );
}
