# Azure Foundry Deployment Sprint

**Sprint Goal**: Deploy Weather Clothing Advisor agent to Azure AI Foundry using OpenAPI tool pattern to call external weather API container

**Sprint Duration**: 1-2 days  
**Start Date**: 2026-01-21  
**Current Commit**: b81ea07

---

## 🎯 Sprint Objective

Deploy the Weather Clothing Advisor agent to **Azure AI Foundry** as a managed agent service, calling the existing **Weather API Container App** as an external OpenAPI tool. This creates a production-ready hybrid architecture:

- **Agent**: Foundry-hosted managed service (serverless, auto-scaling)
- **Weather API**: Container Apps (external HTTP service)
- **Benefits**: Centralized agent management, consistent API patterns, separation of concerns

---

## 📚 Research Summary

### Key Findings from Microsoft Learn

**Best Practice: OpenAPI Tool Pattern**
- Azure AI Foundry supports OpenAPI 3.0 tools for external HTTP APIs
- Preferred over Azure Functions for simple HTTP endpoints
- Three authentication types: anonymous, API key, managed identity
- Agent doesn't execute functions - it requests them, you execute and return results

**Reference**: [How to use Foundry Agent Service with OpenAPI Specified Tools](https://learn.microsoft.com/en-us/azure/ai-foundry/agents/how-to/tools-classic/openapi-spec)

**Agent Creation via Python SDK**
```python
from azure.ai.projects import AIProjectClient
from azure.identity import DefaultAzureCredential

client = AIProjectClient(
    endpoint="https://your-project.services.ai.azure.com/",
    credential=DefaultAzureCredential()
)

agent = client.agents.create(
    name="WeatherClothingAdvisor",
    definition={
        "model": "gpt-4o",
        "instructions": "[system instructions]",
        "tools": [
            {
                "type": "openapi",
                "openapi": {
                    "name": "get_weather",
                    "description": "Get weather for zip code",
                    "spec": {
                        "openapi": "3.0.0",
                        "info": {...},
                        "paths": {...}
                    }
                }
            }
        ]
    }
)
```

**Alternative: Portal-Based Deployment**
- Create agent in Foundry portal UI
- Add OpenAPI tool with JSON schema
- Test in playground before API integration

---

## 🏗️ Architecture

### Current State (Container Apps)
```
┌─────────────────────────────────────────┐
│ Azure Container Apps Environment        │
│                                          │
│  ┌────────────┐      ┌────────────────┐│
│  │  Agent     │─────▶│  Weather API   ││
│  │ Container  │ HTTP │  Container     ││
│  │ (External) │      │  (Internal)    ││
│  └────────────┘      └────────────────┘│
│                                          │
└─────────────────────────────────────────┘
```

### Target State (Foundry Hybrid)
```
┌──────────────────────────┐        ┌─────────────────────────┐
│ Azure AI Foundry         │        │ Azure Container Apps    │
│                          │        │                         │
│  ┌────────────────────┐ │        │  ┌───────────────────┐ │
│  │ Weather Clothing   │ │  HTTPS │  │  Weather API      │ │
│  │ Advisor Agent      │─┼────────┼─▶│  Container        │ │
│  │                    │ │        │  │  (External)       │ │
│  │ Model: gpt-4.1     │ │        │  │                   │ │
│  │ Tool: get_weather  │ │        │  │  /api/weather     │ │
│  │ (OpenAPI spec)     │ │        │  │  /health          │ │
│  └────────────────────┘ │        │  └───────────────────┘ │
│                          │        │                         │
└──────────────────────────┘        └─────────────────────────┘
         │                                     │
         │ Users call via                      │ Calls
         │ Foundry API                         │ OpenWeatherMap
         ▼                                     ▼
```

---

## 📋 Sprint Backlog

### Story 1: Enable External Access to Weather API
**Acceptance Criteria**:
- ✅ Weather API container has external ingress enabled
- ✅ HTTPS endpoint accessible from internet
- ✅ Health check endpoint responds correctly
- ✅ Weather endpoint returns valid JSON for test zip codes

**Tasks**:
1. Update `deploy/container-app/main.bicep` - change weather API ingress to `external: true`
2. Redeploy weather API container
3. Test external endpoint with curl/Invoke-RestMethod
4. Document new external URL

**Estimate**: 30 minutes

---

### Story 2: Create OpenAPI 3.0 Specification for Weather API
**Acceptance Criteria**:
- ✅ Valid OpenAPI 3.0 JSON schema created
- ✅ Describes `/api/weather` GET endpoint with zip_code parameter
- ✅ Includes response schema matching current API contract
- ✅ Schema validated with OpenAPI validator

**Tasks**:
1. Create `src/weather-api/openapi.json` with full specification
2. Include servers, paths, components, security schemes
3. Validate against OpenAPI 3.0 spec
4. Add to repository

**Estimate**: 45 minutes

**Reference OpenAPI Structure**:
```json
{
  "openapi": "3.0.0",
  "info": {
    "title": "Weather API",
    "version": "1.0.0",
    "description": "Provides current weather data for US zip codes"
  },
  "servers": [
    {
      "url": "https://ca-weather-api-dev-ezbvua.mangomushroom-3560f614.swedencentral.azurecontainerapps.io"
    }
  ],
  "paths": {
    "/api/weather": {
      "get": {
        "operationId": "get_weather",
        "summary": "Get current weather for zip code",
        "parameters": [
          {
            "name": "zip_code",
            "in": "query",
            "required": true,
            "schema": {"type": "string", "pattern": "^[0-9]{5}$"}
          }
        ],
        "responses": {
          "200": {
            "description": "Weather data retrieved successfully",
            "content": {
              "application/json": {
                "schema": {
                  "$ref": "#/components/schemas/WeatherResponse"
                }
              }
            }
          }
        }
      }
    }
  },
  "components": {
    "schemas": {
      "WeatherResponse": {
        "type": "object",
        "properties": {
          "zip_code": {"type": "string"},
          "location": {"type": "string"},
          "temperature": {"type": "number"},
          "conditions": {"type": "string"},
          "wind_speed": {"type": "number"},
          "precipitation": {"type": "string"}
        }
      }
    }
  }
}
```

---

### Story 3: Update Foundry Agent Configuration
**Acceptance Criteria**:
- ✅ `src/agent-foundry/agent.yaml` updated with correct model
- ✅ Agent instructions reference existing agent-prompts.md
- ✅ OpenAPI tool configured with weather API endpoint
- ✅ Configuration validated (no syntax errors)

**Tasks**:
1. Update `agent.yaml` with:
   - Model: gpt-4.1 (or gpt-4o if available)
   - Instructions file path to agent-prompts.md
   - OpenAPI tool specification
2. Create/update `.env` file with Foundry endpoint
3. Validate YAML syntax

**Estimate**: 30 minutes

---

### Story 4: Create/Update Foundry Deployment Script
**Acceptance Criteria**:
- ✅ Python script creates agent in Foundry via SDK
- ✅ Script loads instructions from agent-prompts.md
- ✅ Script registers OpenAPI tool from specification
- ✅ Script outputs agent ID and endpoint for testing

**Tasks**:
1. Review existing `src/agent-foundry/register_agent.py`
2. Update to use OpenAPI tool pattern (not function calling)
3. Add OpenAPI spec loading from `openapi.json`
4. Test registration (dry-run if possible)
5. Document script usage

**Estimate**: 1 hour

**Key Code Pattern**:
```python
from azure.ai.projects import AIProjectClient
from azure.identity import DefaultAzureCredential
import json

# Load OpenAPI spec
with open('../weather-api/openapi.json') as f:
    openapi_spec = json.load(f)

# Load instructions
with open('../../specs/001-weather-clothing-advisor/contracts/agent-prompts.md') as f:
    instructions = f.read()

# Create client
client = AIProjectClient(
    endpoint=os.getenv("AZURE_AI_PROJECT_ENDPOINT"),
    credential=DefaultAzureCredential()
)

# Create agent with OpenAPI tool
agent = client.agents.create(
    name="WeatherClothingAdvisor",
    definition={
        "model": "gpt-4.1",
        "instructions": instructions,
        "tools": [
            {
                "type": "openapi",
                "openapi": {
                    "name": "get_weather",
                    "description": "Retrieve current weather data for a US zip code",
                    "spec": openapi_spec
                }
            }
        ]
    }
)

print(f"Agent created: {agent.id}")
```

---

### Story 5: Deploy and Test Foundry Agent
**Acceptance Criteria**:
- ✅ Agent successfully registered in Foundry
- ✅ Agent visible in Foundry portal
- ✅ Test in playground: "What should I wear in 10001?"
- ✅ Agent successfully calls weather API and returns recommendations
- ✅ Response quality matches container-based agent

**Tasks**:
1. Run deployment script: `python src/agent-foundry/register_agent.py`
2. Verify agent in Foundry portal (https://ai.azure.com)
3. Test in playground with multiple zip codes:
   - 10001 (cold weather test)
   - 90210 (warm weather test)
   - 98101 (rainy weather test)
   - 00000 (error handling test)
4. Document agent ID and endpoint
5. Test via API (not just playground)

**Estimate**: 1 hour

**API Test Pattern**:
```powershell
# Get access token
$token = az account get-access-token --resource https://cognitiveservices.azure.com --query accessToken -o tsv

# Create thread
$createThreadBody = @{} | ConvertTo-Json
$thread = Invoke-RestMethod `
  -Uri "https://anfoundy3lsww.services.ai.azure.com/agents/<agent-id>/threads" `
  -Method POST `
  -Headers @{Authorization="Bearer $token"} `
  -Body $createThreadBody `
  -ContentType "application/json"

# Send message
$messageBody = @{
  role = "user"
  content = "What should I wear in 10001?"
} | ConvertTo-Json

Invoke-RestMethod `
  -Uri "https://anfoundy3lsww.services.ai.azure.com/agents/<agent-id>/threads/$($thread.id)/messages" `
  -Method POST `
  -Headers @{Authorization="Bearer $token"} `
  -Body $messageBody `
  -ContentType "application/json"

# Run thread
$runBody = @{} | ConvertTo-Json
Invoke-RestMethod `
  -Uri "https://anfoundy3lsww.services.ai.azure.com/agents/<agent-id>/threads/$($thread.id)/runs" `
  -Method POST `
  -Headers @{Authorization="Bearer $token"} `
  -Body $runBody `
  -ContentType "application/json"
```

---

### Story 6: Comparison Testing
**Acceptance Criteria**:
- ✅ Same test queries run on both Foundry and Container Apps agents
- ✅ Response quality documented and compared
- ✅ Response times measured and documented
- ✅ Error handling validated on both platforms

**Tasks**:
1. Create test script with 5-10 test prompts
2. Run against Container Apps agent endpoint
3. Run against Foundry agent endpoint
4. Compare results in markdown table
5. Document findings

**Estimate**: 1 hour

**Comparison Matrix**:
| Test Case | Container Agent | Foundry Agent | Match? | Notes |
|-----------|----------------|---------------|---------|-------|
| Cold (10001) | ✅ Correct | ✅ Correct | ✅ | Response times similar |
| Hot (90210) | ✅ Correct | ✅ Correct | ✅ | - |
| Rain (98101) | ✅ Correct | ✅ Correct | ✅ | - |
| Invalid (00000) | ✅ Error handled | ✅ Error handled | ✅ | - |

---

## 🧹 Repository Cleanup Tasks

### Cleanup Story: Remove Function-Related Code
**Acceptance Criteria**:
- ✅ All Azure Function artifacts removed
- ✅ No broken references in documentation
- ✅ README/DEPLOYMENT.md updated to reflect current architecture
- ✅ Build/deploy scripts updated

**Tasks to Complete**:

**1. Delete Function Files**
```powershell
Remove-Item -Path "Dockerfile.function" -Force
Remove-Item -Path "deploy/shared/function-app.bicep" -Force
Remove-Item -Path "deploy/shared/deploy-function-code.ps1" -Force
Remove-Item -Path "src/function" -Recurse -Force
```

**2. Update Documentation**
Files to review and update:
- `README.md` - Remove function deployment instructions
- `DEPLOYMENT.md` - Update architecture diagrams
- `QUICKSTART.md` - Remove function setup steps
- `specs/001-weather-clothing-advisor/plan.md` - Mark function approach as deprecated

**3. Update Build Scripts**
- Review `build-and-push.ps1` - ensure only container images built
- Update `deploy/container-app/deploy.ps1` - remove function references

**4. Clean Git History (optional)**
- Consider adding `.gitattributes` to exclude function directory from history
- Or leave as-is for historical reference

**Estimate**: 45 minutes

---

## 📊 Sprint Metrics

### Story Points Breakdown
- Story 1: 1 point (simple config change)
- Story 2: 2 points (requires spec knowledge)
- Story 3: 1 point (config update)
- Story 4: 3 points (code changes, testing)
- Story 5: 3 points (deployment, validation)
- Story 6: 2 points (testing, documentation)
- Cleanup: 2 points

**Total**: 14 points

### Time Estimates
- Technical work: 5-6 hours
- Testing: 2-3 hours
- Documentation: 1 hour
- **Total**: 8-10 hours (1-2 days)

---

## ✅ Definition of Done

### Agent Deployment
- [ ] Weather API container accessible via external HTTPS endpoint
- [ ] OpenAPI 3.0 specification created and validated
- [ ] Agent registered in Azure AI Foundry
- [ ] Agent visible and testable in Foundry portal
- [ ] Agent successfully calls weather API container
- [ ] Test cases pass (cold, hot, rain, invalid zip)
- [ ] Response quality matches container-based agent
- [ ] API integration tested (not just playground)

### Documentation
- [ ] OpenAPI spec documented in repository
- [ ] Agent ID and endpoint documented
- [ ] Comparison test results documented
- [ ] Deployment instructions updated
- [ ] README reflects current architecture

### Code Quality
- [ ] No function-related code remains in repository
- [ ] All broken references fixed
- [ ] Git commit with clear message
- [ ] No linting/syntax errors

---

## 🚀 Deployment Sequence

### Phase 1: Weather API External Access (30 min)
```powershell
# 1. Update Bicep configuration
# Edit deploy/container-app/main.bicep

# 2. Deploy update
cd deploy/container-app
.\deploy.ps1 -ResourceGroupName foundry -OpenWeatherMapApiKey $env:OPENWEATHERMAP_API_KEY -SkipBuild

# 3. Test external endpoint
$weatherUrl = "https://ca-weather-api-dev-ezbvua.mangomushroom-3560f614.swedencentral.azurecontainerapps.io"
Invoke-RestMethod -Uri "$weatherUrl/health"
Invoke-RestMethod -Uri "$weatherUrl/api/weather?zip_code=10001"
```

### Phase 2: OpenAPI Spec Creation (45 min)
```powershell
# 1. Create specification file
New-Item -Path "src/weather-api/openapi.json" -ItemType File

# 2. Validate spec
# Use online validator: https://editor.swagger.io/
# Or install openapi-spec-validator: pip install openapi-spec-validator
```

### Phase 3: Foundry Agent Configuration (30 min)
```powershell
# 1. Update agent.yaml
# Edit src/agent-foundry/agent.yaml

# 2. Create/update .env
cd src/agent-foundry
cp .env.example .env
# Edit with proper values
```

### Phase 4: Deploy to Foundry (1 hour)
```powershell
# 1. Run registration script
cd src/agent-foundry
python register_agent.py

# 2. Verify in portal
# Navigate to https://ai.azure.com
# Find WeatherClothingAdvisor agent

# 3. Test in playground
# Try: "What should I wear in 10001?"
```

### Phase 5: Testing & Validation (2 hours)
```powershell
# 1. Run comparison tests
# Create test-foundry.ps1 script

# 2. Document results
# Update FOUNDRY-DEPLOYMENT-SPRINT.md with findings

# 3. Performance testing
# Measure response times for both deployments
```

### Phase 6: Cleanup (45 min)
```powershell
# 1. Remove function code
Remove-Item -Path "Dockerfile.function", "src/function" -Recurse -Force

# 2. Update documentation
# Edit README.md, DEPLOYMENT.md

# 3. Git commit
git add -A
git commit -m "feat: deploy agent to Azure Foundry with OpenAPI tool"
```

---

## 🔍 Testing Checklist

### Functional Testing
- [ ] Cold weather recommendations (10001, Chicago area)
- [ ] Hot weather recommendations (90210, Beverly Hills)
- [ ] Rainy weather recommendations (98101, Seattle)
- [ ] Invalid zip code handling (00000)
- [ ] Multiple consecutive queries (stateless behavior)
- [ ] Weather API error handling (simulate outage)

### Non-Functional Testing
- [ ] Response time < 5 seconds
- [ ] Error messages clear and helpful
- [ ] Tool calling successful (check logs)
- [ ] Telemetry captured correctly
- [ ] Agent scales under load

### Comparison Testing
- [ ] Same prompts to both agents
- [ ] Response quality equivalent
- [ ] Error handling consistent
- [ ] Performance within acceptable range

---

## 📝 Success Criteria

### Technical Success
✅ Agent deployed to Foundry  
✅ Weather API accessible externally  
✅ OpenAPI tool integration working  
✅ All test cases passing  
✅ Response quality matches container agent

### Business Success
✅ Demonstrates Foundry agent capabilities  
✅ Validates hybrid architecture pattern  
✅ Enables future agent deployments  
✅ Clean, maintainable codebase

### Documentation Success
✅ Complete deployment guide  
✅ Architecture clearly documented  
✅ Testing results recorded  
✅ Comparison analysis complete

---

## 🔗 References

### Azure Documentation
- [OpenAPI Specified Tools](https://learn.microsoft.com/en-us/azure/ai-foundry/agents/how-to/tools-classic/openapi-spec)
- [Azure AI Projects Python SDK](https://azuresdkdocs.z19.web.core.windows.net/python/azure-ai-projects/2.0.0b2/)
- [Agent Service Quickstart](https://learn.microsoft.com/en-us/azure/ai-foundry/agents/quickstart)

### Project Resources
- Foundry endpoint: https://anfoundy3lsww.services.ai.azure.com/
- Model deployment: gpt-4.1
- Weather API: ca-weather-api-dev-ezbvua
- Resource group: foundry
- Region: swedencentral

### Related Documents
- [agent-prompts.md](specs/001-weather-clothing-advisor/contracts/agent-prompts.md) - Agent instructions
- [FOUNDRY-DEPLOYMENT-PLAN.md](docs/FOUNDRY-DEPLOYMENT-PLAN.md) - Original high-level plan
- [DEPLOYMENT.md](DEPLOYMENT.md) - Container Apps deployment guide

---

## 🎯 Next Sprint Planning

### Post-Foundry Deployment
1. **Security Hardening**
   - Add managed identity auth between Foundry and weather API
   - Implement API key rotation
   - Add rate limiting

2. **Multi-Agent Patterns**
   - Explore agent-to-agent communication
   - Build specialized agents (weather only, clothing only)
   - Orchestration patterns

3. **Production Readiness**
   - Load testing
   - Disaster recovery planning
   - SLA definition
   - Cost optimization

---

**Sprint Owner**: Development Team  
**Stakeholders**: Architecture, Platform Engineering  
**Review Date**: End of sprint (2026-01-22 or 2026-01-23)
