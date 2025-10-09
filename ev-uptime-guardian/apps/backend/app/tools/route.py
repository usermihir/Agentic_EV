"""Routing tools for finding nearby charging stations and estimating travel times."""

import math
from fastapi import APIRouter, HTTPException, Query
from typing import List, Tuple
from sqlalchemy.orm import Session

from apps.backend.app.db import SessionLocal
from apps.backend.app.models import Station
from apps.backend.app.utils.osrm_client import route_eta_minutes
from apps.backend.app.utils.haversine import distance_km
from apps.backend.app.utils.colorband import band_from_minutes
from apps.backend.app.config import SETTINGS

router = APIRouter(tags=["tools.route"])

def _all_stations() -> list[Station]:
    """Get all stations from database."""
    db = SessionLocal()
    try:
        return db.query(Station).all()
    finally:
        db.close()
        
def _project_distance_to_line_km(p: tuple[float, float], a: tuple[float, float], b: tuple[float, float]) -> float:
    """Calculate approximate distance from point to line segment using equirectangular projection.
    
    Args:
        p: (lat, lon) of point
        a: (lat, lon) of segment start
        b: (lat, lon) of segment end
    
    Returns:
        Approximate distance in kilometers
    """
    # Convert to radians
    lat_p, lon_p = map(math.radians, p)
    lat_a, lon_a = map(math.radians, a)
    lat_b, lon_b = map(math.radians, b)
    
    # Approximate coordinates in kilometers (equirectangular projection)
    R = 6371  # Earth radius in km
    x_p = R * lon_p * math.cos((lat_a + lat_b) / 2)
    y_p = R * lat_p
    x_a = R * lon_a * math.cos((lat_a + lat_b) / 2)
    y_a = R * lat_a
    x_b = R * lon_b * math.cos((lat_a + lat_b) / 2)
    y_b = R * lat_b
    
    # Point-to-line-segment math in 2D
    segment = ((x_b - x_a) * (x_b - x_a) + (y_b - y_a) * (y_b - y_a))
    
    if segment == 0:  # Degenerate segment
        return distance_km(p[0], p[1], a[0], a[1])
        
    t = max(0, min(1, ((x_p - x_a) * (x_b - x_a) + (y_p - y_a) * (y_b - y_a)) / segment))
    
    x_proj = x_a + t * (x_b - x_a)
    y_proj = y_a + t * (y_b - y_a)
    
    # Convert back to lat/lon and get distance
    lat_proj = math.degrees(y_proj / R)
    lon_proj = math.degrees(x_proj / (R * math.cos((lat_a + lat_b) / 2)))
    
    return distance_km(p[0], p[1], lat_proj, lon_proj)

@router.get("/tool/route/eta")
async def compute_eta(
    origin_lat: float = Query(..., title="Origin latitude"),
    origin_lon: float = Query(..., title="Origin longitude"),
    dest_lat: float = Query(..., title="Destination latitude"),
    dest_lon: float = Query(..., title="Destination longitude")
) -> dict:
    """Compute ETA and distance between two points."""
    try:
        return route_eta_minutes(
            (origin_lat, origin_lon),
            (dest_lat, dest_lon)
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/tool/route/corridor")
async def safe_corridor(
    origin_lat: float = Query(..., title="Origin latitude"),
    origin_lon: float = Query(..., title="Origin longitude"),
    dest_lat: float = Query(..., title="Destination latitude"),
    dest_lon: float = Query(..., title="Destination longitude")
) -> dict:
    """Find stations near the route between two points."""
    try:
        # Get all stations
        stations = _all_stations()
        
        # Filter stations by corridor width
        corridor_stations = []
        for station in stations:
            d_to_line = _project_distance_to_line_km(
                (station.lat, station.lon),
                (origin_lat, origin_lon),
                (dest_lat, dest_lon)
            )
            
            if d_to_line <= SETTINGS.CORRIDOR_WIDTH_KM:
                # Get ETA from origin to this station
                route = route_eta_minutes(
                    (origin_lat, origin_lon),
                    (station.lat, station.lon)
                )
                
                corridor_stations.append({
                    "station_id": station.station_id,
                    "eta_min": route["eta_min"],
                    "distance_km": route["distance_km"],
                    "color_band": band_from_minutes(route["eta_min"])
                })
        
        # Sort by ETA and limit results
        corridor_stations.sort(key=lambda s: s["eta_min"])
        corridor_stations = corridor_stations[:SETTINGS.CORRIDOR_TOPK]
        
        return {"stations": corridor_stations}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))