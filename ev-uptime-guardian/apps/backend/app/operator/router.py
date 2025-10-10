"""Operator-facing API endpoints."""

from fastapi import APIRouter, HTTPException, Query, Body
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta, timezone
from sqlalchemy import select, func, desc
import statistics
from pydantic import BaseModel

from app.db import SessionLocal
from app.models import Station, Connector, Intervention, Reservation, Session
from app.utils.constants import MIN_WAIT_FOR_PARTNER_MIN
from app.utils.trustbadge import station_trust_badge

router = APIRouter(tags=["operator"])

@router.get("/operator/overview")
async def get_overview() -> Dict[str, Any]:
    """Get operator dashboard overview metrics."""
    db = SessionLocal()
    try:
        # Get all stations and their connectors
        stations = db.query(Station).all()
        
        # Calculate uptime by station
        uptime_by_station = []
        buffer_status = []
        trust_leaderboard = []
        
        for station in stations:
            # Count connector statuses for uptime
            total_connectors = len(station.connectors)
            available_charging = sum(1 for c in station.connectors 
                                  if c.status in ['available', 'charging'])
            uptime = (available_charging / total_connectors) if total_connectors > 0 else 0
            
            uptime_by_station.append({
                "station_id": station.station_id,
                "uptime": uptime
            })
            
            # Get buffer status
            reserved_count = sum(1 for c in station.connectors 
                               if c.status == 'reserved')
            buffer_status.append({
                "station_id": station.station_id,
                "configured": station.emergency_buffer,
                "reserved_now": reserved_count
            })
            
            # Calculate trust badge counts
            badges = {c.trust_badge for c in station.connectors if c.trust_badge}
            trust_counts = {
                "A": sum(1 for b in badges if b == 'A'),
                "B": sum(1 for b in badges if b == 'B'),
                "C": sum(1 for b in badges if b == 'C'),
                "D": sum(1 for b in badges if b == 'D')
            }
            trust_leaderboard.append({
                "station_id": station.station_id,
                **trust_counts
            })
        
        # Get suspicious connectors for sniffer list
        window_start = datetime.now(timezone.utc) - timedelta(minutes=10)
        sniffer_list = []
        
        connectors = db.query(Connector).all()
        for connector in connectors:
            if connector.soft_fault_rate > 0.2:
                sniffer_list.append({
                    "connector_id": connector.connector_id,
                    "score": connector.soft_fault_rate,
                    "basis": "soft_fault>0.2"
                })
                continue
                
            # Count recent failures
            recent_failures = db.query(Session).filter(
                Session.connector_id == connector.connector_id,
                Session.status == 'failed',
                Session.end_time >= window_start
            ).count()
            
            if recent_failures >= 2:
                sniffer_list.append({
                    "connector_id": connector.connector_id,
                    "score": min(1.0, recent_failures / 2),
                    "basis": f"failed_sessions>={recent_failures}"
                })
        
        # Calculate reservation accuracy P90
        interventions = db.query(Intervention).filter(
            Intervention.promised_start.isnot(None),
            Intervention.actual_start.isnot(None)
        ).all()
        
        if interventions:
            differences = [
                abs(i.promised_start - i.actual_start)
                for i in interventions
            ]
            reservation_accuracy = statistics.quantiles(differences, n=10)[-1] if differences else 0
        else:
            reservation_accuracy = 0
            
        return {
            "uptime_by_station": uptime_by_station,
            "buffer_status": buffer_status,
            "sniffer_list": sniffer_list,
            "reservation_accuracy_p90": reservation_accuracy,
            "trust_leaderboard": trust_leaderboard
        }
        
    finally:
        db.close()

@router.get("/operator/interventions")
async def get_interventions(
    limit: int = Query(50, description="Maximum number of interventions to return"),
    station_id: Optional[str] = Query(None, description="Filter by station ID"),
    action: Optional[str] = Query(None, description="Filter by action type")
) -> List[Dict]:
    """Get recent interventions with optional filters."""
    db = SessionLocal()
    try:
        query = db.query(Intervention).order_by(desc(Intervention.ts))
        
        if station_id:
            query = query.filter(Intervention.station_id == station_id)
        if action:
            query = query.filter(Intervention.action == action)
            
        interventions = query.limit(limit).all()
        
        return [{
            "id": i.id,
            "ts": i.ts,
            "action": i.action,
            "reason": i.reason,
            "station_id": i.station_id,
            "connector_id": i.connector_id,
            "promised_start": i.promised_start,
            "actual_start": i.actual_start
        } for i in interventions]
        
    finally:
        db.close()

class QuarantineRequest(BaseModel):
    connector_id: str
    action: str  # QUARANTINE or UNQUARANTINE

@router.post("/operator/quarantine")
async def quarantine_connector(request: QuarantineRequest) -> Dict:
    """Quarantine or un-quarantine a connector."""
    if request.action not in ["QUARANTINE", "UNQUARANTINE"]:
        raise HTTPException(status_code=400, detail="Invalid action")
        
    db = SessionLocal()
    try:
        connector = db.query(Connector).filter(
            Connector.connector_id == request.connector_id
        ).first()
        
        if not connector:
            raise HTTPException(status_code=404, detail="Connector not found")
            
        if request.action == "QUARANTINE":
            if connector.status == "charging":
                raise HTTPException(
                    status_code=409,
                    detail="Cannot quarantine a charging connector"
                )
            connector.status = "faulted"
            
        else:  # UNQUARANTINE
            if connector.status in ["charging", "reserved"]:
                raise HTTPException(
                    status_code=409,
                    detail="Cannot mark operative while reserved/charging"
                )
            connector.status = "available"
        
        # Log intervention
        intervention = Intervention(
            ts=datetime.now(timezone.utc),
            action=request.action,
            station_id=connector.station_id,
            connector_id=connector.connector_id,
            reason="operator_action"
        )
        db.add(intervention)
        db.commit()
        
        return {
            "connector_id": connector.connector_id,
            "status": connector.status
        }
        
    finally:
        db.close()