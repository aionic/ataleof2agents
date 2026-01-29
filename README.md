# A Tale of Two Agents

<p align="center">
  <img src="ataleoftwoagents.jpg" alt="A Tale of Two Agents" width="600">
</p>

**Build once, deploy anywhere**: A reference implementation for building AI agents that work in both self-hosted (Azure Container Apps) and managed (Azure AI Foundry) environments.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](./LICENSE)

---

## What This Repo Does

Demonstrates a **Weather Clothing Advisor** agent that:
1. Accepts a zip code from the user
2. Calls an external Weather API to get current conditions
3. Uses AI reasoning to recommend appropriate clothing
4. Returns conversational recommendations

**Real Value**: The portable agent pattern you can adapt for any external API integration.

---

## Quick Start

### Prerequisites
- Azure subscription with CLI authenticated (`az login`)
- Python 3.11+ with uv (`pip install uv`)
- OpenWeatherMap API key ([free tier](https://openweathermap.org/api))

### Setup
```powershell
# Clone and setup
git clone <repo-url>
cd agentdemo
uv sync
.\.venv\Scripts\Activate.ps1

# Configure environment
cp .env.example .env
# Edit .env with your values
```

### Deploy to Container Apps
```powershell
cd deploy/container-app
./deploy.ps1
```

### Deploy to Foundry
```powershell
# Set environment variables
$env:AZURE_AI_PROJECT_ENDPOINT = "https://your-project.services.ai.azure.com/api/projects/your-project"
$env:WEATHER_API_URL = "https://your-weather-api.azurecontainerapps.io"
$env:AZURE_AI_MODEL_DEPLOYMENT_NAME = "gpt-4.1"

# Register and test agent
python deploy/foundry/register_agent.py register --agent-name WeatherClothingAdvisor
python deploy/foundry/test_agent.py WeatherClothingAdvisor --message "What should I wear in 10001?"
```

---

## Choose Your Deployment

| Aspect | Container Apps (ACA) | Azure AI Foundry |
|--------|---------------------|------------------|
| **Response Time** | ~3-5s (faster) | ~10-30s |
| **Infrastructure** | You manage | Microsoft manages |
| **Setup Time** | ~15 min | ~10 min |
| **Best For** | High volume, low latency | Rapid dev, Foundry integration |

**Same agent code works in both**. Choose based on your needs.

---

## Repository Structure

```
src/
├── agent/                    # Unified agent package (runs anywhere)
│   ├── core/                 # Business logic, models, clothing recommendations
│   ├── hosting/              # /responses API server (Foundry protocol)
│   ├── tools/                # Weather tool implementation
│   └── telemetry/            # Application Insights integration
└── weather-api/              # External weather API service

deploy/
├── container-app/            # ACA deployment (Bicep + PowerShell)
├── foundry/                  # Foundry registration scripts
└── shared/                   # Shared infrastructure modules

samples/                      # Standalone SDK usage examples
docs/                         # Comprehensive guides
tests/                        # Test scripts
```

---

## How It Works

```
User: "What should I wear in 10001?"
           │
           ▼
    ┌──────────────┐
    │   Agent      │  ← Runs in ACA or Foundry
    │  (unified)   │
    └──────┬───────┘
           │
           ▼
    ┌──────────────┐
    │ Weather API  │  ← External HTTP call (OpenAPI)
    │ (Container)  │
    └──────┬───────┘
           │
           ▼
    ┌──────────────┐
    │ Azure OpenAI │  ← AI reasoning
    │   (gpt-4.1)  │
    └──────┬───────┘
           │
           ▼
"Based on 23°F weather in NYC, wear a heavy coat..."
```

**Key Insight**: The agent calls external APIs via HTTP, not embedded functions. This makes it portable across deployment targets.

---

## Test It

### ACA Agent (Direct)
```powershell
$body = '{"input": [{"role": "user", "content": "What should I wear in 10001?"}]}'
Invoke-RestMethod -Uri "https://ca-weather-dev-xxx.azurecontainerapps.io/responses" `
  -Method Post -ContentType "application/json" -Body $body
```

### Foundry Agent (via SDK)
```powershell
python deploy/foundry/test_agent.py WeatherClothingAdvisor --message "What should I wear in 90210?"
```

### Compare Both
```powershell
python deploy/foundry/compare_agents.py
```

---

## SDK Samples

See [samples/](./samples/) for standalone examples:

- **[create_simple_agent.py](./samples/create_simple_agent.py)** - Create a basic Foundry agent
- **[add_openapi_tool.py](./samples/add_openapi_tool.py)** - Add OpenAPI tools to agents

Uses `azure-ai-projects` SDK v2.0.0+ with GA API patterns.

---

## Documentation

| Guide | Description |
|-------|-------------|
| [QUICKSTART.md](./QUICKSTART.md) | 5-minute getting started |
| [Unified Agent](./docs/UNIFIED-AGENT.md) | Architecture and API reference |
| [Container Apps Deployment](./docs/guides/DEPLOYMENT-CONTAINER-APPS.md) | Full ACA deployment guide |
| [Foundry Deployment](./docs/guides/DEPLOYMENT-FOUNDRY.md) | Foundry registration guide |
| [Porting Guide](./docs/guides/PORTING-GUIDE.md) | Move between deployments |

---

## Environment Variables

```env
# Required for Foundry
AZURE_AI_PROJECT_ENDPOINT=https://your-project.services.ai.azure.com/api/projects/your-project
AZURE_AI_MODEL_DEPLOYMENT_NAME=gpt-4.1

# Required for Weather API
WEATHER_API_URL=https://your-weather-api.azurecontainerapps.io
OPENWEATHERMAP_API_KEY=your-key

# Optional (for meta-agent pattern)
EXTERNAL_AGENT_URL=https://your-aca-agent.azurecontainerapps.io
```

---

## License

MIT License - see [LICENSE](./LICENSE) for details.

---

**Built with**: Azure AI Projects SDK | Azure Container Apps | Azure AI Foundry | Azure OpenAI
