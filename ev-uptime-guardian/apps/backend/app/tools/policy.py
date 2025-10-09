"""Policy tools for fairness, emergency buffer, and reservation decisions."""

from fastapi import APIRouter, HTTPException, Query
from typing import List, Dict
from datetime import datetime
from pydantic import BaseModel

from apps.backend.app.db import SessionLocal
from apps.backend.app.models import Station
from apps.backend.app.utils.colorband import band_from_minutes
from apps.backend.app.utils.constants import SOS_RISK_THRESHOLD

router = APIRouter(tags=["tools.policy"])

def buffer_size(station_id: str) -> dict:
    """Get emergency buffer size for a station."""
    db = SessionLocal()
    try:
        station = db.query(Station).filter(Station.station_id == station_id).first()
        if not station:
            raise HTTPException(status_code=404, detail="Station not found")
            
        return {
            "station_id": station_id,
            "emergency_buffer": station.emergency_buffer
        }
    finally:
        db.close()

def laxity_minutes(soc: float, eta_min: float, p50_wait: float) -> float:
    """Calculate slack time until critical battery level.
    
    Args:
        soc: State of charge (percent)
        eta_min: Travel time to station (minutes)
        p50_wait: Median wait time at station (minutes)
    
    Returns:
        Minutes of slack time (can be negative)
    """
    SOC_FLOOR = 8  # Minimum safe battery level
    DISCHARGE_RATE = 1.0  # Simple linear placeholder
    
    minutes_to_floor = (soc - SOC_FLOOR) / DISCHARGE_RATE
    return minutes_to_floor - (eta_min + p50_wait)

class ReserveRequest(BaseModel):
    """Request body for reserve decision."""
    soc: float
    eta_min: float
    candidates: List[Dict]  # List of station dicts with required fields

@router.post("/tool/policy/decideReserve")
async def decide_reserve(request: ReserveRequest) -> dict:
    """Decide whether to make a reservation and at which station."""
    # Validate candidates have required fields
    required_fields = {"station_id", "p50_wait", "p90_wait", "free", "trust_badge"}
    for station in request.candidates:
        if not all(f in station for f in required_fields):
            raise HTTPException(
                status_code=400, 
                detail=f"Station candidates must include fields: {required_fields}"
            )
    
    # Check if any stations have free spots
    any_free = any(s["free"] > 0 for s in request.candidates)
    
    # Calculate expected start times and sort by them
    for station in request.candidates:
        station["expected_start"] = request.eta_min + station["p50_wait"]
    
    # Sort by expected start time, breaking ties by trust badge
    request.candidates.sort(
        key=lambda s: (s["expected_start"], {"A":1, "B":2, "C":3, "D":4}.get(s["trust_badge"], 5))
    )
    
    # Assess risk factors
    base_risk = 0.2  # Default low risk
    if request.soc < 10:
        base_risk = max(base_risk, 0.8)  # Critical battery
        
    # Target is first station after sorting (best start time & badge)
    target = request.candidates[0] if request.candidates else None
    if target:
        # Increase risk based on expected wait
        if target["expected_start"] > 25:
            base_risk = 1.0
        elif target["expected_start"] > 10:
            base_risk = max(base_risk, 0.5)
    
    # Make decision
    should_reserve = (
        base_risk >= SOS_RISK_THRESHOLD or  # High risk situation
        not any_free  # No free spots available
    )
    
    # Build response
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
            "reason": "Risk mitigation required" if base_risk >= SOS_RISK_THRESHOLD else "No free spots",
            "target": {"station_id": target["station_id"]},
            "promised_start_min": int(target["expected_start"])
        }

@router.get("/tool/policy/buffer")
async def get_buffer(
    station_id: str = Query(..., title="Station ID")
) -> dict:
    """Get emergency buffer configuration for a station."""
    return buffer_size(station_id)