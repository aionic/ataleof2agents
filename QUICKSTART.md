# Quick Start Guide

Get an agent running in 5 minutes. Choose your path:

---

## Option 1: Container Apps (Self-Hosted)

### Prerequisites
- Azure CLI logged in (`az login`)
- Python 3.11+ with uv
- OpenWeatherMap API key ([get free key](https://openweathermap.org/api))

### Deploy

```powershell
# 1. Clone and setup
git clone <repo-url>
cd agentdemo
uv venv
.\.venv\Scripts\Activate.ps1

# 2. Configure
cp .env.example .env
code .env  # Add your API keys

# 3. Deploy
cd deploy/container-app
./deploy.ps1
```

### Test

```powershell
# Get agent URL from deployment output
curl -X POST https://<your-agent-url>/chat `
  -H "Content-Type: application/json" `
  -d '{"message": "What should I wear in 10001?"}'
```

**Expected**: Clothing recommendations based on current NYC weather.

---

## Option 2: Azure AI Foundry (Managed)

### Prerequisites
- Azure AI Foundry project ([create at ai.azure.com](https://ai.azure.com))
- Weather API deployed (see Option 1 or use existing)
- Python 3.11+ with uv

### Deploy

```powershell
# 1. Clone and setup
git clone <repo-url>
cd agentdemo
uv venv
.\.venv\Scripts\Activate.ps1

# 2. Configure
cp .env.example .env
# Add:
#   AI_PROJECT_CONNECTION_STRING=<from-foundry-portal>
#   WEATHER_API_URL=<your-weather-api-url>

# 3. Register agent
cd src/agent-foundry
python register_agent.py
# Save the agent ID output

# 4. Test
python test_agent.py
```

**Expected**: Same recommendations, but through Foundry managed service.

---

## Option 3: Both (Compare)

Deploy to both platforms and compare:

```powershell
# 1. Deploy Container Apps (see Option 1)

# 2. Deploy Foundry (see Option 2)

# 3. Compare
cd src/agent-foundry
python compare_agents.py
```

**Result**: Side-by-side performance and quality comparison.

---

## What You Built

**An AI agent that**:
1. Takes a location (zip code)
2. Calls external weather API
3. Applies AI reasoning
4. Returns clothing recommendations

**Key Pattern**: Agent calls external HTTP API (portable across platforms)

---

## Next Steps

### Learn the Concepts
👉 **[Agent Framework Tutorial](./docs/AGENT-FRAMEWORK-TUTORIAL.md)**

### Full Deployment Guides
- **[Container Apps Guide](./docs/DEPLOYMENT-CONTAINER-APPS.md)** - Self-hosted details
- **[Foundry Guide](./docs/DEPLOYMENT-FOUNDRY.md)** - Managed service details

### Move Between Platforms
👉 **[Porting Guide](./docs/PORTING-GUIDE.md)**

### Optimize Costs
👉 **[Workflow Patterns](./docs/WORKFLOW-ORCHESTRATION-PATTERNS.md)**

---

## Troubleshooting

### Container Apps: 500 Error

**Check logs**:
```powershell
az containerapp logs show --name <agent-name> --resource-group foundry --tail 50
```

**Common issues**:
- Missing environment variables
- Weather API not accessible
- Azure OpenAI authentication failed

### Foundry: Agent Registration Fails

**Check**:
1. Connection string correct?
2. Weather API has external ingress?
3. OpenAPI spec valid?

**Fix**: See [Foundry Deployment Guide](./docs/DEPLOYMENT-FOUNDRY.md#troubleshooting)

### Weather API Not Responding

**Verify**:
```powershell
curl https://<weather-api-url>/api/weather?zip_code=10001
```

**Should return**: Weather data JSON

---

## Configuration Reference

### .env File

```env
# OpenWeatherMap API
OPENWEATHER_API_KEY=your_key_here

# Azure OpenAI
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/
AZURE_OPENAI_API_KEY=your_key_here
AZURE_OPENAI_DEPLOYMENT_NAME=gpt-4

# For Foundry deployment
AI_PROJECT_CONNECTION_STRING=your_connection_string

# Weather API URL (after Container Apps deployment)
WEATHER_API_URL=https://ca-weather-api-<suffix>.azurecontainerapps.io
```

### Azure Resources Created

**Container Apps deployment creates**:
- Container Apps environment
- Weather API container (internal/external ingress)
- Agent container (external ingress)
- Application Insights workspace
- Container Registry (if doesn't exist)

**Foundry deployment creates**:
- Agent registration in Foundry project
- No additional Azure resources

---

## Support

**Issues**: See troubleshooting sections in deployment guides
**Documentation**: [docs/](./docs/) folder
**Examples**: [samples/](./samples/) folder

---

**🎉 You're ready!** Choose your deployment path and start building.
