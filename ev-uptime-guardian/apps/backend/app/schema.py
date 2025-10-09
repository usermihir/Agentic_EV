"""Pydantic DTOs for API I/O."""

from typing import List, Literal, Optional
from pydantic import BaseModel, Field

# Enums
ConnectorType = Literal["AC", "DC"]
ConnectorStatus = Literal["available", "charging", "reserved", "faulted"]
TrustBadge = Literal["A", "B", "C", "D"]
ColorBand = Literal["green", "amber", "red"]
ReservationState = Literal["active", "expired", "cancelled", "fulfilled"]

# Base DTOs
class ConnectorDTO(BaseModel):
    connector_id: str
    type: ConnectorType
    kw: int
    status: ConnectorStatus
    trust_badge: TrustBadge
    start_success_rate: float
    soft_fault_rate: float
    mttr_h: float

class PartnerDTO(BaseModel):
    partner_id: str
    name: str
    offer: str
    lat: float
    lon: float

class StationDTO(BaseModel):
    station_id: str
    name: str
    lat: float
    lon: float
    emergency_buffer: int
    connectors: Optional[List[ConnectorDTO]] = None
    partners: Optional[List[PartnerDTO]] = None

# Planning DTOs
class StationPlanCard(BaseModel):
    station_id: str
    eta_min: int
    p50_wait: int
    p90_wait: int
    expected_start_min: int
    color_band: ColorBand
    trust_badge: TrustBadge
    connectors: Optional[List[ConnectorDTO]] = None
    safe_wait_partners: Optional[List[PartnerDTO]] = None

class PlanAction(BaseModel):
    type: Literal["RESERVE", "QUARANTINE", "SET_PROFILE", "NONE"]
    station_id: Optional[str] = None
    connector_id: Optional[str] = None
    reason: str
    promised_start_min: Optional[int] = None

class PlanStep(BaseModel):
    tool: str
    args: dict
    result: dict

class Plan(BaseModel):
    steps: List[PlanStep]
    actions: List[PlanAction]
    driver_summary: str
    operator_rationale: str
    stations: List[StationPlanCard]
    safe_corridor: List[str]