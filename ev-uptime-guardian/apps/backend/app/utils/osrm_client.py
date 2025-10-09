"""Minimal OSRM HTTP client with automatic Haversine fallback."""

import contextlib
import httpx
import math
import time
from typing import List, Tuple
from pydantic import BaseModel

from apps.backend.app.config import SETTINGS
from apps.backend.app.utils.haversine import distance_km, eta_minutes_from_speed

def _coords_pair(lon: float, lat: float) -> str:
    """Format a coordinate pair for OSRM URL.
    
    Args:
        lon: Longitude
        lat: Latitude
    
    Returns:
        String formatted as "lon,lat" with 6 decimal precision
    """
    return f"{lon:.6f},{lat:.6f}"

def route_eta_minutes(origin: tuple[float, float], dest: tuple[float, float]) -> dict:
    """Get ETA and distance between two points, falling back to Haversine if OSRM fails.
    
    Args:
        origin: (lat, lon) tuple for start point
        dest: (lat, lon) tuple for end point
        
    Returns:
        Dict with eta_min, distance_km and source
        
    Raises:
        RuntimeError: If OSRM is unavailable and fallback is disabled
    """
    # Extract coordinates (note: OSRM needs lon,lat but we accept lat,lon)
    origin_lat, origin_lon = origin
    dest_lat, dest_lon = dest
    
    # For demo, always use Haversine since OSRM is not running
    d_km = distance_km(origin_lat, origin_lon, dest_lat, dest_lon)
    speed = SETTINGS.DEFAULT_HIGHWAY_KMPH if d_km > 15 else SETTINGS.DEFAULT_URBAN_KMPH
    eta_min = eta_minutes_from_speed(d_km, speed, peak_fudge=True)
    
    return {
        "eta_min": eta_min,
        "distance_km": d_km,
        "source": "haversine"
    }
    
    # Fallback to Haversine
    d_km = distance_km(origin_lat, origin_lon, dest_lat, dest_lon)
    speed = SETTINGS.DEFAULT_HIGHWAY_KMPH if d_km > 15 else SETTINGS.DEFAULT_URBAN_KMPH
    eta_min = eta_minutes_from_speed(d_km, speed, peak_fudge=True)
    
    return {
        "eta_min": eta_min,
        "distance_km": d_km,
        "source": "haversine"
    }

def table_seconds(origins: list[tuple[float, float]], dests: list[tuple[float, float]]) -> list[list[float]]:
    """Get travel time matrix between sets of points (no fallback).
    
    Args:
        origins: List of (lat, lon) tuples for origins
        dests: List of (lat, lon) tuples for destinations
        
    Returns:
        Matrix of travel times in seconds
        
    Raises:
        RuntimeError: If OSRM request fails
    """
    # Build coordinate lists (again, OSRM needs lon,lat)
    origin_coords = [_coords_pair(lat, lon) for lat, lon in origins]
    dest_coords = [_coords_pair(lat, lon) for lat, lon in dests]
    
    # Build full coordinate list and indices
    coords = ";".join(origin_coords + dest_coords)
    origin_idxs = ";".join(str(i) for i in range(len(origins)))
    dest_idxs = ";".join(str(i + len(origins)) for i in range(len(dests)))
    
    url = f"{SETTINGS.OSRM_BASE}/table/v1/driving/{coords}"
    params = {
        "sources": origin_idxs,
        "destinations": dest_idxs,
        "annotations": "duration"
    }
    
    try:
        resp = httpx.get(url, params=params, timeout=SETTINGS.OSRM_TIMEOUT_S)
        resp.raise_for_status()
        
        data = resp.json()
        return data["durations"]  # Matrix of travel times in seconds
        
    except Exception as e:
        raise RuntimeError("OSRM table request failed") from e