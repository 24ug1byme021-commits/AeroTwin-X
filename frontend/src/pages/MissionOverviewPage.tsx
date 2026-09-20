import type { ReactNode } from "react";
import type { ScenarioName, RiskLevel, TelemetryStreamMessage } from "../types/api";
import { DroneTwin } from "../components/DroneTwin";
import { ScenarioControls } from "../components/ScenarioControls";
import {
  Plane,
  Cable,
  Cpu,
  Building2,
  BrainCircuit,
  UserCog,
  ArrowRight,
  Activity,
  Timer,
  ShieldCheck,
  Gauge,
} from "lucide-react";

type Verdict = { label: string; color: string; sub: string };

function readiness(latest: TelemetryStreamMessage | null, missionRisk: RiskLevel | null, running: boolean): Verdict {
  if (!running || !latest?.health) return { label: "STANDBY", color: "var(--color-text-muted)", sub: "Start the simulation to assess mission readiness." };
  const status = latest.health.status;
  const rul = latest.rul?.rul_hours ?? 999;
  if (status === "CRITICAL" || rul < 5 || missionRisk === "RED")
    return { label: "NO-GO", color: "var(--color-critical)", sub: "Engine condition or remaining life below mission threshold — maintenance required before dispatch." };
  if (status === "WARNING" || rul < 20 || missionRisk === "YELLOW")
    return { label: "CAUTION", color: "var(--color-warning)", sub: "Degradation detected — mission feasible with monitoring; shorten profile or inspect at next window." };
  return { label: "GO", color: "var(--color-normal)", sub: "All health indices nominal — engine cleared for the planned mission profile." };
}

export function MissionOverviewPage({
  running,
  activeScenario,
  latest,
  missionRisk,
  onStart,
  onStop,
  onReset,
  onScenarioChange,
  onGoToDashboard,
}: {
  running: boolean;
  activeScenario: string | null;
  latest: TelemetryStreamMessage | null;
  history: TelemetryStreamMessage[];
  missionRisk: RiskLevel | null;
  onStart: () => void;
  onStop: () => void;
  onReset: () => void;
  onScenarioChange: (scenario: ScenarioName) => void;
  onGoToDashboard: () => void;
}) {
  const verdict = readiness(latest, missionRisk, running);
  const health = latest?.health;

  return (
    <main className="mx-auto flex max-w-[1440px] flex-col gap-4 p-6">
      {/* Readiness banner */}
      <section
        className="atx-glass atx-rise flex flex-wrap items-center justify-between gap-4 rounded-xl p-5"
        style={{ boxShadow: running ? `0 0 0 1px ${verdict.color}55, 0 0 40px -10px ${verdict.color}` : undefined }}
      >
        <div className="flex items-center gap-5">
          <div
            className="flex h-20 w-20 flex-col items-center justify-center rounded-2xl border-2 text-center"
            style={{ borderColor: verdict.color, color: verdict.color, boxShadow: `0 0 26px -6px ${verdict.color}` }}
          >
            <ShieldCheck size={22} />
            <span className="mt-0.5 text-lg font-extrabold leading-none">{verdict.label}</span>
          </div>
          <div>
            <div className="text-[11px] uppercase tracking-[0.18em] text-[var(--color-text-muted)]">Mission Readiness Assessment</div>
            <div className="mt-1 max-w-xl text-sm text-[var(--color-text)]">{verdict.sub}</div>
            <div className="mt-1 text-xs text-[var(--color-text-muted)]">
              Operating profile: <span className="text-[var(--color-text)]">{activeScenario?.replace(/_/g, " ") ?? "—"}</span>
            </div>
          </div>
        </div>

        <button
          onClick={onGoToDashboard}
          className="inline-flex items-center gap-2 rounded-lg border border-[var(--color-accent)]/40 bg-[var(--color-accent)]/10 px-4 py-2.5 text-sm font-semibold text-[var(--color-accent)] transition-colors hover:bg-[var(--color-accent)]/20"
        >
          Open Engineering Dashboard <ArrowRight size={15} />
        </button>
      </section>

      {/* Drone twin + key indices */}
      <div className="grid grid-cols-1 gap-4 xl:grid-cols-[1.6fr_1fr]">
        <div className="atx-glass atx-rise rounded-xl p-4">
          <div className="mb-3 flex items-center gap-2.5">
            <span className="atx-heading-bar" />
            <h2 className="flex items-center gap-2 text-[13px] font-semibold uppercase tracking-[0.12em]">
              <Plane size={14} className="text-[var(--color-accent)]" /> Live Airframe Twin
            </h2>
          </div>
          <DroneTwin telemetry={latest?.telemetry ?? null} health={health ?? null} running={running} />
        </div>

        <div className="flex flex-col gap-4">
          <div className="atx-glass atx-rise grid grid-cols-2 gap-3 rounded-xl p-4">
            <Stat icon={<Activity size={14} />} label="Health Index" value={running && health ? `${health.health_index.toFixed(0)}` : "—"} suffix="/100" color={verdict.color} />
            <Stat icon={<Timer size={14} />} label="Est. RUL" value={running && latest?.rul ? `${latest.rul.rul_hours.toFixed(0)}` : "—"} suffix="hrs" />
            <Stat icon={<Gauge size={14} />} label="RPM" value={running && latest?.telemetry ? `${latest.telemetry.rpm.toFixed(0)}` : "—"} suffix="rpm" />
            <Stat icon={<BrainCircuit size={14} />} label="Anomaly" value={running && health ? `${Math.min(100, Math.max(0, health.anomaly_score * 100)).toFixed(0)}` : "—"} suffix="%" />
          </div>

          {/* Quick scenario control so the demo can be driven from here too */}
          <ScenarioControls
            running={running}
            activeScenario={activeScenario}
            onStart={onStart}
            onStop={onStop}
            onReset={onReset}
            onScenarioChange={onScenarioChange}
          />
        </div>
      </div>

      {/* Deployment data-flow chain */}
      <DeploymentFlow running={running} />

      <footer className="pb-6 pt-2 text-center text-[11px] text-[var(--color-text-muted)]">
        AeroTwin-X · Mission Overview · all telemetry is simulated/synthetic · designed for future GCS / edge deployment · SIH26054
      </footer>
    </main>
  );
}

function Stat({ icon, label, value, suffix, color }: { icon: ReactNode; label: string; value: string; suffix: string; color?: string }) {
  return (
    <div className="rounded-lg border border-[var(--color-panel-border)] bg-white/[0.02] px-3 py-2.5">
      <div className="flex items-center gap-1.5 text-[10px] uppercase tracking-[0.1em] text-[var(--color-text-muted)]">
        <span className="text-[var(--color-accent)]">{icon}</span>
        {label}
      </div>
      <div className="mt-1 flex items-baseline gap-1">
        <span className="text-2xl font-bold tabular-nums" style={{ color: color ?? "var(--color-text)" }}>
          {value}
        </span>
        <span className="text-[11px] text-[var(--color-text-muted)]">{suffix}</span>
      </div>
    </div>
  );
}

const FLOW_STAGES: { icon: ReactNode; label: string; sub: string }[] = [
  { icon: <Plane size={18} />, label: "UAV Engine", sub: "ECU / sensors" },
  { icon: <Cable size={18} />, label: "CAN / SocketCAN", sub: "telemetry bus" },
  { icon: <Cpu size={18} />, label: "Edge Gateway", sub: "onboard compute" },
  { icon: <Building2 size={18} />, label: "Ground Station", sub: "GCS link" },
  { icon: <BrainCircuit size={18} />, label: "AeroTwin-X", sub: "digital twin core" },
  { icon: <UserCog size={18} />, label: "Operator", sub: "decision support" },
];

function DeploymentFlow({ running }: { running: boolean }) {
  return (
    <section className="atx-glass atx-rise rounded-xl p-4">
      <div className="mb-1 flex items-center gap-2.5">
        <span className="atx-heading-bar" />
        <h2 className="text-[13px] font-semibold uppercase tracking-[0.12em]">Deployment Architecture</h2>
        <span className={`ml-1 text-[10px] font-semibold ${running ? "text-[var(--color-normal)]" : "text-[var(--color-text-muted)]"}`}>
          {running ? "· telemetry flowing" : "· idle"}
        </span>
      </div>
      <p className="mb-3 pl-4 text-xs text-[var(--color-text-muted)]">
        How the prototype maps onto a real MALE-UAV health-monitoring chain. The current build simulates the engine source; every downstream
        stage is real and unchanged when a live CAN feed replaces the simulator.
      </p>

      <div className="flex items-stretch gap-0 overflow-x-auto pb-1">
        {FLOW_STAGES.map((s, i) => (
          <div key={s.label} className="flex min-w-0 items-center">
            <div
              className="flex min-w-[118px] flex-col items-center gap-1 rounded-xl border px-3 py-3 text-center transition-colors duration-300"
              style={{
                borderColor: running ? "color-mix(in srgb, var(--color-accent) 35%, var(--color-panel-border))" : "var(--color-panel-border)",
                background: running ? "color-mix(in srgb, var(--color-accent) 8%, transparent)" : "transparent",
              }}
            >
              <span className={running ? "text-[var(--color-accent)]" : "text-[var(--color-text-muted)]"}>{s.icon}</span>
              <span className="text-[11px] font-semibold leading-tight text-[var(--color-text)]">{s.label}</span>
              <span className="text-[9px] text-[var(--color-text-muted)]">{s.sub}</span>
            </div>
            {i < FLOW_STAGES.length - 1 && (
              <div className="relative mx-1 h-[2px] w-8 shrink-0 overflow-hidden rounded-full" style={{ background: "var(--color-panel-border)" }}>
                <div
                  className="absolute inset-y-0 w-full"
                  style={{
                    background: "linear-gradient(90deg, transparent, var(--color-accent), transparent)",
                    backgroundSize: "200% 100%",
                    animation: running ? "atx-title-slide 1.1s linear infinite" : "none",
                    opacity: running ? 1 : 0,
                  }}
                />
              </div>
            )}
          </div>
        ))}
      </div>
    </section>
  );
}
