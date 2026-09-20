/**
 * Animated circular instrument gauge (SVG).
 *
 * Draws a 270-degree arc track, a coloured value arc, tick marks and a
 * sweeping needle. The needle and value arc animate smoothly via CSS
 * transitions whenever `value` changes, giving the dashboard a live
 * cockpit-instrument feel. Colour shifts green -> amber -> red as the
 * value approaches optional warning/danger thresholds.
 */
type GaugeProps = {
  label: string;
  value: number | null;
  min: number;
  max: number;
  unit?: string;
  warn?: number; // value at/above which the arc turns amber
  danger?: number; // value at/above which the arc turns red
  decimals?: number;
  size?: number;
};

const START_ANGLE = 135; // degrees, bottom-left
const SWEEP = 270; // total travel

function polar(cx: number, cy: number, r: number, angleDeg: number) {
  const a = (angleDeg * Math.PI) / 180;
  return { x: cx + r * Math.cos(a), y: cy + r * Math.sin(a) };
}

function arcPath(cx: number, cy: number, r: number, startDeg: number, endDeg: number) {
  const start = polar(cx, cy, r, startDeg);
  const end = polar(cx, cy, r, endDeg);
  const largeArc = Math.abs(endDeg - startDeg) > 180 ? 1 : 0;
  return `M ${start.x} ${start.y} A ${r} ${r} 0 ${largeArc} 1 ${end.x} ${end.y}`;
}

export function Gauge({
  label,
  value,
  min,
  max,
  unit,
  warn,
  danger,
  decimals = 0,
  size = 132,
}: GaugeProps) {
  const cx = size / 2;
  const cy = size / 2;
  const r = size / 2 - 14;

  const has = value != null && Number.isFinite(value);
  const v = has ? Math.max(min, Math.min(max, value as number)) : min;
  const frac = (v - min) / (max - min || 1);
  const valueAngle = START_ANGLE + frac * SWEEP;

  let color = "var(--color-normal)";
  if (danger != null && (value ?? -Infinity) >= danger) color = "var(--color-critical)";
  else if (warn != null && (value ?? -Infinity) >= warn) color = "var(--color-warning)";

  // Tick marks around the dial
  const ticks = Array.from({ length: 13 }, (_, i) => {
    const ang = START_ANGLE + (i / 12) * SWEEP;
    const outer = polar(cx, cy, r + 3, ang);
    const inner = polar(cx, cy, r - (i % 3 === 0 ? 8 : 4), ang);
    return { outer, inner, major: i % 3 === 0 };
  });

  const needle = polar(cx, cy, r - 12, valueAngle);

  return (
    <div className="flex flex-col items-center">
      <svg width={size} height={size} viewBox={`0 0 ${size} ${size}`} className="overflow-visible">
        <defs>
          <linearGradient id={`ggrad-${label}`} x1="0" y1="0" x2="1" y2="1">
            <stop offset="0%" stopColor={color} stopOpacity="0.95" />
            <stop offset="100%" stopColor={color} stopOpacity="0.55" />
          </linearGradient>
          <filter id={`gglow-${label}`} x="-50%" y="-50%" width="200%" height="200%">
            <feGaussianBlur stdDeviation="2.4" result="b" />
            <feMerge>
              <feMergeNode in="b" />
              <feMergeNode in="SourceGraphic" />
            </feMerge>
          </filter>
        </defs>

        {/* Track */}
        <path d={arcPath(cx, cy, r, START_ANGLE, START_ANGLE + SWEEP)} fill="none" stroke="var(--color-panel-border)" strokeWidth={7} strokeLinecap="round" />

        {/* Value arc */}
        <path
          d={arcPath(cx, cy, r, START_ANGLE, Math.max(START_ANGLE + 0.01, valueAngle))}
          fill="none"
          stroke={`url(#ggrad-${label})`}
          strokeWidth={7}
          strokeLinecap="round"
          filter={`url(#gglow-${label})`}
          style={{ transition: "all 0.7s cubic-bezier(0.22, 1, 0.36, 1)" }}
        />

        {/* Ticks */}
        {ticks.map((t, i) => (
          <line
            key={i}
            x1={t.inner.x}
            y1={t.inner.y}
            x2={t.outer.x}
            y2={t.outer.y}
            stroke={t.major ? "var(--color-text-muted)" : "var(--color-panel-border)"}
            strokeWidth={t.major ? 1.4 : 1}
            opacity={t.major ? 0.8 : 0.5}
          />
        ))}

        {/* Needle */}
        <line
          x1={cx}
          y1={cy}
          x2={needle.x}
          y2={needle.y}
          stroke={color}
          strokeWidth={2.6}
          strokeLinecap="round"
          filter={`url(#gglow-${label})`}
          style={{ transition: "all 0.7s cubic-bezier(0.22, 1, 0.36, 1)" }}
        />
        <circle cx={cx} cy={cy} r={5.5} fill="var(--color-panel-2)" stroke={color} strokeWidth={2} />

        {/* Readout */}
        <text x={cx} y={cy + r - 6} textAnchor="middle" className="fill-[var(--color-text)]" style={{ fontSize: 20, fontWeight: 700, fontVariantNumeric: "tabular-nums" }}>
          {has ? (value as number).toFixed(decimals) : "—"}
        </text>
        {unit && (
          <text x={cx} y={cy + r + 9} textAnchor="middle" className="fill-[var(--color-text-muted)]" style={{ fontSize: 9.5, letterSpacing: "0.06em" }}>
            {unit}
          </text>
        )}
      </svg>
      <div className="mt-0.5 text-[11px] font-medium uppercase tracking-[0.1em] text-[var(--color-text-muted)]">{label}</div>
    </div>
  );
}
