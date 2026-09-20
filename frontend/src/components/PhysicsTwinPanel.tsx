import { LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid } from "recharts";
import type { TelemetryStreamMessage } from "../types/api";
import { Panel } from "./Panel";

function residualTone(value: number, warnAt: number, critAt: number) {
  const abs = Math.abs(value);
  if (abs >= critAt) return "text-[var(--color-critical)]";
  if (abs >= warnAt) return "text-[var(--color-warning)]";
  return "text-[var(--color-normal)]";
}

export function PhysicsTwinPanel({ history }: { history: TelemetryStreamMessage[] }) {
  const chartData = history.map((m, i) => ({
    i,
    egtActual: m.telemetry.egt_c,
    egtExpected: m.residuals ? m.telemetry.egt_c - m.residuals.egt_residual_c : null,
    chtActual: m.telemetry.cht_c,
    chtExpected: m.residuals ? m.telemetry.cht_c - m.residuals.cht_residual_c : null,
  }));

  const latestResiduals = history.length > 0 ? history[history.length - 1].residuals : null;

  return (
    <Panel title="Physics Twin" subtitle="Actual telemetry vs. healthy-baseline expected values">
      <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
        <div>
          <div className="mb-1 text-xs text-[var(--color-text-muted)]">EGT — Actual vs Expected (°C)</div>
          <ResponsiveContainer width="100%" height={140}>
            <LineChart data={chartData}>
              <CartesianGrid stroke="#223047" strokeDasharray="3 3" />
              <XAxis dataKey="i" hide />
              <YAxis tick={{ fontSize: 10, fill: "#8fa0bd" }} width={36} domain={["auto", "auto"]} />
              <Tooltip contentStyle={{ background: "#111a2e", border: "1px solid #223047", fontSize: 12 }} />
              <Line type="monotone" dataKey="egtActual" stroke="#3aa0ff" dot={false} strokeWidth={2} name="Actual" />
              <Line type="monotone" dataKey="egtExpected" stroke="#8fa0bd" dot={false} strokeWidth={1.5} strokeDasharray="4 3" name="Expected" />
            </LineChart>
          </ResponsiveContainer>
        </div>
        <div>
          <div className="mb-1 text-xs text-[var(--color-text-muted)]">CHT — Actual vs Expected (°C)</div>
          <ResponsiveContainer width="100%" height={140}>
            <LineChart data={chartData}>
              <CartesianGrid stroke="#223047" strokeDasharray="3 3" />
              <XAxis dataKey="i" hide />
              <YAxis tick={{ fontSize: 10, fill: "#8fa0bd" }} width={36} domain={["auto", "auto"]} />
              <Tooltip contentStyle={{ background: "#111a2e", border: "1px solid #223047", fontSize: 12 }} />
              <Line type="monotone" dataKey="chtActual" stroke="#e8b93a" dot={false} strokeWidth={2} name="Actual" />
              <Line type="monotone" dataKey="chtExpected" stroke="#8fa0bd" dot={false} strokeWidth={1.5} strokeDasharray="4 3" name="Expected" />
            </LineChart>
          </ResponsiveContainer>
        </div>
      </div>

      {latestResiduals && (
        <div className="mt-3 grid grid-cols-2 gap-3 sm:grid-cols-4">
          <div className="rounded-md border border-[var(--color-panel-border)] px-3 py-2">
            <div className="text-[11px] uppercase text-[var(--color-text-muted)]">EGT Residual</div>
            <div className={`text-lg font-semibold tabular-nums ${residualTone(latestResiduals.egt_residual_c, 15, 45)}`}>
              {latestResiduals.egt_residual_c >= 0 ? "+" : ""}
              {latestResiduals.egt_residual_c.toFixed(1)} °C
            </div>
          </div>
          <div className="rounded-md border border-[var(--color-panel-border)] px-3 py-2">
            <div className="text-[11px] uppercase text-[var(--color-text-muted)]">CHT Residual</div>
            <div className={`text-lg font-semibold tabular-nums ${residualTone(latestResiduals.cht_residual_c, 6, 18)}`}>
              {latestResiduals.cht_residual_c >= 0 ? "+" : ""}
              {latestResiduals.cht_residual_c.toFixed(1)} °C
            </div>
          </div>
          <div className="rounded-md border border-[var(--color-panel-border)] px-3 py-2">
            <div className="text-[11px] uppercase text-[var(--color-text-muted)]">Oil Temp Residual</div>
            <div className={`text-lg font-semibold tabular-nums ${residualTone(latestResiduals.oil_temperature_residual_c, 8, 20)}`}>
              {latestResiduals.oil_temperature_residual_c >= 0 ? "+" : ""}
              {latestResiduals.oil_temperature_residual_c.toFixed(1)} °C
            </div>
          </div>
          <div className="rounded-md border border-[var(--color-panel-border)] px-3 py-2">
            <div className="text-[11px] uppercase text-[var(--color-text-muted)]">Fuel Flow Residual</div>
            <div className={`text-lg font-semibold tabular-nums ${residualTone(latestResiduals.fuel_flow_residual_lph, 1, 2.5)}`}>
              {latestResiduals.fuel_flow_residual_lph >= 0 ? "+" : ""}
              {latestResiduals.fuel_flow_residual_lph.toFixed(2)} L/h
            </div>
          </div>
        </div>
      )}
    </Panel>
  );
}
