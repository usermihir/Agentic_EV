"""Database initialization and seeding."""

import os
from pathlib import Path
from apps.backend.app.config import SETTINGS
from apps.backend.app.db import rowcount
from apps.backend.app.db.scripts import init_db, seed_db

def ensure_db_seeded() -> None:
    """Ensure database exists and contains data."""
    # Get paths relative to DB path
    db_path = SETTINGS.DB_PATH
    schema_path = os.path.join(os.path.dirname(db_path), "schema.sql")
    seed_sql_path = os.path.join(os.path.dirname(db_path), "seed.sql")
    json_path = "packages/common/mockData.json"
    
    # Log actual database path
    print(f"DB_PATH: {Path(SETTINGS.DB_PATH).resolve()}")
    
    # Create parent directory if needed
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    
    try:
        # Initialize schema (idempotent)
        print("Initializing database schema...")
        init_db.init_db(db_path, schema_path)
        
        # Check if data needed
        if rowcount("stations") == 0:
            print("Database empty, seeding data...")
            try:
                if os.path.exists(json_path):
                    # Try JSON first
                    seed_db.seed_db(db_path=db_path, json_path=json_path)
                else:
                    # Fall back to SQL
                    seed_db.seed_db(db_path=db_path, sql_path=seed_sql_path)
            except Exception as e:
                print(f"Warning: seeding failed - {e}")
                return
        
        # Log table counts
        tables = ["stations", "connectors", "partners", "sessions", 
                  "reservations", "points_ledger", "interventions"]
        counts = {table: rowcount(table) for table in tables}
        print("DB ready:")
        for table, count in counts.items():
            print(f"  {table}: {count} rows")
            
    except Exception as e:
        print(f"Error in database setup: {e}")
        raise