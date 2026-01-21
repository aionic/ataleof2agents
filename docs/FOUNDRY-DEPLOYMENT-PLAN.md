# Azure Foundry Deployment Plan

**Date**: 2026-01-21
**Status**: Planning Phase
**Current Version**: b81ea07 (two-container architecture in Container Apps)

## 🎯 Objective

Deploy the Weather Clothing Advisor agent to **Azure AI Foundry** while maintaining the **weather API container in Container Apps**. This creates a hybrid architecture where:
- **Agent**: Hosted in Azure AI Foundry (managed agent service)
- **Weather API**: Remains in Container Apps (external HTTP service)

## 📐 Architecture Comparison

### Current (Container Apps Only)
```
┌─────────────────────────────────────────────────────────┐
│ Azure Container Apps Environment                        │
│                                                          │
│  ┌──────────────┐  Internal  ┌──────────────────────┐  │
│  │ Agent        │────────────▶│ Weather API          │  │
│  │ Container    │   Network   │ Container            │  │
│  │ (External)   │             │ (Internal Only)      │  │
│  └──────────────┘             └──────────────────────┘  │
│                                                          │
└─────────────────────────────────────────────────────────┘
```

### Target (Foundry + Container Apps Hybrid)
```
┌────────────────────────────────┐      ┌────────────────────────────┐
│ Azure AI Foundry               │      │ Azure Container Apps       │
│                                │      │                            │
│  ┌──────────────────────────┐ │      │  ┌──────────────────────┐ │
│  │ Weather Clothing Advisor │ │ HTTP │  │ Weather API          │ │
│  │ Agent (Foundry Hosted)   │─┼──────┼─▶│ Container            │ │
│  │                          │ │      │  │ (External Ingress)   │ │
│  │ - Model: gpt-4o          │ │      │  │                      │ │
│  │ - Tools: get_weather     │ │      │  │ - OpenWeatherMap     │ │
│  │ - Instructions: prompts  │ │      │  │ - Validation         │ │
│  └──────────────────────────┘ │      │  └──────────────────────┘ │
│                                │      │                            │
└────────────────────────────────┘      └────────────────────────────┘
         │                                       │
         │ User queries via                      │ Calls OpenWeatherMap
         │ Foundry API/Playground                │ API (external)
         │                                       │
         ▼                                       ▼
```

## 🔑 Key Decisions

### 1. Weather API Networking

**Decision**: Enable **external ingress** on weather API container

**Rationale**:
- Foundry-hosted agents cannot access Container Apps internal networks
- Weather API needs public endpoint for Foundry agent to call
- Use HTTPS + managed identity or API key for authentication

**Alternative Considered**: VNET integration (complex, may not be supported)

### 2. Authentication Between Foundry Agent and Weather API

**Options**:
- **Option A**: Managed Identity (preferred if supported)
- **Option B**: API key in Foundry environment variables
- **Option C**: No authentication (simplest for POC, less secure)

**Recommendation**: Start with Option C for POC, upgrade to managed identity

### 3. Agent Tool Definition

**Decision**: Use HTTP function tool pointing to weather API container

**Implementation**:
```json
{
  "type": "function",
  "function": {
    "name": "get_weather",
    "description": "Retrieve current weather data for a US zip code",
    "parameters": {
      "type": "object",
      "properties": {
        "zip_code": {
          "type": "string",
          "description": "5-digit US zip code"
        }
      },
      "required": ["zip_code"]
    },
    "url": "https://ca-weather-api-dev-ezbvua.mangomushroom-3560f614.swedencentral.azurecontainerapps.io/api/weather"
  }
}
```

### 4. Agent Instructions

**Decision**: Reuse existing agent-prompts.md contract

**Rationale**: Instructions are platform-agnostic, tested in container deployment

## 📋 Implementation Plan

### Phase 1: Update Weather API Container (Networking)

**Task 1.1**: Update Bicep to enable external ingress on weather API container

**File**: `deploy/container-app/main.bicep`

**Changes**:
```bicep
// Change from:
ingress: {
  external: false  // Internal only
  targetPort: 8080
}

// To:
ingress: {
  external: true   // Publicly accessible
  targetPort: 8080
  allowInsecure: false
  transport: 'auto'
}
```

**Task 1.2**: Redeploy weather API container

```powershell
.\deploy\container-app\deploy.ps1 `
  -ResourceGroupName foundry `
  -OpenWeatherMapApiKey $env:OPENWEATHERMAP_API_KEY `
  -SkipBuild
```

**Validation**: Test weather API endpoint directly:
```powershell
Invoke-RestMethod -Uri "https://ca-weather-api-dev-ezbvua.mangomushroom-3560f614.swedencentral.azurecontainerapps.io/api/weather?zip_code=10001"
```

### Phase 2: Configure Foundry Agent

**Task 2.1**: Update `src/agent-foundry/agent.yaml`

**Changes**:
```yaml
name: WeatherClothingAdvisor
model:
  deployment_name: gpt-4o  # Or gpt-4.1 if available
  temperature: 0.7
instructions_file: ../../specs/001-weather-clothing-advisor/contracts/agent-prompts.md
tools:
  - name: get_weather
    type: function
    url: https://ca-weather-api-dev-ezbvua.mangomushroom-3560f614.swedencentral.azurecontainerapps.io/api/weather
    parameters:
      type: object
      properties:
        zip_code:
          type: string
          description: 5-digit US zip code
      required:
        - zip_code
telemetry:
  enabled: true
  application_insights:
    connection_string: ${APPLICATIONINSIGHTS_CONNECTION_STRING}
```

**Task 2.2**: Update `src/agent-foundry/.env`

```bash
AZURE_AI_PROJECT_ENDPOINT=https://anfoundy3lsww.services.ai.azure.com/
AZURE_AI_MODEL_DEPLOYMENT_NAME=gpt-4.1
WEATHER_API_URL=https://ca-weather-api-dev-ezbvua.mangomushroom-3560f614.swedencentral.azurecontainerapps.io/api/weather
APPLICATIONINSIGHTS_CONNECTION_STRING=<from-existing-deployment>
```

### Phase 3: Deploy Agent to Foundry

**Task 3.1**: Review/update `register_agent.py`

Ensure script:
- Loads instructions from agent-prompts.md
- Registers get_weather tool with weather API container URL
- Handles authentication with Foundry project

**Task 3.2**: Run registration script

```powershell
cd src/agent-foundry
python register_agent.py
```

**Expected Output**:
```
✅ Agent registered successfully
   Agent ID: <agent-id>
   Agent Name: WeatherClothingAdvisor
   Project: https://anfoundy3lsww.services.ai.azure.com/
   Tools: get_weather
```

### Phase 4: Test Foundry Agent

**Task 4.1**: Test via Azure AI Foundry Playground

1. Navigate to https://anfoundy3lsww.services.ai.azure.com/
2. Select WeatherClothingAdvisor agent
3. Test prompt: "What should I wear in 10001?"

**Expected Behavior**:
- Agent calls get_weather tool with zip_code=10001
- Weather API returns weather data
- Agent generates clothing recommendations

**Task 4.2**: Test via API

```powershell
# Get agent endpoint from Foundry
$agentEndpoint = "https://anfoundy3lsww.services.ai.azure.com/agents/<agent-id>/chat"

# Test query
$body = @{
    messages = @(
        @{
            role = "user"
            content = "What should I wear in 10001?"
        }
    )
} | ConvertTo-Json -Depth 10

# Call agent
$token = az account get-access-token --resource https://cognitiveservices.azure.com --query accessToken -o tsv
Invoke-RestMethod -Uri $agentEndpoint -Method POST -Body $body -ContentType "application/json" -Headers @{Authorization="Bearer $token"}
```

### Phase 5: Comparison Testing

**Task 5.1**: Test same queries on both deployments

**Container Apps Agent**:
```powershell
$containerEndpoint = "https://ca-weather-dev-ezbvua.mangomushroom-3560f614.swedencentral.azurecontainerapps.io/chat"
$body = @{message = "What should I wear in 10001?"} | ConvertTo-Json
Invoke-RestMethod -Uri $containerEndpoint -Method POST -Body $body -ContentType "application/json"
```

**Foundry Agent**:
```powershell
$foundryEndpoint = "https://anfoundy3lsww.services.ai.azure.com/agents/<agent-id>/chat"
# [Same test as Phase 4.2]
```

**Compare**:
- Response quality
- Response time
- Tool calling behavior
- Error handling

## 🔍 Testing Scenarios

### Scenario 1: Basic Weather Query
- Input: "What should I wear in 10001?"
- Expected: Retrieves NYC weather, provides recommendations

### Scenario 2: Invalid Zip Code
- Input: "What about 00000?"
- Expected: Graceful error handling

### Scenario 3: Multiple Queries
- Input: "10001", then "90210", then "60601"
- Expected: Each query independent, correct weather data

### Scenario 4: Weather API Failure
- Simulate: Stop weather API container temporarily
- Expected: Agent handles error gracefully, informs user

## 📊 Success Criteria

- ✅ Weather API container accessible via public HTTPS endpoint
- ✅ Foundry agent registered with correct model and tools
- ✅ Agent successfully calls weather API container
- ✅ Agent generates appropriate clothing recommendations
- ✅ Response quality matches container-based agent
- ✅ Telemetry flowing to Application Insights
- ✅ Error handling works correctly

## 🚧 Known Considerations

### 1. Cold Start Latency
- Foundry-hosted agents may have different cold start characteristics
- Weather API container may scale down if not used frequently

### 2. Network Latency
- Foundry → Container Apps adds network hop
- May increase response time slightly compared to internal networking

### 3. Authentication
- Starting without authentication for simplicity
- Should add managed identity or API keys before production

### 4. Cost
- Foundry hosting charges separate from Container Apps
- Monitor costs for both services

### 5. Monitoring
- Need to correlate logs between Foundry (agent) and Container Apps (weather API)
- Application Insights should capture both

## 📝 Next Steps

1. **Immediate**: Update weather API Bicep for external ingress
2. **Next**: Configure agent.yaml with weather API URL
3. **Then**: Run register_agent.py to deploy to Foundry
4. **Finally**: Test and compare with container-based deployment

## 🔗 References

- Current Foundry endpoint: https://anfoundy3lsww.services.ai.azure.com/
- Current model deployment: gpt-4.1
- Weather API container: ca-weather-api-dev-ezbvua
- Agent container: ca-weather-dev-ezbvua (will remain for comparison)
- Git commit: b81ea07
