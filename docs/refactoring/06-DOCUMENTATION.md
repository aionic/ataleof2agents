# Phase 6: Update Documentation

**Phase:** 6 of 7
**Status:** Not Started
**Estimated Effort:** 1 hour
**Depends On:** Phase 5

---

## Objective

Update all documentation to reflect the unified architecture with three deployment methods sharing a single codebase.

---

## Tasks

### Task 6.1: Update Root README.md
**Status:** [ ] Not Started

Rewrite `README.md` to reflect the unified architecture:

```markdown
# Weather Clothing Advisor Agent

A reference implementation demonstrating how to build an AI agent that runs
**identically** in both Azure Container Apps and Azure AI Foundry.

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Single Agent Image                        │
│            Foundry Responses API (/responses)               │
│                      Port 8088                               │
└─────────────────────────┬───────────────────────────────────┘
                          │
            ┌─────────────┼─────────────┐
            │             │             │
            ▼             ▼             ▼
     ┌──────────┐  ┌──────────┐  ┌──────────┐
     │Container │  │ Foundry  │  │ Foundry  │
     │  Apps    │  │ Hosted   │  │ Native   │
     │(Self-    │  │(Managed) │  │(Legacy)  │
     │ hosted)  │  │          │  │          │
     └──────────┘  └──────────┘  └──────────┘
```

## Quick Start

### Option 1: Container Apps (Self-Hosted)
```bash
cd deploy/container-apps
./deploy.ps1 -ResourceGroupName mygroup -OpenWeatherMapApiKey <key>
```

### Option 2: Foundry Hosted (Managed)
```bash
cd deploy/foundry-hosted
./deploy.ps1 -ContainerRegistry myacr -AgentName WeatherAdvisor
```

## API

All deployments expose the **Foundry Responses API**:

```http
POST /responses
Content-Type: application/json

{
  "input": {
    "messages": [
      {"role": "user", "content": "What should I wear in 10001?"}
    ]
  }
}
```

## Documentation

- [Container Apps Deployment](docs/guides/DEPLOYMENT-CONTAINER-APPS.md)
- [Foundry Hosted Deployment](docs/guides/DEPLOYMENT-FOUNDRY-HOSTED.md)
- [Architecture Overview](docs/architecture/UNIFIED-ARCHITECTURE.md)
```

---

### Task 6.2: Update DEPLOYMENT.md
**Status:** [ ] Not Started

Simplify `DEPLOYMENT.md`:

```markdown
# Deployment Guide

The Weather Clothing Advisor uses a **unified container image** that works
in multiple deployment environments.

## Deployment Methods

| Method | Who Manages | Best For | Guide |
|--------|-------------|----------|-------|
| Container Apps | You | High volume, full control | [Guide](docs/guides/DEPLOYMENT-CONTAINER-APPS.md) |
| Foundry Hosted | Azure | Managed, auto-scaling | [Guide](docs/guides/DEPLOYMENT-FOUNDRY-HOSTED.md) |

## Quick Comparison

| Aspect | Container Apps | Foundry Hosted |
|--------|---------------|----------------|
| Container | Same | Same |
| Port | 8088 | 8088 |
| Endpoint | /responses | /responses |
| Scaling | Manual/KEDA | Automatic |
| Cost Model | Per-resource | Per-use |

## Prerequisites

```bash
# Required tools
az --version      # Azure CLI 2.50+
docker --version  # Docker 20.10+
python --version  # Python 3.11+

# Login
az login
```

## Build Once, Deploy Anywhere

```bash
# Build the unified image
docker build -t myacr.azurecr.io/weather-advisor:v1 .
docker push myacr.azurecr.io/weather-advisor:v1

# Deploy to Container Apps
cd deploy/container-apps && ./deploy.ps1 -SkipBuild ...

# OR Deploy to Foundry Hosted
cd deploy/foundry-hosted && ./deploy.ps1 -SkipBuild ...
```
```

---

### Task 6.3: Create DEPLOYMENT-FOUNDRY-HOSTED.md
**Status:** [ ] Not Started

Create `docs/guides/DEPLOYMENT-FOUNDRY-HOSTED.md`:

```markdown
# Foundry Hosted Deployment Guide

Deploy the Weather Clothing Advisor as an **Azure AI Foundry Hosted Agent**.
Azure manages the container hosting, scaling, and infrastructure.

## Prerequisites

1. **Azure AI Foundry Project** with Capability Host enabled
2. **Azure Container Registry** with your image
3. **Azure CLI** authenticated

### Enable Capability Host

```powershell
cd deploy/shared
./Invoke-AzureCapabilityHost.ps1
# Select: 1=List (check existing)
# Select: 2=Enable (if needed)
```

## Deployment Steps

### 1. Build and Push Image

```bash
# Build
docker build -t myacr.azurecr.io/weather-advisor:v1 .

# Login to ACR
az acr login --name myacr

# Push
docker push myacr.azurecr.io/weather-advisor:v1
```

### 2. Deploy to Foundry

```powershell
cd deploy/foundry-hosted
./deploy.ps1 -ContainerRegistry myacr -AgentName WeatherClothingAdvisor
```

Or use the Python script directly:

```bash
export AZURE_AI_PROJECT_ENDPOINT=https://your-project.azure.com
export AGENT_NAME=WeatherClothingAdvisor
export AGENT_IMAGE=myacr.azurecr.io/weather-advisor:v1

python deploy/shared/azure_agent_manager.py
```

### 3. Test

Use the Azure AI Foundry portal playground, or call via API:

```bash
curl -X POST https://your-project.azure.com/agents/{agent-id}/responses \
  -H "Authorization: Bearer $(az account get-access-token --query accessToken -o tsv)" \
  -H "Content-Type: application/json" \
  -d '{"input": {"messages": [{"role": "user", "content": "What should I wear in 10001?"}]}}'
```

## How It Works

1. You push your container image to ACR
2. Foundry pulls and hosts your container
3. Requests are routed to your agent's `/responses` endpoint
4. Same code, managed by Azure

## Comparison with Container Apps

| Aspect | Foundry Hosted | Container Apps |
|--------|----------------|----------------|
| Infrastructure | Azure manages | You manage |
| Scaling | Automatic | KEDA/manual |
| Networking | Managed | VNet integration |
| Cost | Per-request | Per-resource |
| Portal | Foundry playground | Azure Portal |
```

---

### Task 6.4: Update Architecture Docs
**Status:** [ ] Not Started

Create `docs/architecture/UNIFIED-ARCHITECTURE.md`:

```markdown
# Unified Architecture

This document describes the unified architecture that enables the same
agent code to run in both Container Apps and Foundry Hosted environments.

## Design Principles

1. **Single Codebase**: One set of Python files for all deployments
2. **Single Image**: One Docker image works everywhere
3. **Standard API**: Foundry Responses API (`/responses`) as primary endpoint
4. **Hosting Adapter**: Microsoft's adapter bridges Agent Framework to Foundry protocol

## Component Diagram

```
┌────────────────────────────────────────────────────────────────┐
│                        Docker Image                             │
├────────────────────────────────────────────────────────────────┤
│                                                                │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │                  Hosting Adapter                          │  │
│  │        azure-ai-agentserver-agentframework               │  │
│  │                                                          │  │
│  │  • Exposes /responses endpoint                           │  │
│  │  • Handles Foundry protocol                              │  │
│  │  • OpenTelemetry integration                             │  │
│  │  • SSE streaming support                                 │  │
│  └────────────────────────┬─────────────────────────────────┘  │
│                           │                                    │
│  ┌────────────────────────▼─────────────────────────────────┐  │
│  │                   Agent Framework                         │  │
│  │               ChatAgent + Tools                          │  │
│  │                                                          │  │
│  │  ┌─────────────────┐  ┌─────────────────┐               │  │
│  │  │ agent_service   │  │ clothing_logic  │               │  │
│  │  │                 │  │                 │               │  │
│  │  │ - Instructions  │  │ - Temp ranges   │               │  │
│  │  │ - Tool binding  │  │ - Wind checks   │               │  │
│  │  │ - Session mgmt  │  │ - Rain logic    │               │  │
│  │  └─────────────────┘  └─────────────────┘               │  │
│  │                                                          │  │
│  │  ┌─────────────────┐                                     │  │
│  │  │ weather_tool    │─────► Weather API (external)       │  │
│  │  │ - get_weather() │                                     │  │
│  │  └─────────────────┘                                     │  │
│  └──────────────────────────────────────────────────────────┘  │
│                                                                │
└────────────────────────────────────────────────────────────────┘
```

## Request Flow

1. Client sends POST to `/responses`
2. Hosting adapter receives and parses Foundry protocol
3. Adapter calls `agent.run(message)`
4. Agent uses `get_weather` tool to fetch weather data
5. Agent generates clothing recommendations
6. Adapter formats response in Foundry protocol
7. Response returned to client

## File Structure

```
src/agent/
├── core/                    # Business logic
│   ├── agent_service.py     # Agent lifecycle
│   ├── clothing_logic.py    # Recommendation engine
│   ├── models.py            # Data models
│   └── constants.py         # Configuration
├── hosting/
│   └── responses_server.py  # Entry point
├── tools/
│   └── weather_tool.py      # Weather API integration
└── telemetry/
    └── telemetry.py         # Observability
```

## Why This Architecture?

### Before (Fragmented)
- Different code for Container Apps vs Foundry
- Different endpoints (/chat vs Foundry threads)
- Different deployment scripts
- Hard to maintain consistency

### After (Unified)
- Same code everywhere
- Same endpoint (/responses)
- Same Docker image
- Easy to maintain and test
```

---

## Validation Checklist

- [ ] `README.md` updated
- [ ] `DEPLOYMENT.md` updated
- [ ] `DEPLOYMENT-FOUNDRY-HOSTED.md` created
- [ ] `UNIFIED-ARCHITECTURE.md` created
- [ ] All links in docs verified
- [ ] No references to deprecated code

---

## Dependencies

- Phase 5 completed (legacy code archived)

---

## Next Phase

[Phase 7: Testing & Validation](07-TESTING.md)
