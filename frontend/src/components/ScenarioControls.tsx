import type { ScenarioName } from "../types/api";
import { Panel } from "./Panel";
import { Play, Square, RotateCcw, SlidersHorizontal } from "lucide-react";

const SCENARIOS: { value: ScenarioName; label: string }[] = [
  { value: "NORMAL_CRUISE", label: "Normal Cruise" },
  { value: "HIGH_ALTITUDE", label: "High Altitude" },
  { value: "HOT_WEATHER", label: "Hot Weather" },
  { value: "THERMAL_DEGRADATION", label: "Thermal Degradation" },
  { value: "VIBRATION_DEGRADATION", label: "Vibration Degradation" },
  { value: "SENSOR_DRIFT", label: "Sensor Drift" },
  { value: "COMBUSTION_ANOMALY", label: "Combustion Anomaly" },
  { value: "COMBINED_DEGRADATION", label: "Combined Degradation" },
];

export function ScenarioControls({
  running,
  activeScenario,
  onStart,
  onStop,
  onReset,
  onScenarioChange,
}: {
  running: boolean;
  activeScenario: string | null;
  onStart: () => void;
  onStop: () => void;
  onReset: () => void;
  onScenarioChange: (scenario: ScenarioName) => void;
}) {
  return (
    <Panel
      title="Scenario Controller"
      icon={<SlidersHorizontal size={14} />}
      subtitle="Switch operating scenario live. For the sensor-vs-engine fault demo, select Sensor Drift then Thermal Degradation."
    >
      <div className="flex flex-wrap items-center gap-2">
        <button
          onClick={running ? onStop : onStart}
          className="inline-flex items-center gap-1.5 rounded-lg px-4 py-2 text-xs font-bold tracking-wide transition-all duration-200"
          style={
            running
              ? { background: "color-mix(in srgb, var(--color-critical) 20%, transparent)", color: "var(--color-critical)", border: "1px solid color-mix(in srgb, var(--color-critical) 45%, transparent)" }
              : { background: "color-mix(in srgb, var(--color-normal) 20%, transparent)", color: "var(--color-normal)", border: "1px solid color-mix(in srgb, var(--color-normal) 45%, transparent)", boxShadow: "0 0 20px -6px var(--color-normal)" }
          }
        >
          {running ? <Square size={13} /> : <Play size={13} />}
          {running ? "Stop Simulation" : "Start Simulation"}
        </button>

        <button
          onClick={onReset}
          className="inline-flex items-center gap-1.5 rounded-lg border border-[var(--color-panel-border)] px-3 py-2 text-xs font-semibold text-[var(--color-text-muted)] transition-colors hover:border-[var(--color-accent)]/40 hover:text-[var(--color-text)]"
        >
          <RotateCcw size={13} /> Reset
        </button>

        <div className="mx-1 h-6 w-px bg-[var(--color-panel-border)]" />

        {SCENARIOS.map((s) => {
          const active = activeScenario === s.value;
          return (
            <button
              key={s.value}
              onClick={() => onScenarioChange(s.value)}
              className="rounded-lg border px-3 py-1.5 text-xs font-medium transition-all duration-200"
              style={
                active
                  ? { borderColor: "var(--color-accent)", background: "color-mix(in srgb, var(--color-accent) 15%, transparent)", color: "var(--color-accent)" }
                  : { borderColor: "var(--color-panel-border)", color: "var(--color-text-muted)" }
              }
            >
              {s.label}
            </button>
          );
        })}
      </div>
    </Panel>
  );
}
