# Container Apps Deployment Guide

Deploy the Agent Framework reference implementation to Azure Container Apps for self-hosted, high-performance agent execution.

---

## Overview

**What you're deploying**:
- Weather API container (external HTTP service)
- Agent container (orchestrates workflow, calls weather API)
- Application Insights (telemetry)
- Container Apps environment with networking

**Architecture**:
```
User Request → Agent Container (External Ingress)
                    ↓
           Workflow Orchestrator
                    ↓
         Weather API Container (Internal)
                    ↓
              OpenWeatherMap API
                    ↓
          Clothing Recommendations
```

**Why Container Apps?**
- **Performance**: 2.3x faster than managed alternatives (avg 4.68s vs 10.88s)
- **Control**: Full infrastructure control
- **Cost**: Lower at high volume
- **Portability**: Standard Docker containers

---

## Prerequisites

### Required Tools
```powershell
# Verify installations
az --version                    # Azure CLI 2.50+
docker --version                # Docker 20.10+
python --version                # Python 3.11+
uv --version                    # uv package manager
```

### Azure Setup
- Azure subscription with Contributor role
- Resource group (will be created if doesn't exist)
- OpenWeatherMap API key ([get free key](https://openweathermap.org/api))

### Environment Variables
```powershell
# Copy and configure
cp .env.example .env

# Required values in .env:
# OPENWEATHER_API_KEY=<your-key>
# AZURE_OPENAI_ENDPOINT=<your-endpoint>
# AZURE_OPENAI_API_KEY=<your-key>
# AZURE_OPENAI_DEPLOYMENT_NAME=<deployment-name>
```

---

## Step-by-Step Deployment

### 1. Clone and Setup

```powershell
# Clone repository
git clone <repo-url>
cd agentdemo

# Create and activate virtual environment
uv venv
.\.venv\Scripts\Activate.ps1

# Install dependencies
uv pip install -r pyproject.toml
```

### 2. Configure Environment

```powershell
# Copy environment template
cp .env.example .env

# Edit .env with your values
code .env
```

**Required Configuration**:
```env
# OpenWeatherMap API
OPENWEATHER_API_KEY=your_api_key_here

# Azure OpenAI
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/
AZURE_OPENAI_API_KEY=your_azure_openai_key
AZURE_OPENAI_DEPLOYMENT_NAME=gpt-4

# Application Insights (optional, will be created if not provided)
APPLICATIONINSIGHTS_CONNECTION_STRING=
```

### 3. Login to Azure

```powershell
# Login
az login

# Set subscription (if you have multiple)
az account set --subscription "<subscription-name-or-id>"

# Verify
az account show
```

### 4. Deploy Infrastructure

```powershell
# Navigate to deployment directory
cd deploy/container-app

# Run deployment script
./deploy.ps1
```

**What this does**:
1. Creates resource group (if doesn't exist)
2. Builds Docker images with version tags
3. Pushes images to Azure Container Registry
4. Deploys Container Apps environment
5. Deploys weather API container (internal ingress)
6. Deploys agent container (external ingress)
7. Configures Application Insights
8. Sets up managed identity authentication

**Duration**: ~10-15 minutes

### 5. Verify Deployment

```powershell
# Get agent URL
$agentUrl = az containerapp show `
  --name ca-weather-dev-<suffix> `
  --resource-group foundry `
  --query "properties.configuration.ingress.fqdn" `
  --output tsv

Write-Host "Agent URL: https://$agentUrl"

# Test the agent
$response = Invoke-RestMethod `
  -Uri "https://$agentUrl/chat" `
  -Method Post `
  -ContentType "application/json" `
  -Body '{"message": "What should I wear in 10001?"}'

Write-Host "Response: $($response.response)"
```

**Expected output**:
```json
{
  "response": "Based on the current weather in New York (10001), it's 28°F and clear. I recommend: heavy insulated winter coat, thermal layers, warm hat and gloves, and waterproof boots.",
  "session_id": "...",
  "metadata": {
    "workflow_duration": 4.52,
    "weather_temp": 28.5
  }
}
```

---

## Architecture Details

### Components Deployed

#### 1. Container Apps Environment
```bicep
// Shared environment for both containers
resource environment 'Microsoft.App/managedEnvironments@2023-05-01'
```
- **Log Analytics**: Centralized logging
- **Virtual Network**: Optional custom VNET
- **Region**: Sweden Central (configurable)

#### 2. Weather API Container
```yaml
name: ca-weather-api-dev-<suffix>
image: <registry>/weather-api:<version>
ingress:
  external: false           # Internal only
  targetPort: 8000
  transport: http
env:
  - OPENWEATHER_API_KEY    # From .env
```

**Endpoints**:
- `GET /api/weather?zip_code=10001` - Get weather data

#### 3. Agent Container
```yaml
name: ca-weather-dev-<suffix>
image: <registry>/agent:<version>
ingress:
  external: true            # Public endpoint
  targetPort: 8000
  transport: http
env:
  - WEATHER_API_URL         # Points to weather API container
  - AZURE_OPENAI_*          # OpenAI configuration
```

**Endpoints**:
- `POST /chat` - Agent conversation endpoint

### Code Structure

**Agent Container** (`src/agent-container/`):
```
agent-container/
├── agent.yaml              # Agent configuration
├── workflow.yaml           # Workflow definition
├── workflow_orchestrator.py # Python orchestration
├── agent_service.py        # Agent logic
├── app.py                  # FastAPI app
└── telemetry.py           # Application Insights
```

**Weather API Container** (separate service):
```
weather-api/
├── main.py                # FastAPI app
├── weather_service.py     # OpenWeatherMap integration
└── Dockerfile             # Multi-stage build
```

### Data Flow

```
1. User Request
   POST /chat {"message": "What should I wear in 10001?"}

2. Agent Container
   - FastAPI receives request
   - WorkflowOrchestrator executes

3. Workflow Steps
   Step 1: Parse input (extract zip code)
   Step 2: Call Weather API container
           GET http://ca-weather-api-dev-<suffix>.internal/api/weather?zip_code=10001
   Step 3: Generate recommendations (Azure OpenAI)
   Step 4: Format response

4. Response
   {"response": "...", "session_id": "...", "metadata": {...}}
```

### Networking

**Internal Communication**:
- Weather API: `http://ca-weather-api-dev-<suffix>.internal.swedencentral.azurecontainerapps.io`
- Agent → Weather API: Container Apps internal DNS
- No public internet exposure for weather API

**External Access**:
- Agent: `https://ca-weather-dev-<suffix>.swedencentral.azurecontainerapps.io`
- Public internet access
- HTTPS only

---

## Configuration Reference

### Agent Configuration (`agent.yaml`)

```yaml
name: WeatherClothingAdvisor
model:
  provider: azure_openai
  model_name: gpt-4
  endpoint: ${AZURE_OPENAI_ENDPOINT}
  api_key: ${AZURE_OPENAI_API_KEY}
  deployment_name: ${AZURE_OPENAI_DEPLOYMENT_NAME}

instructions: |
  You are a helpful clothing advisor that provides recommendations based on weather.

  When user provides a location:
  1. Get current weather data
  2. Consider temperature, conditions, precipitation
  3. Recommend appropriate clothing
  4. Be conversational and helpful

tools: []  # External API called via workflow, not as tool
```

### Workflow Configuration (`workflow.yaml`)

```yaml
name: weather_clothing_workflow
type: sequential
steps:
  - name: parse_input
    description: Extract zip code from user message

  - name: get_weather
    description: Call weather API container
    endpoint: ${WEATHER_API_URL}/api/weather

  - name: generate_recommendations
    description: Use AI to create clothing advice

  - name: format_response
    description: Return conversational response
```

---

## Testing Your Deployment

### 1. Health Check

```powershell
# Test agent health
curl https://$agentUrl/health

# Expected: {"status": "healthy"}
```

### 2. Weather API Test

```powershell
# Get weather API URL (internal, test from agent container)
az containerapp exec `
  --name ca-weather-dev-<suffix> `
  --resource-group foundry `
  --command "/bin/sh"

# Inside container:
curl http://ca-weather-api-dev-<suffix>.internal/api/weather?zip_code=10001
```

### 3. End-to-End Test

```powershell
# Run test script
cd tests
python test_container_agent.py
```

**Test cases**:
- Cold weather (NYC 10001)
- Warm weather (LA 90210)
- Rainy weather (Seattle 98101)
- Invalid zip code (error handling)
- Conversational queries

---

## Monitoring & Troubleshooting

### Application Insights

**View logs**:
```powershell
# Get Application Insights workspace ID
$workspaceId = az monitor app-insights component show `
  --app <app-insights-name> `
  --resource-group foundry `
  --query "customerId" `
  --output tsv

# Query logs (last hour)
az monitor app-insights query `
  --app <app-insights-name> `
  --analytics-query "traces | where timestamp > ago(1h) | order by timestamp desc" `
  --offset 1h
```

**Key metrics**:
- Request duration
- Success rate
- Dependency calls (weather API, OpenAI)
- Error rates

### Common Issues

#### Issue: Agent returns 500 error
**Check**:
```powershell
# View container logs
az containerapp logs show `
  --name ca-weather-dev-<suffix> `
  --resource-group foundry `
  --tail 50
```

**Common causes**:
- Missing environment variables
- Weather API not accessible
- OpenAI authentication failure

#### Issue: Weather API timeout
**Check**:
```powershell
# Verify weather API is running
az containerapp show `
  --name ca-weather-api-dev-<suffix> `
  --resource-group foundry `
  --query "properties.runningStatus"
```

**Fix**: Restart weather API container

#### Issue: Slow responses
**Check Application Insights**:
- Weather API call duration
- OpenAI API call duration
- Workflow orchestration overhead

**Optimize**: Consider caching weather data for same zip code

---

## Updating Your Deployment

### Update Agent Code

```powershell
# 1. Make code changes in src/agent-container/

# 2. Rebuild and push image
cd deploy/container-app
./build-and-push.ps1

# 3. Update Container App
az containerapp update `
  --name ca-weather-dev-<suffix> `
  --resource-group foundry `
  --image <registry>/agent:<new-version>
```

### Update Configuration

```powershell
# Update environment variables
az containerapp update `
  --name ca-weather-dev-<suffix> `
  --resource-group foundry `
  --set-env-vars "NEW_VAR=value"

# Or update via Azure Portal
```

---

## Cost Optimization

### Scaling Configuration

```powershell
# Configure autoscaling
az containerapp update `
  --name ca-weather-dev-<suffix> `
  --resource-group foundry `
  --min-replicas 0 `      # Scale to zero when idle
  --max-replicas 10       # Scale up under load
```

### Resource Allocation

**Current**:
- Agent: 0.5 CPU, 1GB memory
- Weather API: 0.25 CPU, 0.5GB memory

**Optimize**:
- Reduce CPU/memory if not needed
- Use consumption plan for variable workloads
- Scale to zero during off-hours

### Estimated Costs

**Light usage** (1000 requests/day):
- Container Apps: ~$10-20/month
- Application Insights: ~$2-5/month
- Container Registry: ~$5/month
- **Total**: ~$17-30/month

**High usage** (100K requests/day):
- Container Apps: ~$200-300/month
- Application Insights: ~$20-50/month
- Container Registry: ~$5/month
- **Total**: ~$225-355/month

---

## Next Steps

### Compare with Foundry
Deploy the same agent to Azure AI Foundry:
👉 **[Foundry Deployment Guide](./DEPLOYMENT-FOUNDRY.md)**

### Port Between Platforms
Learn how to move between Container Apps and Foundry:
👉 **[Porting Guide](./PORTING-GUIDE.md)**

### Advanced Patterns
Explore workflow orchestration and cost optimization:
👉 **[Workflow Patterns](./WORKFLOW-ORCHESTRATION-PATTERNS.md)**

### Customize for Your Use Case
- Replace weather API with your external service
- Update agent instructions in `agent.yaml`
- Modify workflow steps in `workflow_orchestrator.py`

---

## Reference

### Deployment Files
- **Bicep template**: `deploy/container-app/main.bicep`
- **Deploy script**: `deploy/container-app/deploy.ps1`
- **Build script**: `build-and-push.ps1`

### Agent Code
- **Agent config**: `src/agent-container/agent.yaml`
- **Workflow config**: `src/agent-container/workflow.yaml`
- **Orchestrator**: `src/agent-container/workflow_orchestrator.py`
- **FastAPI app**: `src/agent-container/app.py`

### Documentation
- **Architecture**: [Agent Framework Tutorial](./AGENT-FRAMEWORK-TUTORIAL.md#architecture-overview)
- **Agent Framework Tutorial**: [AGENT-FRAMEWORK-TUTORIAL.md](./AGENT-FRAMEWORK-TUTORIAL.md)

---

**Deployment complete!** Your agent is now running on Azure Container Apps with high performance and full control.
