import type { HealthIndexResult, RULEstimate, RiskLevel, HealthStatus, TelemetryFrame, ResidualFrame } from "../types/api";
import { StatusBadge } from "./StatusBadge";
import { EngineSchematic } from "./EngineSchematic";
import { HeartPulse } from "lucide-react";

function glowClass(status: HealthStatus | null, running: boolean): string {
  if (!running) return "";
  if (status === "CRITICAL") return "atx-glow-critical";
  if (status === "WARNING") return "atx-glow-warning";
  return "atx-glow-normal";
}

function HealthRing({ value, status }: { value: number; status: HealthStatus | null }) {
  const size = 118;
  const r = 48;
  const c = 2 * Math.PI * r;
  const frac = Math.max(0, Math.min(100, value)) / 100;
  const color = status === "CRITICAL" ? "var(--color-critical)" : status === "WARNING" ? "var(--color-warning)" : "var(--color-normal)";
  return (
    <svg width={size} height={size} viewBox={`0 0 ${size} ${size}`}>
      <circle cx={size / 2} cy={size / 2} r={r} fill="none" stroke="var(--color-panel-border)" strokeWidth={9} />
      <circle
        cx={size / 2}
        cy={size / 2}
        r={r}
        fill="none"
        stroke={color}
        strokeWidth={9}
        strokeLinecap="round"
        strokeDasharray={c}
        strokeDashoffset={c * (1 - frac)}
        transform={`rotate(-90 ${size / 2} ${size / 2})`}
        style={{ transition: "stroke-dashoffset 0.8s cubic-bezier(0.22,1,0.36,1), stroke 0.4s", filter: `drop-shadow(0 0 6px ${color})` }}
      />
      <text x={size / 2} y={size / 2 - 2} textAnchor="middle" style={{ fontSize: 26, fontWeight: 800 }} className="fill-[var(--color-text)]">
        {value.toFixed(0)}
      </text>
      <text x={size / 2} y={size / 2 + 16} textAnchor="middle" style={{ fontSize: 9, letterSpacing: "0.1em" }} className="fill-[var(--color-text-muted)]">
        HEALTH
      </text>
    </svg>
  );
}

export function EngineStatusPanel({
  health,
  rul,
  telemetry,
  residuals,
  operatingMode,
  missionRisk,
  running,
}: {
  health: HealthIndexResult | null;
  rul: RULEstimate | null;
  telemetry: TelemetryFrame | null;
  residuals: ResidualFrame | null;
  operatingMode: string | null;
  missionRisk: RiskLevel | null;
  running: boolean;
}) {
  return (
    <section className={`atx-glass atx-rise rounded-xl p-4 transition-all duration-500 ${glowClass(health?.status ?? null, running)}`}>
      <div className="mb-3 flex items-center gap-2.5">
        <span className="atx-heading-bar" />
        <h2 className="flex items-center gap-2 text-[13px] font-semibold uppercase tracking-[0.12em]">
          <HeartPulse size={14} className="text-[var(--color-accent)]" /> Engine Health &amp; Digital Twin
        </h2>
      </div>

      <div className="grid grid-cols-1 gap-4 lg:grid-cols-[1.35fr_1fr]">
        {/* Left: live engine schematic */}
        <EngineSchematic telemetry={telemetry} residuals={residuals} status={health?.status ?? null} running={running} />

        {/* Right: health ring + key indices */}
        <div className="flex flex-col gap-3">
          <div className="flex items-center gap-4 rounded-lg border border-[var(--color-panel-border)] bg-white/[0.02] p-3">
            <HealthRing value={running ? health?.health_index ?? 0 : 0} status={running ? health?.status ?? null : null} />
            <div className="flex flex-col gap-1.5">
              <StatusBadge label={running ? health?.status ?? "NORMAL" : "STANDBY"} />
              <div className="text-xs text-[var(--color-text-muted)]">
                Trend: <span className="text-[var(--color-text)]">{running ? health?.degradation_trend ?? "—" : "—"}</span>
              </div>
              <div className="text-xs text-[var(--color-text-muted)]">
                Mode: <span className="text-[var(--color-text)]">{operatingMode?.replace(/_/g, " ") ?? "—"}</span>
              </div>
            </div>
          </div>

          <div className="grid grid-cols-2 gap-2">
            <Stat label="RUL" value={running && rul ? `${rul.rul_hours.toFixed(0)}` : "—"} sub={running && rul ? `± ${rul.uncertainty_hours.toFixed(0)} hrs` : "hrs"} />
            <Stat label="RUL Confidence" value={running && rul ? `${rul.confidence_pct.toFixed(0)}%` : "—"} sub="model certainty" />
          </div>

          {missionRisk && (
            <div className="flex items-center justify-between rounded-lg border border-[var(--color-panel-border)] bg-white/[0.02] px-3 py-2 text-xs">
              <span className="text-[var(--color-text-muted)]">Last mission assessment</span>
              <StatusBadge label={missionRisk} />
            </div>
          )}

          {running && health?.suspected_fault && (
            <div className="rounded-lg border border-[var(--color-warning)]/30 bg-[var(--color-warning)]/10 px-3 py-2 text-xs text-[var(--color-warning)]">
              ⚠ Suspected: {health.suspected_fault.replace(/_/g, " ")} · confidence {health.confidence_pct.toFixed(0)}%
            </div>
          )}
        </div>
      </div>
    </section>
  );
}

function Stat({ label, value, sub }: { label: string; value: string; sub: string }) {
  return (
    <div className="rounded-lg border border-[var(--color-panel-border)] bg-white/[0.02] px-3 py-2.5">
      <div className="text-[10px] uppercase tracking-[0.1em] text-[var(--color-text-muted)]">{label}</div>
      <div className="mt-0.5 text-2xl font-bold tabular-nums text-[var(--color-text)]">{value}</div>
      <div className="text-[10px] text-[var(--color-text-muted)]">{sub}</div>
    </div>
  );
}
