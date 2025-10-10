"""LangChain StructuredTool wrappers around deterministic logic."""

from langchain.tools import StructuredTool
from pydantic import BaseModel, Field
from typing import List, Optional, Tuple, Dict, Any
from datetime import datetime, timezone, timedelta
import uuid

from app.db import SessionLocal
from app.models import Station, Connector, Reservation, Intervention, Session
from app.utils.osrm_client import route_eta_minutes
from app.utils.haversine import distance_km
from app.utils.colorband import band_from_minutes
from app.utils.constants import (
    AVG_SESSION_MIN_DC,
    AVG_SESSION_MIN_AC,
    TRUST_FACTOR,
    MIN_WAIT_FOR_PARTNER_MIN
)
from app.utils.trustbadge import station_trust_badge

def route_compute_eta(origin_lat: float, origin_lon: float, dest_lat: float, dest_lon: float) -> dict:
    """Compute ETA and distance between points."""
    try:
        # Try OSRM first
        eta_min = route_eta_minutes(origin_lat, origin_lon, dest_lat, dest_lon)
        source = "osrm"
    except:
        # Fallback to haversine
        dist = distance_km(origin_lat, origin_lon, dest_lat, dest_lon)
        eta_min = dist * 2  # Simple estimate: 30 km/h average
        source = "haversine"
    
    return {
        "eta_min": eta_min,
        "distance_km": distance_km(origin_lat, origin_lon, dest_lat, dest_lon),
        "source": source
    }

def station_search_nearby(lat: float, lon: float, limit: int = 6) -> List[dict]:
    """Find nearest stations to given coordinates."""
    db = SessionLocal()
    try:
        stations = db.query(Station).all()
        with_distance = [
            {
                "station_id": s.station_id,
                "name": s.name,
                "lat": s.lat,
                "lon": s.lon,
                "distance_km": distance_km(lat, lon, s.lat, s.lon)
            }
            for s in stations
        ]
        with_distance.sort(key=lambda x: x["distance_km"])
        return with_distance[:limit]
    finally:
        db.close()

def station_predict(station_id: str) -> dict:
    """Predict wait times for a station."""
    db = SessionLocal()
    try:
        station = db.query(Station).filter(Station.station_id == station_id).first()
        if not station:
            raise ValueError("Station not found")
            
        connectors = station.connectors
        
        # Count statuses
        active = sum(1 for c in connectors if c.status == 'charging')
        free = sum(1 for c in connectors if c.status == 'available')
        
        # Calculate load factor
        load_factor = max(0, active - free)
        
        # Calculate weighted average session time
        dc_count = sum(1 for c in connectors if c.connector_type == 'DC')
        ac_count = len(connectors) - dc_count
        
        if dc_count + ac_count == 0:
            avg_session_min = AVG_SESSION_MIN_DC
        else:
            avg_session_min = (
                (dc_count * AVG_SESSION_MIN_DC + ac_count * AVG_SESSION_MIN_AC) /
                (dc_count + ac_count)
            )
        
        # Get trust badge and factor
        trust_badge = station_trust_badge(connectors)
        trust_factor = TRUST_FACTOR.get(trust_badge, TRUST_FACTOR['D'])
        
        # Calculate wait times
        p50_wait = load_factor * avg_session_min * trust_factor
        p90_wait = 1.6 * p50_wait
        
        return {
            "station_id": station_id,
            "p50_wait": p50_wait,
            "p90_wait": p90_wait,
            "free": free,
            "trust_badge": trust_badge
        }
    finally:
        db.close()

def policy_decide_reserve(soc: float, eta_min: float, candidates: List[dict]) -> dict:
    """Make a reservation decision based on policy."""
    # Validate required fields
    required_fields = {"station_id", "p50_wait", "p90_wait", "free", "trust_badge"}
    for station in candidates:
        if not all(f in station for f in required_fields):
            raise ValueError(f"Station candidates must include fields: {required_fields}")
    
    # Check if any stations have free spots
    any_free = any(s["free"] > 0 for s in candidates)
    
    # Add expected start times and sort
    for station in candidates:
        station["expected_start"] = eta_min + station["p50_wait"]
    candidates.sort(
        key=lambda s: (s["expected_start"], {"A":1, "B":2, "C":3, "D":4}[s["trust_badge"]])
    )
    
    # Assess risk
    base_risk = 0.2  # Default low risk
    if soc < 10:
        base_risk = max(base_risk, 0.8)  # Critical battery
        
    # Target is first station after sorting
    target = candidates[0] if candidates else None
    if target:
        if target["expected_start"] > 25:
            base_risk = 1.0
        elif target["expected_start"] > 10:
            base_risk = max(base_risk, 0.5)
    
    should_reserve = (
        base_risk >= 0.7 or  # High risk situation
        not any_free  # No free spots available
    )
    
    if not should_reserve or not target:
        return {
            "decision": "NO",
            "reason": "Risk level acceptable" if not should_reserve else "No valid targets",
            "target": None,
            "promised_start_min": None
        }
    else:
        return {
            "decision": "YES",
            "reason": "Risk mitigation required" if base_risk >= 0.7 else "No free spots",
            "target": {"station_id": target["station_id"]},
            "promised_start_min": int(target["expected_start"])
        }

def ocpp_reserve_now(
    station_id: str,
    connector_id: Optional[str],
    promised_start_min: int,
    eta_min: int,
    user_id: str
) -> dict:
    """Create a reservation at a station."""
    db = SessionLocal()
    try:
        # Get station
        station = db.query(Station).filter(Station.station_id == station_id).first()
        if not station:
            raise ValueError("Station not found")
        
        # Find available connector
        if connector_id:
            connector = db.query(Connector).filter(
                Connector.connector_id == connector_id,
                Connector.status == 'available'
            ).first()
            if not connector:
                raise ValueError("Specified connector not available")
        else:
            connector = db.query(Connector).filter(
                Connector.station_id == station_id,
                Connector.status == 'available'
            ).first()
            if not connector:
                raise ValueError("No available connectors at station")
        
        # Create reservation
        reservation_id = str(uuid.uuid4())
        expires_at = datetime.now(timezone.utc) + timedelta(
            minutes=max(15, promised_start_min + 10)
        )
        
        reservation = Reservation(
            reservation_id=reservation_id,
            connector_id=connector.connector_id,
            user_id=user_id,
            state='active',
            expires_at=expires_at
        )
        
        # Update connector status
        connector.status = 'reserved'
        
        # Log intervention
        intervention = Intervention(
            ts=datetime.now(timezone.utc),
            action="RESERVE",
            reason="policy_decision",
            station_id=station_id,
            connector_id=connector.connector_id,
            promised_start=promised_start_min
        )
        
        db.add(reservation)
        db.add(intervention)
        db.commit()
        
        return {
            "reservation_id": reservation_id,
            "promised_start_min": promised_start_min,
            "connector_id": connector.connector_id
        }
        
    finally:
        db.close()

def partners_nearby(station_id: str, wait_min: int) -> List[dict]:
    """Get nearby partner offers if wait time is long enough."""
    if wait_min < MIN_WAIT_FOR_PARTNER_MIN:
        return []
        
    db = SessionLocal()
    try:
        station = db.query(Station).filter(Station.station_id == station_id).first()
        if not station:
            raise ValueError("Station not found")
            
        return [
            {
                "partner_id": p.partner_id,
                "name": p.name,
                "type": p.type,
                "distance_m": p.distance_m,
                "avg_duration_min": p.avg_duration_min
            }
            for p in station.partners
        ]
        
    finally:
        db.close()

# Create StructuredTool wrappers
AGENT_TOOLS = [
    StructuredTool.from_function(
        func=route_compute_eta,
        name="route_compute_eta",
        description="Compute ETA and distance between coordinates"
    ),
    StructuredTool.from_function(
        func=station_search_nearby,
        name="station_search_nearby",
        description="Find nearest stations to coordinates"
    ),
    StructuredTool.from_function(
        func=station_predict,
        name="station_predict",
        description="Predict wait times for a station"
    ),
    StructuredTool.from_function(
        func=policy_decide_reserve,
        name="policy_decide_reserve",
        description="Make reservation decision based on policy"
    ),
    StructuredTool.from_function(
        func=ocpp_reserve_now,
        name="ocpp_reserve_now",
        description="Create reservation at a station"
    ),
    StructuredTool.from_function(
        func=partners_nearby,
        name="partners_nearby",
        description="Get nearby partner offers"
    )
]