export type ColorBand = "green" | "amber" | "red";
export type TrustBadge = "A" | "B" | "C" | "D";

export interface ConnectorDTO {
  connector_id: string;
  type: "AC" | "DC";
  kw: number;
  status: "available" | "charging" | "reserved" | "faulted";
  trust_badge: TrustBadge;
  start_success_rate: number;
  soft_fault_rate: number;
  mttr_h: number;
}

export interface PartnerDTO {
  partner_id: string;
  name: string;
  offer: string;
  lat: number;
  lon: number;
}

export interface StationPlanCard {
  station_id: string;
  eta_min: number;
  p50_wait: number;
  p90_wait: number;
  expected_start_min: number;
  color_band: ColorBand;
  trust_badge: TrustBadge;
  connectors?: ConnectorDTO[];
  safe_wait_partners?: PartnerDTO[];
}

export interface PlanAction {
  type: "RESERVE" | "QUARANTINE" | "SET_PROFILE" | "NONE";
  station_id?: string;
  connector_id?: string;
  reason: string;
  promised_start_min?: number;
}

export interface PlanStep {
  tool: string;
  args: Record<string, any>;
  result: Record<string, any>;
}

export interface Plan {
  steps: PlanStep[];
  actions: PlanAction[];
  driver_summary: string;
  operator_rationale: string;
  stations: StationPlanCard[];
  safe_corridor: string[];
}

export interface OperatorOverview {
  uptime_by_station: { station_id: string; uptime: number }[];
  buffer_status: { station_id: string; configured: number; reserved_now: number }[];
  sniffer_list: { connector_id: string; score: number; basis: string }[];
  reservation_accuracy_p90: number;
  trust_leaderboard: { station_id: string; A: number; B: number; C: number; D: number }[];
}

export interface Intervention {
  id: number;
  ts: string;
  action: string;
  reason?: string;
  station_id?: string;
  connector_id?: string;
  promised_start?: number;
  actual_start?: number;
}