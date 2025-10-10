"""LangGraph state management and execution graph definition."""

from typing import TypedDict, List, Dict, Any, Optional
from langchain.tools import BaseTool, StructuredTool
from langgraph.prebuilt import ToolExecutor
from langgraph.graph import END, StateGraph

from app.agent.tools import AGENT_TOOLS
from app.models.schema import Plan
from app.utils.colorband import band_from_minutes

class State(TypedDict, total=False):
    """State tracked for agent execution."""
    input: Dict[str, Any]
    eta: Dict[str, Any]
    candidates: List[Dict[str, Any]]
    decision: Dict[str, Any]
    reservation: Dict[str, Any]
    summary: Dict[str, str]
    plan: Dict[str, Any]

# Define state schema
class AgentState(TypedDict):
    """State tracked for agent execution."""
    input: dict  # Original input from API
    plan: Plan   # Current plan being built
    steps: List[Dict[str, Any]]  # Executed steps and their outputs
    next_step: str  # Next action to take
    error: str  # Error if any occurred

# Graph node implementations
def plan_init(state: State) -> State:
    """Validate and initialize plan state."""
    input = state["input"]
    
    # Validate required fields
    required = ["origin_lat", "origin_lon", "dest_lat", "dest_lon", "soc"]
    for field in required:
        if field not in input:
            raise ValueError(f"Missing required field: {field}")
            
    # Clamp SOC to 0-100
    input["soc"] = max(0, min(100, input["soc"]))
    
    # Set default intent
    if "intent" not in input:
        input["intent"] = "PLAN"
        
    return state

def route_node(state: State) -> State:
    """Compute route ETA."""
    input = state["input"]
    tools = {t.name: t for t in AGENT_TOOLS}
    
    eta = tools["route_compute_eta"].invoke({
        "origin_lat": input["origin_lat"],
        "origin_lon": input["origin_lon"],
        "dest_lat": input["dest_lat"],
        "dest_lon": input["dest_lon"]
    })
    
    state["eta"] = eta
    return state

def predict_node(state: State) -> State:
    """Find and predict nearby stations."""
    input = state["input"]
    eta = state["eta"]
    tools = {t.name: t for t in AGENT_TOOLS}
    
    # Find nearby stations
    stations = tools["station_search_nearby"].invoke({
        "lat": input["origin_lat"],
        "lon": input["origin_lon"],
        "limit": 6
    })
    
    # Get predictions for each
    candidates = []
    for station in stations:
        prediction = tools["station_predict"].invoke({
            "station_id": station["station_id"]
        })
        
        # Compute expected start
        expected_start = eta["eta_min"] + prediction["p50_wait"]
        
        # Add to candidates with metadata
        candidates.append({
            **station,
            **prediction,
            "expected_start_min": expected_start,
            "color_band": band_from_minutes(expected_start)
        })
        
    # Sort by expected start time
    candidates.sort(key=lambda x: x["expected_start_min"])
    state["candidates"] = candidates
    return state

def policy_node(state: State) -> State:
    """Make reservation decision."""
    input = state["input"]
    eta = state["eta"]
    tools = {t.name: t for t in AGENT_TOOLS}
    
    decision = tools["policy_decide_reserve"].invoke({
        "soc": input["soc"],
        "eta_min": eta["eta_min"],
        "candidates": state["candidates"]
    })
    
    state["decision"] = decision
    return state

def act_node(state: State) -> State:
    """Execute reservation if needed."""
    if state["decision"]["decision"] != "YES":
        return state
        
    input = state["input"]
    decision = state["decision"]
    tools = {t.name: t for t in AGENT_TOOLS}
    
    reservation = tools["ocpp_reserve_now"].invoke({
        "station_id": decision["target"]["station_id"],
        "connector_id": None,  # Let it choose
        "promised_start_min": decision["promised_start_min"],
        "eta_min": state["eta"]["eta_min"],
        "user_id": input["user_id"]
    })
    
    state["reservation"] = reservation
    return state

def summarize_node(state: State) -> State:
    """Generate summaries."""
    # Deterministic summary (override in planner if using Gemini)
    station = next(s for s in state["candidates"] if s["station_id"] == state["decision"]["target"]["station_id"]) \
             if state["decision"]["decision"] == "YES" else state["candidates"][0]
             
    driver_msg = (
        f"Reserved {station['name']}, start in {station['p50_wait']}-{station['p90_wait']}min ({station['color_band']})" 
        if state["decision"]["decision"] == "YES"
        else f"Try {station['name']}, likely {station['p50_wait']}-{station['p90_wait']}min wait ({station['color_band']})"
    )
    
    operator_msg = (
        f"SOC {state['input']['soc']}%, ETA {state['eta']['eta_min']}min, "
        f"P50 wait {station['p50_wait']}min. {state['decision']['reason']}"
    )
    
    state["summary"] = {
        "driver": driver_msg[:140],
        "operator": operator_msg[:140]
    }
    return state

def build_plan_node(state: State) -> State:
    """Assemble final plan."""
    # Build steps
    steps = [
        {"tool": "route_compute_eta", "result": state["eta"]},
        {"tool": "station_predict", "result": state["candidates"]},
        {"tool": "policy_decide_reserve", "result": state["decision"]}
    ]
    if state["decision"]["decision"] == "YES":
        steps.append({
            "tool": "ocpp_reserve_now",
            "result": state["reservation"]
        })
        
    # Build actions
    actions = []
    if state["decision"]["decision"] == "YES":
        actions.append({
            "type": "RESERVE",
            "station_id": state["decision"]["target"]["station_id"],
            "reservation_id": state["reservation"]["reservation_id"],
            "promised_start_min": state["reservation"]["promised_start_min"]
        })
    else:
        actions.append({
            "type": "NONE",
            "reason": state["decision"]["reason"]
        })
        
    # Build plan
    state["plan"] = {
        "steps": steps,
        "actions": actions,
        "stations": state["candidates"][:4],
        "safe_corridor": [s["station_id"] for s in sorted(
            state["candidates"], 
            key=lambda x: x["expected_start_min"]
        )],
        "driver_summary": state["summary"]["driver"],
        "operator_rationale": state["summary"]["operator"]
    }
    
    return state

def validate_node(state: State) -> State:
    """Validate final plan."""
    plan = Plan.model_validate(state["plan"])
    state["plan"] = plan.model_dump()
    return state

def build_graph(tools: List[StructuredTool]) -> StateGraph:
    """Create the agent execution graph."""
    workflow = StateGraph(State)
    
    # Add nodes
    workflow.add_node("init", plan_init)
    workflow.add_node("route", route_node)
    workflow.add_node("predict", predict_node)
    workflow.add_node("policy", policy_node)
    workflow.add_node("act", act_node)
    workflow.add_node("summarize", summarize_node)
    workflow.add_node("build", build_plan_node)
    workflow.add_node("validate", validate_node)
    
    # Add edges
    workflow.add_edge("init", "route")
    workflow.add_edge("route", "predict")
    workflow.add_edge("predict", "policy")
    workflow.add_edge("policy", "act")
    workflow.add_edge("act", "summarize")
    workflow.add_edge("summarize", "build")
    workflow.add_edge("build", "validate")
    workflow.add_edge("validate", END)
    
    # Set entry point
    workflow.set_entry_point("init")
    
    return workflow