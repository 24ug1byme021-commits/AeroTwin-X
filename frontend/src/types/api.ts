// Mirrors backend/schemas/telemetry.py, health.py, mission.py, prediction.py.
// Kept as one file so the frontend has a single source of truth for the
// wire format, matching the backend's "one data contract" philosophy.

export type DataSource = "simulated" | "replay" | "real_hardware";

export interface TelemetryFrame {
  timestamp: string;
  source: DataSource;
  rpm: number;
  cht_c: number;
  egt_c: number;
  oil_pressure_psi: number;
  oil_temperature_c: number;
  fuel_flow_lph: number;
  vibration_mms: number;
  battery_voltage_v: number;
  alternator_load_pct: number;
  injection_timing_deg: number;
  altitude_ft: number;
  ambient_temperature_c: number;
  throttle_pct: number;
  engine_load_pct: number;
  scenario?: string | null;
}

export type ScenarioName =
  | "NORMAL_CRUISE"
  | "HIGH_ALTITUDE"
  | "HOT_WEATHER"
  | "THERMAL_DEGRADATION"
  | "VIBRATION_DEGRADATION"
  | "SENSOR_DRIFT"
  | "COMBUSTION_ANOMALY"
  | "COMBINED_DEGRADATION";

export interface ResidualFrame {
  timestamp: string;
  egt_residual_c: number;
  cht_residual_c: number;
  oil_temperature_residual_c: number;
  fuel_flow_residual_lph: number;
}

export type DiagnosisCategory =
  | "NONE"
  | "POSSIBLE_SENSOR_FAULT"
  | "POSSIBLE_ENGINE_FAULT"
  | "INSUFFICIENT_EVIDENCE";

export type Severity = "NONE" | "LOW" | "MEDIUM" | "HIGH";

export interface SensorFaultDiagnosis {
  timestamp: string;
  category: DiagnosisCategory;
  severity: Severity;
  confidence_pct: number;
  affected_sensors: string[];
  explanation: string;
}

export type HealthStatus = "NORMAL" | "WARNING" | "CRITICAL";

export interface HealthIndexResult {
  timestamp: string;
  health_index: number;
  status: HealthStatus;
  anomaly_score: number;
  suspected_fault: string | null;
  degradation_trend: string;
  confidence_pct: number;
  contributing_signals: string[];
}

export interface DegradationState {
  timestamp: string;
  degradation_index: number;
  thermal_component: number;
  vibration_component: number;
  residual_component: number;
  accumulated_operating_hours: number;
}

export interface RULEstimate {
  timestamp: string;
  rul_hours: number;
  uncertainty_hours: number;
  confidence_pct: number;
  basis: string;
}

export interface EngineStateSnapshot {
  timestamp: string;
  telemetry_source: string;
  residuals: ResidualFrame | null;
  sensor_fault: SensorFaultDiagnosis | null;
  health: HealthIndexResult | null;
  degradation: DegradationState | null;
  rul: RULEstimate | null;
}

export interface SystemStatus {
  timestamp: string;
  simulation_running: boolean;
  active_scenario: string | null;
  frames_processed: number;
  uptime_seconds: number;
  detector_mode?: "statistical" | "ml" | "hybrid";
}

export interface RunRecord {
  run_id: number;
  started_at: string;
  ended_at: string | null;
  scenario: string;
  detector_mode: string;
  frame_count: number;
}

export interface RunReport extends RunRecord {
  summary: {
    frames: number;
    min_health: number | null;
    avg_health: number | null;
    peak_cht: number | null;
    peak_egt: number | null;
    peak_vibration: number | null;
    peak_anomaly: number | null;
    peak_degradation: number | null;
    min_rul: number | null;
  };
}

export interface TelemetryStreamMessage {
  telemetry: TelemetryFrame;
  residuals: ResidualFrame | null;
  sensor_fault: SensorFaultDiagnosis | null;
  health: HealthIndexResult | null;
  degradation: DegradationState | null;
  rul: RULEstimate | null;
}

// --- Mission Twin -----------------------------------------------------

export type MissionType =
  | "NORMAL_ISR"
  | "HIGH_ALTITUDE"
  | "HOT_WEATHER"
  | "HIGH_LOAD_ENDURANCE"
  | "CUSTOM";

export interface MissionInput {
  mission_type: MissionType;
  duration_hours: number;
  cruise_altitude_ft: number;
  max_altitude_ft: number;
  ambient_temperature_c: number;
  average_throttle_pct: number;
  endurance_requirement_hours?: number | null;
}

export type RiskLevel = "GREEN" | "YELLOW" | "RED";

export interface MissionTrajectoryPoint {
  t_hours: number;
  health_index: number;
  egt_c: number;
  cht_c: number;
  vibration_mms: number;
  degradation_index: number;
}

export interface MissionResult {
  mission_input: MissionInput;
  trajectory: MissionTrajectoryPoint[];
  predicted_end_of_mission_health: number;
  predicted_rul_hours: number;
  rul_uncertainty_hours: number;
  risk_level: RiskLevel;
  critical_phase: string;
  main_contributors: string[];
  recommendation: string;
}

export interface NaturalLanguageMissionParse {
  raw_text: string;
  parsed: MissionInput;
  parser_used: string;
  parse_notes: string[];
}
