import { useCallback, useEffect, useState } from "react";
import { api } from "../services/api";
import type { RunRecord, RunReport } from "../types/api";
import { Panel } from "./Panel";
import { Database, RefreshCw } from "lucide-react";

/**
 * Post-Flight Log — reads recorded runs from the backend's SQLite store.
 * This is the visible proof of the persistence layer and delivers the PS's
 * "post-flight analysis and mission replay" requirement: every run is
 * stored and can be summarised after the fact.
 */
export function PostFlightLogPanel({ running }: { running: boolean }) {
  const [runs, setRuns] = useState<RunRecord[]>([]);
  const [report, setReport] = useState<RunReport | null>(null);
  const [persistence, setPersistence] = useState<string>("");

  const load = useCallback(async () => {
    try {
      const res = await api.listRuns();
      setRuns(res.runs);
      setPersistence(res.persistence);
    } catch {
      setPersistence("unavailable");
    }
  }, []);

  useEffect(() => {
    load();
  }, [load, running]);

  async function openReport(id: number) {
    try {
      setReport(await api.runReport(id));
    } catch {
      setReport(null);
    }
  }

  return (
    <Panel
      title="Post-Flight Log"
      icon={<Database size={14} />}
      subtitle={`Recorded runs persisted to on-device SQLite${persistence ? ` · store: ${persistence}` : ""}`}
      actions={
        <button
          onClick={load}
          className="inline-flex items-center gap-1.5 rounded-md border border-[var(--color-panel-border)] px-2.5 py-1 text-[11px] font-semibold text-[var(--color-text-muted)] transition-colors hover:text-[var(--color-text)]"
        >
          <RefreshCw size={12} /> Refresh
        </button>
      }
    >
      {runs.length === 0 ? (
        <p className="text-xs text-[var(--color-text-muted)]">
          No recorded runs yet. Start a simulation — each session is stored automatically for post-flight analysis.
        </p>
      ) : (
        <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
          <div className="overflow-hidden rounded-lg border border-[var(--color-panel-border)]">
            <table className="w-full text-left text-xs">
              <thead className="bg-white/[0.03] text-[10px] uppercase tracking-wide text-[var(--color-text-muted)]">
                <tr>
                  <th className="px-3 py-2">Run</th>
                  <th className="px-3 py-2">Scenario</th>
                  <th className="px-3 py-2">Detector</th>
                  <th className="px-3 py-2">Frames</th>
                </tr>
              </thead>
              <tbody>
                {runs.map((r) => (
                  <tr
                    key={r.run_id}
                    onClick={() => openReport(r.run_id)}
                    className="cursor-pointer border-t border-[var(--color-panel-border)] transition-colors hover:bg-white/[0.03]"
                  >
                    <td className="px-3 py-2 font-semibold text-[var(--color-accent)]">#{r.run_id}</td>
                    <td className="px-3 py-2">{r.scenario?.replace(/_/g, " ")}</td>
                    <td className="px-3 py-2 text-[var(--color-text-muted)]">{r.detector_mode}</td>
                    <td className="px-3 py-2 tabular-nums">{r.frame_count}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          <div className="rounded-lg border border-[var(--color-panel-border)] bg-white/[0.02] p-3">
            {report ? (
              <div>
                <div className="mb-2 text-xs font-semibold text-[var(--color-text)]">
                  Run #{report.run_id} · {report.scenario?.replace(/_/g, " ")} · post-flight summary
                </div>
                <div className="grid grid-cols-2 gap-2 text-xs sm:grid-cols-3">
                  <ReportStat label="Frames" value={report.summary.frames} />
                  <ReportStat label="Min Health" value={fmt(report.summary.min_health)} />
                  <ReportStat label="Avg Health" value={fmt(report.summary.avg_health)} />
                  <ReportStat label="Peak CHT" value={fmt(report.summary.peak_cht, "°C")} />
                  <ReportStat label="Peak EGT" value={fmt(report.summary.peak_egt, "°C")} />
                  <ReportStat label="Peak Vib" value={fmt(report.summary.peak_vibration, " mm/s")} />
                  <ReportStat label="Peak Anomaly" value={fmt(report.summary.peak_anomaly)} />
                  <ReportStat label="Peak Degr." value={fmt(report.summary.peak_degradation)} />
                  <ReportStat label="Min RUL" value={fmt(report.summary.min_rul, " h")} />
                </div>
              </div>
            ) : (
              <p className="text-xs text-[var(--color-text-muted)]">Select a run to see its post-flight summary report.</p>
            )}
          </div>
        </div>
      )}
    </Panel>
  );
}

function fmt(v: number | null | undefined, suffix = ""): string {
  return v == null ? "—" : `${v}${suffix}`;
}

function ReportStat({ label, value }: { label: string; value: string | number }) {
  return (
    <div className="rounded-md border border-[var(--color-panel-border)] bg-white/[0.02] px-2.5 py-1.5">
      <div className="text-[9px] uppercase tracking-wide text-[var(--color-text-muted)]">{label}</div>
      <div className="mt-0.5 text-sm font-semibold tabular-nums text-[var(--color-text)]">{value}</div>
    </div>
  );
}
