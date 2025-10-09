"""Station search and wait time prediction tools."""

from fastapi import APIRouter, HTTPException, Query
from typing import List
from sqlalchemy.orm import Session

from apps.backend.app.db import SessionLocal
from apps.backend.app.models import Station, Connector
from apps.backend.app.utils.haversine import distance_km
from apps.backend.app.utils.constants import (
    AVG_SESSION_MIN_DC, 
    AVG_SESSION_MIN_AC, 
    TRUST_FACTOR
)
from apps.backend.app.utils.trustbadge import station_trust_badge

router = APIRouter(tags=["tools.station"])

def _all_stations() -> list[Station]:
    """Get all stations from database."""
    db = SessionLocal()
    try:
        return db.query(Station).all()
    finally:
        db.close()

@router.get("/tool/station/nearby")
async def search_nearby(
    lat: float = Query(..., title="Latitude"),
    lon: float = Query(..., title="Longitude"),
    limit: int = Query(5, title="Maximum stations to return")
) -> dict:
    """Find nearest charging stations to a location."""
    try:
        stations = _all_stations()
        
        # Calculate distances and sort
        station_distances = [
            {
                "station_id": station.station_id,
                "name": station.name,
                "lat": station.lat,
                "lon": station.lon,
                "distance_km": distance_km(lat, lon, station.lat, station.lon)
            }
            for station in stations
        ]
        
        # Sort by distance and limit results
        station_distances.sort(key=lambda s: s["distance_km"])
        station_distances = station_distances[:limit]
        
        return {"stations": station_distances}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/tool/station/predict")
async def predict_wait(
    station_id: str = Query(..., title="Station ID")
) -> dict:
    """Predict waiting time at a station."""
    db = SessionLocal()
    try:
        # Get station and its connectors
        station = db.query(Station).filter(Station.station_id == station_id).first()
        if not station:
            raise HTTPException(status_code=404, detail="Station not found")
            
        connectors = station.connectors
        if not connectors:
            return {
                "station_id": station_id,
                "p50_wait": 0,
                "p90_wait": 0,
                "free": 0,
                "trust_badge": "D"  # Most conservative when no data
            }
        
        # Count connector states
        active = sum(1 for c in connectors if c.status == 'charging')
        free = sum(1 for c in connectors if c.status == 'available')
        
        # Calculate load factor
        load_factor = max(0, active - free)
        
        # Calculate average session time based on connector types
        dc_count = sum(1 for c in connectors if c.type == 'DC')
        ac_count = len(connectors) - dc_count
        
        if dc_count + ac_count > 0:
            avg_session_min = (
                (dc_count * AVG_SESSION_MIN_DC + ac_count * AVG_SESSION_MIN_AC) / 
                (dc_count + ac_count)
            )
        else:
            avg_session_min = 0
            
        # Get station trust badge and factor
        trust_badge = station_trust_badge([c.trust_badge for c in connectors])
        trust_factor = TRUST_FACTOR.get(trust_badge, TRUST_FACTOR["D"])
        
        # Calculate wait times
        p50_wait = load_factor * avg_session_min * trust_factor
        p90_wait = 1.6 * p50_wait  # P90 multiplier per spec
        
        return {
            "station_id": station_id,
            "p50_wait": p50_wait,
            "p90_wait": p90_wait,
            "free": free,
            "trust_badge": trust_badge
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()