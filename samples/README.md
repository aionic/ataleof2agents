# Code Samples

Quick-start examples demonstrating key Agent Framework patterns.

---

## Available Samples

### create_simple_agent.py
**Purpose**: Create a basic Foundry agent with no external tools

**What it demonstrates**:
- Minimal agent setup
- Conversation flow
- Thread management
- Resource cleanup

**Prerequisites**:
```powershell
# Set in .env
AI_PROJECT_CONNECTION_STRING=<from-foundry-portal>
```

**Run**:
```powershell
.\.venv\Scripts\Activate.ps1
python samples/create_simple_agent.py
```

**Output**:
```
Creating simple agent...
Agent created: SimpleAssistant (asst_abc123)

Sending message...
Assistant: Hello! I'm here to help. What can I assist you with today?

Cleaning up...
Agent deleted
Thread deleted
```

**Use this when**: Learning Foundry basics, testing connectivity

---

### add_openapi_tool.py
**Purpose**: Create agent with external API integration

**What it demonstrates**:
- OpenAPI tool definition
- External API integration (Weather API example)
- Tool invocation flow
- Handling API responses

**Prerequisites**:
```powershell
# Set in .env
AI_PROJECT_CONNECTION_STRING=<from-foundry-portal>
WEATHER_API_KEY=<your-key>  # Optional - uses mock data if not set
```

**Run**:
```powershell
.\.venv\Scripts\Activate.ps1
python samples/add_openapi_tool.py
```

**Output**:
```
Creating agent with OpenAPI tool...

Tool Definition:
{
  "name": "get_weather",
  "type": "openapi",
  "spec": { ... }
}

Agent created with tool: WeatherAgent (asst_xyz789)

Testing tool invocation...
User: What's the weather in New York?

Agent calls tool: get_weather(location="New York")
Tool response: { "temp": 72, "conditions": "sunny" }