-- SQLite schema for Agentic EV Uptime Guardian
-- Tables: stations, connectors, sessions, reservations, partners, points_ledger, interventions

-- Stations table
CREATE TABLE IF NOT EXISTS stations (
    station_id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    lat REAL NOT NULL,
    lon REAL NOT NULL,
    emergency_buffer INTEGER NOT NULL DEFAULT 1
);

-- Connectors table with station relationship
CREATE TABLE IF NOT EXISTS connectors (
    connector_id TEXT PRIMARY KEY,
    station_id TEXT NOT NULL REFERENCES stations(station_id) ON DELETE CASCADE,
    type TEXT NOT NULL CHECK (type IN ('AC','DC')),
    kw INTEGER NOT NULL,
    status TEXT NOT NULL CHECK (status IN ('available','charging','reserved','faulted')),
    start_success_rate REAL NOT NULL DEFAULT 0.9,
    soft_fault_rate REAL NOT NULL DEFAULT 0.0,
    mttr_h REAL NOT NULL DEFAULT 0.0,
    trust_badge TEXT NOT NULL CHECK (trust_badge IN ('A','B','C','D'))
);

-- Sessions table for charging sessions
CREATE TABLE IF NOT EXISTS sessions (
    session_id TEXT PRIMARY KEY,
    connector_id TEXT NOT NULL REFERENCES connectors(connector_id),
    user_id TEXT,
    start_ts TEXT,
    stop_ts TEXT,
    status TEXT NOT NULL CHECK (status IN ('pending','active','stopped','failed')),
    delivered_kwh REAL NOT NULL DEFAULT 0
);

-- Reservations table for charging slots
CREATE TABLE IF NOT EXISTS reservations (
    reservation_id TEXT PRIMARY KEY,
    station_id TEXT NOT NULL REFERENCES stations(station_id),
    connector_id TEXT NOT NULL REFERENCES connectors(connector_id),
    user_id TEXT,
    eta_min INTEGER NOT NULL,
    expires_at TEXT NOT NULL,
    promised_start_min INTEGER NOT NULL,
    state TEXT NOT NULL CHECK (state IN ('active','expired','cancelled','fulfilled'))
);

-- Partners table for nearby amenities/offers
CREATE TABLE IF NOT EXISTS partners (
    partner_id TEXT PRIMARY KEY,
    station_id TEXT NOT NULL REFERENCES stations(station_id),
    name TEXT NOT NULL,
    offer TEXT NOT NULL,
    lat REAL NOT NULL,
    lon REAL NOT NULL
);

-- Points ledger for user rewards/spending
CREATE TABLE IF NOT EXISTS points_ledger (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id TEXT NOT NULL,
    reason TEXT NOT NULL, -- e.g., 'report_fault', 'slot_resale', 'purchase'
    delta INTEGER NOT NULL, -- signed points change
    ts TEXT NOT NULL
);

-- Interventions log for system actions
CREATE TABLE IF NOT EXISTS interventions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ts TEXT NOT NULL,
    action TEXT NOT NULL, -- e.g., 'RESERVE', 'QUARANTINE'
    reason TEXT,
    station_id TEXT,
    connector_id TEXT,
    promised_start INTEGER,
    actual_start INTEGER
);

-- Indices for performance
CREATE INDEX IF NOT EXISTS idx_connectors_station ON connectors(station_id);
CREATE INDEX IF NOT EXISTS idx_reservations_station ON reservations(station_id);
CREATE INDEX IF NOT EXISTS idx_sessions_connector ON sessions(connector_id);
CREATE INDEX IF NOT EXISTS idx_interventions_ts ON interventions(ts);