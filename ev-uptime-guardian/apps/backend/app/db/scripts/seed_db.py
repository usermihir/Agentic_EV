#!/usr/bin/env python3
"""Seed SQLite database with demo data from JSON or SQL."""

import argparse
import json
import os
import sqlite3
from pathlib import Path
from typing import Dict, List, Optional, Union

def seed_from_json(db_path: str, json_path: str) -> None:
    """Seed database from JSON file.
    
    Args:
        db_path: Path to SQLite database
        json_path: Path to JSON data file
    """
    # Read JSON data
    with open(json_path, 'r') as f:
        data = json.load(f)
    
    with sqlite3.connect(db_path) as conn:
        # Seed stations
        if 'stations' in data:
            for station in data['stations']:
                conn.execute(
                    'INSERT OR REPLACE INTO stations (station_id, name, lat, lon, emergency_buffer) VALUES (?, ?, ?, ?, ?)',
                    (station['station_id'], station['name'], station['lat'], station['lon'], 
                     station.get('emergency_buffer', 1))
                )
                
                # Seed associated connectors
                if 'connectors' in station:
                    for connector in station['connectors']:
                        conn.execute(
                            '''INSERT OR REPLACE INTO connectors 
                               (connector_id, station_id, type, kw, status, 
                                start_success_rate, soft_fault_rate, mttr_h, trust_badge)
                               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                            (connector['connector_id'], station['station_id'],
                             connector['type'], connector['kw'], connector['status'],
                             connector.get('start_success_rate', 0.9),
                             connector.get('soft_fault_rate', 0.0),
                             connector.get('mttr_h', 0.0),
                             connector.get('trust_badge', 'A'))
                        )
                
                # Seed associated partners
                if 'partners' in station:
                    for partner in station['partners']:
                        conn.execute(
                            'INSERT OR REPLACE INTO partners (partner_id, station_id, name, offer, lat, lon) VALUES (?, ?, ?, ?, ?, ?)',
                            (partner['partner_id'], station['station_id'],
                             partner['name'], partner['offer'], partner['lat'], partner['lon'])
                        )
        
        # Optional: seed sessions
        if 'sessions' in data:
            for session in data['sessions']:
                conn.execute(
                    '''INSERT OR REPLACE INTO sessions 
                       (session_id, connector_id, user_id, start_ts, stop_ts, status, delivered_kwh)
                       VALUES (?, ?, ?, ?, ?, ?, ?)''',
                    (session['session_id'], session['connector_id'],
                     session.get('user_id'), session.get('start_ts'),
                     session.get('stop_ts'), session['status'],
                     session.get('delivered_kwh', 0))
                )
        
        # Optional: seed reservations
        if 'reservations' in data:
            for res in data['reservations']:
                conn.execute(
                    '''INSERT OR REPLACE INTO reservations
                       (reservation_id, station_id, connector_id, user_id,
                        eta_min, expires_at, promised_start_min, state)
                       VALUES (?, ?, ?, ?, ?, ?, ?, ?)''',
                    (res['reservation_id'], res['station_id'],
                     res['connector_id'], res.get('user_id'),
                     res['eta_min'], res['expires_at'],
                     res['promised_start_min'], res['state'])
                )
        
        # Optional: seed points ledger
        if 'points_ledger' in data:
            for entry in data['points_ledger']:
                conn.execute(
                    'INSERT OR REPLACE INTO points_ledger (user_id, reason, delta, ts) VALUES (?, ?, ?, ?)',
                    (entry['user_id'], entry['reason'], entry['delta'], entry['ts'])
                )
        
        conn.commit()

def seed_from_sql(db_path: str, sql_path: str) -> None:
    """Seed database from SQL file.
    
    Args:
        db_path: Path to SQLite database
        sql_path: Path to seed SQL file
    """
    with open(sql_path, 'r') as f:
        seed_sql = f.read()
    
    with sqlite3.connect(db_path) as conn:
        # Split into statements and execute each
        statements = seed_sql.split(';')
        for stmt in statements:
            if stmt.strip():
                conn.execute(stmt)
        conn.commit()

def seed_db(db_path: str, json_path: str = None, sql_path: str = None) -> None:
    """Main seeding function that can be called programmatically."""
    if json_path and os.path.exists(json_path):
        seed_from_json(db_path, json_path)
    elif sql_path and os.path.exists(sql_path):
        seed_from_sql(db_path, sql_path)
    else:
        raise FileNotFoundError("Neither JSON nor SQL seed file found")

def main():
    """CLI entry point."""
    parser = argparse.ArgumentParser(description='Seed database with demo data')
    parser.add_argument('--db', default='apps/backend/app/db/demo.sqlite3',
                      help='Path to SQLite database')
    parser.add_argument('--json', default='packages/common/mockData.json',
                      help='Path to JSON mock data')
    parser.add_argument('--sql', default='apps/backend/app/db/seed.sql',
                      help='Path to seed SQL file (used if JSON not found)')
    
    try:
        # Only parse args when run as script
        args = parser.parse_args() if __name__ == '__main__' else None
        
        # Use default values when imported as module
        db_path = args.db if args else 'apps/backend/app/db/demo.sqlite3'
        json_path = args.json if args else 'packages/common/mockData.json'  
        sql_path = args.sql if args else 'apps/backend/app/db/seed.sql'
        
        seed_db(db_path, json_path, sql_path)
        print("OK: seed_db")
        return 0
    except Exception as e:
        print(f"Error: {e}")
        return 1

if __name__ == '__main__':
    exit(main())