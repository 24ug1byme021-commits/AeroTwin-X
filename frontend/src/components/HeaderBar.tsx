import type { ConnectionState } from "../hooks/useTelemetryStream";
import { Plane, Radio } from "lucide-react";

export function HeaderBar({
  connectionState,
  simulationRunning,
  activeScenario,
}: {
  connectionState: ConnectionState;
  simulationRunning: boolean;
  activeScenario: string | null;
}) {
  const connColor =
    connectionState === "open" ? "var(--color-normal)" : connectionState === "connecting" ? "var(--color-warning)" : "var(--color-critical)";
  const connLabel = connectionState === "open" ? "Live Link" : connectionState === "connecting" ? "Linking…" : "Link Lost";

  return (
    <header className="relative overflow-hidden border-b border-[var(--color-panel-border)]">
      {/* animated backdrop glow */}
      <div className="pointer-events-none absolute inset-0 opacity-70">
        <div className="atx-sweep absolute inset-y-0 w-1/2" style={{ background: "linear-gradient(90deg, transparent, rgba(52,211,255,0.07), transparent)" }} />
      </div>

      <div className="relative mx-auto flex max-w-[1440px] flex-wrap items-center justify-between gap-4 px-6 py-4">
        <div className="flex items-center gap-3.5">
          <div className="flex h-11 w-11 items-center justify-center rounded-xl border border-[var(--color-accent)]/40 bg-[var(--color-accent)]/10" style={{ boxShadow: "0 0 22px -6px var(--color-accent)" }}>
            <Plane size={22} className="text-[var(--color-accent)]" />
          </div>
          <div>
            <h1 className="text-[22px] font-extrabold leading-none tracking-tight">
              <span className="atx-title-gradient">AeroTwin-X</span>
            </h1>
            <p className="mt-1 text-[11px] uppercase tracking-[0.16em] text-[var(--color-text-muted)]">
              AI Digital Twin · MALE-UAV Aero-Piston Engine · SIH26054
            </p>
          </div>
        </div>

        <div className="flex items-center gap-2.5">
          <div className="flex items-center gap-2 rounded-full border border-[var(--color-panel-border)] bg-white/[0.02] px-3 py-1.5 text-xs">
            <span className="atx-live-dot h-2 w-2 rounded-full" style={{ color: connColor, background: connColor }} />
            <Radio size={12} className="text-[var(--color-text-muted)]" />
            <span className="text-[var(--color-text-muted)]">{connLabel}</span>
          </div>

          <div
            className="rounded-full border px-3.5 py-1.5 text-xs font-semibold tracking-wide"
            style={
              simulationRunning
                ? { borderColor: "color-mix(in srgb, var(--color-normal) 45%, transparent)", color: "var(--color-normal)", background: "color-mix(in srgb, var(--color-normal) 12%, transparent)" }
                : { borderColor: "var(--color-panel-border)", color: "var(--color-text-muted)" }
            }
          >
            {simulationRunning ? "● LIVE SIMULATION" : "○ STANDBY"}
            {activeScenario ? ` · ${activeScenario.replace(/_/g, " ")}` : ""}
          </div>
        </div>
      </div>
    </header>
  );
}
