import { LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid } from "recharts";
import type { TelemetryStreamMessage } from "../types/api";
import { Panel } from "./Panel";
import { StatusBadge } from "./StatusBadge";

type Mode = "statistical" | "ml" | "hybrid";

const MODE_LABEL: Record<Mode, string> = {
  statistical: "Statistical (Mahalanobis · no ML)",
  ml: "IsolationForest (ML)",
  hybrid: "Hybrid (both)",
};

const MODE_SUBTITLE: Record<Mode, string> = {
  statistical: "White-box Mahalanobis distance on physics residuals — pure math, no ML library in the detection path.",
  ml: "IsolationForest unsupervised anomaly detection, trained on simulated healthy data.",
  hybrid: "Physics-residual statistics + IsolationForest — the more conservative score drives health.",
};

export function AIHealthPanel({
  history,
  detectorMode = "hybrid",
  onSetDetectorMode,
}: {
  history: TelemetryStreamMessage[];
  detectorMode?: Mode;
  onSetDetectorMode?: (m: Mode) => void;
}) {
  const latest = history.length > 0 ? history[history.length - 1] : null;
  const chartData = history.map((m, i) => ({
    i,
    anomaly: m.health?.anomaly_score ?? 0,
    degradation: m.degradation?.degradation_index ?? 0,
  }));

  return (
    <Panel
      title="AI Health Twin"
      subtitle={MODE_SUBTITLE[detectorMode]}
      actions={
        <div className="flex items-center gap-1 rounded-lg border border-[var(--color-panel-border)] p-0.5">
          {(["statistical", "ml", "hybrid"] as Mode[]).map((m) => {
            const active = detectorMode === m;
            return (
              <button
                key={m}
                onClick={() => onSetDetectorMode?.(m)}
                title={MODE_LABEL[m]}
                className="rounded-md px-2.5 py-1 text-[11px] font-semibold transition-colors"
                style={
                  active
                    ? { background: "color-mix(in srgb, var(--color-accent) 20%, transparent)", color: "var(--color-accent)" }
                    : { color: "var(--color-text-muted)" }
                }
              >
                {m === "statistical" ? "Statistical" : m === "ml" ? "ML" : "Hybrid"}
              </button>
            );
          })}
        </div>
      }
    >
      <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
        <div>
          <div className="mb-1 text-xs text-[var(--color-text-muted)]">Anomaly Score & Degradation Index</div>
          <ResponsiveContainer width="100%" height={140}>
            <LineChart data={chartData}>
              <CartesianGrid stroke="#223047" strokeDasharray="3 3" />
              <XAxis dataKey="i" hide />
              <YAxis tick={{ fontSize: 10, fill: "#8fa0bd" }} width={30} />
              <Tooltip contentStyle={{ background: "#111a2e", border: "1px solid #223047", fontSize: 12 }} />
              <Line type="monotone" dataKey="anomaly" stroke="#e2483c" dot={false} strokeWidth={2} name="Anomaly score" />
              <Line type="monotone" dataKey="degradation" stroke="#e8b93a" dot={false} strokeWidth={2} name="Degradation index" />
            </LineChart>
          </ResponsiveContainer>
        </div>

        <div className="space-y-3">
          <div className="flex flex-wrap items-center gap-2 text-xs">
            <span className="text-[var(--color-text-muted)]">Sensor Fault Isolation:</span>
            <StatusBadge label={latest?.sensor_fault?.category ?? "INSUFFICIENT_EVIDENCE"} />
            {latest?.sensor_fault && latest.sensor_fault.severity !== "NONE" && (
              <StatusBadge label={latest.sensor_fault.severity} />
            )}
          </div>
          {latest?.sensor_fault?.explanation && (
            <p className="rounded-md border border-[var(--color-panel-border)] bg-white/[0.02] p-2.5 text-xs text-[var(--color-text-muted)]">
              {latest.sensor_fault.explanation}
            </p>
          )}
          {latest?.health?.contributing_signals && latest.health.contributing_signals.length > 0 && (
            <div className="flex flex-wrap gap-1.5">
              {latest.health.contributing_signals.map((s) => (
                <span key={s} className="rounded-full border border-white/10 bg-white/5 px-2 py-0.5 text-[11px] text-[var(--color-text-muted)]">
                  {s}
                </span>
              ))}
            </div>
          )}
        </div>
      </div>
    </Panel>
  );
}
