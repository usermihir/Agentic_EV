#!/usr/bin/env python3
"""Initialize SQLite database from schema.sql"""

import argparse
import os
import sqlite3
from pathlib import Path

def init_db(db_path: str, schema_path: str) -> None:
    """Create SQLite database and apply schema.
    
    Args:
        db_path: Path to SQLite database file
        schema_path: Path to schema.sql file
    """
    # Ensure parent directory exists
    db_dir = os.path.dirname(os.path.abspath(db_path))
    os.makedirs(db_dir, exist_ok=True)
    
    # Read schema SQL
    with open(schema_path, 'r') as f:
        schema_sql = f.read()
    
    # Create/connect to database and apply schema
    with sqlite3.connect(db_path) as conn:
        # Split schema into individual statements
        statements = schema_sql.split(';')
        # Execute each statement (ignore empty ones)
        for stmt in statements:
            if stmt.strip():
                try:
                    conn.execute(stmt)
                except sqlite3.OperationalError as e:
                    # Ignore "table already exists" errors for idempotency
                    if not "already exists" in str(e):
                        raise
        conn.commit()

def main():
    parser = argparse.ArgumentParser(description='Initialize SQLite database from schema')
    parser.add_argument('--db', default='apps/backend/app/db/demo.sqlite3',
                      help='Path to SQLite database')
    parser.add_argument('--schema', default='apps/backend/app/db/schema.sql',
                      help='Path to schema.sql file')
    
    args = parser.parse_args()
    
    try:
        init_db(args.db, args.schema)
        print("OK: init_db")
        return 0
    except Exception as e:
        print(f"Error: {e}")
        return 1

if __name__ == '__main__':
    exit(main())