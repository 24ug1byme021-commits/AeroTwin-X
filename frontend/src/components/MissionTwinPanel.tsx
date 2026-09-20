import { useState } from "react";
import { LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid, Legend } from "recharts";
import type { MissionInput, MissionResult, MissionType } from "../types/api";
import { Panel } from "./Panel";
import { StatusBadge } from "./StatusBadge";
import { api } from "../services/api";

const DEFAULT_MISSION: MissionInput = {
  mission_type: "NORMAL_ISR",
  duration_hours: 8,
  cruise_altitude_ft: 8000,
  max_altitude_ft: 10000,
  ambient_temperature_c: 20,
  average_throttle_pct: 60,
};

const MISSION_TYPES: MissionType[] = ["NORMAL_ISR", "HIGH_ALTITUDE", "HOT_WEATHER", "HIGH_LOAD_ENDURANCE", "CUSTOM"];

export function MissionTwinPanel({ onResult }: { onResult?: (result: MissionResult) => void }) {
  const [mission, setMission] = useState<MissionInput>(DEFAULT_MISSION);
  const [nlText, setNlText] = useState("Plan an 8 hour ISR mission at high altitude in hot weather.");
  const [result, setResult] = useState<MissionResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [parseNotes, setParseNotes] = useState<string[]>([]);

  function updateField<K extends keyof MissionInput>(key: K, value: MissionInput[K]) {
    setMission((m) => ({ ...m, [key]: value }));
  }

  async function runSimulation(input: MissionInput) {
    setLoading(true);
    setError(null);
    try {
      const r = await api.missionSimulate(input);
      setResult(r);
      onResult?.(r);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Mission simulation failed");
    } finally {
      setLoading(false);
    }
  }

  async function handleParseAndRun() {
    setLoading(true);
    setError(null);
    try {
      const parsed = await api.missionParse(nlText);
      setMission(parsed.parsed);
      setParseNotes(parsed.parse_notes);
      await runSimulation(parsed.parsed);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Mission parsing failed");
      setLoading(false);
    }
  }

  const chartData = result?.trajectory.map((p) => ({
    t: Number(p.t_hours.toFixed(2)),
    health: p.health_index,
    egt: p.egt_c,
    cht: p.cht_c,
    vibration: p.vibration_mms,
  }));

  return (
    <Panel
      title="Mission Twin — What-If Simulator"
      subtitle="Projects current engine condition forward through a proposed mission profile"
    >
      <div className="grid grid-cols-1 gap-4 lg:grid-cols-3">
        {/* Inputs */}
        <div className="space-y-3 lg:col-span-1">
          <div>
            <label className="mb-1 block text-[11px] uppercase text-[var(--color-text-muted)]">
              Natural-language mission input
            </label>
            <textarea
              value={nlText}
              onChange={(e) => setNlText(e.target.value)}
              rows={2}
              className="w-full rounded-md border border-[var(--color-panel-border)] bg-white/[0.03] p-2 text-xs text-[var(--color-text)] focus:border-[var(--color-accent)] focus:outline-none"
              placeholder='e.g. "Plan an 8 hour ISR mission at high altitude in hot weather."'
            />
            <button
              onClick={handleParseAndRun}
              disabled={loading}
              className="mt-2 w-full rounded-md bg-[var(--color-accent)]/20 px-3 py-1.5 text-xs font-semibold text-[var(--color-accent)] hover:bg-[var(--color-accent)]/30 disabled:opacity-50"
            >
              Parse &amp; Run Mission Twin
            </button>
            {parseNotes.length > 0 && (
              <ul className="mt-1.5 space-y-0.5 text-[11px] text-[var(--color-text-muted)]">
                {parseNotes.map((n, i) => (
                  <li key={i}>· {n}</li>
                ))}
              </ul>
            )}
          </div>

          <div className="border-t border-[var(--color-panel-border)] pt-3">
            <label className="mb-1 block text-[11px] uppercase text-[var(--color-text-muted)]">Or set parameters manually</label>
            <div className="grid grid-cols-2 gap-2">
              <FieldNumber label="Duration (h)" value={mission.duration_hours} onChange={(v) => updateField("duration_hours", v)} />
              <FieldNumber label="Avg Throttle (%)" value={mission.average_throttle_pct} onChange={(v) => updateField("average_throttle_pct", v)} />
              <FieldNumber label="Cruise Alt (ft)" value={mission.cruise_altitude_ft} onChange={(v) => updateField("cruise_altitude_ft", v)} />
              <FieldNumber label="Max Alt (ft)" value={mission.max_altitude_ft} onChange={(v) => updateField("max_altitude_ft", v)} />
              <FieldNumber label="Ambient (°C)" value={mission.ambient_temperature_c} onChange={(v) => updateField("ambient_temperature_c", v)} />
              <div>
                <label className="mb-0.5 block text-[10px] text-[var(--color-text-muted)]">Mission Type</label>
                <select
                  value={mission.mission_type}
                  onChange={(e) => updateField("mission_type", e.target.value as MissionType)}
                  className="w-full rounded-md border border-[var(--color-panel-border)] bg-white/[0.03] px-2 py-1 text-xs text-[var(--color-text)]"
                >
                  {MISSION_TYPES.map((t) => (
                    <option key={t} value={t}>
                      {t.replace(/_/g, " ")}
                    </option>
                  ))}
                </select>
              </div>
            </div>
            <button
              onClick={() => runSimulation(mission)}
              disabled={loading}
              className="mt-2 w-full rounded-md border border-[var(--color-panel-border)] px-3 py-1.5 text-xs text-[var(--color-text)] hover:border-[var(--color-accent)]/40 disabled:opacity-50"
            >
              Run with manual parameters
            </button>
          </div>

          {error && <p className="text-xs text-[var(--color-critical)]">{error}</p>}
        </div>

        {/* Results */}
        <div className="lg:col-span-2">
          {!result ? (
            <div className="flex h-full min-h-[220px] items-center justify-center rounded-md border border-dashed border-[var(--color-panel-border)] text-xs text-[var(--color-text-muted)]">
              Run a mission to see the projected health trajectory and readiness assessment.
            </div>
          ) : (
            <div className="space-y-3">
              <ResponsiveContainer width="100%" height={180}>
                <LineChart data={chartData}>
                  <CartesianGrid stroke="#223047" strokeDasharray="3 3" />
                  <XAxis dataKey="t" tick={{ fontSize: 10, fill: "#8fa0bd" }} label={{ value: "Mission hour", position: "insideBottom", offset: -2, fontSize: 10, fill: "#8fa0bd" }} />
                  <YAxis tick={{ fontSize: 10, fill: "#8fa0bd" }} width={32} />
                  <Tooltip contentStyle={{ background: "#111a2e", border: "1px solid #223047", fontSize: 12 }} />
                  <Legend wrapperStyle={{ fontSize: 11 }} />
                  <Line type="monotone" dataKey="health" stroke="#35c07a" dot={false} strokeWidth={2} name="Health %" />
                  <Line type="monotone" dataKey="cht" stroke="#e8b93a" dot={false} strokeWidth={1.5} name="CHT °C" />
                  <Line type="monotone" dataKey="egt" stroke="#3aa0ff" dot={false} strokeWidth={1.5} name="EGT °C" />
                </LineChart>
              </ResponsiveContainer>

              <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
                <MiniStat label="Risk Level" value={<StatusBadge label={result.risk_level} />} />
                <MiniStat label="End-of-Mission Health" value={`${result.predicted_end_of_mission_health.toFixed(0)}%`} />
                <MiniStat label="Projected RUL" value={`${result.predicted_rul_hours.toFixed(0)} ± ${result.rul_uncertainty_hours.toFixed(0)} h`} />
                <MiniStat label="Critical Phase" value={result.critical_phase} />
              </div>

              <div className="rounded-md border border-[var(--color-panel-border)] bg-white/[0.02] p-3">
                <div className="text-[11px] uppercase text-[var(--color-text-muted)]">Main Contributors</div>
                <ul className="mt-1 list-inside list-disc text-xs text-[var(--color-text)]">
                  {result.main_contributors.map((c, i) => (
                    <li key={i}>{c}</li>
                  ))}
                </ul>
                <div className="mt-2 text-[11px] uppercase text-[var(--color-text-muted)]">Recommendation</div>
                <p className="text-xs text-[var(--color-text)]">{result.recommendation}</p>
              </div>
            </div>
          )}
        </div>
      </div>
    </Panel>
  );
}

function FieldNumber({ label, value, onChange }: { label: string; value: number; onChange: (v: number) => void }) {
  return (
    <div>
      <label className="mb-0.5 block text-[10px] text-[var(--color-text-muted)]">{label}</label>
      <input
        type="number"
        value={value}
        onChange={(e) => onChange(Number(e.target.value))}
        className="w-full rounded-md border border-[var(--color-panel-border)] bg-white/[0.03] px-2 py-1 text-xs text-[var(--color-text)] focus:border-[var(--color-accent)] focus:outline-none"
      />
    </div>
  );
}

function MiniStat({ label, value }: { label: string; value: React.ReactNode }) {
  return (
    <div className="rounded-md border border-[var(--color-panel-border)] px-3 py-2">
      <div className="text-[11px] uppercase text-[var(--color-text-muted)]">{label}</div>
      <div className="mt-1 text-sm font-semibold text-[var(--color-text)]">{value}</div>
    </div>
  );
}
