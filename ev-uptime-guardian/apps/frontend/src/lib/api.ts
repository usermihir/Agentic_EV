import type { Plan, OperatorOverview, Intervention, TrustBadge } from './types';

const BASE = import.meta.env.VITE_API_BASE || "http://127.0.0.1:8000";

async function j<T>(r: Response): Promise<T> {
  if (!r.ok) throw new Error(`${r.status} ${r.statusText}`);
  return r.json();
}

export async function postPlan(body: any) {
  return j<Plan>(await fetch(`${BASE}/agent/plan`, {
    method: "POST",
    headers: {"Content-Type":"application/json"},
    body: JSON.stringify(body)
  }));
}

export async function getOperatorOverview() {
  return j<OperatorOverview>(await fetch(`${BASE}/operator/overview`));
}

export async function getOperatorInterventions(params?: {
  limit?: number;
  station_id?: string;
  action?: string;
}) {
  const q = new URLSearchParams();
  if (params?.limit) q.set("limit", String(params.limit));
  if (params?.station_id) q.set("station_id", params.station_id);
  if (params?.action) q.set("action", params.action);
  return j<Intervention[]>(await fetch(`${BASE}/operator/interventions?${q.toString()}`));
}

export async function postQuarantine(body: {
  connector_id: string;
  action: "QUARANTINE" | "UNQUARANTINE";
}) {
  return j<{connector_id: string; status: "faulted"|"available"}>(
    await fetch(`${BASE}/operator/quarantine`, {
      method: "POST",
      headers: {"Content-Type":"application/json"},
      body: JSON.stringify(body)
    })
  );
}

export async function getNearby(lat: number, lon: number, limit=6) {
  return j<{stations: {
    station_id:string;
    name:string;
    lat:number;
    lon:number;
    distance_km:number;
  }[]}>(
    await fetch(`${BASE}/tool/station/nearby?lat=${lat}&lon=${lon}&limit=${limit}`)
  );
}

export async function predictStation(station_id: string) {
  return j<{
    station_id: string;
    p50_wait: number;
    p90_wait: number;
    free: number;
    trust_badge: TrustBadge;
  }>(
    await fetch(`${BASE}/tool/station/predict?station_id=${station_id}`)
  );
}

export async function reserveNow(body: {
  station_id: string;
  connector_id?: string|null;
  promised_start_min: number;
  eta_min: number;
  user_id: string;
}) {
  return j<{reservation_id: string; promised_start_min: number; connector_id: string}>(
    await fetch(`${BASE}/tool/ocpp/reserveNow`, {
      method: "POST",
      headers: {"Content-Type":"application/json"},
      body: JSON.stringify(body)
    })
  );
}

export async function earnPoints(body: {
  user_id: string;
  reason: "report_fault"|"slot_resale"|"purchase";
}) {
  return j<{new_balance: number}>(
    await fetch(`${BASE}/tool/points/earn`, {
      method: "POST",
      headers: {"Content-Type":"application/json"},
      body: JSON.stringify(body)
    })
  );
}