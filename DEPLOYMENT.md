# Weather-Based Clothing Advisor - Deployment Guide

Complete guide for deploying the Weather-Based Clothing Advisor POC to both **Azure Container Apps** and **Azure AI Foundry Workflow Service**.

**Both deployments use workflow orchestration with a 4-step pattern**: Parse Input → Get Weather → Generate Recommendations → Format Response

---

## Table of Contents

- [Overview](#overview)
- [Prerequisites](#prerequisites)
- [Architecture](#architecture)
- [Deployment Option 1: Azure Container Apps](#deployment-option-1-azure-container-apps)
- [Deployment Option 2: Azure AI Foundry Workflow](#deployment-option-2-azure-ai-foundry-workflow)
- [Post-Deployment Testing](#post-deployment-testing)
- [Monitoring & Observability](#monitoring--observability)
- [Troubleshooting](#troubleshooting)
- [Cost Optimization](#cost-optimization)
- [Cleanup](#cleanup)

---

## Overview

This POC demonstrates **dual workflow orchestration patterns** for AI agents:

| Deployment | Type | Workflow Pattern | Configuration | Use Case |
|------------|------|-----------------|---------------|----------|
| **Container Apps** | Self-hosted | Programmatic (Python) | WorkflowOrchestrator class | Full control, custom logic |
| **Foundry Workflow** | Managed service | Declarative (YAML) | agent.yaml + workflow.yaml | Rapid deployment, versioning |

**Shared Components**:

- Weather Function (Azure Functions) - used by both deployments as workflow tool
- Application Insights - unified telemetry backend
- OpenWeatherMap API - external weather data source
- Workflow Pattern - 4-step orchestration in both deployments

---

## Prerequisites

### Azure Resources

- **Azure Subscription** with Owner or Contributor role
- **Resource Group** in Sweden Central region (or modify deployment scripts)
- **Azure CLI** installed and authenticated
  ```bash
  az login
  az account set --subscription <subscription-id>
  ```

### Development Tools

- **Python 3.11+**
- **uv** package manager: `curl -LsSf https://astral.sh/uv/install.sh | sh` (Windows: `powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"`)
- **Azure Functions Core Tools** v4:
  - Windows: `winget install Microsoft.Azure.FunctionsCoreTools` or `choco install azure-functions-core-tools`
  - macOS: `brew tap azure/functions && brew install azure-functions-core-tools@4`
  - Linux: Download from https://github.com/Azure/azure-functions-core-tools/releases
- **Docker Desktop** (for Container Apps deployment)
- **Git** for version control

### API Keys & Credentials

1. **OpenWeatherMap API Key** (free tier)
   - Sign up at https://openweathermap.org/appid
   - Wait 10-15 minutes for key activation
   - 1,000 API calls/day limit

2. **Azure Container Registry** (for Container Apps)
   - Create registry: `az acr create --resource-group foundry --name anacr123 --sku Basic`
   - Enable admin: `az acr update --name anacr123 --admin-enabled true`

3. **Azure AI Foundry Project** (for Foundry deployment)
   - Create in Azure Portal: AI + Machine Learning → Azure AI Foundry
   - Note the project endpoint URL
   - Deploy GPT-4 or GPT-4o model

### Environment Setup

```powershell
# Clone repository
git clone <repository-url>
Set-Location agentdemo

# Install dependencies (includes all required packages)
uv sync --prerelease=allow
```

**Note**: The `--prerelease=allow` flag is required because the Microsoft Agent Framework is currently in preview/beta.

---

## Architecture

### High-Level Architecture

```text
┌─────────────────────────────────────────────────────────────┐
│                 Weather Clothing Advisor POC                │
│          Dual Workflow Orchestration Demonstration          │
└─────────────────────────────────────────────────────────────┘

Option 1: Azure Container Apps (Programmatic Workflow)
┌──────────┐    ┌────────────────────┐    ┌──────────────┐
│  User    │───▶│  Container App     │───▶│   Weather    │
│  (HTTP)  │    │  FastAPI Server    │    │   Function   │
│          │◀───│  WorkflowOrchest   │◀───│   (Tool)     │
└──────────┘    └────────────────────┘    └──────────────┘
                          │                        │
                          └────────┬───────────────┘
                                   ▼
                         ┌──────────────────┐
                         │  App Insights    │
                         │  (Workflow Steps)│
                         └──────────────────┘

Option 2: Azure AI Foundry (Declarative Workflow)
┌──────────┐    ┌────────────────────┐    ┌──────────────┐
│  User    │───▶│  Foundry Workflow  │───▶│   Weather    │
│ (Portal/ │    │  agent.yaml +      │    │   Function   │
│   API)   │◀───│  workflow.yaml     │◀───│   (Tool)     │
└──────────┘    └────────────────────┘    └──────────────┘
                          │                        │
                          └────────┬───────────────┘
                                   ▼
                         ┌──────────────────┐
                         │  App Insights    │
                         │  (Native)        │
                         └──────────────────┘

Shared Weather Function (Tool for Both Workflows)
┌──────────────┐      ┌─────────────────────┐
│   Weather    │─────▶│  OpenWeatherMap API │
│   Function   │      │  (External Service) │
│   (Python)   │◀─────│                     │
└──────────────┘      └─────────────────────┘
```

### Workflow Execution Pattern (Both Deployments)

```text
4-Step Workflow Orchestration:

1. Parse Input
   ├─ Extract zip code from user message
   ├─ Validate zip code format (5 digits)
   └─ Duration: ~100ms

2. Get Weather Data (depends on step 1)
   ├─ Call Azure Function tool with zip code
   ├─ Function queries OpenWeatherMap API
   ├─ Return: {temperature, conditions, wind, precipitation}
   └─ Duration: ~1-2 seconds

3. Generate Recommendations (depends on step 2)
   ├─ AI model analyzes weather conditions
   ├─ Generate 3-5 clothing recommendations
   ├─ Consider temperature, precipitation, wind
   └─ Duration: ~1-2 seconds

4. Format Response (depends on step 3)
   ├─ Convert recommendations to conversational format
   ├─ Include weather context
   ├─ Add conversational tone
   └─ Duration: ~100ms

Total Duration: <5 seconds (SC-001 compliance)
Telemetry: Each step tracked in Application Insights
```

### Component Interaction Example

```text
User Request: "What should I wear in 10001?"

Container Apps (Programmatic):
  WorkflowOrchestrator.execute_workflow()
    → Step 1: _execute_agent_reasoning() → zip="10001"
    → Step 2: _execute_tool_call() → weather={temp: 45°F, cloudy}
    → Step 3: _execute_agent_response() → AI reasoning
    → Step 4: Format final response

Foundry (Declarative):
  Foundry Workflow Engine
    → parse_user_input (agent.yaml) → zip="10001"
    → get_weather_data (tool call) → weather={temp: 45°F, cloudy}
    → generate_recommendations (agent) → AI reasoning
    → format_response (agent) → Final output

Response: "For 45°F cloudy weather in New York:
- Light jacket or fleece (moderate temperature)
- Long sleeves with light sweater (layering)
- Comfortable walking shoes (dry conditions)"

Telemetry: workflow_id, step_durations, success=true → App Insights
```

---

## Deployment Option 1: Azure Container Apps

This deployment uses **programmatic workflow orchestration** with the WorkflowOrchestrator Python class.

### Step 1: Configure Environment Variables

First, set up your environment variables by copying and configuring the .env file:

```powershell
# From project root
Copy-Item .env.example .env

# Edit .env and fill in your values:
# - AZURE_RESOURCE_GROUP (e.g., rg-weather-advisor-dev)
# - AZURE_LOCATION (e.g., swedencentral)
# - OPENWEATHERMAP_API_KEY (from https://openweathermap.org/appid)
# - AZURE_OPENAI_ENDPOINT and AZURE_OPENAI_DEPLOYMENT_NAME
```

### Step 2: Deploy Shared Infrastructure

The shared infrastructure includes Application Insights, Log Analytics, and the Weather Function. These are used by both deployments.

```powershell
# Navigate to deployment directory
Set-Location deploy/container-app

# Load variables from .env file into PowerShell variables
Get-Content ../../.env | ForEach-Object {
    if ($_ -match '^([^#][^=]+)=(.*)$') {
        $varName = $matches[1].Trim()
        $varValue = $matches[2].Trim()
        Set-Variable -Name $varName -Value $varValue -Scope Global
        Write-Host "Loaded: $varName = $varValue"
    }
}

# Set default environment name if not provided
if (-not $ENVIRONMENT_NAME) {
    $ENVIRONMENT_NAME = "dev"
    Write-Host "Using default ENVIRONMENT_NAME: dev"
}

# Create resource group
az group create --name $AZURE_RESOURCE_GROUP --location $AZURE_LOCATION

# Deploy shared infrastructure (App Insights + Weather Function)
az deployment group create `
    --resource-group $AZURE_RESOURCE_GROUP `
    --template-file ../shared/monitoring.bicep `
    --parameters location=$AZURE_LOCATION environmentName=$ENVIRONMENT_NAME

# Get Application Insights connection string
# List all App Insights in resource group and get the most recent one
$APP_INSIGHTS_NAME = az monitor app-insights component list `
    --resource-group $AZURE_RESOURCE_GROUP `
    --query "[?starts_with(name, 'appi-weather-advisor')].name | [0]" `
    -o tsv

if (-not $APP_INSIGHTS_NAME) {
    Write-Error "App Insights component not found. Check deployment output."
    exit 1
}

$APP_INSIGHTS_CS = az monitor app-insights component show `
    --resource-group $AZURE_RESOURCE_GROUP `
    --app $APP_INSIGHTS_NAME `
    --query connectionString -o tsv

Write-Host "✓ App Insights: $APP_INSIGHTS_NAME"
Write-Host "✓ Connection String: $($APP_INSIGHTS_CS.Substring(0,50))..."

# Save to .env file (update if exists, add if not)
$envPath = "../../.env"
$envContent = Get-Content $envPath -ErrorAction SilentlyContinue
if ($envContent -match '^APPLICATIONINSIGHTS_CONNECTION_STRING=') {
    $envContent = $envContent -replace '^APPLICATIONINSIGHTS_CONNECTION_STRING=.*', "APPLICATIONINSIGHTS_CONNECTION_STRING=$APP_INSIGHTS_CS"
    $envContent | Set-Content $envPath
} else {
    Add-Content $envPath "APPLICATIONINSIGHTS_CONNECTION_STRING=$APP_INSIGHTS_CS"
}

# Deploy Weather Function
az deployment group create `
    --resource-group $AZURE_RESOURCE_GROUP `
    --template-file ../shared/function-app.bicep `
    --parameters `
        location=$AZURE_LOCATION `
        environmentName=$ENVIRONMENT_NAME `
        openWeatherMapApiKey=$OPENWEATHERMAP_API_KEY `
        appInsightsConnectionString=$APP_INSIGHTS_CS
```

### Step 3: Build and Push Container Image

```powershell
# Build and push from project root (run this ONCE)
# This script handles everything: build, tag, login, push
./build-and-push.ps1

# The script will:
# - Read CONTAINER_REGISTRY_NAME from .env
# - Build the Docker image from project root
# - Tag it for your ACR
# - Login to ACR
# - Push the image

# If you need to specify a different registry:
# ./build-and-push.ps1 -RegistryName "myregistry"
```

### Step 4: Deploy Container App

```powershell
# Navigate to deployment directory
Set-Location deploy/container-app

# Deploy (script reads CONTAINER_REGISTRY_NAME from .env)
./deploy.ps1 `
    -ResourceGroupName foundry `
    -OpenWeatherMapApiKey $OPENWEATHERMAP_API_KEY

# Get Container App URL
$CONTAINER_APP_NAME = az containerapp list `
    --resource-group foundry `
    --query "[?starts_with(name, 'ca-weather-advisor-dev')].name | [0]" -o tsv

$CONTAINER_APP_URL = az containerapp show `
    --resource-group foundry `
    --name $CONTAINER_APP_NAME `
    --query properties.configuration.ingress.fqdn -o tsv

Write-Host "✅ Container App deployed: https://$CONTAINER_APP_URL"
```

### Step 5: Verify Deployment

```powershell
# Test health endpoint
Invoke-RestMethod -Uri "https://$CONTAINER_APP_URL/health"

# Test chat endpoint
$body = @{
    message = "What should I wear in 10001?"
} | ConvertTo-Json

Invoke-RestMethod -Uri "https://$CONTAINER_APP_URL/chat" `
    -Method Post `
    -ContentType "application/json" `
    -Body $body

# View logs
az containerapp logs show `
    --resource-group $RESOURCE_GROUP `
    --name ca-weather-advisor-dev-* `
    --follow
```

---

## Deployment Option 2: Azure AI Foundry Workflow

### Step 1: Deploy Weather Function (if not already deployed)

If you haven't deployed the Weather Function from Option 1:

```powershell
Set-Location deploy/shared

# Load variables from .env file (if not already loaded)
Get-Content ../../.env | ForEach-Object {
    if ($_ -match '^([^#][^=]+)=(.*)$') {
        $varName = $matches[1].Trim()
        $varValue = $matches[2].Trim()
        Set-Variable -Name $varName -Value $varValue -Scope Global
    }
}

# Deploy monitoring
az deployment group create `
    --resource-group $AZURE_RESOURCE_GROUP `
    --template-file monitoring.bicep `
    --parameters location=$AZURE_LOCATION environmentName=$ENVIRONMENT_NAME

# Get App Insights connection string
$APP_INSIGHTS_NAME = az monitor app-insights component list `
    --resource-group $AZURE_RESOURCE_GROUP `
    --query "[?starts_with(name, 'appi-weather-advisor')].name | [0]" `
    -o tsv

$APP_INSIGHTS_CS = az monitor app-insights component show `
    --resource-group $AZURE_RESOURCE_GROUP `
    --app $APP_INSIGHTS_NAME `
    --query connectionString -o tsv

# Save to .env (update if exists, add if not)
$envPath = "../../.env"
$envContent = Get-Content $envPath -ErrorAction SilentlyContinue
if ($envContent -match '^APPLICATIONINSIGHTS_CONNECTION_STRING=') {
    $envContent = $envContent -replace '^APPLICATIONINSIGHTS_CONNECTION_STRING=.*', "APPLICATIONINSIGHTS_CONNECTION_STRING=$APP_INSIGHTS_CS"
    $envContent | Set-Content $envPath
} else {
    Add-Content $envPath "APPLICATIONINSIGHTS_CONNECTION_STRING=$APP_INSIGHTS_CS"
}

# Deploy Weather Function
az deployment group create `
    --resource-group $AZURE_RESOURCE_GROUP `
    --template-file function-app.bicep `
    --parameters `
        location=$AZURE_LOCATION `
        environmentName=$ENVIRONMENT_NAME `
        openWeatherMapApiKey=$OPENWEATHERMAP_API_KEY `
        appInsightsConnectionString=$APP_INSIGHTS_CS

# Get function URL
$WEATHER_FUNCTION_URL = az functionapp show `
    --resource-group $RESOURCE_GROUP `
    --name func-weather-dev-* `
    --query defaultHostName -o tsv
$WEATHER_FUNCTION_URL = "https://$WEATHER_FUNCTION_URL/api/get_weather"
```

### Step 2: Deploy Weather Function Code

```powershell
Set-Location ../../src/function

# Create local.settings.json
@"
{
  "IsEncrypted": false,
  "Values": {
    "AzureWebJobsStorage": "UseDevelopmentStorage=true",
    "FUNCTIONS_WORKER_RUNTIME": "python",
    "OPENWEATHERMAP_API_KEY": "$OPENWEATHERMAP_API_KEY",
    "APPLICATIONINSIGHTS_CONNECTION_STRING": "$APP_INSIGHTS_CS"
  }
}
"@ | Out-File -FilePath local.settings.json -Encoding utf8

# Deploy function code
func azure functionapp publish func-weather-dev-<suffix> --python
```

### Step 3: Configure Foundry Environment

```powershell
Set-Location ../agent-foundry

# Create .env file
@"
AZURE_AI_PROJECT_ENDPOINT=https://your-project.cognitiveservices.azure.com/
AZURE_AI_MODEL_DEPLOYMENT_NAME=gpt-4
WEATHER_FUNCTION_URL=$WEATHER_FUNCTION_URL
APPLICATIONINSIGHTS_CONNECTION_STRING=$APP_INSIGHTS_CS
ENVIRONMENT=production
"@ | Out-File -FilePath .env -Encoding utf8

# Load environment variables
Get-Content .env | ForEach-Object {
    if ($_ -match '^([^=]+)=(.*)$') {
        [System.Environment]::SetEnvironmentVariable($matches[1], $matches[2])
    }
}
```

### Step 4: Validate Workflow Configuration

```powershell
# Validate YAML configuration
python deploy_workflow.py validate

# Expected output:
# ✓ Configuration validation passed
#   - agent.yaml: Valid
#   - workflow.yaml: Valid
#   - Instructions file: Found
#   - Environment variables: Set
```

### Step 5: Deploy Foundry Workflow

```powershell
# Deploy the workflow
python deploy_workflow.py deploy

# Expected output:
# ✓ Workflow deployed successfully
#   Agent ID: asst_abc123xyz
#   Workflow: weather-clothing-advisor-workflow
#   Agent: WeatherClothingAdvisor
#   Tools: 1

# Save the Agent ID for later use
$AGENT_ID = "asst_abc123xyz"  # Replace with actual ID from output
```

### Step 6: Test Foundry Workflow

**Option A: Test via Azure Portal**

1. Navigate to Azure AI Foundry portal: https://ai.azure.com
2. Open your project
3. Go to "Agents" section
4. Find "WeatherClothingAdvisor" agent
5. Click "Test in playground"
6. Send message: "What should I wear in 10001?"

**Option B: Test via Python SDK**

```python
# test_foundry_agent.py
from azure.ai.projects import AIProjectClient
from azure.identity import DefaultAzureCredential
import os

# Initialize client
credential = DefaultAzureCredential()
client = AIProjectClient(
    endpoint=os.getenv("AZURE_AI_PROJECT_ENDPOINT"),
    credential=credential
)

# Create thread and send message
thread = client.agents.create_thread()
message = client.agents.create_message(
    thread_id=thread.id,
    role="user",
    content="What should I wear in 10001?"
)

# Run agent
run = client.agents.create_run(
    thread_id=thread.id,
    agent_id=os.getenv("AGENT_ID")  # From deployment output
)

# Wait for completion and get response
run = client.agents.wait_until_done(thread_id=thread.id, run_id=run.id)
messages = client.agents.list_messages(thread_id=thread.id)

print("Response:", messages.data[0].content[0].text.value)
```

**Option C: Test via REST API**

```powershell
# Get access token
$ACCESS_TOKEN = az account get-access-token --query accessToken -o tsv

# Create thread
$THREAD_RESPONSE = Invoke-RestMethod -Uri "$AZURE_AI_PROJECT_ENDPOINT/threads" `
    -Method Post `
    -Headers @{Authorization = "Bearer $ACCESS_TOKEN"} `
    -ContentType "application/json"

$THREAD_ID = $THREAD_RESPONSE.id

# Send message
$messageBody = @{
    role = "user"
    content = "What should I wear in 10001?"
} | ConvertTo-Json

Invoke-RestMethod -Uri "$AZURE_AI_PROJECT_ENDPOINT/threads/$THREAD_ID/messages" `
    -Method Post `
    -Headers @{Authorization = "Bearer $ACCESS_TOKEN"} `
    -ContentType "application/json" `
    -Body $messageBody

# Run agent
$runBody = @{
    agent_id = $AGENT_ID
} | ConvertTo-Json

Invoke-RestMethod -Uri "$AZURE_AI_PROJECT_ENDPOINT/threads/$THREAD_ID/runs" `
    -Method Post `
    -Headers @{Authorization = "Bearer $ACCESS_TOKEN"} `
    -ContentType "application/json" `
    -Body $runBody
```

---

## Post-Deployment Testing

### Automated Test Suite

Use the provided test script for both deployments:

```powershell
Set-Location tests/manual

# Test Container Apps deployment
python manual_test.py container-app "https://$CONTAINER_APP_URL"

# Test Foundry deployment (requires custom test implementation)
# Note: Foundry testing typically done via portal or SDK
```

### Manual Test Scenarios

| Scenario | Input | Expected Output | Success Criteria |
|----------|-------|-----------------|------------------|
| **Valid NYC zip** | "What should I wear in 10001?" | Weather + 3-5 recommendations | Response <5s, includes temp classification |
| **Valid LA zip** | "Check 90210" | Weather + recommendations | Hot weather items (>85°F typical) |
| **Invalid zip** | "What about 99999?" | Error message | Graceful error, helpful message |
| **Re-lookup** | "10001" then "60601" | Both responses | Session preserved, fresh data |
| **Rain conditions** | Test zip with rain | Umbrella, waterproof items | Precipitation-appropriate gear |
| **Cold weather** | Test zip <32°F | Winter coat, gloves, hat | Temperature-appropriate layers |

### Sample Test Commands

```powershell
# Test 1: Valid zip code
$body1 = @{ message = "What should I wear in 10001?" } | ConvertTo-Json
Invoke-RestMethod -Uri "https://$CONTAINER_APP_URL/chat" `
    -Method Post `
    -ContentType "application/json" `
    -Body $body1

# Test 2: Invalid zip code
$body2 = @{ message = "What about 99999?" } | ConvertTo-Json
Invoke-RestMethod -Uri "https://$CONTAINER_APP_URL/chat" `
    -Method Post `
    -ContentType "application/json" `
    -Body $body2

# Test 3: Re-lookup with session
$SESSION_ID = "test-session-123"
$body3 = @{
    message = "Check 10001"
    session_id = $SESSION_ID
} | ConvertTo-Json

Invoke-RestMethod -Uri "https://$CONTAINER_APP_URL/chat" `
    -Method Post `
    -ContentType "application/json" `
    -Body $body3

$body4 = @{
    message = "Now check 90210"
    session_id = $SESSION_ID
} | ConvertTo-Json

Invoke-RestMethod -Uri "https://$CONTAINER_APP_URL/chat" `
    -Method Post `
    -ContentType "application/json" `
    -Body $body4
```

---

## Monitoring & Observability

### Application Insights Queries

Access Application Insights in Azure Portal and run these KQL queries:

**1. Response Time Analysis (SC-001)**

```kql
traces
| where customDimensions.deployment_type in ("container-app", "foundry-agent")
| extend responseTime = todouble(customDimensions.response_time)
| where isnotnull(responseTime)
| summarize
    avg_response_time=avg(responseTime),
    p95_response_time=percentile(responseTime, 95),
    p99_response_time=percentile(responseTime, 99),
    total_requests=count()
    by bin(timestamp, 1h), tostring(customDimensions.deployment_type)
| render timechart
```

**2. Weather Function Calls**

```kql
dependencies
| where name == "get_weather"
| extend zip_code = tostring(customDimensions.zip_code)
| summarize
    total_calls=count(),
    avg_duration=avg(duration),
    success_rate=countif(success == true) * 100.0 / count()
    by zip_code
| order by total_calls desc
```

**3. Error Analysis**

```kql
exceptions
| where customDimensions.deployment_type in ("container-app", "foundry-agent")
| summarize error_count=count() by
    error_type=tostring(customDimensions.error_code),
    deployment=tostring(customDimensions.deployment_type)
| order by error_count desc
```

**4. Recommendation Counts (SC-002)**

```kql
traces
| where message contains "recommendations"
| extend rec_count = toint(customDimensions.recommendation_count)
| where isnotnull(rec_count)
| summarize
    total=count(),
    within_range=countif(rec_count >= 3 and rec_count <= 5),
    compliance_rate=countif(rec_count >= 3 and rec_count <= 5) * 100.0 / count()
    by bin(timestamp, 1h)
```

### Metrics Dashboard

Create a custom dashboard in Azure Portal with these tiles:

1. **Request Volume** - Total requests by deployment type
2. **Response Time** - P95 and P99 response times
3. **Success Rate** - Percentage of successful requests
4. **Error Rate** - Errors per hour by type
5. **Tool Calls** - get_weather function invocations
6. **Compliance** - SC-002 recommendation count compliance

### Alerts

Configure alerts for:

```bash
# Alert 1: High response time (SC-001 violation)
az monitor metrics alert create `
    --resource-group $RESOURCE_GROUP `
    --name "High Response Time" `
    --condition "avg traces.responseTime > 5" `
    --window-size 5m `
    --evaluation-frequency 1m

# Alert 2: High error rate
az monitor metrics alert create `
    --resource-group $RESOURCE_GROUP `
    --name "High Error Rate" `
    --condition "count exceptions > 10" `
    --window-size 5m `
    --evaluation-frequency 1m

# Alert 3: Weather Function failures
az monitor metrics alert create `
    --resource-group $RESOURCE_GROUP `
    --name "Weather Function Failures" `
    --condition "count dependencies where success == false > 5" `
    --window-size 5m `
    --evaluation-frequency 1m
```

---

## Troubleshooting

### Container Apps Issues

**Problem**: Container app not starting

```bash
# Check container logs
az containerapp logs show `
    --resource-group $RESOURCE_GROUP `
    --name ca-weather-advisor-dev-* `
    --follow

# Check revision status
az containerapp revision list `
    --resource-group $RESOURCE_GROUP `
    --name ca-weather-advisor-dev-*

# Common fixes:
# 1. Verify environment variables are set
# 2. Check container image exists in registry
# 3. Verify registry credentials are correct
# 4. Check Application Insights connection string
```

**Problem**: 503 errors from container app

```powershell
# Scale up replicas
az containerapp update `
    --resource-group $RESOURCE_GROUP `
    --name ca-weather-advisor-dev-* `
    --min-replicas 2 `
    --max-replicas 5

# Check health endpoint
Invoke-RestMethod -Uri "https://$CONTAINER_APP_URL/health"

# Verify Weather Function is accessible
Invoke-RestMethod -Uri "$WEATHER_FUNCTION_URL?zip_code=10001"
```

**Problem**: Slow response times

```bash
# Check Application Insights for bottlenecks
# Common causes:
# 1. OpenWeatherMap API timeout (check network)
# 2. Cold start (first request after idle)
# 3. Model inference latency (check AI model deployment)

# Optimize:
# - Increase CPU/memory allocation
# - Enable persistent connections
# - Add caching layer (if needed)
```

### Foundry Workflow Issues

**Problem**: Agent not found

```powershell
# List all agents
python deploy_workflow.py list

# Redeploy if missing
python deploy_workflow.py deploy

# Check Azure Portal: AI Foundry → Agents section
```

**Problem**: Tool execution failures

```powershell
# Verify Weather Function URL is accessible
Invoke-RestMethod -Uri "$WEATHER_FUNCTION_URL?zip_code=10001"

# Check agent configuration
cat agent.yaml | grep -A5 "tools:"

# Update agent with correct URL
# 1. Edit agent.yaml with correct WEATHER_FUNCTION_URL
# 2. python deploy_workflow.py update --agent-id $AGENT_ID
```

**Problem**: Workflow validation errors

```powershell
# Run validation
python deploy_workflow.py validate

# Common issues:
# 1. Missing environment variables
# 2. Invalid YAML syntax
# 3. Instructions file not found

# Fix:
# - Check .env file has all required variables
# - Validate YAML with: python -m yaml agent.yaml
# - Verify path: ../../specs/001-.../agent-prompts.md exists
```

### Weather Function Issues

**Problem**: OpenWeatherMap API errors

```powershell
# Test API key directly
Invoke-RestMethod -Uri "https://api.openweathermap.org/data/2.5/weather?zip=10001,US&appid=$OPENWEATHERMAP_API_KEY&units=imperial"

# Common issues:
# 1. API key not activated (wait 10-15 minutes after signup)
# 2. Rate limit exceeded (1000 calls/day on free tier)
# 3. Invalid zip code format

# Check function logs
func azure functionapp logstream func-weather-dev-<suffix>
```

**Problem**: Function cold start delays

```bash
# Enable Always On (requires Premium plan)
az functionapp config set `
    --resource-group $RESOURCE_GROUP `
    --name func-weather-dev-* `
    --always-on true

# Or switch to Premium plan
az functionapp plan update `
    --resource-group $RESOURCE_GROUP `
    --name asp-weather-dev-* `
    --sku P1V2
```

### Network & Connectivity

**Problem**: Cannot reach Weather Function from agent

```powershell
# Test network connectivity
# From Container App:
az containerapp exec `
    --resource-group $AZURE_RESOURCE_GROUP `
    --name ca-weather-advisor-dev-* `
    --command "curl $WEATHER_FUNCTION_URL?zip_code=10001"

# Check function app networking
az functionapp config access-restriction list `
    --resource-group $RESOURCE_GROUP `
    --name func-weather-dev-*

# Ensure function allows traffic from Container Apps
# Add Container Apps VNet to function app allowed networks if needed
```

---

## Cost Optimization

### Estimated Monthly Costs (Sweden Central)

| Component | Tier | Estimated Cost |
|-----------|------|----------------|
| **Container Apps** | Consumption | $5-20/month (depends on usage) |
| **Azure Functions** | Consumption | $0-5/month (1M executions free) |
| **Application Insights** | Standard | $2-10/month (1GB/month free) |
| **Log Analytics** | Pay-as-you-go | $2-5/month |
| **Azure AI Foundry** | Pay-per-use | $10-50/month (depends on model usage) |
| **Container Registry** | Basic | $5/month |
| **Total (Container Apps)** | | **~$15-45/month** |
| **Total (Foundry)** | | **~$20-70/month** |

**Note**: Costs vary based on:
- Request volume
- Model token usage (GPT-4 vs GPT-4o)
- Telemetry data volume
- Storage retention

### Cost Reduction Tips

1. **Use consumption-based tiers** - Pay only for actual usage
2. **Limit telemetry sampling** - Reduce to 20% in `host.json`
3. **Set retention policies** - 30 days for logs (vs 90 default)
4. **Use cheaper models** - GPT-3.5 Turbo vs GPT-4 for testing
5. **Enable auto-shutdown** - Stop dev environments when not in use
6. **Monitor usage** - Set budget alerts in Azure Portal

### Cleanup Script

```bash
# Delete Container Apps deployment
az containerapp delete `
    --resource-group $RESOURCE_GROUP `
    --name ca-weather-advisor-dev-* `
    --yes

# Delete Foundry agent
python deploy_workflow.py delete --agent-id $AGENT_ID

# Delete entire resource group (removes everything)
az group delete --name $RESOURCE_GROUP --yes --no-wait
```

---

## Cleanup

### Remove Container Apps Deployment Only

```powershell
Set-Location deploy/container-app

# Delete Container App
az containerapp delete `
    --resource-group $RESOURCE_GROUP `
    --name ca-weather-advisor-dev-* `
    --yes

# Keep shared resources (function, monitoring) for Foundry deployment
```

### Remove Foundry Deployment Only

```powershell
Set-Location src/agent-foundry

# Delete workflow/agent
python deploy_workflow.py delete --agent-id $AGENT_ID

# Shared resources remain intact
```

### Remove All Resources

```powershell
# Complete cleanup - deletes everything
az group delete --name $RESOURCE_GROUP --yes --no-wait

# Verify deletion
az group show --name $RESOURCE_GROUP
# Expected: ResourceGroupNotFound
```

### Selective Cleanup

```powershell
# Delete only specific resources
az containerapp delete --resource-group $AZURE_RESOURCE_GROUP --name ca-weather-advisor-dev-* --yes
az functionapp delete --resource-group $AZURE_RESOURCE_GROUP --name func-weather-dev-* --yes
az monitor app-insights component delete --resource-group $AZURE_RESOURCE_GROUP --app appi-weather-advisor-dev-*

# Keep resource group and other resources
```

---

## Next Steps

After successful deployment:

1. **Load Testing** - Test with high request volume to validate scaling
2. **Security Hardening** - Add authentication, network restrictions, secrets management
3. **CI/CD Pipeline** - Automate deployments with GitHub Actions or Azure DevOps
4. **Multi-Region** - Deploy to additional regions for high availability
5. **Caching Layer** - Add Redis for weather data caching
6. **Advanced Features** - Multi-day forecasts, location-based recommendations

---

## Additional Resources

- **Project Documentation**: [README.md](README.md)
- **Feature Specification**: [specs/001-weather-clothing-advisor/spec.md](specs/001-weather-clothing-advisor/spec.md)
- **Container Apps Guide**: [deploy/container-app/README.md](deploy/container-app/README.md)
- **Foundry Workflow Guide**: [src/agent-foundry/README.md](src/agent-foundry/README.md)
- **Azure Documentation**:
  - [Azure Container Apps](https://learn.microsoft.com/azure/container-apps/)
  - [Azure AI Foundry](https://learn.microsoft.com/azure/ai-foundry/)
  - [Azure Functions](https://learn.microsoft.com/azure/azure-functions/)
  - [Application Insights](https://learn.microsoft.com/azure/azure-monitor/app/app-insights-overview)

---

## Support

For issues or questions:
- Check [Troubleshooting](#troubleshooting) section
- Review [IMPLEMENTATION_STATUS.md](IMPLEMENTATION_STATUS.md) for known limitations
- Open an issue in the repository
- Consult Azure documentation for service-specific issues

---

**Status**: ✅ Production-ready deployment guide
**Last Updated**: 2026-01-20
**POC Version**: 1.0.0
