#!/usr/bin/env python3
"""Export SQLite database contents to JSON."""

import argparse
import json
import os
import sqlite3
from pathlib import Path
from typing import Dict, List

def row_to_dict(cursor: sqlite3.Cursor, row: sqlite3.Row) -> Dict:
    """Convert a database row to a dictionary."""
    return {col[0]: row[idx] for idx, col in enumerate(cursor.description)}

def dump_db(db_path: str, json_path: str) -> None:
    """Export all database tables to JSON file.
    
    Args:
        db_path: Path to SQLite database
        json_path: Output JSON file path
    """
    with sqlite3.connect(db_path) as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # Initialize output structure
        output = {
            'stations': [],
            'connectors': [],
            'partners': [],
            'sessions': [],
            'reservations': [],
            'points_ledger': [],
            'interventions': []
        }
        
        # Dump stations
        cursor.execute('SELECT * FROM stations')
        output['stations'] = [row_to_dict(cursor, row) for row in cursor.fetchall()]
        
        # Dump connectors
        cursor.execute('SELECT * FROM connectors')
        output['connectors'] = [row_to_dict(cursor, row) for row in cursor.fetchall()]
        
        # Dump partners
        cursor.execute('SELECT * FROM partners')
        output['partners'] = [row_to_dict(cursor, row) for row in cursor.fetchall()]
        
        # Dump sessions
        cursor.execute('SELECT * FROM sessions')
        output['sessions'] = [row_to_dict(cursor, row) for row in cursor.fetchall()]
        
        # Dump reservations
        cursor.execute('SELECT * FROM reservations')
        output['reservations'] = [row_to_dict(cursor, row) for row in cursor.fetchall()]
        
        # Dump points_ledger
        cursor.execute('SELECT * FROM points_ledger')
        output['points_ledger'] = [row_to_dict(cursor, row) for row in cursor.fetchall()]
        
        # Dump interventions
        cursor.execute('SELECT * FROM interventions')
        output['interventions'] = [row_to_dict(cursor, row) for row in cursor.fetchall()]
        
        # Write to JSON file
        os.makedirs(os.path.dirname(json_path), exist_ok=True)
        with open(json_path, 'w') as f:
            json.dump(output, f, indent=2)

def main():
    parser = argparse.ArgumentParser(description='Export database to JSON')
    parser.add_argument('--db', default='apps/backend/app/db/demo.sqlite3',
                      help='Path to SQLite database')
    parser.add_argument('--out', default='packages/common/mockData.json',
                      help='Output JSON file path')
    
    args = parser.parse_args()
    
    try:
        dump_db(args.db, args.out)
        print(f"OK: dump_db -> {args.out}")
    except Exception as e:
        print(f"Error: {e}")
        exit(1)

if __name__ == '__main__':
    main()