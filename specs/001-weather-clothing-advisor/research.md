# Research: Weather-Based Clothing Advisor

**Purpose**: Document technology decisions, API selection, and best practices research for the Weather-Based Clothing Advisor POC.

**Research Phase**: Phase 0 (Prerequisite for implementation)

**Date**: 2026-01-20

## Overview

This document captures research findings and decisions made during the planning phase of the Weather-Based Clothing Advisor project. All decisions are made following POC Constitution Principle II (Documentation-Driven Development) by consulting Microsoft Learn and Context7 documentation.

## Technology Stack Decisions

### 1. Azure Agent Framework SDK

**Decision**: Use `agent-framework` and `agent-framework-azure-ai` Python packages

**Source**: [Microsoft Learn - Azure Agent Framework](https://learn.microsoft.com/en-us/agent-framework/)

**Rationale**:
- Official Microsoft SDK for building AI agents on Azure
- Supports both local development (OpenAI) and Azure AI Foundry deployment
- Built-in support for function calling/tools (required for weather API integration)
- Streaming responses for better UX
- Async/await patterns for Python

**Key Capabilities**:
- `ChatAgent` class for simple agents with chat client implementations
- `AzureAIAgentClient` for managed Azure AI Foundry agents
- Function tools via decorators or explicit tool definitions
- Thread-based conversation management (stateful agents)
- SDK type bindings for rich Azure service integration

**Installation**:

```bash
uv add agent-framework agent-framework-azure-ai
```

**Authentication**: Use `DefaultAzureCredential` or `AzureCliCredential` for local dev

**Documentation Links**:
- Quick Start: <https://learn.microsoft.com/en-us/agent-framework/tutorials/quick-start>
- Agent Types: <https://learn.microsoft.com/en-us/agent-framework/user-guide/agents/agent-types/>
- Azure AI Agents: <https://learn.microsoft.com/en-us/agent-framework/user-guide/agents/agent-types/azure-ai-foundry-agent>

### 2. Weather API Service (Container Apps)

**Decision**: Use a lightweight FastAPI service for the weather tool

**Rationale**:
- Aligns with Container Apps deployment model
- Easy to run locally and in Azure Container Apps
- Simple HTTP interface for agent tool calls
- Reusable across both Container Apps and Foundry deployments

**Key Features for POC**:
- FastAPI route for `/api/weather`
- Environment variables via `os.getenv()` for API keys
- JSON request/response handling

**Deployment Target**:
- Azure Container Apps (Weather API service)

### 3. uv Package Management

**Decision**: Use `uv` as primary package manager for local development

**Source**: [Context7 - uv Documentation](https://docs.astral.sh/uv/)

**Rationale**:
- 10-100x faster than pip/poetry (Rust-based)
- Single tool replaces pip, pip-tools, poetry, pyenv, virtualenv
- Native `pyproject.toml` support (PEP 621)
- Can generate `requirements.txt` for container deployment
- Project-level Python version management

**Key Commands**:

```bash
# Initialize project
uv init weather-clothing-advisor --python 3.11

# Add dependencies
uv add agent-framework agent-framework-azure-ai requests

# Generate requirements.txt for Azure
uv pip compile pyproject.toml -o requirements.txt

# Sync dependencies
uv sync
```

**Project Structure**:

```text
pyproject.toml          # Primary dependency definition
.python-version         # Python 3.11
uv.lock                 # Locked dependency versions
requirements.txt        # Generated for container deployment
```

**Documentation Links**:
- uv Getting Started: <https://docs.astral.sh/uv/getting-started/>
- Project Management: <https://docs.astral.sh/uv/guides/projects/>

### 4. Weather API Selection

**Decision**: Use OpenWeatherMap Free Tier API

**Source**: [OpenWeatherMap Current Weather Data API](https://openweathermap.org/current)

**Rationale**:
- Free tier: 1,000 calls/day (sufficient for POC)
- Supports US zip code lookup (required FR-001)
- Returns temperature, conditions, humidity, wind (matches FR-003)
- Simple REST API with JSON responses
- No credit card required for free tier
- Good documentation and Python examples

**API Endpoint**:

```text
https://api.openweathermap.org/data/2.5/weather?zip={zip},US&appid={API_KEY}&units=imperial
```

**Response Data (Relevant Fields)**:

```json
{
  "main": {
    "temp": 72.5,
    "humidity": 65
  },
  "weather": [
    {
      "main": "Rain",
      "description": "light rain"
    }
  ],
  "wind": {
    "speed": 12.5
  }
}
```

**Error Handling**:
- 404: Invalid zip code
- 401: Invalid API key
- 429: Rate limit exceeded (unlikely in POC)

**Alternative Considered**: WeatherAPI.com - similar features but OpenWeatherMap has better zip code support

**Documentation**: <https://openweathermap.org/current#zip>

### 5. Azure Application Insights & Telemetry

**Decision**: Integrate both deployments with Azure AI Foundry telemetry via Application Insights

**Source**: [Microsoft Learn - Application Insights](https://learn.microsoft.com/en-us/azure/azure-monitor/app/app-insights-overview)

**Rationale**:
- Unified observability for both Container Apps and Foundry Agent deployments
- Distributed tracing across agent → weather API → external API calls
- Built-in dashboards for request rates, failures, performance
- Query agent conversations and tool invocations
- Essential for demonstrating deployment patterns (key POC requirement)

**Telemetry Strategy by Deployment**:

**Container Apps Deployment**:
- Manual instrumentation via `azure-monitor-opentelemetry` package
- Custom span creation for agent operations
- Automatic HTTP request tracking
- Manual logging of agent responses

```python
from azure.monitor.opentelemetry import configure_azure_monitor
from opentelemetry import trace

configure_azure_monitor(
    connection_string=os.getenv("APPLICATIONINSIGHTS_CONNECTION_STRING")
)

tracer = trace.get_tracer(__name__)
with tracer.start_as_current_span("agent_process_request"):
    # Agent logic here
    pass
```

**Foundry Agent Service Deployment**:
- Native telemetry (automatic via Azure AI Agent Service)
- Agent threads and messages logged automatically
- Tool calls tracked in Foundry dashboard
- No manual instrumentation required

**Key Telemetry Data Captured**:

1. **Request Metrics**:
   - Total requests per deployment
  - Response times (agent + weather API)
   - Success/failure rates

2. **Agent Operations**:
   - User prompts and agent responses
   - Tool invocations (get_weather calls)
   - Token usage (for cost tracking)

3. **Weather API Calls**:
   - Weather API latency
   - API success/failure rates
   - Zip code patterns (for debugging)

4. **Errors & Exceptions**:
   - Invalid zip code frequency
   - API failures (OpenWeatherMap down)
   - Agent errors (malformed tool responses)

**Dependencies**:

```bash
# Container Apps deployment
uv add azure-monitor-opentelemetry

# Foundry deployment (built-in, no extra packages)
```

**Application Insights Configuration**:
- One Application Insights resource shared by both deployments
- Separate custom dimensions to differentiate:
  - `deployment_type`: "container-app" or "foundry-agent"
  - `agent_id`: unique identifier per deployment
- Retention: 30 days (sufficient for POC)

**Querying Telemetry**:

```kql
// All agent requests in last hour
requests
| where timestamp > ago(1h)
| where customDimensions["deployment_type"] in ("container-app", "foundry-agent")
| summarize count() by bin(timestamp, 5m), tostring(customDimensions["deployment_type"])
| render timechart

// Weather API calls with errors
requests
| where name == "get_weather"
| where success == false
| project timestamp, url, resultCode, duration
```

**POC Scope**:
- Basic telemetry only (not production-grade alerting or anomaly detection)
- Manual dashboard review (no automated alerts)
- Demonstrates telemetry integration patterns, not comprehensive monitoring

**Documentation Links**:
- Application Insights Overview: <https://learn.microsoft.com/en-us/azure/azure-monitor/app/app-insights-overview>
- OpenTelemetry Python: <https://learn.microsoft.com/en-us/azure/azure-monitor/app/opentelemetry-enable?tabs=python>
- Azure AI Agent Telemetry: <https://learn.microsoft.com/en-us/agent-framework/user-guide/telemetry>

## Deployment Options Research

### Option 1: Azure Container Apps

**Decision**: Use Container Apps for containerized agent deployment

**Source**: [Microsoft Learn - Python Container Apps](https://learn.microsoft.com/en-us/azure/developer/python/tutorial-deploy-python-web-app-azure-container-apps-01)

**Rationale**:
- Fully managed container hosting (no Kubernetes management)
- Auto-scaling with scale-to-zero (cost-effective for POC)
- Built-in ingress and load balancing
- Integrated with Container Registry
- Sweden Central region supported

**Architecture**:
- Container Apps Environment (shared boundary)
- Container App (agent application)
- Azure Container Registry (image storage)
- User-assigned managed identity for ACR pull

**Key Configuration**:
- External ingress for HTTP access
- Port: 8000 (FastAPI/agent server)
- Min replicas: 0 (scale to zero when idle)
- Max replicas: 1 (POC single instance)

**Deployment Flow**:

```bash
1. Build Docker image locally
2. Push to Azure Container Registry
3. Create Container Apps environment
4. Deploy container app from registry
5. Configure environment variables (API keys, endpoints)
```

**Documentation Links**:
- Container Apps Overview: <https://learn.microsoft.com/en-us/azure/container-apps/overview>
- Python Deployment Tutorial: <https://learn.microsoft.com/en-us/azure/developer/python/tutorial-deploy-python-web-app-azure-container-apps-02>

### Option 2: Azure AI Foundry Agent Service

**Decision**: Use Azure AI Foundry for managed agent deployment

**Source**: [Microsoft Learn - Azure AI Agents](https://learn.microsoft.com/en-us/agent-framework/user-guide/agents/agent-types/azure-ai-foundry-agent)

**Rationale**:
- Managed agent hosting (no container management)
- Built-in agent thread persistence
- Direct integration with Azure AI models
- Agent dashboard for monitoring/debugging
- Simpler deployment than containers

**Architecture**:
- Azure AI Project (Foundry)
- Agent Definition (instructions, tools, model)
- Weather API tool registration
- API endpoint auto-generated

**Agent Configuration**:

```python
agent = AzureAIAgentClient(
    async_credential=credential,
    endpoint=os.getenv("AZURE_AI_PROJECT_ENDPOINT")
).create_agent(
    name="ClothingAdvisor",
    instructions="You are a clothing recommendation assistant...",
    model=os.getenv("AZURE_AI_MODEL_DEPLOYMENT_NAME")
)
```

**Prerequisites**:
- Azure AI Project in Foundry portal
- Model deployment (e.g., gpt-4o-mini)
- Weather API deployed and accessible

**Documentation Links**:
- Azure AI Foundry Agents: <https://learn.microsoft.com/en-us/agent-framework/user-guide/agents/agent-types/azure-ai-foundry-agent>
- Agent Service Overview: <https://learn.microsoft.com/en-us/python/api/overview/azure/ai-agents-readme>

## Regional Deployment

**Decision**: Deploy all resources to Sweden Central region

**Rationale**:
- User requirement for this POC
- Sweden Central supports all required services:
  - Weather API (Container Apps)
  - Azure Container Apps
  - Azure AI Services (Foundry)
  - Azure Container Registry

**Region Configuration**:
- Azure CLI: `--location swedencentral`
- Bicep/ARM: `location: 'swedencentral'`
- Portal: Select "Sweden Central" from region dropdown

## Implementation Best Practices

### Agent Design

**Source**: [Microsoft Learn - Agent Framework Best Practices](https://learn.microsoft.com/en-us/agent-framework/)

**Instructions Pattern**:
- Clear role definition: "You are a clothing recommendation assistant"
- Explicit behavior guidelines: temperature ranges, recommendation format
- Tool usage instructions: when to call weather API

**Weather API Tool Design**:
- Single responsibility: weather lookup only
- Clear parameter schema: zip code (string, 5 digits)
- Structured response: JSON with temperature, conditions, humidity, wind
- Error handling: return error codes/messages in response

### Weather API Best Practices

**For POC**:
- Keep the API stateless (no global state)
- Use environment variables for API keys
- Return JSON responses with proper status codes
- Minimal dependencies to reduce cold start time

**Error Handling**:
- Return HTTP 200 with error object (agent can interpret)
- Don't raise exceptions for invalid zip codes (expected scenario)
- Log errors to Application Insights (minimal for POC)

### Container Best Practices

**Source**: [Microsoft Learn - Container Apps Best Practices](https://learn.microsoft.com/en-us/azure/container-apps/overview)

**Dockerfile Optimization**:
- Use slim Python base image (`python:3.11-slim`)
- Multi-stage build to reduce image size
- Copy only necessary files (use `.dockerignore`)
- Install uv in container for fast dependency installation

**Environment Configuration**:
- Use Container Apps secrets for sensitive values
- Reference secrets as environment variables
- Store non-sensitive config in app settings

## Security Considerations (POC-Appropriate)

**Per POC Constitution**: Minimal security for demonstration purposes

**Implemented**:
- Managed identities for Azure resource access
- Azure Key Vault for API keys (weather API, etc.)
- Restrict Weather API ingress where possible (called by agent only)
- HTTPS by default (Container Apps)

**Intentionally Omitted (Not Required for POC)**:
- User authentication/authorization
- Rate limiting
- Input sanitization beyond basic format check
- Comprehensive audit logging
- Network isolation (VNet integration)

## Testing Strategy

**Per POC Constitution Principle III**: Manual testing prioritized

**Manual Test Cases**:

1. **Weather Lookup**: Test with 5 sample zip codes
   - 10001 (NYC - varied weather)
   - 90210 (LA - warm/sunny)
   - 60601 (Chicago - cold/variable)
   - 33139 (Miami - hot/humid)
   - 00000 (Invalid - error handling)

2. **Clothing Recommendations**: Verify logic
   - <32°F → winter gear
   - 32-50°F → cool weather clothing
   - 50-70°F → moderate clothing
   - 70-85°F → light clothing
   - >85°F → hot weather gear
   - Rain → add rain gear
   - Wind → add windbreaker suggestions

3. **Deployment Validation**:
   - Test Container Apps endpoint responds
   - Test Foundry agent responds
   - Verify both produce same recommendations
  - Check Weather API logs for API calls

**No Automated Tests**: Per Constitution, manual testing sufficient for POC

## Cost Estimation (POC)

**Expected Monthly Cost**: ~$0-5 USD

**Free Tier Resources**:
- Container Apps: 180,000 vCPU-seconds + 360,000 GiB-seconds free/month
- OpenWeatherMap: 1,000 API calls/day free
- Container Registry: Basic tier ~$5/month (only paid resource)

**POC Usage Pattern**:
- <100 total requests during demo
- Weather API requests: <0.001% of free tier
- Container: runs <1 hour total (well within free tier)
- Weather API: <100 calls (10% of daily free limit)

**Cost Optimization**:
- Container Apps scale-to-zero when idle
- Container Apps scale-to-zero when idle
- Use free tier AI model in Foundry if available

## Alternatives Considered

### Alternative 1: FastAPI + Direct Azure OpenAI

**Rejected Because**: Doesn't demonstrate Agent Framework SDK (POC goal)

**Pros**: Simpler architecture, fewer dependencies
**Cons**: Misses key value prop (agent framework capabilities)

### Alternative 2: Single Deployment Model

**Rejected Because**: POC requires demonstrating both deployment options

**Pros**: Less code duplication, simpler testing
**Cons**: Doesn't showcase technology options (user requirement)

### Alternative 3: WeatherAPI.com Instead of OpenWeatherMap

**Rejected Because**: OpenWeatherMap has better zip code support and documentation

**Pros**: WeatherAPI.com has more generous free tier (1M calls/month)
**Cons**: Slightly more complex zip code handling, less Python examples

## References

### Microsoft Learn Documentation

- Azure Agent Framework: <https://learn.microsoft.com/en-us/agent-framework/>
- Azure Container Apps: <https://learn.microsoft.com/en-us/azure/container-apps/>
- Python on Azure: <https://learn.microsoft.com/en-us/azure/developer/python/>

### Context7 Documentation

- uv Package Manager: <https://docs.astral.sh/uv/>

### External API Documentation

- OpenWeatherMap Current Weather: <https://openweathermap.org/current>
- OpenWeatherMap API Guide: <https://openweathermap.org/guide>

## Next Steps (Phase 1)

After this research phase, proceed to Phase 1:

1. **data-model.md**: Define WeatherData and ClothingRecommendation structures
2. **contracts/**: Create function tool JSON schema and agent instructions
3. **quickstart.md**: Document manual testing procedures with sample zip codes
4. **Update agent context**: Run `.specify/scripts/powershell/update-agent-context.ps1`

All design artifacts should reference the decisions documented in this research file.
