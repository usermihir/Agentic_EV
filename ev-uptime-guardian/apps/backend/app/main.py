"""FastAPI application entrypoint."""

import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Import our modules using correct paths
import sys
import os

# Add project root to Python path
project_root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from apps.backend.app.seed import ensure_db_seeded

# Create FastAPI app
app = FastAPI(
    title="EV Uptime Guardian",
    version="0.1.0",
    description="Agentic EV charging station monitoring and planning"
)

# Configure CORS for development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Startup event to initialize database
@app.on_event("startup")
async def _startup():
    """Initialize and seed database on startup."""
    from apps.backend.app.seed import ensure_db_seeded
    ensure_db_seeded()

# Health check endpoint
@app.get("/healthz")
def healthz():
    """Health check endpoint."""
    return {"status": "ok"}

# Include routing tools
from apps.backend.app.tools.route import router as route_router
from apps.backend.app.tools.station import router as station_router
from apps.backend.app.operator.router import router as operator_router
from apps.backend.app.agent.router import router as agent_router

# Wire all routers
app.include_router(operator_router, prefix="")
app.include_router(route_router, prefix="")
app.include_router(station_router)
app.include_router(agent_router)
from apps.backend.app.tools.ocpp import router as ocpp_router
from apps.backend.app.tools.health import router as health_router
from apps.backend.app.tools.partners import router as partners_router
from apps.backend.app.tools.points import router as points_router
from apps.backend.app.tools.kpis import router as kpis_router

app.include_router(route_router, prefix="")
app.include_router(station_router)
app.include_router(ocpp_router)
app.include_router(health_router)
app.include_router(partners_router)
app.include_router(points_router)
app.include_router(kpis_router)