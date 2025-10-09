-- Seed data for demo stations, connectors, and partners

-- Demo Stations
INSERT OR REPLACE INTO stations (station_id, name, lat, lon, emergency_buffer) VALUES
('ST001', 'Downtown Express Hub', 40.7128, -74.0060, 1),
('ST002', 'Midtown Rapid Station', 40.7589, -73.9851, 2),
('ST003', 'Uptown Quick Charge', 40.7829, -73.9654, 1);

-- Demo Connectors (2 per station)
INSERT OR REPLACE INTO connectors (connector_id, station_id, type, kw, status, start_success_rate, soft_fault_rate, mttr_h, trust_badge) VALUES
('CN001A', 'ST001', 'DC', 150, 'available', 0.98, 0.01, 2.0, 'A'),
('CN001B', 'ST001', 'AC', 22, 'available', 0.95, 0.02, 1.5, 'B'),
('CN002A', 'ST002', 'DC', 350, 'available', 0.99, 0.005, 1.0, 'A'),
('CN002B', 'ST002', 'DC', 150, 'available', 0.97, 0.015, 2.5, 'B'),
('CN003A', 'ST003', 'DC', 150, 'available', 0.96, 0.02, 2.0, 'B'),
('CN003B', 'ST003', 'AC', 43, 'available', 0.94, 0.03, 1.5, 'C');

-- Demo Partners (one per station)
INSERT OR REPLACE INTO partners (partner_id, station_id, name, offer, lat, lon) VALUES
('PT001', 'ST001', 'City Cafe', 'Free coffee during charging', 40.7129, -74.0061),
('PT002', 'ST002', 'Quick Mart', '10% off while you charge', 40.7590, -73.9852),
('PT003', 'ST003', 'Park & Charge', '2h free parking with charge', 40.7830, -73.9655);