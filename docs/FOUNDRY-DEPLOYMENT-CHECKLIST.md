# Azure AI Foundry Deployment Checklist

**Date**: 2026-01-21
**Sprint**: Story 5 - Deploy and Test Foundry Agent

## Current Environment Status

### ✅ Completed Setup
- Weather API deployed with external ingress
  - Endpoint: `https://ca-weather-api-dev-ezbvua.mangomushroom-3560f614.swedencentral.azurecontainerapps.io`
  - OpenAPI spec created: `src/weather-api/openapi.json`
- Container agent working with Agent Framework + external API
- Foundry agent configuration created: `src/agent-foundry/agent.yaml`
- Registration script updated: `src/agent-foundry/register_agent.py`

### 🔍 Need to Verify in Foundry Portal

1. **Project Configuration**
   - Portal: https://anfoundy3lsww.services.ai.azure.com/
   - Project name: `weatheragentlsww` (assumed from legacy env var)
   - Resource group: `foundry`
   - Location: `swedencentral`

2. **Model Deployment**
   - Model: `gpt-4.1`
   - Verify deployment exists in Foundry portal under "Deployments"
   - Check quota and availability

3. **Permissions**
   - Current identity has "Contributor" or "AI Developer" role on project
   - Can create/update agents
   - Can register OpenAPI tools

### 📝 Environment Variables to Set

Before running `register_agent.py`, set these:

```powershell
# Project endpoint (verify correct format from portal)
$env:AZURE_AI_PROJECT_ENDPOINT = "https://anfoundy3lsww.services.ai.azure.com/api/projects/weatheragentlsww"

# Weather API URL (external Container App)
$env:WEATHER_API_URL = "https://ca-weather-api-dev-ezbvua.mangomushroom-3560f614.swedencentral.azurecontainerapps.io"

# Model deployment name
$env:AZURE_AI_MODEL_DEPLOYMENT_NAME = "gpt-4.1"
```

### ⚠️ Known Issues to Address

1. **Azure CLI Extension**
   - `az ai` command not available (extension not installed)
   - Not blocking - can use portal or SDK directly

2. **Project Endpoint Format**
   - Legacy env var has full project endpoint
   - Register_agent.py expects project endpoint
   - Verify correct format: `https://{resource}.services.ai.azure.com/api/projects/{project}`

3. **OpenAPI Tool Support**
   - Foundry SDK may use different structure for OpenAPI tools
   - May need to adjust tool definition format in register_agent.py
   - Check SDK docs: https://learn.microsoft.com/en-us/python/api/azure-ai-projects

## Deployment Steps (Story 5)

### Step 1: Verify Foundry Project (Manual - Portal)
- [ ] Login to https://anfoundy3lsww.services.ai.azure.com/
- [ ] Verify project `weatheragentlsww` exists
- [ ] Check model deployment `gpt-4.1` is available
- [ ] Note exact project endpoint from portal settings

### Step 2: Update Environment Variables
- [ ] Update `.env` with correct `AZURE_AI_PROJECT_ENDPOINT`
- [ ] Add `WEATHER_API_URL` to `.env`
- [ ] Load variables into current session

### Step 3: Test Registration Script (Dry Run)
```powershell
cd src/agent-foundry
python register_agent.py list
```
- Verifies SDK connection to Foundry
- Lists any existing agents

### Step 4: Register Agent
```powershell
python register_agent.py register --agent-name WeatherClothingAdvisor
```
- Creates agent in Foundry
- Registers OpenAPI tool
- Outputs agent ID

### Step 5: Test in Foundry Portal
- [ ] Navigate to Agents in Foundry portal
- [ ] Find WeatherClothingAdvisor agent
- [ ] Open Playground
- [ ] Test query: "What should I wear in 10001?"
- [ ] Verify weather API is called
- [ ] Verify recommendations are returned

### Step 6: Test via API
```powershell
# Create thread
$token = az account get-access-token --resource https://cognitiveservices.azure.com --query accessToken -o tsv
$endpoint = "https://anfoundy3lsww.services.ai.azure.com"
$agentId = "<agent-id-from-registration>"

$threadResponse = Invoke-RestMethod -Uri "$endpoint/agents/$agentId/threads" -Method POST -Headers @{Authorization="Bearer $token"; "Content-Type"="application/json"} -Body '{}'
$threadId = $threadResponse.id

# Send message
$messageBody = @{role = "user"; content = "What should I wear in 10001?"} | ConvertTo-Json
Invoke-RestMethod -Uri "$endpoint/agents/$agentId/threads/$threadId/messages" -Method POST -Headers @{Authorization="Bearer $token"; "Content-Type"="application/json"} -Body $messageBody

# Create run
$runResponse = Invoke-RestMethod -Uri "$endpoint/agents/$agentId/threads/$threadId/runs" -Method POST -Headers @{Authorization="Bearer $token"; "Content-Type"="application/json"} -Body '{}'
$runId = $runResponse.id

# Poll for completion
do {
  Start-Sleep -Seconds 2
  $runStatus = Invoke-RestMethod -Uri "$endpoint/agents/$agentId/threads/$threadId/runs/$runId" -Method GET -Headers @{Authorization="Bearer $token"}
} while ($runStatus.status -in @('queued', 'in_progress'))

# Get response
$messages = Invoke-RestMethod -Uri "$endpoint/agents/$agentId/threads/$threadId/messages" -Method GET -Headers @{Authorization="Bearer $token"}
$messages.data[0].content[0].text.value | ConvertTo-Json -Depth 10
```

## Potential Issues & Solutions

### Issue 1: OpenAPI Tool Format
**Symptom**: Registration fails with tool validation error

**Solution**: Check Azure AI Projects SDK version and adjust tool format:
```python
# May need to use different format
tool_definition = {
    "type": "azure_openapi",  # or "http"
    "azure_openapi": {
        "url": self.weather_api_url,
        "spec": openapi_spec,
        ...
    }
}
```

### Issue 2: Project Endpoint Not Found
**Symptom**: `AIProjectClient` connection fails

**Solution**: Verify endpoint format from portal:
1. Go to Foundry portal → Settings → API endpoint
2. Copy exact endpoint URL
3. Update `.env` file

### Issue 3: Model Deployment Not Available
**Symptom**: Registration succeeds but agent runs fail

**Solution**: 
1. Check deployments in portal
2. Verify `gpt-4.1` name matches exactly
3. May need to create deployment if missing

## Success Criteria

- [x] Environment variables verified
- [ ] Agent registered in Foundry (agent ID obtained)
- [ ] Agent visible in Foundry portal
- [ ] Test in playground returns clothing recommendations
- [ ] API test (threads/runs) works end-to-end
- [ ] Weather API called successfully (check logs)
- [ ] Response time < 5 seconds (SC-001)
- [ ] Recommendations match format (SC-002)

## Next Steps After Story 5

Once agent is deployed and tested:
- **Story 6**: Run comparison tests (Container agent vs Foundry agent)
- **Story 7**: Create advanced workflow orchestration examples
