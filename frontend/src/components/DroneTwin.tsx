/**
 * Animated MALE-UAV digital twin.
 *
 * A hand-drawn (no stock assets) side-profile of a Medium-Altitude
 * Long-Endurance UAV with a pusher propeller, ISR sensor turret and a
 * high-aspect-ratio wing. The airframe floats, the prop spins with RPM,
 * and the engine bay + health halo change colour with the live health
 * status — so the same numbers driving the engineering dashboard are
 * mapped onto the aircraft the operator is actually flying.
 */
import type { TelemetryFrame, HealthIndexResult, HealthStatus } from "../types/api";

function statusColor(status: HealthStatus | null, running: boolean): string {
  if (!running) return "var(--color-text-muted)";
  if (status === "CRITICAL") return "var(--color-critical)";
  if (status === "WARNING") return "var(--color-warning)";
  return "var(--color-normal)";
}

function Callout({
  x,
  y,
  anchorX,
  anchorY,
  label,
  value,
  color,
  align = "start",
}: {
  x: number;
  y: number;
  anchorX: number;
  anchorY: number;
  label: string;
  value: string;
  color: string;
  align?: "start" | "end";
}) {
  return (
    <g>
      <line x1={anchorX} y1={anchorY} x2={x} y2={y} stroke={color} strokeWidth={1} opacity={0.5} strokeDasharray="2 2" />
      <circle cx={anchorX} cy={anchorY} r={3} fill={color} style={{ filter: `drop-shadow(0 0 4px ${color})` }} />
      <text x={x} y={y - 4} textAnchor={align} style={{ fontSize: 9, letterSpacing: "0.08em" }} className="fill-[var(--color-text-muted)]">
        {label}
      </text>
      <text x={x} y={y + 11} textAnchor={align} style={{ fontSize: 14, fontWeight: 700 }} fill={color}>
        {value}
      </text>
    </g>
  );
}

export function DroneTwin({
  telemetry,
  health,
  running,
}: {
  telemetry: TelemetryFrame | null;
  health: HealthIndexResult | null;
  running: boolean;
}) {
  const t = telemetry;
  const color = statusColor(health?.status ?? null, running);
  const rpm = t?.rpm ?? 0;
  const spinClass = !running || rpm < 50 ? "" : rpm > 3800 ? "atx-spin-med" : "atx-spin-slow";

  return (
    <div className="relative overflow-hidden rounded-xl border border-[var(--color-panel-border)]" style={{ background: "linear-gradient(180deg,#08101f 0%, #0a1526 55%, #0c1a30 100%)" }}>
      {/* drifting sky bands */}
      <div className="pointer-events-none absolute inset-0 opacity-60">
        <div className="atx-sweep absolute top-10 h-16 w-1/3" style={{ background: "radial-gradient(ellipse at center, rgba(52,211,255,0.05), transparent 70%)" }} />
      </div>

      <svg viewBox="0 0 640 380" className="w-full">
        <defs>
          <linearGradient id="fuse" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor="#33465f" />
            <stop offset="55%" stopColor="#1a2740" />
            <stop offset="100%" stopColor="#0f1a2c" />
          </linearGradient>
          <linearGradient id="wing" x1="0" y1="0" x2="1" y2="0">
            <stop offset="0%" stopColor="#26364f" />
            <stop offset="100%" stopColor="#16233a" />
          </linearGradient>
          <radialGradient id="engineGlow" cx="50%" cy="50%" r="50%">
            <stop offset="0%" stopColor={color} stopOpacity="0.9" />
            <stop offset="100%" stopColor={color} stopOpacity="0" />
          </radialGradient>
          <filter id="softGlow" x="-50%" y="-50%" width="200%" height="200%">
            <feGaussianBlur stdDeviation="3" result="b" />
            <feMerge>
              <feMergeNode in="b" />
              <feMergeNode in="SourceGraphic" />
            </feMerge>
          </filter>
        </defs>

        {/* horizon + altitude ticks */}
        <line x1="0" y1="300" x2="640" y2="300" stroke="var(--color-panel-border)" strokeWidth="1" opacity="0.5" />
        {[40, 130, 220, 310, 400, 490, 580].map((x) => (
          <line key={x} x1={x} y1="300" x2={x} y2="306" stroke="var(--color-panel-border)" strokeWidth="1" opacity="0.5" />
        ))}

        {/* health halo */}
        <ellipse cx="320" cy="175" rx="150" ry="70" fill="none" stroke={color} strokeWidth="1" opacity={running ? 0.25 : 0.08} strokeDasharray="4 6" />

        {/* ==== aircraft (floats gently) ==== */}
        <g style={{ animation: running ? "atx-bob 4s ease-in-out infinite" : "none" }}>
          {/* far wing (behind fuselage) */}
          <path d="M300 168 L250 120 L268 120 L340 165 Z" fill="#121d31" opacity="0.7" />

          {/* pusher propeller at tail (left) */}
          <g transform="translate(150,175)">
            <ellipse cx="0" cy="0" rx="6" ry="34" fill={color} opacity={running ? 0.18 : 0.06} />
            <g className={spinClass}>
              <rect x="-3" y="-36" width="6" height="72" rx="3" fill={running ? color : "var(--color-panel-border)"} opacity={running ? 0.8 : 0.5} />
            </g>
          </g>

          {/* engine bay glow */}
          <circle cx="185" cy="175" r="26" fill="url(#engineGlow)" opacity={running ? 1 : 0.3} />

          {/* fuselage: tail(left) -> nose dome(right) */}
          <path
            d="M168 175
               C168 160, 190 156, 230 156
               L470 158
               C520 159, 560 165, 588 175
               C560 185, 520 191, 470 192
               L230 194
               C190 194, 168 190, 168 175 Z"
            fill="url(#fuse)"
            stroke={color}
            strokeWidth="1.2"
            opacity="0.98"
          />

          {/* nose SATCOM dome */}
          <circle cx="585" cy="175" r="17" fill="#26364f" stroke={color} strokeWidth="1.2" />

          {/* cockpit/avionics accents */}
          <circle cx="545" cy="172" r="3" fill={color} opacity="0.8" />
          <circle cx="520" cy="172" r="2.4" fill={color} opacity="0.6" />

          {/* main wing (high aspect ratio, foreground) */}
          <path d="M300 176 L430 205 L470 205 L360 176 Z" fill="url(#wing)" stroke={color} strokeWidth="0.8" opacity="0.95" />
          <path d="M330 176 L250 205 L288 205 L372 176 Z" fill="url(#wing)" stroke={color} strokeWidth="0.8" opacity="0.95" />

          {/* inverted-V tail */}
          <path d="M195 176 L168 150 L176 150 L215 174 Z" fill="#16233a" stroke={color} strokeWidth="0.7" opacity="0.9" />
          <path d="M195 176 L168 202 L176 202 L215 178 Z" fill="#16233a" stroke={color} strokeWidth="0.7" opacity="0.9" />

          {/* ISR sensor turret under nose */}
          <circle cx="560" cy="200" r="11" fill="#0f1a2c" stroke={color} strokeWidth="1.2" />
          <circle cx="560" cy="202" r="4.5" fill={color} opacity="0.85" style={{ filter: `drop-shadow(0 0 4px ${color})` }} />
        </g>

        {/* ==== telemetry callouts ==== */}
        <Callout x={70} y={90} anchorX={175} anchorY={168} label="RPM" value={t ? rpm.toFixed(0) : "—"} color={color} />
        <Callout x={70} y={250} anchorX={185} anchorY={185} label="CHT / EGT" value={t ? `${t.cht_c.toFixed(0)} / ${t.egt_c.toFixed(0)}°C` : "—"} color={color} />
        <Callout x={572} y={95} anchorX={585} anchorY={158} label="ISR PAYLOAD" value={running ? "ACTIVE" : "STBY"} color={color} align="end" />
        <Callout x={588} y={250} anchorX={560} anchorY={205} label="ALTITUDE" value={t ? `${(t.altitude_ft / 1000).toFixed(1)}k ft` : "—"} color={color} align="end" />
      </svg>

      <div className="flex items-center justify-between border-t border-[var(--color-panel-border)] px-4 py-2 text-[10px] text-[var(--color-text-muted)]">
        <span>MALE-UAV airframe twin · live-synced to engine telemetry (synthetic)</span>
        <span style={{ color }}>{running ? "● IN FLIGHT" : "○ ON GROUND"}</span>
      </div>
    </div>
  );
}
