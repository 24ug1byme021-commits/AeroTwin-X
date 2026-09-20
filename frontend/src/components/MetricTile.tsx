export function MetricTile({
  label,
  value,
  unit,
  hint,
}: {
  label: string;
  value: number | string;
  unit?: string;
  hint?: string;
}) {
  return (
    <div className="rounded-md border border-[var(--color-panel-border)] bg-white/[0.02] px-3 py-2.5" title={hint}>
      <div className="text-[11px] uppercase tracking-wide text-[var(--color-text-muted)]">{label}</div>
      <div className="mt-1 flex items-baseline gap-1">
        <span className="text-xl font-semibold text-[var(--color-text)] tabular-nums">
          {typeof value === "number" ? value.toFixed(1) : value}
        </span>
        {unit && <span className="text-xs text-[var(--color-text-muted)]">{unit}</span>}
      </div>
    </div>
  );
}
