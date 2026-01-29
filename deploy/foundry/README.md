# Azure AI Foundry Deployment Scripts

Scripts for registering and testing agents in Azure AI Foundry.

---

## Prerequisites

1. **Azure CLI** authenticated (`az login`)
2. **Python environment** with azure-ai-projects SDK:
   ```bash
   pip install azure-ai-projects>=2.0.0b2 azure-identity python-dotenv
   ```
3. **Environment variables** (set in `.env` or shell):
   ```env
   AZURE_AI_PROJECT_ENDPOINT=https://your-project.services.ai.azure.com/api/projects/your-project-name
   AZURE_AI_MODEL_DEPLOYMENT_NAME=gpt-4.1
   WEATHER_API_URL=https://ca-weather-api-dev-xxx.azurecontainerapps.io
   EXTERNAL_AGENT_URL=https://ca-weather-dev-xxx.azurecontainerapps.io  # For meta-agent
   ```

---

## Scripts

### `register_agent.py` - Native Foundry Agent

Registers a native Foundry agent with OpenAPI tools.

```powershell
# List all registered agents
python deploy/foundry/register_agent.py list

# Register the WeatherClothingAdvisor agent
python deploy/foundry/register_agent.py register --agent-name WeatherClothingAdvisor

# Delete an agent
python deploy/foundry/register_agent.py delete --agent-name WeatherClothingAdvisor
```

**What it creates**:
- Agent with `PromptAgentDefinition` using your Foundry model deployment
- OpenAPI tool (`get_weather`) pointing to your Weather API
- Instructions loaded from `specs/001-weather-clothing-advisor/contracts/agent-prompts.md`

---

### `register_external_agent.py` - Meta-Agent (ACA Integration)

Registers a meta-agent that calls your ACA-hosted agent via OpenAPI.

```powershell
# Register meta-agent that calls ACA agent
python deploy/foundry/register_external_agent.py register --agent-name WeatherAdvisorMeta

# List registered agents (same as register_agent.py)
python deploy/foundry/register_external_agent.py list
```

**What it creates**:
- Meta-agent with OpenAPI tool pointing to your ACA `/responses` endpoint
- Allows Foundry to orchestrate the ACA agent as a tool

---

### `test_agent.py` - Test Any Agent

Tests a registered Foundry agent via the conversations/responses API.

```powershell
# Test native agent
python deploy/foundry/test_agent.py WeatherClothingAdvisor --message "What should I wear in 10001?"

# Test meta-agent
python deploy/foundry/test_agent.py WeatherAdvisorMeta --message "What should I wear in 90210?"
```

**Output includes**:
- Agent response text
- Response time
- Success criteria validation

---

### `compare_agents.py` - Performance Comparison

Compares Foundry-native agent vs ACA agent performance.

```powershell
# Run comparison with default test queries
python deploy/foundry/compare_agents.py

# Custom test message
python deploy/foundry/compare_agents.py --message "What should I wear in Chicago?"
```

**Output includes**:
- Side-by-side response times
- Response quality comparison
- Recommendation summary

---

## Typical Workflow

### Deploy Fresh Environment

```powershell
# 1. Deploy Weather API to ACA (if not already deployed)
cd deploy/container-app
./deploy.ps1 -ResourceGroupName foundry

# 2. Set environment variables
$env:AZURE_AI_PROJECT_ENDPOINT = "https://your-project.services.ai.azure.com/api/projects/your-project"
$env:WEATHER_API_URL = "https://ca-weather-api-dev-xxx.azurecontainerapps.io"
$env:AZURE_AI_MODEL_DEPLOYMENT_NAME = "gpt-4.1"

# 3. Register native agent
python deploy/foundry/register_agent.py register --agent-name WeatherClothingAdvisor

# 4. Test it
python deploy/foundry/test_agent.py WeatherClothingAdvisor --message "What should I wear in NYC?"
```

### Add Meta-Agent (Optional)

```powershell
# 1. Set ACA agent URL
$env:EXTERNAL_AGENT_URL = "https://ca-weather-dev-xxx.azurecontainerapps.io"

# 2. Register meta-agent
python deploy/foundry/register_external_agent.py register --agent-name WeatherAdvisorMeta

# 3. Compare performance
python deploy/foundry/compare_agents.py
```

---

## SDK Version

These scripts use **azure-ai-projects SDK v2.0.0+** with the GA API:

- `AIProjectClient` for project connection
- `PromptAgentDefinition` for agent configuration
- `OpenApiAgentTool` with `OpenApiFunctionDefinition` for tools
- `conversations/responses` API for agent invocation

See [samples/](../../samples/) for more SDK usage examples.

---

## Troubleshooting

### "Agent not found"
- Run `register_agent.py list` to see registered agents
- Check that agent name matches exactly (case-sensitive)

### "Weather API error"
- Verify `WEATHER_API_URL` is accessible: `curl $env:WEATHER_API_URL/health`
- Check that the Weather API has external ingress enabled

### "Authentication failed"
- Run `az login` to refresh credentials
- Ensure your account has access to the Foundry project

### "Model deployment not found"
- Verify `AZURE_AI_MODEL_DEPLOYMENT_NAME` matches a deployment in your Foundry project
- Check the Foundry portal for available model deployments
