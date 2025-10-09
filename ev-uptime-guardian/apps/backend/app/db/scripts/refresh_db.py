#!/usr/bin/env python3
"""Refresh database from external data source (mock for now)."""

import argparse
import os
from seed_db import seed_from_json

def refresh_db(db_path: str, json_path: str) -> None:
    """Refresh database from mock data (future: Open Charge Map API).
    
    Args:
        db_path: Path to SQLite database
        json_path: Path to mock data JSON (temporary until OCM integration)
    """
    # TODO: Future enhancement - Fetch from Open Charge Map API
    # 1. Call OCM API to get nearby stations
    # 2. Transform response to match our schema
    # 3. Merge with existing station metadata (trust scores etc)
    # 4. Update database (similar to seed_from_json)
    
    # For now, just re-apply mock data if it exists
    if os.path.exists(json_path):
        seed_from_json(db_path, json_path)
    else:
        print("Warning: No mock data found - database unchanged")

def main():
    parser = argparse.ArgumentParser(description='Refresh database from external source')
    parser.add_argument('--db', default='apps/backend/app/db/demo.sqlite3',
                      help='Path to SQLite database')
    parser.add_argument('--json', default='packages/common/mockData.json',
                      help='Path to mock data JSON')
    
    args = parser.parse_args()
    
    try:
        refresh_db(args.db, args.json)
        print("OK: refresh_db")
    except Exception as e:
        print(f"Error: {e}")
        exit(1)

if __name__ == '__main__':
    main()