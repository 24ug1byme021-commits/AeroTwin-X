import type { TelemetryStreamMessage } from "../types/api";
import { Panel } from "./Panel";
import { StatusBadge } from "./StatusBadge";

interface AlertEntry {
  timestamp: string;
  severity: string;
  explanation: string;
  recommendation: string;
}

function buildAlerts(history: TelemetryStreamMessage[]): AlertEntry[] {
  const alerts: AlertEntry[] = [];
  for (const m of history) {
    if (m.health && m.health.status !== "NORMAL" && m.health.suspected_fault) {
      alerts.push({
        timestamp: m.telemetry.timestamp,
        severity: m.health.status,
        explanation: `${m.health.suspected_fault} (health index ${m.health.health_index.toFixed(0)}, confidence ${m.health.confidence_pct.toFixed(0)}%)`,
        recommendation:
          m.health.status === "CRITICAL"
            ? "Recommend inspection before next flight."
            : "Monitor trend; inspect if condition persists or worsens.",
      });
    } else if (m.sensor_fault && m.sensor_fault.category === "POSSIBLE_SENSOR_FAULT") {
      alerts.push({
        timestamp: m.telemetry.timestamp,
        severity: m.sensor_fault.severity,
        explanation: m.sensor_fault.explanation,
        recommendation: "Cross-check affected sensor against a secondary source before acting on its reading.",
      });
    }
  }
  // Most recent first, capped so the panel stays scannable.
  return alerts.reverse().slice(0, 8);
}

export function AlertsPanel({ history }: { history: TelemetryStreamMessage[] }) {
  const alerts = buildAlerts(history);

  return (
    <Panel title="Alerts" subtitle="Derived from the live Health Twin and Sensor Fault Isolation stream">
      {alerts.length === 0 ? (
        <p className="text-xs text-[var(--color-text-muted)]">No alerts — all monitored signals within normal bands.</p>
      ) : (
        <ul className="space-y-2">
          {alerts.map((a, idx) => (
            <li key={idx} className="rounded-md border border-[var(--color-panel-border)] bg-white/[0.02] p-2.5">
              <div className="flex items-center justify-between gap-2">
                <StatusBadge label={a.severity} />
                <span className="text-[11px] text-[var(--color-text-muted)]">
                  {new Date(a.timestamp).toLocaleTimeString()}
                </span>
              </div>
              <p className="mt-1.5 text-xs text-[var(--color-text)]">{a.explanation}</p>
              <p className="mt-1 text-xs text-[var(--color-text-muted)]">→ {a.recommendation}</p>
            </li>
          ))}
        </ul>
      )}
    </Panel>
  );
}
