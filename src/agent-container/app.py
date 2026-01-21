"""
FastAPI server for the Weather-Based Clothing Advisor agent.

This server provides HTTP endpoints for interacting with the Azure Agent Framework
agent using a workflow orchestration pattern for Container Apps deployment.
"""

import os
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional, Dict, Any
import sys

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from agent_service import AgentService
from workflow_orchestrator import WorkflowOrchestrator

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize services
agent_service = None
workflow_orchestrator = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize and cleanup agent service and workflow orchestrator."""
    global agent_service, workflow_orchestrator
    logger.info("Initializing agent service with workflow orchestration...")
    agent_service = AgentService()
    workflow_orchestrator = WorkflowOrchestrator(agent_service)
    logger.info("Workflow orchestrator initialized successfully")
    yield
    logger.info("Shutting down services...")


# Create FastAPI app
app = FastAPI(
    title="Weather-Based Clothing Advisor (Container Apps - Workflow Pattern)",
    description="AI agent with workflow orchestration for weather information and clothing recommendations",
    version="1.0.0",
    lifespan=lifespan
)


# Request/Response models
class ChatRequest(BaseModel):
    """Request model for chat endpoint."""
    message: str
    session_id: Optional[str] = None


class ChatResponse(BaseModel):
    """Response model for chat endpoint."""
    response: str
    session_id: str
    metadata: Optional[Dict[str, Any]] = None


@app.get("/")
async def root():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "weather-clothing-advisor",
        "deployment": "container-app"
    }


@app.get("/health")
async def health():
    """Detailed health check."""
    return {
        "status": "healthy",
        "agent": "initialized" if agent_service else "not initialized",
        "deployment": "container-app"
    }


@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """
    Chat with the weather clothing advisor agent using workflow orchestration.

    This endpoint executes a 4-step workflow:
    1. Parse user input (extract zip code)
    2. Get weather data (call weather function tool)
    3. Generate recommendations (AI reasoning)
    4. Format response (conversational output)

    Args:
        request: ChatRequest with message and optional session_id

    Returns:
        ChatResponse with agent's response, session_id, and workflow metadata

    Raises:
        HTTPException: If services are not initialized or workflow execution fails
    """
    if not agent_service or not workflow_orchestrator:
        logger.error("Services not initialized")
        raise HTTPException(status_code=503, detail="Services not available")

    try:
        logger.info(f"Processing chat request via workflow: {request.message[:50]}...")

        # Execute workflow
        workflow_result = await workflow_orchestrator.execute_workflow(
            message=request.message,
            session_id=request.session_id
        )

        logger.info(
            f"Workflow completed for session {workflow_result['session_id']} "
            f"(workflow_id: {workflow_result.get('metadata', {}).get('workflow_id', 'unknown')}, "
            f"duration: {workflow_result.get('metadata', {}).get('workflow_duration', 0):.2f}s)"
        )

        return ChatResponse(
            response=workflow_result["response"],
            session_id=workflow_result["session_id"],
            metadata=workflow_result.get("metadata", {})
        )

    except Exception as e:
        logger.exception("Error processing chat request")
        raise HTTPException(
            status_code=500,
            detail=f"Error processing request: {str(e)}"
        )


@app.post("/reset")
async def reset_session(session_id: str):
    """
    Reset a conversation session.

    Args:
        session_id: Session ID to reset

    Returns:
        Confirmation message
    """
    if not agent_service:
        raise HTTPException(status_code=503, detail="Agent service not available")

    try:
        agent_service.reset_session(session_id)
        logger.info(f"Reset session: {session_id}")
        return {"status": "success", "message": f"Session {session_id} reset"}
    except Exception as e:
        logger.exception(f"Error resetting session {session_id}")
        raise HTTPException(
            status_code=500,
            detail=f"Error resetting session: {str(e)}"
        )


if __name__ == "__main__":
    import uvicorn

    port = int(os.getenv("PORT", "8000"))
    uvicorn.run(
        "app:app",
        host="0.0.0.0",
        port=port,
        log_level="info",
        reload=False
    )
