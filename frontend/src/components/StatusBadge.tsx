type Tone = "normal" | "warning" | "critical" | "neutral";

const TONE_STYLES: Record<Tone, string> = {
  normal: "bg-[color-mix(in_srgb,var(--color-normal)_18%,transparent)] text-[var(--color-normal)] border-[var(--color-normal)]/40",
  warning: "bg-[color-mix(in_srgb,var(--color-warning)_18%,transparent)] text-[var(--color-warning)] border-[var(--color-warning)]/40",
  critical: "bg-[color-mix(in_srgb,var(--color-critical)_18%,transparent)] text-[var(--color-critical)] border-[var(--color-critical)]/40",
  neutral: "bg-white/5 text-[var(--color-text-muted)] border-white/10",
};

function toneFor(value: string): Tone {
  const v = value.toUpperCase();
  if (["NORMAL", "GREEN", "LOW", "NONE"].includes(v)) return "normal";
  if (["WARNING", "YELLOW", "MEDIUM", "POSSIBLE_SENSOR_FAULT"].includes(v)) return "warning";
  if (["CRITICAL", "RED", "HIGH", "POSSIBLE_ENGINE_FAULT"].includes(v)) return "critical";
  return "neutral";
}

export function StatusBadge({ label, tone }: { label: string; tone?: Tone }) {
  const resolved = tone ?? toneFor(label);
  return (
    <span
      className={`inline-flex items-center rounded-full border px-2.5 py-1 text-xs font-semibold tracking-wide ${TONE_STYLES[resolved]}`}
    >
      {label.replace(/_/g, " ")}
    </span>
  );
}
