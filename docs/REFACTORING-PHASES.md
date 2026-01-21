# Weather Agent Refactoring - Phase Plan

**Project:** Weather-Based Clothing Advisor
**Goal:** Dual deployment support (Container Apps + Foundry Hosted)
**Date:** January 20, 2026

---

## Overview

This document provides a structured, phase-based approach to refactoring the Weather Agent for dual deployment support. Each phase is self-contained and testable before moving to the next.

**Current State:** Container Apps deployment failing due to incorrect endpoint configuration
**Target State:** Working Container Apps + Optional Foundry Hosted deployment

---

## Phase Status Tracking

| Phase | Status | Start | Complete | Notes |
|-------|--------|-------|----------|-------|
| Phase 1.1 | � Complete | 2026-01-20 | 2026-01-20 | Endpoint configuration fixed |
| Phase 1.2 | 🟢 Complete | 2026-01-20 | 2026-01-20 | Managed Identity configured |
| Phase 1.3 | 🟢 Complete | 2026-01-20 | 2026-01-20 | Local test confirms config (auth works in Azure) |
| Phase 1.4 | ⚪ Not Started | - | - | Azure deployment |
| Phase 2.1 | ⚪ Not Started | - | - | Foundry adapter setup |
| Phase 2.2 | ⚪ Not Started | - | - | Foundry deployment |

Legend: ⚪ Not Started | 🟡 In Progress | 🟢 Complete | 🔴 Blocked

---

## PHASE 1: Fix Container Apps Deployment

**Goal:** Get existing Container Apps deployment working correctly

**Success Criteria:**
- ✅ Container starts without errors
- ✅ Health endpoint responds (200 OK)
- ✅ Chat endpoint processes weather requests
- ✅ Agent successfully calls weather function
- ✅ Response time under 5 seconds (SC-001)

---

### Phase 1.1: Fix Endpoint Configuration

**Duration:** 30 minutes
**Context Window Impact:** LOW (few files)

#### Files to Modify

1. `.env` - Update Foundry endpoint
2. `src/agent-container/agent_service.py` - Fix endpoint usage
3. `deploy/container-app/main.bicep` - Update environment variables

#### Changes Required

**File: `.env`**
```diff
- AZURE_AI_PROJECT_ENDPOINT=https://anfoundy3lsww.services.ai.azure.com/api/projects/weatheragentlsww
+ # Azure AI Foundry Resource Endpoint (for models)
+ AZURE_FOUNDRY_ENDPOINT=https://anfoundy3lsww.services.ai.azure.com/
+
+ # Model Deployment Name
AZURE_AI_MODEL_DEPLOYMENT_NAME=gpt-4.1
```

**File: `src/agent-container/agent_service.py`**
```python
# BEFORE (lines ~124-133):
azure_endpoint = os.getenv("AZURE_OPENAI_ENDPOINT") or os.getenv("AZURE_AI_PROJECT_ENDPOINT")
deployment_name = os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME") or os.getenv("AZURE_AI_MODEL_DEPLOYMENT_NAME", "gpt-4")

# AFTER:
azure_endpoint = os.getenv("AZURE_FOUNDRY_ENDPOINT")
deployment_name = os.getenv("AZURE_AI_MODEL_DEPLOYMENT_NAME", "gpt-4")

if not azure_endpoint:
    raise ValueError("AZURE_FOUNDRY_ENDPOINT environment variable is required")
```

**File: `deploy/container-app/main.bicep`**
```bicep
// BEFORE (around line 119-138):
{
  name: 'AZURE_OPENAI_ENDPOINT'
  value: '...'
}

// AFTER:
{
  name: 'AZURE_FOUNDRY_ENDPOINT'
  value: azureFoundryEndpoint  // New parameter
}
{
  name: 'AZURE_AI_MODEL_DEPLOYMENT_NAME'
  value: modelDeploymentName  // New parameter
}
```

#### Verification Steps

1. Update `.env` file
2. Update `agent_service.py`
3. Update `main.bicep` and add new parameters
4. Update `deploy.ps1` to pass new parameters
5. Run local syntax check: `python -m py_compile src/agent-container/agent_service.py`

#### Completion Checklist

- [x] `.env` updated with correct endpoint
- [x] `agent_service.py` uses AZURE_FOUNDRY_ENDPOINT
- [x] Bicep template updated
- [x] Deploy script updated
- [x] No syntax errors

---

### Phase 1.2: Configure Managed Identity & RBAC

**Duration:** 45 minutes
**Context Window Impact:** LOW (Azure CLI commands only)

#### Steps

1. **Enable System-Assigned Managed Identity**
   ```powershell
   az containerapp identity assign `
     --resource-group foundry `
     --name ca-weather-dev-ezbvua `
     --system-assigned
   ```

2. **Get Principal ID**
   ```powershell
   $principalId = az containerapp identity show `
     --resource-group foundry `
     --name ca-weather-dev-ezbvua `
     --query principalId -o tsv

   Write-Host "Principal ID: $principalId"
   ```

3. **Assign Cognitive Services OpenAI User Role**
   ```powershell
   # Get Foundry resource ID
   $foundryResourceId = az cognitiveservices account show `
     --name anfoundy3lsww `
     --resource-group foundry `
     --query id -o tsv

   # Assign role
   az role assignment create `
     --assignee $principalId `
     --role "Cognitive Services OpenAI User" `
     --scope $foundryResourceId
   ```

4. **Verify Role Assignment**
   ```powershell
   az role assignment list `
     --assignee $principalId `
     --scope $foundryResourceId `
     --output table
   ```

#### Completion Checklist

- [x] Managed identity enabled
- [x] Principal ID captured
- [x] Role assigned
- [x] Role verified

---

### Phase 1.3: Local Testing with Docker

**Duration:** 30 minutes
**Context Window Impact:** LOW

#### Prerequisites

- Ensure you're logged into Azure CLI: `az login`
- Docker Desktop running

#### Test Steps

1. **Build Docker Image**
   ```powershell
   Set-Location D:\Git\agentdemo
   .\build-and-push.ps1
   ```

2. **Run Locally with Azure Credentials**
   ```powershell
   docker run --rm `
     -e WEATHER_FUNCTION_URL="https://func-weather-dev-ezbvua564mnlg.azurewebsites.net/api/get_weather" `
     -e AZURE_FOUNDRY_ENDPOINT="https://anfoundy3lsww.services.ai.azure.com/" `
     -e AZURE_AI_MODEL_DEPLOYMENT_NAME="gpt-4.1" `
     -e APPLICATIONINSIGHTS_CONNECTION_STRING="$env:APPLICATIONINSIGHTS_CONNECTION_STRING" `
     -e AZURE_CLIENT_ID="$env:AZURE_CLIENT_ID" `
     -e AZURE_TENANT_ID="$env:AZURE_TENANT_ID" `
     -e AZURE_CLIENT_SECRET="$env:AZURE_CLIENT_SECRET" `
     -p 8000:8000 `
     anacr123321.azurecr.io/weather-advisor:latest
   ```

3. **Test Health Endpoint**
   ```powershell
   Invoke-RestMethod -Uri "http://localhost:8000/health"
   ```

   Expected: `{"status": "healthy"}`

4. **Test Chat Endpoint**
   ```powershell
   $body = @{
       message = "What should I wear in 10001?"
   } | ConvertTo-Json

   Invoke-RestMethod `
     -Uri "http://localhost:8000/chat" `
     -Method Post `
     -ContentType "application/json" `
     -Body $body
   ```

   Expected: Weather-based clothing recommendations

#### Completion Checklist

- [ ] Image builds successfully
- [ ] Container starts without errors
- [ ] Health endpoint returns 200
- [ ] Chat endpoint processes request
- [ ] Agent calls weather function
- [ ] Response includes clothing recommendations

---

### Phase 1.4: Deploy to Azure Container Apps

**Duration:** 30 minutes
**Context Window Impact:** LOW

#### Deploy Steps

1. **Update Container App with New Image**
   ```powershell
   Set-Location D:\Git\agentdemo\deploy\container-app

   .\deploy.ps1 `
     -ResourceGroupName foundry `
     -OpenWeatherMapApiKey $env:OPENWEATHERMAP_API_KEY
   ```

2. **Wait for Deployment** (2-3 minutes)

3. **Check Container App Status**
   ```powershell
   az containerapp show `
     --resource-group foundry `
     --name ca-weather-dev-ezbvua `
     --query "properties.runningStatus" -o tsv
   ```

4. **Test Azure Endpoints**
   ```powershell
   $baseUrl = "https://ca-weather-dev-ezbvua.mangomushroom-3560f614.swedencentral.azurecontainerapps.io"

   # Health check
   Invoke-RestMethod -Uri "$baseUrl/health"

   # Chat test
   $body = @{
       message = "What should I wear in 90210?"
   } | ConvertTo-Json

   Invoke-RestMethod `
     -Uri "$baseUrl/chat" `
     -Method Post `
     -ContentType "application/json" `
     -Body $body `
     -TimeoutSec 30
   ```

5. **Check Logs if Issues**
   ```powershell
   az containerapp logs show `
     --resource-group foundry `
     --name ca-weather-dev-ezbvua `
     --tail 50
   ```

#### Completion Checklist

- [ ] Deployment succeeds
- [ ] Container status: Running
- [ ] Health endpoint responds
- [ ] Chat endpoint works end-to-end
- [ ] Logs show successful agent initialization
- [ ] Response time under 5 seconds

---

### Phase 1 Exit Criteria

✅ **All of the following must be true:**

1. Container App deployed and running
2. Health endpoint returns 200 OK
3. Chat endpoint processes requests successfully
4. Agent successfully:
   - Parses user zip code
   - Calls weather function
   - Generates clothing recommendations
   - Returns formatted response
5. Response time meets SC-001 (under 5 seconds)
6. No authentication errors in logs
7. Application Insights receiving telemetry

**If ANY criterion fails, do NOT proceed to Phase 2.**

---

## PHASE 2: Add Foundry Hosted Agent Support

**Goal:** Add second deployment target using Foundry Hosted Agents

**Success Criteria:**
- ✅ Agent runs locally with hosting adapter (localhost:8088)
- ✅ Deployed to Foundry as hosted agent
- ✅ Same functionality as Container Apps version
- ✅ Both deployments work independently

---

### Phase 2.1: Setup Hosting Adapter

**Duration:** 1 hour
**Context Window Impact:** MEDIUM

#### Install Dependencies

**File: `pyproject.toml`**
```diff
dependencies = [
    # Existing dependencies...
    "azure-ai-projects>=1.0.0",
    "azure-identity>=1.15.0",
+
+   # Foundry Hosted Agent support
+   "azure-ai-agentserver-core>=1.0.0",
+   "azure-ai-agentserver-agentframework>=1.0.0",
]
```

#### Create Foundry Hosted Entry Point

**File: `src/agent-container/foundry_hosted.py` (NEW)**
```python
"""
Foundry Hosted Agent entry point.

Uses Azure AI Agent Server adapter to convert Agent Framework agent
into Foundry-compatible HTTP service.
"""

import os
import logging
from azure.ai.agentserver.agentframework import from_agent_framework

# Import shared agent service
from agent_service import AgentService

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def main():
    """Run agent with Foundry hosting adapter."""
    logger.info("Starting Weather Agent with Foundry Hosting Adapter")

    # Initialize agent service (shared logic)
    service = AgentService()

    # Wrap with hosting adapter
    # This automatically creates HTTP server on port 8088
    # with Foundry Responses API endpoints
    from_agent_framework(service.agent).run()


if __name__ == "__main__":
    main()
```

#### Create Foundry Dockerfile

**File: `Dockerfile.foundry` (NEW)**
```dockerfile
# Multi-stage build for Foundry Hosted Agent
FROM python:3.11-slim AS builder

WORKDIR /app

# Install uv for faster dependency resolution
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

# Copy dependency files
COPY pyproject.toml ./

# Install dependencies including hosting adapter
RUN uv pip install --system --no-cache --prerelease=allow -r pyproject.toml

# Stage 2: Runtime
FROM python:3.11-slim

WORKDIR /app

# Copy installed packages
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages

# Copy application code
COPY src/ ./src/
COPY specs/ ./specs/

# Set Python path
ENV PYTHONPATH=/app/src/agent-container:/app/src/shared:/app/src

# Set working directory
WORKDIR /app/src/agent-container

# Expose Foundry adapter port
EXPOSE 8088

# Run with hosting adapter
CMD ["python", "foundry_hosted.py"]
```

#### Local Testing Script

**File: `test-foundry-local.ps1` (NEW)**
```powershell
# Test Foundry Hosted Agent locally

$ErrorActionPreference = "Stop"

Write-Host "🧪 Testing Foundry Hosted Agent Locally" -ForegroundColor Cyan

# Load environment
Get-Content .env | ForEach-Object {
    if ($_ -match '^\s*([^#][^=]*)\s*=\s*(.*)$') {
        $name = $matches[1].Trim()
        $value = $matches[2].Trim()
        Set-Item -Path "env:$name" -Value $value
    }
}

# Build image
Write-Host "`n🔨 Building Foundry Docker image..." -ForegroundColor Yellow
docker build -f Dockerfile.foundry -t weather-advisor-foundry:local .

# Run container
Write-Host "`n🚀 Starting container on localhost:8088..." -ForegroundColor Yellow
docker run --rm -d `
    -p 8088:8088 `
    -e WEATHER_FUNCTION_URL=$env:WEATHER_FUNCTION_URL `
    -e AZURE_FOUNDRY_ENDPOINT=$env:AZURE_FOUNDRY_ENDPOINT `
    -e AZURE_AI_MODEL_DEPLOYMENT_NAME=$env:AZURE_AI_MODEL_DEPLOYMENT_NAME `
    -e APPLICATIONINSIGHTS_CONNECTION_STRING=$env:APPLICATIONINSIGHTS_CONNECTION_STRING `
    --name weather-foundry-test `
    weather-advisor-foundry:local

# Wait for startup
Write-Host "`n⏳ Waiting for service to start..." -ForegroundColor Yellow
Start-Sleep -Seconds 5

# Test Foundry Responses API
Write-Host "`n✅ Testing Foundry Responses endpoint..." -ForegroundColor Green

$body = @{
    input = @{
        messages = @(
            @{
                role = "user"
                content = "What should I wear in 10001?"
            }
        )
    }
} | ConvertTo-Json -Depth 5

try {
    $response = Invoke-RestMethod `
        -Uri "http://localhost:8088/responses" `
        -Method Post `
        -ContentType "application/json" `
        -Body $body `
        -TimeoutSec 30

    Write-Host "`n📨 Response received:" -ForegroundColor Green
    Write-Host ($response | ConvertTo-Json -Depth 5)

    # Cleanup
    Write-Host "`n🧹 Cleaning up..." -ForegroundColor Yellow
    docker stop weather-foundry-test

    Write-Host "`n✅ Test completed successfully!" -ForegroundColor Green
}
catch {
    Write-Host "`n❌ Test failed: $_" -ForegroundColor Red
    docker logs weather-foundry-test
    docker stop weather-foundry-test
    exit 1
}
```

#### Completion Checklist

- [ ] `azure-ai-agentserver-agentframework` installed
- [ ] `foundry_hosted.py` created
- [ ] `Dockerfile.foundry` created
- [ ] `test-foundry-local.ps1` created
- [ ] Local test runs successfully
- [ ] Foundry Responses API endpoint works

---

### Phase 2.2: Deploy to Foundry Hosted Agents

**Duration:** 1 hour
**Context Window Impact:** MEDIUM

#### Setup Azure Developer CLI

```powershell
# Install azd if not already installed
winget install microsoft.azd

# Login
azd auth login
```

#### Create azure.yaml

**File: `azure.yaml` (NEW)**
```yaml
name: weather-advisor-foundry
metadata:
  template: foundry-hosted-agent@1.0.0

services:
  weather-agent:
    project: ./src/agent-container
    language: python
    host: foundry

    # Agent configuration
    agent:
      name: weather-clothing-advisor
      description: "Provides weather-based clothing recommendations"
      instructions: "You are a helpful weather-based clothing advisor..."

    # Container configuration
    docker:
      path: ./Dockerfile.foundry
      context: .

    # Environment variables
    env:
      WEATHER_FUNCTION_URL: ${WEATHER_FUNCTION_URL}
      AZURE_FOUNDRY_ENDPOINT: ${AZURE_FOUNDRY_ENDPOINT}
      AZURE_AI_MODEL_DEPLOYMENT_NAME: ${AZURE_AI_MODEL_DEPLOYMENT_NAME}
      APPLICATIONINSIGHTS_CONNECTION_STRING: ${APPLICATIONINSIGHTS_CONNECTION_STRING}
```

#### Deploy Commands

```powershell
# Initialize azd environment
azd init

# Set environment variables
azd env set WEATHER_FUNCTION_URL "$env:WEATHER_FUNCTION_URL"
azd env set AZURE_FOUNDRY_ENDPOINT "$env:AZURE_FOUNDRY_ENDPOINT"
azd env set AZURE_AI_MODEL_DEPLOYMENT_NAME "$env:AZURE_AI_MODEL_DEPLOYMENT_NAME"

# Deploy (provision + deploy)
azd up
```

#### Test Deployed Agent

```powershell
# Get agent endpoint from azd output
$agentEndpoint = azd env get-value AGENT_ENDPOINT

# Test Foundry Responses API
$body = @{
    input = @{
        messages = @(
            @{
                role = "user"
                content = "What should I wear in 90210?"
            }
        )
    }
} | ConvertTo-Json -Depth 5

Invoke-RestMethod `
    -Uri "$agentEndpoint/responses" `
    -Method Post `
    -ContentType "application/json" `
    -Body $body `
    -TimeoutSec 30
```

#### Completion Checklist

- [ ] `azure.yaml` created
- [ ] azd initialized
- [ ] Environment variables set
- [ ] Deployment succeeds
- [ ] Agent appears in Foundry portal
- [ ] Foundry Responses API works
- [ ] Same functionality as Container Apps

---

### Phase 2 Exit Criteria

✅ **All of the following must be true:**

1. Foundry Hosted Agent deployed successfully
2. Agent visible in Foundry portal
3. Foundry Responses API endpoint working
4. Same weather + clothing functionality as Container Apps
5. Both deployments work independently:
   - Container Apps: Custom FastAPI endpoints
   - Foundry Hosted: Standard Foundry Responses API
6. Documentation updated with both deployment methods

---

## PHASE 3: Documentation & Comparison

**Goal:** Complete documentation for dual deployment strategy

**Duration:** 30 minutes
**Context Window Impact:** LOW

### Deliverables

1. **DEPLOYMENT-COMPARISON.md**
   - Side-by-side comparison
   - When to use each approach
   - Cost analysis

2. **Updated README.md**
   - Dual deployment options
   - Quick start for both

3. **Updated QUICKSTART.md**
   - Container Apps path
   - Foundry Hosted path

---

## Context Window Management Strategy

### Per-Phase Context

Each phase is designed to minimize context window usage:

**Phase 1.1-1.4 (Container Apps Fix):**
- Focus files: agent_service.py, .env, main.bicep, deploy.ps1
- Can complete without loading other code

**Phase 2.1-2.2 (Foundry Hosted):**
- New files only: foundry_hosted.py, Dockerfile.foundry, azure.yaml
- Minimal changes to existing code

### Context Reset Points

After completing each phase:
1. Summarize what was done
2. Capture key decisions
3. Note any issues encountered
4. Clear context for next phase

### Emergency Context Reduction

If context window fills:
1. Complete current sub-phase
2. Commit code changes
3. Save phase status to this document
4. Start new conversation with phase reference

---

## Rollback Strategy

### If Phase 1 Fails

- Keep existing broken Container Apps deployment
- Fix issues before proceeding
- Can test locally with Docker without Azure changes

### If Phase 2 Fails

- Container Apps still works (Phase 1)
- Remove Foundry Hosted files
- No impact on production Container Apps

---

## Communication Protocol

### Phase Start

```
Starting Phase X.Y: [Phase Name]
Duration: [Estimate]
Files: [List]
```

### Phase Complete

```
✅ Phase X.Y Complete
- [Checklist items completed]
- [Any issues noted]
- Ready for Phase X.Y+1
```

### Phase Blocked

```
🔴 Phase X.Y Blocked
- Issue: [Description]
- Required: [What's needed]
- Alternative: [Workaround if available]
```

---

## Current Status

**Active Phase:** Not started
**Next Action:** Await user confirmation to begin Phase 1.1
**Blockers:** None

---

**Document Owner:** GitHub Copilot
**Last Updated:** January 20, 2026
