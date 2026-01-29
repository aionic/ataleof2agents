# Code Samples

Quick-start examples demonstrating key Agent Framework patterns.
Uses the azure-ai-projects SDK v2.0.0+ (GA API with conversations/responses).

---

## Environment Setup

All samples require the following environment variables in `.env`:

```env
# Required - Azure AI Project endpoint
AZURE_AI_PROJECT_ENDPOINT=https://your-project.services.ai.azure.com/api/projects/your-project-name

# Required - Model deployment name
AZURE_AI_MODEL_DEPLOYMENT_NAME=gpt-4.1

# Optional - Weather API URL (for add_openapi_tool.py)
WEATHER_API_URL=https://your-weather-api.azurecontainerapps.io
```

---

## Available Samples

### create_simple_agent.py

**Purpose**: Create a basic Foundry agent with no external tools

**What it demonstrates**:

- Minimal agent setup using `PromptAgentDefinition`
- Conversation flow with `conversations/responses` API
- Agent invocation using `agent_reference` pattern
- Resource cleanup

**Run**:

```powershell
.\.venv\Scripts\Activate.ps1
python samples/create_simple_agent.py
```

**Output**:

```text
✓ Agent created: SimpleAssistant (ID: SimpleAssistant:1)
✓ Conversation created: conv_abc123...

Agent: Hello! I'm here to help. What can I assist you with today?

✓ Cleaned up
```

**Use this when**: Learning Foundry basics, testing connectivity

---

### add_openapi_tool.py

**Purpose**: Create agent with external API integration

**What it demonstrates**:

- OpenAPI tool definition using SDK models (`OpenApiAgentTool`, `OpenApiFunctionDefinition`)
- External API integration (Weather API example)
- Agent creation with tools using `PromptAgentDefinition`
- Tool invocation via `agent_reference` pattern

**Run**:

```powershell
.\.venv\Scripts\Activate.ps1
python samples/add_openapi_tool.py
```

**Output**:

```text
✓ Agent created with OpenAPI tool: WeatherBot:1
  Agent Name: WeatherBot

User: What's the weather in 10001?
Agent: The current weather in New York (10001) is 28°F with clear skies...

✓ Cleaned up
```

**Use this when**: Integrating external APIs, building weather/data agents

---

## SDK API Reference

### Key Classes

```python
from azure.ai.projects import AIProjectClient
from azure.ai.projects.models import (
    PromptAgentDefinition,      # For native agents
    OpenApiAgentTool,           # OpenAPI tool wrapper
    OpenApiFunctionDefinition,  # OpenAPI function definition
    OpenApiAnonymousAuthDetails # Anonymous auth for OpenAPI
)
```

### Creating Agents

```python
# Connect to project
client = AIProjectClient(
    endpoint=os.getenv("AZURE_AI_PROJECT_ENDPOINT"),
    credential=DefaultAzureCredential()
)

# Create agent with definition
definition = PromptAgentDefinition(
    model="gpt-4.1",
    instructions="Your instructions here",
    tools=[...]  # Optional: OpenApiAgentTool instances
)

agent = client.agents.create(
    name="AgentName",
    definition=definition,
    description="Agent description"
)
```

### Invoking Agents

```python
# Get OpenAI client
openai = client.get_openai_client()

# Create conversation
conversation = openai.conversations.create(
    items=[{'type': 'message', 'role': 'user', 'content': 'Your message'}]
)

# Invoke agent with agent_reference
response = openai.responses.create(
    conversation=conversation.id,
    extra_body={'agent': {'name': 'AgentName', 'type': 'agent_reference'}},
    input='',
)

print(response.output_text)

# Cleanup
openai.conversations.delete(conversation_id=conversation.id)
client.agents.delete("AgentName")
```

---

## Related Documentation

- [Azure AI Foundry Deployment Guide](../docs/guides/DEPLOYMENT-FOUNDRY.md)
- [Agent Framework Tutorial](../docs/guides/AGENT-FRAMEWORK-TUTORIAL.md)
- [Workflow Integration Patterns](../docs/architecture/WORKFLOW-INTEGRATION-PATTERNS.md)
