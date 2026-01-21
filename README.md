# Weather-Based Clothing Advisor POC

AI agent that provides personalized clothing recommendations based on current weather conditions using workflow orchestration.

## Overview

This POC demonstrates a **two-container microservices architecture** for AI agents:

1. **Agent Container**: Workflow orchestration with Microsoft Agent Framework
2. **Weather API Container**: FastAPI service for weather data retrieval

**Architecture implements the following pattern**:
1. **User Request**: Sent to agent container endpoint
2. **Parse Input**: Extract zip code from user message
3. **Get Weather**: Call internal weather API container via HTTP
4. **Generate Recommendations**: AI reasoning for clothing advice with Azure OpenAI
5. **Format Response**: Conversational output with telemetry

This architecture showcases:
- **Microservices Pattern**: Separation of concerns (agent logic vs. data services)
- **Internal Networking**: Containers communicate via Container Apps internal ingress
- **Managed Identity**: End-to-end authentication without keys
- **Version Tracking**: Git hash + timestamp for deployment traceability

## Features

- **US1 (P1)**: Basic weather lookup by zip code
- **US2 (P2)**: AI-generated clothing recommendations based on temperature, precipitation, and wind
- **US3 (P3)**: Multiple lookups in a single session

## Architecture

### Current Deployment (Container Apps)
```
User Request → Agent Container (External Ingress)
                    ↓
           WorkflowOrchestrator
                    ↓
    ┌───────────────┴─────────────────┐
    │  Workflow Execution             │
    ├─────────────────────────────────┤
    │ 1. Parse Input (zip code)       │
    │ 2. Call Weather API Container   │
    │    (Internal HTTP)              │
    │ 3. Generate Recommendations     │
    │    (Azure OpenAI via Foundry)   │
    │ 4. Format Response              │
    └─────────────────┬───────────────┘
                      ↓
            Application Insights
```

### Weather API Container (Internal)
```
Agent Container → Weather API Container
                       ↓
              FastAPI /api/weather
                       ↓
             OpenWeatherMap API
                       ↓
              Weather Data JSON
```

### Planned: Azure Foundry Deployment
```
User Request → Azure AI Foundry (Managed Agent)
                    ↓
              OpenAPI Tool Call
                    ↓
         Weather API Container (External)
                    ↓
              OpenWeatherMap API
```

## Technology Stack

- **Language**: Python 3.11
- **Package Manager**: uv
- **Agent Framework**: [Microsoft Agent Framework](https://github.com/microsoft/agent-framework)
- **Workflow**: WorkflowOrchestrator (programmatic Python orchestration)
- **Configuration**: YAML (agent.yaml, workflow.yaml)
- **Web Framework**: FastAPI (both containers)
- **Containers**: Docker multi-stage builds with uv package manager
- **Deployment**: Azure Container Apps with managed identity
- **Telemetry**: Azure Application Insights
- **Region**: Sweden Central
- **Versioning**: Git hash + timestamp (e.g., 5f000f4-20260121-093731)

## Quick Start

### Prerequisites

- Python 3.11+
- [uv](https://docs.astral.sh/uv/) package manager
- Azure CLI (for deployment)
- OpenWeatherMap API key (free tier)

### Local Development Setup

1. **Clone the repository**

   ```bash
   git clone <repository-url>
   cd agentdemo
   ```

2. **Install dependencies**

   ```bash
   uv sync --prerelease=allow
   ```

   **Note**: `--prerelease=allow` is required because the Microsoft Agent Framework is currently in preview.

3. **Configure environment variables**

   ```bash
   cp .env.example .env
   # Edit .env and add your OPENWEATHERMAP_API_KEY
   ```

4. **Run the weather function locally**

   ```bash
   cd src/function
   func start
   ```

5. **Run the Container Apps agent locally**

   ```bash
   cd src/agent-container
   uvicorn app:app --reload
   ```

## Project Structure

```text
src/
├── shared/              # Common data models and constants
│   ├── models.py        # WeatherRequest, WeatherData, ClothingRecommendation
│   └── constants.py     # REGION, DEFAULT_TEMP_UNIT, ZIP_CODE_PATTERN
│
├── function/            # Azure Function (weather API tool)
│   ├── function_app.py  # HTTP trigger for get_weather
│   └── requirements.txt # Function dependencies
│
├── agent-container/     # Container Apps Workflow (Programmatic)
│   ├── app.py           # FastAPI server with workflow endpoints
│   ├── agent_service.py # Agent lifecycle management
│   ├── workflow_orchestrator.py  # WorkflowOrchestrator class
│   ├── agent.yaml       # Agent configuration (model, tools, settings)
│   └── workflow.yaml    # Workflow definition (4 steps, dependencies)
│
└── agent-foundry/       # Foundry Workflow (Declarative)
    ├── agent.yaml       # Agent configuration (matches Container Apps)
    ├── workflow.yaml    # Declarative workflow orchestration
    ├── deploy_workflow.py  # Python deployment script
    └── README.md        # Foundry deployment guide

deploy/
├── shared/              # Shared infrastructure (monitoring, function)
├── container-app/       # Container Apps Bicep templates
└── foundry/             # Foundry infrastructure (TBD)

tests/manual/            # Manual testing scripts
specs/                   # Feature specifications
```

### Key Files in Both Workflow Deployments

**Container Apps** (Programmatic Workflow):
- **`workflow_orchestrator.py`**: Python class executing 4-step workflow
- **`agent.yaml`**: Agent configuration (model, tools, instructions)
- **`workflow.yaml`**: Workflow definition (steps, dependencies, validation)
- **`app.py`**: FastAPI server integrating WorkflowOrchestrator

**Foundry** (Declarative Workflow):
- **`agent.yaml`**: Agent configuration (model, tools, instructions)
- **`workflow.yaml`**: Declarative workflow orchestration
- **`deploy_workflow.py`**: Deployment script with YAML parsing

## Deployment

### Container Apps Deployment

See [deploy/container-app/README.md](deploy/container-app/README.md) for detailed deployment instructions.

```bash
cd deploy/container-app
./deploy.ps1 -ResourceGroupName "rg-weather-advisor-dev" -OpenWeatherMapApiKey "your-key"
```

### Foundry Workflow Deployment

See [src/agent-foundry/README.md](src/agent-foundry/README.md) for detailed deployment instructions.

**Using declarative YAML workflow**:
```bash
cd src/agent-foundry

# Validate configuration
python deploy_workflow.py validate

# Deploy workflow
python deploy_workflow.py deploy
```

The Foundry deployment uses:
- **`agent.yaml`**: Agent configuration (model, tools, instructions)
- **`workflow.yaml`**: Workflow orchestration (steps, validation, telemetry)
- **Declarative approach**: Version-controlled YAML files instead of imperative code

## Testing

Manual testing guide: [specs/001-weather-clothing-advisor/quickstart.md](specs/001-weather-clothing-advisor/quickstart.md)

**Sample Test Zip Codes**:

- 10001 (NYC) - Varied weather
- 90210 (Beverly Hills) - Hot weather
- 60601 (Chicago) - Cold weather
- 00000 - Invalid (error testing)

## Success Criteria

- ✅ SC-001: Response time <5 seconds
- ✅ SC-002: 3-5 clothing recommendations per query
- ✅ SC-003: 95% success rate for valid zip codes
- ✅ SC-004: Understandable recommendations
- ✅ SC-005: Handles extreme weather conditions

## Workflow Pattern Benefits

Both deployments demonstrate workflow orchestration with:

- **Structured Execution**: 4-step workflow with clear dependencies
- **Comprehensive Telemetry**: Track each step's duration and success
- **Error Handling**: Graceful degradation with appropriate fallback messages
- **Performance Validation**: SC-001 enforcement (5-second threshold)
- **Observability**: Application Insights integration for monitoring

**Implementation Comparison**:

| Aspect | Container Apps | Foundry |
|--------|---------------|---------|
| Pattern | Programmatic (Python) | Declarative (YAML) |
| Orchestration | WorkflowOrchestrator class | Foundry workflow engine |
| Configuration | agent.yaml + workflow.yaml | agent.yaml + workflow.yaml |
| Deployment | Docker container | Azure AI Foundry |
| Flexibility | Full Python control | YAML constraints |
| Best For | Custom logic, testing | Production, versioning |

## POC Scope

This is a **proof-of-concept** demonstrating:

- Azure Agent Framework SDK capabilities
- **Workflow orchestration patterns** (programmatic and declarative)
- Dual deployment patterns (Container Apps vs Foundry)
- Agent-function integration
- Telemetry with Application Insights

**Intentionally out of scope** (per POC Constitution):

- Production-grade error handling
- User authentication/authorization
- Data persistence
- Caching layer
- Rate limiting
- CI/CD automation

## Documentation

- [Feature Specification](specs/001-weather-clothing-advisor/spec.md)
- [Implementation Plan](specs/001-weather-clothing-advisor/plan.md)
- [Tasks](specs/001-weather-clothing-advisor/tasks.md)
- [Quick Start Testing](specs/001-weather-clothing-advisor/quickstart.md)
- [Data Model](specs/001-weather-clothing-advisor/data-model.md)
- [Technology Research](specs/001-weather-clothing-advisor/research.md)

## Constitution

This POC follows the [Agent Demo POC Constitution](.specify/memory/constitution.md) with three core principles:

1. **POC-First Simplicity**: Focus on essential features, avoid over-engineering
2. **Documentation-Driven Development**: Consult Microsoft Learn and Context7 for all technical decisions
3. **Rapid Validation**: Manual testing preferred, strategic automation only

## License

[Specify license]

## Contributing

[Specify contribution guidelines if applicable]
