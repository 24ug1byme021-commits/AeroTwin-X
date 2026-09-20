import { useCallback, useEffect, useState } from "react";
import type { ReactNode } from "react";
import { useTelemetryStream } from "./hooks/useTelemetryStream";
import { api } from "./services/api";
import type { ScenarioName, RiskLevel } from "./types/api";
import { HeaderBar } from "./components/HeaderBar";
import { DashboardPage } from "./pages/DashboardPage";
import { MissionOverviewPage } from "./pages/MissionOverviewPage";
import { LayoutDashboard, Radar } from "lucide-react";

type Tab = "overview" | "dashboard";

function App() {
  // ONE telemetry stream + one piece of sim state, shared by both tabs, so
  // switching tabs never tears down the WebSocket or loses live data.
  const { latest, history, connectionState, clear } = useTelemetryStream(300);
  const [running, setRunning] = useState(false);
  const [activeScenario, setActiveScenario] = useState<string | null>(null);
  const [missionRisk, setMissionRisk] = useState<RiskLevel | null>(null);
  const [detectorMode, setDetectorMode] = useState<"statistical" | "ml" | "hybrid">("hybrid");
  const [tab, setTab] = useState<Tab>("overview");

  const refreshStatus = useCallback(async () => {
    try {
      const status = await api.systemStatus();
      setRunning(status.simulation_running);
      setActiveScenario(status.active_scenario);
      if (status.detector_mode) setDetectorMode(status.detector_mode);
    } catch {
      // HeaderBar's link indicator already communicates an unreachable backend.
    }
  }, []);

  useEffect(() => {
    refreshStatus();
    const interval = setInterval(refreshStatus, 3000);
    return () => clearInterval(interval);
  }, [refreshStatus]);

  const handleStart = useCallback(async () => {
    clear();
    await api.startSimulation();
    await refreshStatus();
  }, [clear, refreshStatus]);

  const handleStop = useCallback(async () => {
    await api.stopSimulation();
    clear();
    await refreshStatus();
  }, [clear, refreshStatus]);

  const handleReset = useCallback(async () => {
    await api.resetSimulation();
    clear();
    setMissionRisk(null);
    await refreshStatus();
  }, [clear, refreshStatus]);

  const handleScenarioChange = useCallback(
    async (scenario: ScenarioName) => {
      await api.setScenario(scenario);
      await refreshStatus();
    },
    [refreshStatus],
  );

  const handleSetDetectorMode = useCallback(
    async (mode: "statistical" | "ml" | "hybrid") => {
      setDetectorMode(mode); // optimistic
      await api.setDetectorMode(mode);
      await refreshStatus();
    },
    [refreshStatus],
  );

  const liveLatest = running ? latest : null;
  const liveHistory = running ? history : [];

  return (
    <div className="min-h-screen">
      <HeaderBar connectionState={connectionState} simulationRunning={running} activeScenario={activeScenario} />

      <div className="sticky top-0 z-20 border-b border-[var(--color-panel-border)] bg-[var(--color-bg)]/85 backdrop-blur">
        <div className="mx-auto flex max-w-[1440px] items-center gap-1 px-6">
          <TabButton active={tab === "overview"} onClick={() => setTab("overview")} icon={<Radar size={15} />} label="Mission Overview" />
          <TabButton active={tab === "dashboard"} onClick={() => setTab("dashboard")} icon={<LayoutDashboard size={15} />} label="Engineering Dashboard" />
        </div>
      </div>

      {tab === "overview" ? (
        <MissionOverviewPage
          running={running}
          activeScenario={activeScenario}
          latest={liveLatest}
          history={liveHistory}
          missionRisk={missionRisk}
          onStart={handleStart}
          onStop={handleStop}
          onReset={handleReset}
          onScenarioChange={handleScenarioChange}
          onGoToDashboard={() => setTab("dashboard")}
        />
      ) : (
        <DashboardPage
          running={running}
          activeScenario={activeScenario}
          latest={liveLatest}
          history={liveHistory}
          missionRisk={missionRisk}
          setMissionRisk={setMissionRisk}
          detectorMode={detectorMode}
          onSetDetectorMode={handleSetDetectorMode}
          onStart={handleStart}
          onStop={handleStop}
          onReset={handleReset}
          onScenarioChange={handleScenarioChange}
        />
      )}
    </div>
  );
}

function TabButton({ active, onClick, icon, label }: { active: boolean; onClick: () => void; icon: ReactNode; label: string }) {
  return (
    <button
      onClick={onClick}
      className="relative flex items-center gap-2 px-4 py-3 text-sm font-semibold transition-colors"
      style={{ color: active ? "var(--color-accent)" : "var(--color-text-muted)" }}
    >
      {icon}
      {label}
      {active && <span className="absolute inset-x-2 bottom-0 h-0.5 rounded-full bg-[var(--color-accent)]" style={{ boxShadow: "0 0 10px var(--color-accent)" }} />}
    </button>
  );
}

export default App;
