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
app.include_router(route_router, prefix="")