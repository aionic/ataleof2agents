# Azure AI Foundry Deployment Guide

Deploy the Agent Framework reference implementation to Azure AI Foundry for managed, serverless agent execution.

---

## Overview

**What you're deploying**:
Azure AI Foundry provides two deployment patterns for agents:

### Pattern 1: Native Runtime Agent (Recommended)
Agent runs in Foundry's managed runtime with OpenAPI tools calling your external APIs.

### Pattern 2: External Agent Registration
Existing Container Apps agent registered as an OpenAPI tool in Foundry for hybrid orchestration.

**Why Foundry?**
- **Managed Service**: No infrastructure to maintain
- **Built-in Features**: Conversation threads, tool management, portal UI
- **Orchestration**: Native multi-agent and workflow support
- **Rapid Development**: Deploy in minutes without containers

---

## Prerequisites

### Required
- Azure AI Foundry project ([create one](https://ai.azure.com))
- Azure OpenAI deployment (gpt-4 or gpt-4o)
- Python 3.11+ with uv
- Azure CLI with authentication

### Optional (for Pattern 2)
- Container Apps agent already deployed
- External agent endpoint accessible

### Get Project Connection String

```powershell
# In Azure AI Foundry portal (https://ai.azure.com)
# Navigate to your project → Settings → Copy connection string

# Or via CLI
az ml workspace show `
  --name <project-name> `
  --resource-group <resource-group> `
  --query "discovery_url" `
  --output tsv
```

---

## Pattern 1: Native Runtime Agent

### What It Is

Agent runs entirely within Foundry's managed runtime. External APIs are called via OpenAPI tools.

```
User → Foundry Agent Runtime
         ↓
    OpenAPI Tool Invocation
         ↓
    External Weather API (Container Apps)
         ↓
    OpenWeatherMap
         ↓
    Agent Reasoning (Azure OpenAI)
         ↓
    Clothing Recommendations
```

### When to Use

✅ **Use this pattern when**:
- Building new agents
- Want managed service benefits
- Need Foundry portal features
- Don't want to manage containers

❌ **Don't use when**:
- Need fastest possible responses (Container Apps 2.3x faster)
- Have complex container orchestration
- Require custom infrastructure

### Step-by-Step Deployment

#### 1. Setup Environment

```powershell
# Clone repository
git clone <repo-url>
cd agentdemo

# Activate venv
.\.venv\Scripts\Activate.ps1

# Configure .env
cp .env.example .env
code .env
```

**Required in `.env`**:
```env
# Foundry connection (new SDK v2.0.0+ uses endpoint)
AZURE_AI_PROJECT_ENDPOINT=https://your-project.services.ai.azure.com/api/projects/your-project-name

# Model deployment name
AZURE_AI_MODEL_DEPLOYMENT_NAME=gpt-4.1

# Weather API endpoint (must be externally accessible)
WEATHER_API_URL=https://ca-weather-api-dev-<suffix>.azurecontainerapps.io

# Note: OpenAI config comes from Foundry project model deployment
```

#### 2. Enable External Ingress on Weather API

If your weather API is internal-only, enable external access:

```powershell
# Update weather API to allow external ingress
az containerapp ingress update `
  --name ca-weather-api-dev-<suffix> `
  --resource-group foundry `
  --target-port 8000 `
  --external true `
  --transport http

# Get new external URL
az containerapp show `
  --name ca-weather-api-dev-<suffix> `
  --resource-group foundry `
  --query "properties.configuration.ingress.fqdn" `
  --output tsv
```

#### 3. Review Agent Configuration

**File**: `src/agent-foundry/agent.yaml`

```yaml
name: WeatherClothingAdvisor
description: Provides clothing recommendations based on current weather

instructions: |
  You are a helpful clothing advisor.

  When user provides a location (zip code):
  1. Use the get_weather tool to retrieve current weather
  2. Analyze temperature, conditions, and precipitation
  3. Recommend appropriate clothing
  4. Be conversational and helpful

# Model config comes from Foundry project
model: gpt-4

# OpenAPI tool for weather API
tools:
  - type: openapi
    openapi:
      name: get_weather
      description: Get current weather for a US zip code
      spec: ../weather-api/openapi.json  # Reference to OpenAPI spec
      auth:
        type: anonymous  # Public endpoint
```

**Important**: The OpenAPI spec must be complete and valid. See `weather-api/openapi.json` for reference.

#### 4. Register Agent in Foundry

```powershell
# Navigate to deploy/foundry directory (scripts are here now)
cd deploy/foundry

# Register the agent
python register_agent.py register --agent-name WeatherClothingAdvisor

# Or list existing agents
python register_agent.py list
```

**What this does**:
1. Loads agent configuration from `agent.yaml`
2. Loads OpenAPI spec from referenced file
3. Creates agent in Foundry with OpenAPI tool
4. Returns agent ID

**Output**:
```
Loading OpenAPI spec from weather-api/openapi.json...
✓ Loaded OpenAPI spec

Creating agent in Foundry...
✓ Agent created successfully!

Agent ID: asst_52uP9hfMXCf2bKDIuSTBzZdz
Name: WeatherClothingAdvisor
Model: gpt-4
Tools: 1 (get_weather - OpenAPI)

✓ Registration complete
```

**Save the agent ID** - you'll need it for testing.

#### 5. Test Your Agent

```powershell
# Run test script
python test_agent.py
```

**Or test programmatically** (SDK v2.0.0+ with conversations/responses):

```python
from azure.ai.projects import AIProjectClient
from azure.identity import DefaultAzureCredential
import os

# Connect to Foundry (use endpoint, not connection string)
client = AIProjectClient(
    endpoint=os.getenv("AZURE_AI_PROJECT_ENDPOINT"),
    credential=DefaultAzureCredential()
)

# Get OpenAI client for conversations
openai = client.get_openai_client()

# Create conversation with initial message
conversation = openai.conversations.create(
    items=[{'type': 'message', 'role': 'user', 'content': 'What should I wear in 10001?'}]
)

# Invoke agent using agent_reference pattern
response = openai.responses.create(
    conversation=conversation.id,
    extra_body={'agent': {'name': 'WeatherClothingAdvisor', 'type': 'agent_reference'}},
    input='',
)

print(f"Agent: {response.output_text}")

# Cleanup
openai.conversations.delete(conversation_id=conversation.id)
```

**Expected response**:
```
Agent: Based on the current weather in New York (10001), it's 28°F and clear.
I recommend wearing a heavy insulated winter coat, thermal layers underneath,
warm hat and gloves, and waterproof boots to stay comfortable.
```

#### 6. View in Foundry Portal

1. Go to [Azure AI Foundry](https://ai.azure.com)
2. Navigate to your project
3. Click **Agents** in left menu
4. See your registered agent
5. Test in portal playground

---

## Pattern 2: External Agent Registration

### What It Is

Register your existing Container Apps agent as an OpenAPI tool in Foundry. Foundry becomes the orchestrator calling your self-hosted agent.

```
User → Foundry Meta-Agent
         ↓
    OpenAPI Tool (External Agent)
         ↓
    Container Apps Agent
         ↓
    Weather API → OpenWeatherMap
         ↓
    Response back through Foundry
```

### When to Use

✅ **Use this pattern when**:
- Already have Container Apps agent deployed
- Want Foundry orchestration without full migration
- Need hybrid deployment (both platforms)
- Testing migration strategy

❌ **Don't use when**:
- Starting fresh (use Pattern 1 instead)
- Don't need Foundry features
- Want simplest architecture

### Step-by-Step Deployment

#### 1. Prerequisites

Ensure your Container Apps agent is deployed and accessible:

```powershell
# Verify agent is running
curl https://ca-weather-dev-<suffix>.azurecontainerapps.io/health

# Test agent directly using /responses endpoint
curl -X POST https://ca-weather-dev-<suffix>.azurecontainerapps.io/responses `
  -H "Content-Type: application/json" `
  -d '{"input": "What should I wear in 10001?"}'
```

#### 2. Create OpenAPI Spec for External Agent

**File**: `src/agent-foundry/external-agent-openapi.json`

```json
{
  "openapi": "3.0.0",
  "info": {
    "title": "Weather Clothing Advisor Agent (Container Apps)",
    "version": "2.0.0",
    "description": "Container Apps-hosted agent using /responses endpoint"
  },
  "servers": [
    {
      "url": "https://ca-weather-dev-<suffix>.azurecontainerapps.io",
      "description": "Container Apps agent endpoint"
    }
  ],
  "paths": {
    "/responses": {
      "post": {
        "operationId": "getClothingRecommendations",
        "summary": "Get clothing recommendations from agent",
        "requestBody": {
          "required": true,
          "content": {
            "application/json": {
              "schema": {
                "type": "object",
                "properties": {
                  "input": {
                    "type": "string",
                    "description": "User message (e.g., 'What should I wear in 10001?')"
                  },
                  "conversation_id": {
                    "type": "string",
                    "description": "Optional conversation ID"
                  }
                },
                "required": ["input"]
              }
            }
          }
        },
        "responses": {
          "200": {
            "description": "Agent response",
            "content": {
              "application/json": {
                "schema": {
                  "type": "object",
                  "properties": {
                    "id": { "type": "string" },
                    "choices": {
                      "type": "array",
                      "items": {
                        "type": "object",
                        "properties": {
                          "message": {
                            "type": "object",
                            "properties": {
                              "role": { "type": "string" },
                              "content": { "type": "string" }
                            }
                          }
                        }
                      }
                    }
                  }
                }
              }
            }
          }
        }
      }
    }
  }
}
```

**Update the server URL** with your actual Container Apps agent endpoint.

#### 3. Configure Environment

```powershell
# Add to .env
EXTERNAL_AGENT_URL=https://ca-weather-dev-<suffix>.azurecontainerapps.io
```

#### 4. Register Meta-Agent

```powershell
cd deploy/foundry
python register_external_agent.py register --agent-name WeatherAdvisorMeta
```

**What this does**:
1. Loads external agent OpenAPI spec
2. Updates server URL from environment variable
3. Creates "meta-agent" in Foundry that invokes external agent
4. Returns meta-agent ID

**Output**:
```
Loading external agent OpenAPI spec...
✓ Loaded spec from external-agent-openapi.json

Updating server URL from environment...
✓ Server URL: https://ca-weather-dev-ezbvua.azurecontainerapps.io

Registering meta-agent in Foundry...
✓ Meta-agent created successfully!

Agent ID: asst_xy8at7THZ5PsaUHXykELNcDP
Name: ExternalAgentInvoker
Description: Invokes external Container Apps agent
Tool: chatWithExternalAgent (OpenAPI)

✓ Registration complete

Usage:
- Send messages to this agent in Foundry
- It will call your Container Apps agent
- Response comes back through Foundry
```

#### 5. Test External Agent Invocation

```powershell
# Test via SDK
python deploy/foundry/test_agent.py WeatherAdvisorMeta --message "What should I wear in 10001?"

# Or compare both agents
python deploy/foundry/compare_agents.py
```

**Result**: Foundry agent calls your Container Apps agent, returns response.

---

## Comparison: Pattern 1 vs Pattern 2

| Aspect | Pattern 1 (Native) | Pattern 2 (External) |
|--------|-------------------|---------------------|
| **Agent Runtime** | Foundry managed | Container Apps |
| **API Calls** | Direct from Foundry | Via Foundry meta-agent |
| **Setup Complexity** | Simpler | More complex |
| **Performance** | Slower (10.88s avg) | Faster (4.68s avg) |
| **Use Case** | New development | Existing agents |
| **Maintenance** | Microsoft manages | You manage containers |
| **Cost** | Higher at volume | Lower at volume |
| **Portability** | Foundry-specific | Works anywhere |

### Decision Guide

```
Do you have existing Container Apps agent?
├─ YES → Pattern 2 (External Registration)
│         Benefit: Keep container performance + add Foundry orchestration
│
└─ NO → Pattern 1 (Native Runtime)
          Benefit: Simpler, managed, no containers to maintain
```

---

## Code References

### Pattern 1 Files

```
src/agent-foundry/
├── agent.yaml                  # Agent configuration
├── register_agent.py           # Registration script
└── test_agent.py              # Test script

weather-api/
└── openapi.json               # OpenAPI spec for weather API
```

**Key Code** (`register_agent.py`) - SDK v2.0.0+ pattern:

```python
from azure.ai.projects.models import (
    PromptAgentDefinition,
    OpenApiAgentTool,
    OpenApiFunctionDefinition,
    OpenApiAnonymousAuthDetails,
)

def register_agent():
    # Load configuration
    agent_config = load_agent_config("agent.yaml")
    openapi_spec = load_openapi_spec("../weather-api/openapi.json")

    # Create tool definition using SDK models
    tool = OpenApiAgentTool(
        openapi=OpenApiFunctionDefinition(
            name="get_weather",
            description="Get current weather data",
            spec=openapi_spec,
            auth=OpenApiAnonymousAuthDetails(),
        )
    )

    # Create agent definition
    definition = PromptAgentDefinition(
        model=os.getenv("AZURE_AI_MODEL_DEPLOYMENT_NAME"),
        instructions=agent_config["instructions"],
        tools=[tool],
    )

    # Create agent using new SDK API
    agent = client.agents.create(
        name=agent_config["name"],
        definition=definition,
        description="Weather-based clothing advisor"
    )

    return agent.id
```

### Pattern 2 Files

```
src/agent-foundry/
├── external-agent-openapi.json     # External agent API spec
├── register_external_agent.py      # Meta-agent registration
└── test_external_agent.py         # Test script
```

**Key Code** (`register_external_agent.py`) - SDK v2.0.0+ pattern:

```python
from azure.ai.projects.models import (
    PromptAgentDefinition,
    OpenApiAgentTool,
    OpenApiFunctionDefinition,
    OpenApiAnonymousAuthDetails,
)

def register_meta_agent():
    # Load and update spec with actual URL
    spec = load_external_agent_spec("external-agent-openapi.json")
    spec["servers"][0]["url"] = os.getenv("EXTERNAL_AGENT_URL")

    # Create meta-agent tool using SDK models
    tool = OpenApiAgentTool(
        openapi=OpenApiFunctionDefinition(
            name="getClothingRecommendations",
            description="Invoke external Container Apps agent via /responses endpoint",
            spec=spec,
            auth=OpenApiAnonymousAuthDetails(),
        )
    )

    # Create agent definition
    definition = PromptAgentDefinition(
        model=os.getenv("AZURE_AI_MODEL_DEPLOYMENT_NAME"),
        instructions="You invoke an external agent. Forward user requests to the getClothingRecommendations tool.",
        tools=[tool],
    )

    # Create meta-agent using new SDK API
    agent = client.agents.create(
        name="WeatherAdvisorMeta",
        definition=definition,
        description="Meta-agent that invokes external Container Apps agent"
    )

    return agent.id
```

---

## Troubleshooting

### Issue: Agent registration fails with "auth type error"

**Error**: `Missing required parameter: 'tools[0].openapi.auth'`

**Cause**: Using `"type": "none"` instead of `"type": "anonymous"`

**Fix**:
```python
# ❌ Wrong
"auth": {"type": "none"}

# ✅ Correct
"auth": {"type": "anonymous"}
```

### Issue: OpenAPI tool call fails

**Check**:
1. Weather API has external ingress enabled
2. URL in OpenAPI spec is correct
3. Endpoint is accessible from internet

```powershell
# Test endpoint accessibility
curl https://ca-weather-api-dev-<suffix>.azurecontainerapps.io/api/weather?zip_code=10001
```

### Issue: Meta-agent doesn't call external agent

**Debug**:
1. Check meta-agent instructions tell it to use the tool
2. Verify external agent URL in environment variable
3. Test external agent directly first

```powershell
# Test external agent
curl -X POST https://ca-weather-dev-<suffix>.azurecontainerapps.io/chat `
  -H "Content-Type: application/json" `
  -d '{"message": "test"}'
```

### Issue: Slow response times

**Expected**: Foundry agents are slower than Container Apps (10.88s vs 4.68s average)

**Reasons**:
- SDK overhead (thread creation, polling)
- Network latency (Foundry → external API)
- Cold start on first request

**Optimization**:
- Reuse threads for conversations
- Cache weather data
- Consider Container Apps for high-volume

---

## Updating Your Agent

### Update Native Agent (Pattern 1)

```powershell
# 1. Modify agent.yaml or OpenAPI spec

# 2. Re-register (will update existing agent)
cd src/agent-foundry
python register_agent.py

# Or update via Portal
# Navigate to Agents → Select agent → Edit
```

### Update External Agent (Pattern 2)

```powershell
# Update Container Apps agent code
# (See Container Apps deployment guide)

# No Foundry changes needed unless API contract changes
# If API contract changes, update external-agent-openapi.json
```

---

## Monitoring

### Foundry Portal

1. Go to [Azure AI Foundry](https://ai.azure.com)
2. Navigate to your project
3. Click **Monitoring** → **Agent Runs**
4. Filter by agent ID
5. View:
   - Request/response history
   - Tool invocations
   - Error logs
   - Performance metrics

### Application Insights (Pattern 2 only)

For external agents, also check Container Apps monitoring:

```powershell
# View logs
az containerapp logs show `
  --name ca-weather-dev-<suffix> `
  --resource-group foundry `
  --tail 100
```

---

## Cost Considerations

### Pattern 1 (Native)

**Costs**:
- Azure OpenAI token usage (input + output)
- Foundry compute (managed, included with workspace)
- External API calls (weather API hosting)

**Optimization**:
- Use GPT-3.5 for simpler queries
- Implement caching for repeated zip codes
- Batch requests when possible

### Pattern 2 (External)

**Costs**:
- Azure OpenAI token usage (meta-agent)
- Container Apps hosting (external agent)
- Foundry compute (minimal, just orchestration)

**Optimization**:
- Scale Container Apps to zero when idle
- Use consumption plan
- Bypass Foundry for simple cases (call Container Apps directly)

---

## Next Steps

### Compare with Container Apps
See performance and cost differences:
👉 **[Container Apps Deployment Guide](./DEPLOYMENT-CONTAINER-APPS.md)**

### Port Between Platforms
Learn migration strategies:
👉 **[Porting Guide](./PORTING-GUIDE.md)**

### Advanced Orchestration
Multi-agent patterns and workflows:
👉 **[Workflow Patterns](./WORKFLOW-ORCHESTRATION-PATTERNS.md)**

---

## Reference

### SDK Documentation
- [Azure AI Projects Python SDK](https://learn.microsoft.com/python/api/azure-ai-projects/)
- [Agent Service API](https://learn.microsoft.com/azure/ai-foundry/agents/)
- [OpenAPI Tools](https://learn.microsoft.com/azure/ai-foundry/agents/how-to/tools-classic/openapi-spec)

### Related Files
- **Agent config**: `src/agent-foundry/agent.yaml`
- **Registration**: `src/agent-foundry/register_agent.py`
- **Test script**: `src/agent-foundry/test_agent.py`
- **OpenAPI spec**: `weather-api/openapi.json`

---

**Deployment complete!** Your agent is now running in Azure AI Foundry with managed infrastructure and built-in orchestration capabilities.
