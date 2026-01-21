# Implementation Plan: Weather-Based Clothing Advisor

**Branch**: `001-weather-clothing-advisor` | **Date**: 2026-01-20 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `/specs/001-weather-clothing-advisor/spec.md`

## Summary

Build a POC AI agent that accepts a US zip code, retrieves current weather data via a Weather API tool, and provides personalized clothing recommendations. The solution demonstrates **two deployment architectures** on Azure:

1. **Container Apps Deployment**: Agent + Weather API deployed as containers with Azure AI Foundry telemetry
2. **Foundry Agent Service Deployment**: Agent hosted by managed service + Weather API with Azure AI Foundry telemetry

**Technical Approach**: Python 3.11 with Azure Agent Framework SDK for agent logic, FastAPI Weather API service for weather data, OpenWeatherMap API for weather data source, uv for package management, deployed to Sweden Central region. Both deployments integrate with Azure AI Foundry for observability and tracing.

**POC Focus**: Demonstrate dual deployment patterns, agent-function integration, and Foundry telemetry - NOT production-grade error handling or enterprise features.

## Technical Context

**Language/Version**: Python 3.11

**Web Framework**: FastAPI (for Container Apps agent HTTP server)

**Primary Dependencies**:

- `agent-framework` (≥0.1.0) - Core Azure Agent Framework
- `agent-framework-azure-ai` (≥0.1.0) - Azure AI Foundry integration
- `fastapi` (≥0.109.0) - Web framework for Container Apps agent
- `uvicorn` (≥0.27.0) - ASGI server for FastAPI
- `requests` (≥2.31.0) - HTTP client for OpenWeatherMap API
- `azure-identity` (≥1.15.0) - Azure authentication (DefaultAzureCredential)
- `azure-monitor-opentelemetry` (≥1.2.0) - Telemetry integration for Foundry

**Storage**: N/A (stateless POC, agent conversation threads managed by Azure AI Agent Service in Foundry deployment)

**Testing**: Manual testing per quickstart.md (POC approach per Constitution Principle III)

**Target Platform**: Azure (Sweden Central region)

- Azure Container Apps (for agent deployment #1)
- Azure AI Foundry Agent Service (for agent deployment #2)
- Azure Application Insights (telemetry backend for both deployments)

**Project Type**: Multi-component hybrid (shared Weather API + dual agent deployments)

**Performance Goals**: <5 seconds end-to-end response time (SC-001: weather fetch + agent processing)

**Constraints**:

- OpenWeatherMap free tier: 1,000 API calls/day
- 5-digit US zip codes only (FR-001)
- No persistent storage required (stateless weather lookups)
- Manual deployment demonstrations required (no CI/CD automation for POC)

**Scale/Scope**: POC for 1-10 concurrent users, ~50-100 requests/day during demo period

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### Principle I: POC-First Simplicity

**Status**: ✅ PASS

**Evidence**:

- Feature scope limited to 3 user stories (weather lookup, recommendations, re-lookup)
- No database - stateless operation
- Manual testing only (no automated test suite)
- Inline recommendation logic (no complex rule engine)
- Free-tier external API (OpenWeatherMap)
- Essential features only: weather + recommendations

**POC Simplifications Applied**:

- No user authentication or authorization
- No data persistence or history tracking
- No caching layer (fresh API calls every time)
- No rate limiting beyond API quotas
- No production monitoring dashboards (basic telemetry only)
- No comprehensive error recovery strategies

### Principle II: Documentation-Driven Development

**Status**: ✅ PASS

**Evidence**:

- All technology decisions in [research.md](research.md) cite authoritative sources:
  - Azure Agent Framework: Microsoft Learn documentation
  - Weather API service (FastAPI): Implementation notes
  - Azure Container Apps: Microsoft Learn tutorials
  - Azure AI Foundry: Official agent service documentation
  - uv package manager: Context7 documentation (official Astral docs)
  - OpenWeatherMap: API provider documentation

**Documentation Checkpoints Completed**:

- ✅ Agent Framework best practices reviewed (Durable Agents patterns)
- ✅ Weather API service design documented
- ✅ Container Apps deployment workflows researched
- ✅ Foundry Agent Service registration patterns reviewed
- ✅ Application Insights telemetry integration documented
- ✅ uv project initialization patterns consulted

### Principle III: Rapid Validation

**Status**: ✅ PASS

**Evidence**:

- Clear acceptance criteria for each user story (Given/When/Then scenarios)
- Manual test scenarios defined in [quickstart.md](quickstart.md)
- 5 success criteria with measurable thresholds (SC-001 through SC-005)
- Sample test zip codes provided (10001, 90210, 60601, etc.)
- Demo script included for stakeholder validation
- Both deployment models testable independently

**Validation Plan**:

- Phase 0: Technology choices validated via documentation research ✅
- Phase 1: Data model + contracts validated against requirements ✅
- Phase 2: Implementation tasks prioritized by user story (P1 → P2 → P3)
- Phase 3: Manual testing per quickstart.md for both deployments
- Phase 4: Demo to stakeholders using provided demo script

**Overall Constitution Compliance**: 3/3 principles PASS - No violations requiring justification

## Project Structure

### Documentation (this feature)

```text
specs/001-weather-clothing-advisor/
├── plan.md              # This file (/speckit.plan command output)
├── research.md          # Phase 0 output - technology decisions with sources
├── data-model.md        # Phase 1 output - entity definitions and schemas
├── quickstart.md        # Phase 1 output - manual testing guide
├── contracts/           # Phase 1 output - function tool + agent prompts
│   ├── weather-api-tool.json
│   └── agent-prompts.md
└── tasks.md             # Phase 2 output (/speckit.tasks command - pending)
```

### Source Code (repository root)

```text
src/
├── shared/                         # Shared code between deployments
│   ├── models.py                   # Data models (Location, WeatherData, etc.)
│   └── constants.py                # Shared constants (temp ranges, API config)
│
├── weather-api/                    # Weather API service (shared by both deployments)
│   ├── app.py                      # FastAPI endpoint for get_weather tool
│   ├── weather_service.py          # OpenWeatherMap API client
│   ├── requirements.txt            # Generated from pyproject.toml by uv
│   └── .env.example                # Weather API environment variables
│
├── agent-container/                # Deployment 1: Container Apps
│   ├── app.py                      # Agent application entry point
│   ├── agent_service.py            # Agent initialization with tools
│   ├── clothing_logic.py           # Recommendation generation logic
│   ├── telemetry.py                # Application Insights integration
│   ├── Dockerfile                  # Container image definition
│   ├── requirements.txt            # Generated from pyproject.toml by uv
│   └── .env.example                # Environment variables template
│
├── agent-foundry/                  # Deployment 2: Foundry Agent Service
│   ├── register_agent.py           # Script to register agent in Foundry
│   ├── agent_config.py             # Agent configuration (tools, prompts)
│   ├── clothing_logic.py           # Recommendation logic (same as container)
│   ├── requirements.txt            # Generated from pyproject.toml by uv
│   └── .env.example                # Environment variables template
│
└── deployments/                    # Infrastructure and deployment scripts
    ├── container-app/
    │   ├── deploy.sh                # Deployment script for Container Apps
    │   ├── bicep/
    │   │   ├── main.bicep           # Main infrastructure template
    │   │   ├── container-app.bicep  # Container Apps resources
    │   │   └── monitoring.bicep     # Application Insights resources
    │   └── README.md                # Container Apps deployment guide
    │
    └── foundry-agent/
        ├── deploy.sh                # Deployment script for Foundry Agent
        ├── bicep/
        │   ├── main.bicep           # Main infrastructure template
        │   ├── ai-foundry.bicep     # AI Foundry resources
        │   └── monitoring.bicep     # Application Insights resources
        └── README.md                # Foundry Agent deployment guide

tests/                               # Manual test scripts (optional for POC)
└── manual/
  ├── test_weather_api.py          # Direct Weather API testing
  └── test_agent.py                # Agent interaction testing

pyproject.toml                       # Root project configuration (uv)
uv.lock                              # Lock file (generated by uv)
README.md                            # Repository overview and setup
.env.example                         # Global environment variables template
```

**Structure Decision**: Multi-component hybrid architecture

**Rationale**:

1. **Shared Weather API**: Single Weather API service serves both deployments (DRY principle, consistent weather data)
2. **Dual Agent Deployments**: Two separate agent implementations demonstrate different hosting patterns:
   - `agent-container/`: Full control, containerized, self-hosted in Azure Container Apps
   - `agent-foundry/`: Managed service, simpler deployment, hosted by Azure AI Foundry
3. **Shared Code**: `src/shared/` contains data models and constants used by both agents
4. **Separate Deployment Configs**: Each deployment has its own Bicep templates and scripts to showcase deployment differences
5. **Telemetry Integration**: Both deployments wire into Azure Application Insights via different integration patterns

**Key Architectural Decisions**:

- **Single Weather API, Dual Agents**: Weather API is deployed once, consumed by both agent deployments via HTTP (shared endpoint)
- **Code Reuse**: `clothing_logic.py` is identical in both agent deployments (symlink or copy during build)
- **Telemetry Strategy**:
  - Container Apps: Manual Application Insights integration via `azure-monitor-opentelemetry`
  - Foundry Agent: Native Foundry telemetry (automatic via agent service)
- **Deployment Isolation**: Each deployment can be tested independently, no shared runtime state

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

**No Violations**: All three constitution principles pass. The dual deployment architecture is justified by the explicit POC requirement to demonstrate both deployment patterns - this is core to the POC's value proposition, not unnecessary complexity.
