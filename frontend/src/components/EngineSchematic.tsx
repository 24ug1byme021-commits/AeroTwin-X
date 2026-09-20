/**
 * Live engine schematic.
 *
 * A stylised cross-section of an aero-piston engine with a spinning
 * crank/prop, moving pistons and sensor pickup nodes (CHT, EGT, oil,
 * fuel, vibration, RPM, battery) that light up and change colour based on
 * the current telemetry frame and health status. This is the "digital
 * twin" made visual — the same numbers on the gauges, mapped onto the
 * physical layout of the engine the operator is actually monitoring.
 *
 * All geometry is hand-drawn SVG; nothing here is a stock image, so it
 * themes perfectly with the rest of the console and carries no asset
 * baggage.
 */
import type { TelemetryFrame, HealthStatus, ResidualFrame } from "../types/api";

type NodeState = "idle" | "normal" | "warning" | "critical";

const NODE_COLOR: Record<NodeState, string> = {
  idle: "var(--color-text-muted)",
  normal: "var(--color-normal)",
  warning: "var(--color-warning)",
  critical: "var(--color-critical)",
};

function band(value: number, warn: number, danger: number, running: boolean): NodeState {
  if (!running) return "idle";
  if (value >= danger) return "critical";
  if (value >= warn) return "warning";
  return "normal";
}

// Residual-based banding: the twin flags a subsystem when its ACTUAL reading
// diverges from the physics-model EXPECTED value for the current operating
// point — so a legitimately hot cylinder at high altitude (large absolute
// value, ~zero residual) stays green, while a degrading one (rising residual)
// is caught even before it hits an absolute redline.
function bandResidual(residual: number | undefined, warn: number, danger: number, running: boolean): NodeState {
  if (!running || residual == null) return "idle";
  const r = Math.abs(residual);
  if (r >= danger) return "critical";
  if (r >= warn) return "warning";
  return "normal";
}

function SensorNode({
  x,
  y,
  label,
  reading,
  state,
}: {
  x: number;
  y: number;
  label: string;
  reading: string;
  state: NodeState;
}) {
  const color = NODE_COLOR[state];
  return (
    <g>
      {/* connector stub */}
      <circle cx={x} cy={y} r={13} fill="none" stroke={color} strokeWidth={1} opacity={0.35} />
      <circle
        cx={x}
        cy={y}
        r={6}
        fill={color}
        style={{
          filter: `drop-shadow(0 0 6px ${color})`,
          // @ts-expect-error CSS custom props for keyframe radii
          "--r0": "5px",
          "--r1": "7.5px",
          animation: state === "idle" ? "none" : "atx-node-pulse 1.8s ease-in-out infinite",
        }}
      />
      <text x={x} y={y - 18} textAnchor="middle" style={{ fontSize: 9, letterSpacing: "0.08em" }} className="fill-[var(--color-text-muted)]">
        {label}
      </text>
      <text x={x} y={y + 26} textAnchor="middle" style={{ fontSize: 10, fontWeight: 700 }} fill={color}>
        {reading}
      </text>
    </g>
  );
}

export function EngineSchematic({
  telemetry,
  residuals,
  status,
  running,
}: {
  telemetry: TelemetryFrame | null;
  residuals: ResidualFrame | null;
  status: HealthStatus | null;
  running: boolean;
}) {
  const t = telemetry;
  const res = residuals;
  const rpm = t?.rpm ?? 0;
  // Prop/crank spin speed scales with RPM (visual only).
  const spinClass = !running || rpm < 50 ? "" : rpm > 3600 ? "atx-spin-med" : "atx-spin-slow";

  const nodes = [
    {
      x: 150,
      y: 70,
      label: "CHT",
      reading: t ? `${t.cht_c.toFixed(0)}°C` : "—",
      state: bandResidual(res?.cht_residual_c, 8, 20, running),
    },
    {
      x: 360,
      y: 70,
      label: "EGT",
      reading: t ? `${t.egt_c.toFixed(0)}°C` : "—",
      state: bandResidual(res?.egt_residual_c, 12, 22, running),
    },
    {
      x: 452,
      y: 150,
      label: "VIBRATION",
      reading: t ? `${t.vibration_mms.toFixed(1)}` : "—",
      state: band(t?.vibration_mms ?? 0, 5, 7, running),
    },
    {
      x: 452,
      y: 232,
      label: "FUEL",
      reading: t ? `${t.fuel_flow_lph.toFixed(1)}` : "—",
      state: bandResidual(res?.fuel_flow_residual_lph, 2, 4, running),
    },
    {
      x: 256,
      y: 300,
      label: "OIL P/T",
      reading: t ? `${t.oil_pressure_psi.toFixed(0)}psi` : "—",
      state: bandResidual(res?.oil_temperature_residual_c, 5, 10, running),
    },
    {
      x: 60,
      y: 232,
      label: "BATTERY",
      reading: t ? `${t.battery_voltage_v.toFixed(1)}V` : "—",
      state: running ? (t && t.battery_voltage_v < 26 ? "warning" : "normal") : "idle",
    },
    {
      x: 60,
      y: 150,
      label: "RPM",
      reading: t ? `${t.rpm.toFixed(0)}` : "—",
      state: running ? "normal" : "idle",
    },
  ] as const;

  const ringColor =
    !running ? "var(--color-panel-border)" : status === "CRITICAL" ? "var(--color-critical)" : status === "WARNING" ? "var(--color-warning)" : "var(--color-normal)";

  return (
    <div className="relative overflow-hidden rounded-lg border border-[var(--color-panel-border)] bg-[var(--color-bg-2)]/60">
      {/* scan sweep */}
      <div className="pointer-events-none absolute inset-0">
        <div
          className={running ? "atx-sweep h-full w-1/3" : "h-full w-1/3 opacity-0"}
          style={{ background: "linear-gradient(90deg, transparent, rgba(52,211,255,0.06), transparent)" }}
        />
      </div>

      <svg viewBox="0 0 512 360" className="w-full">
        <defs>
          <radialGradient id="crankGrad" cx="50%" cy="50%" r="50%">
            <stop offset="0%" stopColor="#20304e" />
            <stop offset="100%" stopColor="#0d1526" />
          </radialGradient>
          <linearGradient id="blockGrad" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor="#16233c" />
            <stop offset="100%" stopColor="#0e1729" />
          </linearGradient>
        </defs>

        {/* engine block */}
        <rect x="120" y="120" width="272" height="150" rx="16" fill="url(#blockGrad)" stroke={ringColor} strokeWidth="1.5" opacity="0.95" />

        {/* two cylinders with pistons */}
        {[176, 300].map((cx, i) => (
          <g key={i}>
            <rect x={cx - 26} y={60} width={52} height={78} rx={8} fill="#0e1729" stroke="var(--color-panel-border)" strokeWidth="1.4" />
            {/* cooling fins */}
            {[0, 1, 2, 3].map((f) => (
              <line key={f} x1={cx - 30} y1={72 + f * 14} x2={cx + 30} y2={72 + f * 14} stroke="var(--color-panel-border)" strokeWidth="1" opacity="0.6" />
            ))}
            {/* piston (bobs with a simple offset per cylinder) */}
            <rect
              x={cx - 18}
              y={running ? 92 + (i === 0 ? -8 : 8) : 96}
              width={36}
              height={20}
              rx={4}
              fill={running ? "var(--color-accent)" : "var(--color-panel-border)"}
              opacity={running ? 0.85 : 0.5}
              style={{ transition: "y 0.5s ease-in-out" }}
            />
          </g>
        ))}

        {/* crankshaft / prop hub */}
        <g transform="translate(256, 195)">
          <circle r="40" fill="url(#crankGrad)" stroke={ringColor} strokeWidth="1.5" />
          <g className={spinClass}>
            {[0, 60, 120, 180, 240, 300].map((a) => (
              <rect key={a} x={-2.5} y={-38} width={5} height={26} rx={2} transform={`rotate(${a})`} fill={running ? "var(--color-accent-2)" : "var(--color-panel-border)"} opacity={running ? 0.9 : 0.5} />
            ))}
            <circle r="9" fill={running ? "var(--color-accent)" : "var(--color-panel-border)"} />
          </g>
          <text y="62" textAnchor="middle" style={{ fontSize: 9, letterSpacing: "0.1em" }} className="fill-[var(--color-text-muted)]">
            {running ? `${rpm.toFixed(0)} RPM` : "IDLE"}
          </text>
        </g>

        {/* sensor nodes */}
        {nodes.map((n) => (
          <SensorNode key={n.label} x={n.x} y={n.y} label={n.label} reading={n.reading} state={n.state as NodeState} />
        ))}
      </svg>

      <div className="flex items-center justify-between border-t border-[var(--color-panel-border)] px-3 py-1.5 text-[10px] text-[var(--color-text-muted)]">
        <span>Live sensor map · synthetic telemetry</span>
        <span className="flex items-center gap-3">
          <LegendDot color="var(--color-normal)" label="Nominal" />
          <LegendDot color="var(--color-warning)" label="Watch" />
          <LegendDot color="var(--color-critical)" label="Alert" />
        </span>
      </div>
    </div>
  );
}

function LegendDot({ color, label }: { color: string; label: string }) {
  return (
    <span className="inline-flex items-center gap-1">
      <span className="h-2 w-2 rounded-full" style={{ background: color, boxShadow: `0 0 6px ${color}` }} />
      {label}
    </span>
  );
}
