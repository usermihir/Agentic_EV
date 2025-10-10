"""Planner module integrating LangChain with Gemini or fallback LLM."""

import os
from pathlib import Path
from typing import Dict, Any
from tenacity import retry, stop_after_attempt

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.prompts import SystemMessagePromptTemplate

from app.agent.tools import AGENT_TOOLS
from app.agent.graph import build_graph, summarize_node
from app.models.schema import Plan
from app.utils.env import get_env_or_default

def load_prompt() -> str:
    """Load prompt template from file."""
    prompt_path = Path(__file__).parent / "prompt.txt"
    with open(prompt_path) as f:
        return f.read()

def get_gemini() -> ChatGoogleGenerativeAI:
    """Get Gemini model if configured."""
    api_key = get_env_or_default("GEMINI_API_KEY", None)
    if not api_key:
        return None
        
    return ChatGoogleGenerativeAI(
        model="gemini-pro",
        temperature=0.1,
        google_api_key=api_key
    )

def load_prompt() -> str:
    """Load system prompt from file."""
    prompt_path = Path(__file__).parent / "prompt.txt"
    with open(prompt_path) as f:
        return f.read()

@retry(stop=stop_after_attempt(2))
def run_plan(request_body: dict) -> dict:
    """Run the planning workflow with Gemini or deterministic fallback."""
    # Create graph
    workflow = build_graph(AGENT_TOOLS)
    
    # Initialize state
    state = {
        "input": request_body
    }
    
    # Configure Gemini for summaries if available
    llm = get_gemini()
    if llm:
        # Load prompt for summaries
        system_prompt = load_prompt()
        prompt = SystemMessagePromptTemplate.from_template(system_prompt)
        
        # Override summarize node to use Gemini
        def summarize_with_llm(state):
            try:
                response = llm.invoke(prompt.format() + "\n\nSummarize plan:\n" + str(state))
                summaries = response.content.split("\n")
                state["summary"] = {
                    "driver": summaries[0][:140],
                    "operator": summaries[1][:140] if len(summaries) > 1 else ""
                }
            except:
                # Fall back to deterministic on any error
                state = summarize_node(state)
            return state
            
        workflow.update_node("summarize", summarize_with_llm)
    
    # Execute graph
    for state in workflow.stream(state):
        pass
    
    # Validate and return plan
    return state["plan"]