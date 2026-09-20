import type { TelemetryFrame } from "../types/api";
import { Panel } from "./Panel";
import { Gauge } from "./Gauge";
import { Gauge as GaugeIcon } from "lucide-react";

export function LiveTelemetryPanel({ telemetry }: { telemetry: TelemetryFrame | null }) {
  const t = telemetry;
  return (
    <Panel
      title="Live Telemetry"
      icon={<GaugeIcon size={14} />}
      subtitle={t ? `Source: ${t.source} · synthetic feed` : "Awaiting simulation start…"}
    >
      <div className="grid grid-cols-2 gap-2 sm:grid-cols-4">
        <Gauge label="RPM" value={t?.rpm ?? null} min={0} max={6000} warn={5400} danger={5800} />
        <Gauge label="CHT" value={t?.cht_c ?? null} min={0} max={260} unit="°C" warn={225} danger={245} />
        <Gauge label="EGT" value={t?.egt_c ?? null} min={0} max={1000} unit="°C" warn={850} danger={890} />
        <Gauge label="Vibration" value={t?.vibration_mms ?? null} min={0} max={15} unit="mm/s" warn={6} danger={9} decimals={1} />
        <Gauge label="Oil Press" value={t?.oil_pressure_psi ?? null} min={0} max={120} unit="psi" decimals={0} />
        <Gauge label="Oil Temp" value={t?.oil_temperature_c ?? null} min={0} max={160} unit="°C" warn={125} danger={140} />
        <Gauge label="Fuel Flow" value={t?.fuel_flow_lph ?? null} min={0} max={60} unit="L/h" decimals={1} />
        <Gauge label="Battery" value={t?.battery_voltage_v ?? null} min={20} max={32} unit="V" decimals={1} />
      </div>

      {/* Electrical + injection strip — the PS-required extras, shown as compact readouts */}
      <div className="mt-3 grid grid-cols-2 gap-2 sm:grid-cols-4">
        <Readout label="Alternator Load" value={t ? `${t.alternator_load_pct.toFixed(0)}%` : "—"} />
        <Readout label="Injection Timing" value={t ? `${t.injection_timing_deg.toFixed(1)}° BTDC` : "—"} />
        <Readout label="Throttle" value={t ? `${t.throttle_pct.toFixed(0)}%` : "—"} />
        <Readout label="Altitude" value={t ? `${t.altitude_ft.toFixed(0)} ft` : "—"} />
      </div>
    </Panel>
  );
}

function Readout({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-md border border-[var(--color-panel-border)] bg-white/[0.02] px-3 py-2">
      <div className="text-[10px] uppercase tracking-[0.1em] text-[var(--color-text-muted)]">{label}</div>
      <div className="mt-0.5 text-sm font-semibold tabular-nums text-[var(--color-text)]">{value}</div>
    </div>
  );
}
