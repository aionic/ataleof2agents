# Unified Agent Package

This document describes the unified `src/agent/` package that enables the Weather-Based Clothing Advisor to run identically in both **Container Apps** and **Azure AI Foundry Hosted Agents** deployments.

## Package Structure

```
src/agent/
├── __init__.py              # Package root
├── main.py                  # Unified entry point
├── requirements.txt         # Python dependencies
├── core/
│   ├── __init__.py
│   ├── agent_service.py     # Core agent using Microsoft Agent Framework
│   ├── clothing_logic.py    # Business logic for recommendations
│   ├── constants.py         # Shared constants and thresholds
│   ├── models.py            # Data models (WeatherData, ClothingRecommendation, etc.)
│   └── workflow_orchestrator.py  # 4-step workflow execution
├── hosting/
│   ├── __init__.py
│   └── responses_server.py  # Foundry Responses API server (/responses endpoint)
├── tools/
│   ├── __init__.py
│   └── weather_tool.py      # Weather API tool implementation
└── telemetry/
    ├── __init__.py
    └── telemetry.py         # Application Insights integration
```

## Running the Agent

### Responses Mode (Foundry Compatible)

Exposes the `/responses` endpoint on port 8088, compatible with Azure AI Foundry Hosted Agents protocol.

```bash
# Run directly
python -m agent.main --mode responses --port 8088

# Or with Docker
docker build -f Dockerfile.agent -t weather-advisor:latest .
docker run -p 8088:8088 -e WEATHER_API_URL=http://weather-api:8080 weather-advisor:latest
```

### Legacy Mode (Container Apps)

Exposes the `/chat` endpoint on port 8000, compatible with the original Container Apps deployment.

```bash
# Run directly
python -m agent.main --mode legacy --port 8000

# Or with Docker
docker build -f Dockerfile.container-app -t weather-advisor:latest .
docker run -p 8000:8000 -e WEATHER_API_URL=http://weather-api:8080 weather-advisor:latest
```

### Interactive Mode (Testing)

For local testing without HTTP server:

```bash
python -m agent.main --mode interactive
```

## API Endpoints

### Responses API (Foundry Mode)

**POST /responses**

```json
{
  "messages": [
    {"role": "user", "content": "What should I wear in 10001?"}
  ],
  "conversation_id": "optional-session-id",
  "stream": false
}
```

Response:
```json
{
  "id": "resp-uuid",
  "object": "response",
  "choices": [{
    "index": 0,
    "message": {
      "role": "assistant",
      "content": "Based on the weather in New York..."
    },
    "finish_reason": "stop"
  }],
  "conversation_id": "session-id"
}
```

### Legacy API (Container Apps Mode)

**POST /chat**

```json
{
  "message": "What should I wear in 10001?",
  "session_id": "optional-session-id"
}
```

Response:
```json
{
  "response": "Based on the weather in New York...",
  "session_id": "session-id",
  "metadata": {
    "response_time": 1.23,
    "within_threshold": true
  }
}
```

## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `WEATHER_API_URL` | Yes | URL of the weather API service |
| `AZURE_FOUNDRY_ENDPOINT` | For agent | Azure AI Foundry endpoint |
| `AZURE_AI_MODEL_DEPLOYMENT_NAME` | For agent | Model deployment name (default: gpt-4) |
| `APPLICATIONINSIGHTS_CONNECTION_STRING` | No | Application Insights for telemetry |
| `LOG_LEVEL` | No | Logging level (default: INFO) |
| `ENVIRONMENT` | No | Deployment environment name |

## Deployment

### To Container Apps

```bash
# Build and deploy
cd deploy/container-app
./deploy.ps1 -ResourceGroupName my-rg -OpenWeatherMapApiKey <key>
```

### To Foundry Hosted Agents

```bash
# Build container
docker build -f Dockerfile.agent --target foundry -t myregistry.azurecr.io/weather-advisor:v1 .
docker push myregistry.azurecr.io/weather-advisor:v1

# Register with Foundry
python deploy/scripts/azure_agent_manager.py
```

## Testing

```bash
# Run all tests
pytest tests/test_unified_agent.py -v

# Run specific test class
pytest tests/test_unified_agent.py::TestClothingLogic -v

# With coverage
pytest tests/test_unified_agent.py --cov=agent --cov-report=html
```

## Migration from Legacy Code

The unified package replaces:

- `src/agent-container/` → `src/agent/core/` + `src/agent/hosting/`
- `src/shared/` → `src/agent/core/`
- `src/agent-foundry/` → `deploy/scripts/azure_agent_manager.py`

Import changes:
```python
# Old
from shared.constants import SC_001_RESPONSE_TIME_SECONDS
from shared.models import WeatherData

# New
from agent.core.constants import SC_001_RESPONSE_TIME_SECONDS
from agent.core.models import WeatherData
```
