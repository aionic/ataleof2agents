# Porting Guide: Moving Between Container Apps and Foundry

Learn how to move your agent between Azure Container Apps and Azure AI Foundry with minimal code changes.

---

## Overview

**The Promise**: Build once, deploy anywhere

**The Reality**: It's true! Same agent logic works in both environments with minimal configuration changes.

**Time to Port**: ~30-60 minutes per direction

---

## What Stays the Same

✅ **Agent Instructions**: Your system prompt
✅ **Business Logic**: Clothing recommendations, data processing
✅ **External API**: Weather API stays unchanged
✅ **Models & Data Structures**: Shared code in `src/shared/`
✅ **Testing Strategy**: Same test cases work for both

---

## What Changes

🔄 **Deployment Method**: Containers vs. Managed Service
🔄 **Tool Registration**: Manual API calls vs. OpenAPI spec
🔄 **Invocation Pattern**: HTTP POST vs. SDK threads/runs
🔄 **Configuration**: YAML + Python vs. Python SDK
🔄 **Monitoring**: Container logs vs. Foundry portal

---

## Container Apps → Foundry

### Scenario
You have a working Container Apps agent and want to add Foundry deployment.

### Prerequisites
- Container Apps agent deployed and working
- Azure AI Foundry project created
- Weather API has external ingress enabled

### Step-by-Step Migration

#### 1. Enable External Access to Weather API

Foundry needs to call your weather API from outside:

```powershell
# Update weather API for external access
az containerapp ingress update `
  --name ca-weather-api-dev-<suffix> `
  --resource-group foundry `
  --external true

# Get new external URL
$weatherUrl = az containerapp show `
  --name ca-weather-api-dev-<suffix> `
  --resource-group foundry `
  --query "properties.configuration.ingress.fqdn" `
  --output tsv

Write-Host "Weather API URL: https://$weatherUrl"
```

#### 2. Create Foundry Agent Configuration

**New file**: `src/agent-foundry/agent.yaml`

```yaml
name: WeatherClothingAdvisor
description: Clothing recommendations based on weather

# Instructions from Container Apps agent
instructions: |
  You are a helpful clothing advisor.

  When user provides a location:
  1. Use get_weather tool to retrieve current weather
  2. Analyze temperature, conditions, precipitation
  3. Recommend appropriate clothing
  4. Be conversational and helpful

model: gpt-4  # Foundry project's deployed model

tools:
  - type: openapi
    openapi:
      name: get_weather
      description: Get current weather for US zip code
      spec_file: ../../weather-api/openapi.json
      auth:
        type: anonymous
```

**Key Changes**:
- Container Apps: Workflow orchestrator calls API
- Foundry: OpenAPI tool definition, Foundry calls API

#### 3. Verify OpenAPI Spec

Ensure `weather-api/openapi.json` has external URL:

```json
{
  "servers": [
    {
      "url": "https://ca-weather-api-dev-<suffix>.azurecontainerapps.io"
    }
  ]
}
```

#### 4. Set Environment Variables

```powershell
# Add to .env
AI_PROJECT_CONNECTION_STRING=<from-foundry-portal>
```

#### 5. Register Agent in Foundry

```powershell
cd src/agent-foundry
python register_agent.py
```

**Output**: Agent ID (save this!)

#### 6. Test Foundry Agent

```powershell
python test_agent.py
```

**Verify**: Same recommendations as Container Apps agent

#### 7. Compare Results

```powershell
# Run comparison tests
python compare_agents.py
```

**Expected**: Both agents return equivalent recommendations

### Code Comparison

**Container Apps** (`workflow_orchestrator.py`):
```python
class WorkflowOrchestrator:
    def run(self, message: str):
        # You control the flow
        zip_code = self._extract_zip_code(message)
        weather = self._get_weather(zip_code)
        recommendations = self._generate_recommendations(message, weather)
        return {"response": recommendations}

    def _get_weather(self, zip_code: str):
        # Direct HTTP call
        response = requests.get(
            f"{self.weather_api_url}/api/weather",
            params={"zip_code": zip_code}
        )
        return response.json()
```

**Foundry** (`register_agent.py`):
```python
# Define tool, Foundry handles invocation
tool = {
    "type": "openapi",
    "openapi": {
        "name": "get_weather",
        "spec": load_openapi_spec(),
        "auth": {"type": "anonymous"}
    }
}

agent = client.agents.create_agent(
    model="gpt-4",
    instructions="...",  # Same instructions
    tools=[tool]
)
# Foundry calls weather API automatically when needed
```

**Key Insight**: Same business logic, different orchestration.

---

## Foundry → Container Apps

### Scenario
You have a Foundry agent and want to self-host for performance/cost.

### Prerequisites
- Foundry agent working
- Docker installed
- Azure Container Registry access

### Step-by-Step Migration

#### 1. Extract Agent Instructions

From `src/agent-foundry/agent.yaml`:
```yaml
instructions: |
  You are a helpful clothing advisor...
```

Copy these to Container Apps configuration.

#### 2. Create Workflow Orchestrator

**New file**: `src/agent-container/workflow_orchestrator.py`

```python
class WorkflowOrchestrator:
    def __init__(self):
        self.weather_api_url = os.getenv("WEATHER_API_URL")
        self.openai_client = self._init_openai()

    def run(self, user_message: str) -> Dict[str, Any]:
        # Step 1: Parse input
        zip_code = self._extract_zip_code(user_message)

        # Step 2: Get weather (same API as Foundry used)
        weather = self._get_weather(zip_code)

        # Step 3: Generate recommendations (same model)
        recommendations = self._generate_recommendations(
            user_message, weather
        )

        return {
            "response": recommendations,
            "metadata": {"zip_code": zip_code, "weather": weather}
        }

    def _get_weather(self, zip_code: str):
        # Same weather API Foundry was calling
        response = requests.get(
            f"{self.weather_api_url}/api/weather",
            params={"zip_code": zip_code}
        )
        return response.json()

    def _generate_recommendations(self, message, weather):
        # Use same model as Foundry
        context = f"Weather: {weather['temperature']}°F, {weather['condition']}"

        response = self.openai_client.complete(
            messages=[
                {"role": "system", "content": self.agent_instructions},
                {"role": "user", "content": f"{context}\n\n{message}"}
            ]
        )

        return response.choices[0].message.content
```

**Key Changes**:
- Foundry: Automatic tool invocation
- Container Apps: Manual API orchestration

#### 3. Create FastAPI Endpoint

**File**: `src/agent-container/app.py`

```python
from fastapi import FastAPI
from workflow_orchestrator import WorkflowOrchestrator

app = FastAPI()
orchestrator = WorkflowOrchestrator()

@app.post("/chat")
async def chat(request: ChatRequest):
    result = orchestrator.run(request.message)
    return result
```

#### 4. Create Dockerfile

```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY src/agent-container/ .
COPY src/shared/ ./shared/

CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]
```

#### 5. Deploy to Container Apps

```powershell
cd deploy/container-app
./deploy.ps1
```

#### 6. Test Container Apps Agent

```powershell
$agentUrl = az containerapp show `
  --name ca-weather-dev-<suffix> `
  --resource-group foundry `
  --query "properties.configuration.ingress.fqdn" `
  --output tsv

curl -X POST "https://$agentUrl/chat" `
  -H "Content-Type: application/json" `
  -d '{"message": "What should I wear in 10001?"}'
```

#### 7. Compare Performance

Run same test cases on both:

| Metric | Foundry | Container Apps |
|--------|---------|----------------|
| Avg Response Time | 10.88s | 4.68s |
| Cold Start | ~5s | ~2s |
| Success Rate | 100% | 100% |

**Result**: Container Apps 2.3x faster!

---

## Hybrid Deployment: Run Both

### Use Case
- Foundry for portal/orchestration
- Container Apps for high-performance API

### Pattern: External Agent Registration

Register your Container Apps agent as a tool in Foundry:

```python
# src/agent-foundry/register_external_agent.py
external_agent_tool = {
    "type": "openapi",
    "openapi": {
        "name": "chatWithExternalAgent",
        "spec": {
            "openapi": "3.0.0",
            "paths": {
                "/chat": {
                    "post": {
                        "operationId": "chat",
                        "requestBody": {...},
                        "responses": {...}
                    }
                }
            },
            "servers": [{
                "url": "https://ca-weather-dev-<suffix>.azurecontainerapps.io"
            }]
        },
        "auth": {"type": "anonymous"}
    }
}

meta_agent = client.agents.create_agent(
    model="gpt-4",
    name="ExternalAgentInvoker",
    instructions="Forward requests to external agent tool",
    tools=[external_agent_tool]
)
```

**Result**: Foundry meta-agent calls your Container Apps agent.

**Benefits**:
- Keep Container Apps performance
- Add Foundry orchestration
- Best of both worlds

---

## Configuration Mapping

### Agent Instructions

**Container Apps**: `src/agent-container/agent.yaml`
```yaml
instructions: |
  Your system prompt here...
```

**Foundry**: `src/agent-foundry/agent.yaml`
```yaml
instructions: |
  Same system prompt...
```

**Migration**: Copy/paste instructions between files.

### API Endpoints

**Container Apps**: Environment variables
```env
WEATHER_API_URL=http://ca-weather-api.internal
```

**Foundry**: OpenAPI spec
```json
{
  "servers": [{"url": "https://ca-weather-api.azurecontainerapps.io"}]
}
```

**Migration**: Update URL from internal to external.

### Model Configuration

**Container Apps**: Environment variables
```env
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/
AZURE_OPENAI_DEPLOYMENT_NAME=gpt-4
```

**Foundry**: Project configuration
```python
# Model comes from Foundry project
agent = client.agents.create_agent(
    model="gpt-4"  # References project's deployment
)
```

**Migration**: Ensure same model in both environments.

---

## Testing Strategy

### Test Cases (Work for Both)

```python
test_cases = [
    {"message": "What should I wear in 10001?", "expected": "cold weather clothing"},
    {"message": "Clothing for 90210?", "expected": "warm weather clothing"},
    {"message": "What to wear in Seattle 98101?", "expected": "rain gear"},
]

def test_agent(agent_endpoint):
    for case in test_cases:
        response = call_agent(agent_endpoint, case["message"])
        assert case["expected"] in response.lower()
```

### Comparison Testing

```python
# test_both.py
container_result = test_container_agent(test_cases)
foundry_result = test_foundry_agent(test_cases)

assert container_result.success_rate == foundry_result.success_rate
print(f"Container Apps: {container_result.avg_time:.2f}s")
print(f"Foundry: {foundry_result.avg_time:.2f}s")
```

---

## Common Challenges

### Challenge 1: Internal vs External URLs

**Issue**: Foundry can't reach internal Container Apps URLs

**Solution**: Enable external ingress for APIs Foundry needs
```powershell
az containerapp ingress update --external true
```

### Challenge 2: Authentication

**Issue**: Different auth patterns

**Container Apps**: Managed identity between containers
**Foundry**: Anonymous or API key for public endpoints

**Solution**: Use anonymous auth for Foundry-accessible APIs

### Challenge 3: Response Format

**Issue**: Different response structures

**Container Apps**: Custom format
```json
{"response": "...", "metadata": {...}}
```

**Foundry**: Message content
```python
message.content[0].text.value
```

**Solution**: Normalize in test code or adapter layer

---

## Decision Matrix

| Consideration | Choose Container Apps | Choose Foundry | Use Both |
|---------------|----------------------|----------------|----------|
| **Performance Critical** | ✅ 2.3x faster | ❌ Slower | 🟡 Hybrid |
| **Development Speed** | ❌ More setup | ✅ Rapid | 🟡 Foundry first |
| **Cost Sensitive** | ✅ Lower at scale | ❌ Higher | 🟡 Optimize routing |
| **Need Portal UI** | ❌ Build yourself | ✅ Built-in | ✅ Use Foundry |
| **Custom Infrastructure** | ✅ Full control | ❌ Limited | 🟡 Container Apps |
| **No Ops Team** | ❌ Need DevOps | ✅ Managed | ✅ Foundry |

---

## Next Steps

### Deploy to Both Platforms

**Container Apps**:
👉 **[Container Apps Deployment Guide](./DEPLOYMENT-CONTAINER-APPS.md)**

**Foundry**:
👉 **[Foundry Deployment Guide](./DEPLOYMENT-FOUNDRY.md)**

### Learn More

**Patterns**:
👉 **[Workflow Orchestration Patterns](./WORKFLOW-ORCHESTRATION-PATTERNS.md)**

**Deep Dive**:
👉 **[Agent Framework Tutorial](./AGENT-FRAMEWORK-TUTORIAL.md)**

---

## Summary

**Porting is easy** because:
- Same agent instructions
- Same external APIs
- Same business logic
- Different orchestration layer only

**Time investment**:
- Container Apps → Foundry: 30 minutes
- Foundry → Container Apps: 60 minutes
- Hybrid deployment: 45 minutes

**Result**: Flexibility to choose best deployment for each use case without rewriting agents.
