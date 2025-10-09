"""Haversine formula and related distance/time estimation utilities."""

import math
from datetime import datetime

def distance_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculate distance between two points using Haversine formula.
    
    Args:
        lat1: Latitude of first point
        lon1: Longitude of first point
        lat2: Latitude of second point
        lon2: Longitude of second point
        
    Returns:
        Distance in kilometers
    """
    R = 6371  # Earth radius in kilometers
    
    # Convert decimal degrees to radians
    lat1_rad = math.radians(lat1)
    lon1_rad = math.radians(lon1)
    lat2_rad = math.radians(lat2)
    lon2_rad = math.radians(lon2)
    
    # Differences in coordinates
    dlat = lat2_rad - lat1_rad
    dlon = lon2_rad - lon1_rad
    
    # Haversine formula
    a = math.sin(dlat/2)**2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlon/2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
    
    return R * c

def eta_minutes_from_speed(distance_km: float, speed_kmph: float, peak_fudge: bool = False) -> float:
    """Calculate ETA in minutes based on distance and speed, with optional peak-hour multiplier.
    
    Args:
        distance_km: Distance in kilometers
        speed_kmph: Average speed in km/h
        peak_fudge: Whether to apply peak hour multiplier
        
    Returns:
        Estimated time in minutes
    """
    # Base ETA
    minutes = distance_km / speed_kmph * 60.0
    
    # Apply peak hour multiplier if requested
    if peak_fudge:
        current_hour = datetime.now().hour
        if current_hour in range(8, 11) or current_hour in range(17, 21):
            minutes *= 1.15
            
    return minutes