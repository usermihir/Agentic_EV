"""FastAPI router for agent endpoints."""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.agent.graph import create_graph, AgentState
from app.models.schema import Plan

router = APIRouter(prefix="/agent")

class PlanRequest(BaseModel):
    """Request model for plan generation."""
    soc: float = Field(..., description="Current state of charge (0-100)")
    lat: float = Field(..., description="Current latitude")
    lon: float = Field(..., description="Current longitude")
    user_id: str = Field(..., description="User requesting the plan")

@router.post("/plan", response_model=Plan)
async def create_plan(request: PlanRequest) -> Plan:
    """Generate a plan for the given request."""
    try:
        # Create workflow
        workflow = create_graph()
        
        # Initialize state
        initial_state = AgentState(
            input=request.dict(),
            plan=Plan(actions=[], results={}, error=""),
            steps=[],
            next_step="generate_plan",
            error=""
        )
        
        # Execute workflow
        for state in workflow.stream(initial_state):
            # Can log state transitions here if needed
            pass
            
        final_state = state
        
        # Return plan from final state
        return final_state["plan"]
        
    except Exception as e:
        # Log error
        print(f"Error in plan creation: {str(e)}")
        
        # Return error plan
        return Plan(
            actions=[],
            results={},
            error=f"Failed to generate plan: {str(e)}"
        )