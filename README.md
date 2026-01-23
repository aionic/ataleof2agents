# A Tale of Two Agents

<p align="center">
  <img src="ataleoftwoagents.jpg" alt="A Tale of Two Agents" width="600">
</p>

**Build once, deploy anywhere**: A practical reference for building AI agents that work in both self-hosted (Azure Container Apps) and managed (Azure AI Foundry) environments.

> **Use Case**: Weather-based clothing advisor (throwaway example)
> **Real Value**: Portable agent pattern you can adapt for any external API integration

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](./LICENSE)

---

## Why This Repo?

You're evaluating Agent Framework and need to decide:
- **Container Apps** (self-hosted): Full control, faster responses
- **Foundry Hosted** (managed): No infrastructure, Foundry protocol compatibility
- **Both**: Same code, multiple deployment targets!

**This repo shows you**: Same agent code works in both environments. Choose based on your needs, not code limitations.

---

## Unified Agent Package 🆕

The **unified agent package** (`src/agent/`) enables true "write once, deploy anywhere":

```
src/agent/
├── main.py           # Unified entry point (responses/legacy/interactive modes)
├── core/             # Agent logic, models, business rules
├── hosting/          # Responses API server for Foundry protocol
├── tools/            # Weather tool implementation
└── telemetry/        # Application Insights integration
```

**Run modes:**
- `--mode responses` → Foundry Hosted compatible (`/responses` on port 8088)
- `--mode legacy` → Container Apps compatible (`/chat` on port 8000)
- `--mode interactive` → Local testing

👉 **[Unified Agent Documentation](./docs/UNIFIED-AGENT.md)**

---

## Quick Start (5 Minutes)

### What You'll Build
An AI agent that:
1. Calls an external weather API
2. Applies AI reasoning
3. Returns clothing recommendations

### Deploy to Container Apps
```powershell
# Clone and setup
git clone <repo-url>
cd agentdemo
.\.venv\Scripts\Activate.ps1

# Configure (add your keys to .env)
cp .env.example .env

# Deploy
./deploy/container-app/deploy.ps1
```

### Deploy to Foundry Hosted
```powershell
# Build and push container
docker build -f Dockerfile.agent --target foundry -t myregistry.azurecr.io/weather-advisor:v1 .
docker push myregistry.azurecr.io/weather-advisor:v1

# Register with Foundry
python deploy/scripts/azure_agent_manager.py
```

**⏱️ Total time**: ~15 minutes per deployment

---

## Choose Your Path

### 🚀 Container Apps (Self-Hosted)
**Best for**:
- High-volume workloads (2.3x faster responses)
- Full infrastructure control
- Custom networking requirements

**You get**:
- Docker containers deployed to Azure Container Apps
- Direct HTTP API calls
- Managed identity authentication
- Application Insights monitoring

👉 **[Container Apps Deployment Guide](./docs/guides/DEPLOYMENT-CONTAINER-APPS.md)**

---

### ☁️ Azure AI Foundry Hosted (Managed)
**Best for**:
- Rapid development
- No infrastructure management
- Foundry Responses API compatibility

**You get**:
- Container-based agent with Foundry protocol
- Managed agent runtime
- Built-in conversation management
- Foundry portal integration

👉 **[Foundry Deployment Guide](./docs/guides/DEPLOYMENT-FOUNDRY.md)**

---

### 🔄 Both (Side-by-Side)
**Best for**:
- Evaluating performance/cost
- Hybrid deployment strategies
- Migration scenarios

**Compare**:
- Same agent code, two deployment models
- See performance differences (tested: Container Apps 4.68s avg vs Foundry 10.88s avg)
- Cost analysis: 70% savings with hybrid pattern

👉 **[Comparison Report](./docs/comparison-report.md)** | **[Porting Guide](./docs/PORTING-GUIDE.md)**

---

## What's Inside

### Architecture
```
┌─────────────────────────────────────────────────────────┐
│  Agent (Either deployment model)                        │
├─────────────────────────────────────────────────────────┤
│  • Orchestrates workflow                                │
│  • Calls external Weather API                           │
│  • Applies AI reasoning (Azure OpenAI)                  │
│  • Returns recommendations                              │
└──────────────────┬──────────────────────────────────────┘
                   ↓
         External Weather API
         (OpenWeatherMap via Container Apps)
```

**Key Concept**: The agent calls external HTTP APIs - not embedded functions. This makes it portable.

### Repository Structure
```
src/
├── agent-container/       # Container Apps agent code
├── agent-foundry/         # Foundry registration & tests
└── shared/                # Common business logic

deploy/
├── container-app/         # Bicep templates & scripts
└── shared/                # Shared infrastructure

docs/                      # Comprehensive guides
tests/                     # Test scripts
samples/                   # Minimal code examples
```

---

## Documentation

### Getting Started
- **[Agent Framework Tutorial](./docs/AGENT-FRAMEWORK-TUTORIAL.md)** - Learn the concepts
- **[Quickstart](./QUICKSTART.md)** - Deploy in 5 minutes

### Deployment Guides
- **[Container Apps Deployment](./docs/DEPLOYMENT-CONTAINER-APPS.md)** - Self-hosted path
- **[Foundry Deployment](./docs/DEPLOYMENT-FOUNDRY.md)** - Managed path (both patterns)
- **[Porting Guide](./docs/PORTING-GUIDE.md)** - Move between deployments

### Reference
- **[Architecture Deep Dive](./docs/AGENT-FRAMEWORK-TUTORIAL.md#architecture-overview)** - How it all works
- **[Workflow Patterns](./docs/WORKFLOW-ORCHESTRATION-PATTERNS.md)** - Cost-effective patterns
- **[Comparison Report](./docs/comparison-report.md)** - Performance benchmarks

---

## Example: Weather Clothing Advisor

**What it does**: Takes a zip code, gets weather, recommends clothing.

**Why it matters**: Simple enough to understand quickly, complex enough to show real patterns.

**Your use case**: Replace weather API with your own external service. The pattern stays the same.

### Try It

**Container Apps**:
```bash
curl https://ca-weather-dev-<your-id>.azurecontainerapps.io/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "What should I wear in 10001?"}'
```

**Foundry**:
```python
from azure.ai.projects import AIProjectClient
from azure.identity import DefaultAzureCredential

client = AIProjectClient.from_connection_string(
    credential=DefaultAzureCredential(),
    conn_str="<your-connection-string>"
)

# Create thread and run agent
thread = client.agents.threads.create()
message = client.agents.messages.create(
    thread_id=thread.id,
    role="user",
    content="What should I wear in 10001?"
)
run = client.agents.runs.create_and_process(
    thread_id=thread.id,
    agent_id="<your-agent-id>"
)
```

---

## Key Concepts

### 1. Agent Framework
Microsoft's framework for building AI agents with:
- Declarative configuration (YAML)
- External API integration (OpenAPI)
- Workflow orchestration
- Portability across environments

### 2. External API Pattern
**Traditional**: Agent → Embedded function → External API
**This pattern**: Agent → External HTTP API (directly)

**Why**: Portability. HTTP APIs work everywhere.

### 3. Deployment Models
**Container Apps**: You manage Docker containers
**Foundry**: Microsoft manages the runtime
**Your agent code**: Works in both

### 4. Cost Optimization
**Agent-only**: Expensive (every request uses LLM)
**Hybrid**: 70% cheaper (use business logic for simple cases, agents for complex reasoning)

👉 **[Workflow Patterns Guide](./docs/WORKFLOW-ORCHESTRATION-PATTERNS.md)**

---

## Performance

Based on 7 test cases across both deployments:

| Metric | Container Apps | Foundry | Winner |
|--------|---------------|---------|--------|
| **Success Rate** | 100% (7/7) | 100% (7/7) | Tie ✅ |
| **Avg Response Time** | 4.68s | 10.88s | Container Apps 🚀 |
| **Setup Complexity** | High | Low | Foundry 👍 |
| **Cost (high volume)** | Lower | Higher | Container Apps 💰 |
| **Maintenance** | You | Microsoft | Foundry ⚙️ |

**Verdict**: Both work reliably. Choose based on your priorities.

👉 **[Full Comparison Report](./docs/comparison-report.md)**

---

## Prerequisites

### Required
- **Azure Subscription** with Owner or Contributor role
- **Azure CLI** - [Install](https://docs.microsoft.com/cli/azure/install-azure-cli)
- **Python 3.11+** - [Download](https://www.python.org/downloads/)
- **uv** - `pip install uv` or [install guide](https://docs.astral.sh/uv/)
- **OpenWeatherMap API Key** - [Free tier](https://openweathermap.org/api)

### Optional
- **Docker Desktop** - For local testing
- **VS Code** - Recommended editor
- **Azure AI Foundry Project** - For Foundry deployment

---

## Next Steps

1. **Learn the concepts**: [Agent Framework Tutorial](./docs/AGENT-FRAMEWORK-TUTORIAL.md)
2. **Deploy Container Apps**: [Deployment Guide](./docs/DEPLOYMENT-CONTAINER-APPS.md)
3. **Deploy Foundry**: [Deployment Guide](./docs/DEPLOYMENT-FOUNDRY.md)
4. **Compare both**: [Porting Guide](./docs/PORTING-GUIDE.md)
5. **Adapt for your use case**: Replace weather API with your own

---

## Contributing

This is a reference implementation. Feel free to:
- Adapt for your use case
- Submit improvements
- Share your experiences

## License

MIT License - see [LICENSE](./LICENSE) file for details.

---

## Support

- **Issues**: [GitHub Issues](link-to-issues)
- **Documentation**: See [docs/](./docs/) folder
- **Examples**: See [samples/](./samples/) folder

---

**Built with**: Microsoft Agent Framework | Azure Container Apps | Azure AI Foundry
**Example Use Case**: Weather-based clothing recommendations
**Real Value**: Portable agent pattern for any external API integration

👉 **[Get Started Now](./QUICKSTART.md)**
