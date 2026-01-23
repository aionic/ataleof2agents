# Phase 2: Create Hosting Adapter

**Phase:** 2 of 7
**Status:** Not Started
**Estimated Effort:** 1-2 hours
**Depends On:** Phase 1

---

## Objective

Create the Foundry Responses API hosting adapter that exposes the `/responses` endpoint. This becomes the **primary entry point** for the agent, used by both Container Apps and Foundry Hosted deployments.

---

## Background

### What is the Hosting Adapter?

The **hosting adapter** (`azure-ai-agentserver-agentframework`) is Microsoft's framework that:
- Wraps your agent code
- Exposes the Foundry Responses API on port 8088
- Handles protocol translation between Foundry format ↔ Agent Framework format
- Provides built-in OpenTelemetry tracing, CORS, SSE streaming

### Foundry Responses API

```http
POST /responses
Content-Type: application/json

{
    "input": {
        "messages": [
            {
                "role": "user",
                "content": "What should I wear in 10001?"
            }
        ]
    }
}
```

Response:
```json
{
    "output": {
        "messages": [
            {
                "role": "assistant",
                "content": "Based on the current weather in New York (10001)..."
            }
        ]
    }
}
```

---

## Tasks

### Task 2.1: Create Weather Tool Module
**Status:** [ ] Not Started

Create `src/agent/tools/weather_tool.py`:

```python
"""
Weather API tool for the Clothing Advisor Agent.

Provides the get_weather function that can be registered with the Agent Framework.
"""

import os
import json
import logging
import requests
from typing import Annotated
from pydantic import Field

logger = logging.getLogger(__name__)


def get_weather(
    zip_code: Annotated[str, Field(description="5-digit US zip code (e.g., '10001', '90210')")]
) -> str:
    """
    Retrieve current weather data for a US zip code.

    Args:
        zip_code: 5-digit US zip code

    Returns:
        JSON string with weather data including temperature, conditions, humidity, wind speed
    """
    weather_api_url = os.getenv("WEATHER_API_URL")
    if not weather_api_url:
        return json.dumps({"error": "WEATHER_API_URL not configured"})

    try:
        # Call weather API
        url = f"{weather_api_url}/api/weather"
        response = requests.get(url, params={"zip_code": zip_code}, timeout=10)

        if response.status_code == 200:
            data = response.json()
            logger.info(f"Weather retrieved for {zip_code}: {data.get('temperature')}°F")
            return json.dumps(data)
        else:
            error_msg = f"Weather API returned {response.status_code}"
            logger.error(error_msg)
            return json.dumps({"error": error_msg})

    except requests.Timeout:
        logger.error(f"Weather API timeout for {zip_code}")
        return json.dumps({"error": "Weather API timeout"})
    except requests.RequestException as e:
        logger.error(f"Weather API error: {e}")
        return json.dumps({"error": str(e)})


# Export for agent registration
__all__ = ["get_weather"]
```

---

### Task 2.2: Create Responses Server
**Status:** [ ] Not Started

Create `src/agent/hosting/responses_server.py`:

```python
"""
Foundry Responses API Server.

This module creates a server that exposes the /responses endpoint,
compatible with both Container Apps and Foundry Hosted deployments.
"""

import os
import logging
from typing import Optional

# Agent Framework imports
from agent_framework import ChatAgent
from agent_framework.azure import AzureOpenAIChatClient
from azure.identity import DefaultAzureCredential

# Hosting adapter import
try:
    from azure.ai.agentserver.agentframework import from_agent_framework
    HOSTING_ADAPTER_AVAILABLE = True
except ImportError:
    HOSTING_ADAPTER_AVAILABLE = False
    logging.warning("Hosting adapter not available. Install: pip install azure-ai-agentserver-agentframework")

# Local imports
from agent.tools.weather_tool import get_weather

logger = logging.getLogger(__name__)


def load_agent_instructions() -> str:
    """Load agent instructions from contracts file."""
    contracts_path = os.path.join(
        os.path.dirname(__file__),
        '..', '..', '..',
        'specs', '001-weather-clothing-advisor', 'contracts', 'agent-prompts.md'
    )

    try:
        with open(contracts_path, 'r', encoding='utf-8') as f:
            return f.read()
    except FileNotFoundError:
        logger.warning(f"Instructions file not found: {contracts_path}")
        return get_fallback_instructions()


def get_fallback_instructions() -> str:
    """Provide fallback instructions if file not found."""
    return """You are a weather-based clothing advisor assistant.

When a user provides a zip code:
1. Use the get_weather tool to retrieve current weather conditions
2. Analyze the weather data (temperature, conditions, wind, precipitation)
3. Provide 3-5 specific clothing recommendations based on the weather
4. Organize recommendations by category (outerwear, layers, accessories, footwear)
5. Explain why each item is recommended

Be helpful, concise, and practical in your recommendations."""


def create_agent() -> ChatAgent:
    """
    Create and configure the Weather Clothing Advisor agent.

    Returns:
        Configured ChatAgent instance
    """
    # Get configuration from environment
    azure_endpoint = os.getenv("AZURE_FOUNDRY_ENDPOINT")
    deployment_name = os.getenv("AZURE_AI_MODEL_DEPLOYMENT_NAME", "gpt-4")

    if not azure_endpoint:
        raise ValueError("AZURE_FOUNDRY_ENDPOINT environment variable is required")

    logger.info(f"Creating agent with endpoint: {azure_endpoint}")
    logger.info(f"Using model deployment: {deployment_name}")

    # Load instructions
    instructions = load_agent_instructions()

    # Create chat client
    chat_client = AzureOpenAIChatClient(
        endpoint=azure_endpoint,
        deployment_name=deployment_name,
        credential=DefaultAzureCredential()
    )

    # Create agent with tools
    agent = ChatAgent(
        name="WeatherClothingAdvisor",
        instructions=instructions,
        chat_client=chat_client,
        tools=[get_weather]
    )

    logger.info("Agent created successfully with get_weather tool")
    return agent


def create_responses_server():
    """
    Create a Foundry Responses API server.

    Returns:
        Hosting adapter server instance
    """
    if not HOSTING_ADAPTER_AVAILABLE:
        raise RuntimeError(
            "Hosting adapter not available. "
            "Install: pip install azure-ai-agentserver-agentframework"
        )

    agent = create_agent()
    server = from_agent_framework(agent)

    logger.info("Responses server created - ready to serve on port 8088")
    return server


def main():
    """Entry point for running the Responses API server."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    logger.info("Starting Weather Clothing Advisor (Foundry Responses API)")
    logger.info("Endpoint: http://0.0.0.0:8088/responses")

    server = create_responses_server()
    server.run(host="0.0.0.0", port=8088)


if __name__ == "__main__":
    main()
```

---

### Task 2.3: Create Legacy FastAPI Wrapper (Optional)
**Status:** [ ] Not Started

Create `src/agent/hosting/legacy_fastapi.py` for backwards compatibility:

```python
"""
Legacy FastAPI server providing /chat endpoint.

This wraps the Responses API for backwards compatibility with existing clients.
Consider migrating clients to use /responses directly.
"""

import os
import logging
from typing import Optional, Dict, Any
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from agent.hosting.responses_server import create_agent

logger = logging.getLogger(__name__)

# Global agent instance
_agent = None


class ChatRequest(BaseModel):
    """Request model for legacy /chat endpoint."""
    message: str
    session_id: Optional[str] = None


class ChatResponse(BaseModel):
    """Response model for legacy /chat endpoint."""
    response: str
    session_id: str
    metadata: Optional[Dict[str, Any]] = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize agent on startup."""
    global _agent
    logger.info("Initializing agent for legacy FastAPI server...")
    _agent = create_agent()
    yield
    logger.info("Shutting down legacy FastAPI server...")


app = FastAPI(
    title="Weather Clothing Advisor (Legacy API)",
    description="Legacy /chat endpoint - consider migrating to /responses",
    version="2.0.0",
    lifespan=lifespan
)


@app.get("/health")
async def health():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "api": "legacy",
        "note": "Consider migrating to /responses endpoint"
    }


@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """
    Legacy chat endpoint.

    This endpoint wraps the agent for backwards compatibility.
    New integrations should use the /responses endpoint instead.
    """
    if _agent is None:
        raise HTTPException(status_code=503, detail="Agent not initialized")

    try:
        # Run agent
        result = await _agent.run(request.message)

        return ChatResponse(
            response=result.content if hasattr(result, 'content') else str(result),
            session_id=request.session_id or "default",
            metadata={"api_version": "legacy"}
        )
    except Exception as e:
        logger.error(f"Agent error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
```

---

## Validation Checklist

- [ ] `weather_tool.py` created and tested
- [ ] `responses_server.py` created
- [ ] Agent can be created with `create_agent()`
- [ ] Server starts on port 8088
- [ ] `/responses` endpoint accepts Foundry format
- [ ] (Optional) Legacy `/chat` endpoint works

---

## Testing Commands

```powershell
# Test responses endpoint locally
cd src/agent
python -m hosting.responses_server

# In another terminal
Invoke-RestMethod -Uri 'http://localhost:8088/responses' `
  -Method Post -ContentType 'application/json' `
  -Body '{"input": {"messages": [{"role": "user", "content": "What should I wear in 10001?"}]}}'
```

---

## Dependencies

- Phase 1 completed (source restructure)
- `azure-ai-agentserver-agentframework` package

---

## Next Phase

[Phase 3: Dockerfile & Dependencies](03-DOCKERFILE-DEPS.md)
