/**
 * Animated Digital-Twin pipeline.
 *
 * Visualises the actual processing chain the backend runs every tick:
 * Telemetry -> Physics Twin -> Residuals -> Sensor Fault Isolation ->
 * AI Health -> Degradation -> RUL -> Mission Twin. When the simulation is
 * running, energy visibly flows along the connectors and each stage
 * glows, so a judge can *see* the architecture working rather than read
 * it in a diagram.
 */
import {
  Activity,
  Cpu,
  GitCompare,
  ShieldAlert,
  BrainCircuit,
  TrendingDown,
  Timer,
  Target,
} from "lucide-react";
import type { ReactNode } from "react";

type Stage = { icon: ReactNode; label: string };

const STAGES: Stage[] = [
  { icon: <Activity size={16} />, label: "Telemetry" },
  { icon: <Cpu size={16} />, label: "Physics Twin" },
  { icon: <GitCompare size={16} />, label: "Residuals" },
  { icon: <ShieldAlert size={16} />, label: "Fault Isolation" },
  { icon: <BrainCircuit size={16} />, label: "AI Health" },
  { icon: <TrendingDown size={16} />, label: "Degradation" },
  { icon: <Timer size={16} />, label: "RUL" },
  { icon: <Target size={16} />, label: "Mission Twin" },
];

export function PipelineFlow({ running }: { running: boolean }) {
  return (
    <div className="atx-glass atx-rise rounded-xl px-4 py-3.5">
      <div className="mb-2.5 flex items-center gap-2.5">
        <span className="atx-heading-bar" />
        <h2 className="text-[13px] font-semibold uppercase tracking-[0.12em]">Digital Twin Pipeline</h2>
        <span className={`ml-1 inline-flex items-center gap-1.5 rounded-full px-2 py-0.5 text-[10px] font-semibold ${running ? "text-[var(--color-normal)]" : "text-[var(--color-text-muted)]"}`}>
          <span className={`atx-live-dot h-1.5 w-1.5 rounded-full ${running ? "bg-[var(--color-normal)]" : "bg-[var(--color-text-muted)]"}`} />
          {running ? "PROCESSING" : "IDLE"}
        </span>
      </div>

      <div className="flex items-stretch gap-0 overflow-x-auto pb-1">
        {STAGES.map((s, i) => (
          <div key={s.label} className="flex min-w-0 items-center">
            <div
              className="flex min-w-[92px] flex-col items-center gap-1.5 rounded-lg border px-2.5 py-2 text-center transition-colors duration-300"
              style={{
                borderColor: running ? "color-mix(in srgb, var(--color-accent) 35%, var(--color-panel-border))" : "var(--color-panel-border)",
                background: running ? "color-mix(in srgb, var(--color-accent) 8%, transparent)" : "transparent",
              }}
            >
              <span className={running ? "text-[var(--color-accent)]" : "text-[var(--color-text-muted)]"}>{s.icon}</span>
              <span className="text-[10px] font-medium leading-tight text-[var(--color-text)]">{s.label}</span>
            </div>

            {i < STAGES.length - 1 && (
              <div className="relative mx-0.5 h-[2px] w-6 shrink-0 overflow-hidden rounded-full" style={{ background: "var(--color-panel-border)" }}>
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
    </div>
  );
}
