# Calling Azure Foundry Agents from Workflows

**Purpose**: Document patterns for invoking Foundry-hosted agents as part of larger workflows and automation scenarios

**Date**: 2026-01-21  
**Sprint**: Foundry Deployment  
**Status**: Research Complete

---

## 🎯 Overview

Azure AI Foundry agents can be invoked as part of workflows using multiple integration patterns. This enables the Weather Clothing Advisor agent to be called programmatically from:

- Custom applications and services
- Azure Logic Apps workflows
- Scheduled automation tasks
- Event-driven architectures
- Multi-agent orchestrations

---

## 📋 Integration Patterns

### Pattern 1: Direct API Calls (Threads/Runs)

**Best For**: Custom applications, programmatic integration, full control over conversation flow

**How It Works**:
1. Create a **thread** (conversation context)
2. Add **message** to thread (user input)
3. Create a **run** to process the message
4. **Poll** for run completion
5. Retrieve **messages** from thread (agent response)

**Code Example** (PowerShell):

```powershell
# Configuration
$endpoint = "https://anfoundy3lsww.services.ai.azure.com"
$agentId = "weather-clothing-advisor"
$token = az account get-access-token --resource https://cognitiveservices.azure.com --query accessToken -o tsv

# 1. Create thread
$threadResponse = Invoke-RestMethod `
  -Uri "$endpoint/agents/$agentId/threads" `
  -Method POST `
  -Headers @{Authorization="Bearer $token"; "Content-Type"="application/json"} `
  -Body '{}'

$threadId = $threadResponse.id

# 2. Add message
$messageBody = @{
  role = "user"
  content = "What should I wear in 10001?"
} | ConvertTo-Json

Invoke-RestMethod `
  -Uri "$endpoint/agents/$agentId/threads/$threadId/messages" `
  -Method POST `
  -Headers @{Authorization="Bearer $token"; "Content-Type"="application/json"} `
  -Body $messageBody

# 3. Create run
$runResponse = Invoke-RestMethod `
  -Uri "$endpoint/agents/$agentId/threads/$threadId/runs" `
  -Method POST `
  -Headers @{Authorization="Bearer $token"; "Content-Type"="application/json"} `
  -Body '{}'

$runId = $runResponse.id

# 4. Poll for completion
do {
  Start-Sleep -Seconds 2
  $runStatus = Invoke-RestMethod `
    -Uri "$endpoint/agents/$agentId/threads/$threadId/runs/$runId" `
    -Method GET `
    -Headers @{Authorization="Bearer $token"}
  Write-Host "Run status: $($runStatus.status)"
} while ($runStatus.status -in @('queued', 'in_progress'))

# 5. Get response
$messages = Invoke-RestMethod `
  -Uri "$endpoint/agents/$agentId/threads/$threadId/messages" `
  -Method GET `
  -Headers @{Authorization="Bearer $token"}

# Display agent response
$response = $messages.data[0].content[0].text.value
Write-Host "`nAgent Response:`n$response"
```

**Python Example**:

```python
from azure.ai.projects import AIProjectClient
from azure.identity import DefaultAzureCredential
import time

# Initialize client
credential = DefaultAzureCredential()
project_client = AIProjectClient(
    endpoint="https://anfoundy3lsww.services.ai.azure.com/",
    credential=credential
)

# Get OpenAI-compatible client
openai_client = project_client.get_openai_client()

# 1. Create thread
thread = openai_client.beta.threads.create()
print(f"Created thread: {thread.id}")

# 2. Add message
message = openai_client.beta.threads.messages.create(
    thread_id=thread.id,
    role="user",
    content="What should I wear in 10001?"
)

# 3. Create run
run = openai_client.beta.threads.runs.create(
    thread_id=thread.id,
    assistant_id="weather-clothing-advisor"
)

# 4. Poll for completion
while run.status in ['queued', 'in_progress']:
    time.sleep(2)
    run = openai_client.beta.threads.runs.retrieve(
        thread_id=thread.id,
        run_id=run.id
    )
    print(f"Run status: {run.status}")

# 5. Get messages
messages = openai_client.beta.threads.messages.list(thread_id=thread.id)
response = messages.data[0].content[0].text.value
print(f"\nAgent Response:\n{response}")
```

**Pros**:
- Full control over conversation flow
- Can maintain conversation context across multiple turns
- Programmatic access from any language
- Integration with existing applications

**Cons**:
- Requires manual polling for completion
- More code to write and maintain
- Need to handle authentication and errors

**Use Cases**:
- Web applications calling agent as backend service
- CLI tools for agent interaction
- Batch processing of queries
- Integration with existing microservices

---

### Pattern 2: Azure Logic Apps Integration

**Best For**: Low-code/no-code orchestration, scheduled tasks, event-driven workflows

**How It Works**:
1. Add **Foundry Agent Service connectors** to Logic App workflow
2. Configure triggers (schedule, HTTP, queue message, etc.)
3. Add agent actions: Create Thread, Create Run, Get Run, List Messages
4. Process agent responses and integrate with other services

**Logic Apps Workflow Example**:

```
Trigger: Recurrence (daily at 9 AM)
  ↓
Action: Create Thread (Foundry connector)
  ↓
Action: Create Run (Foundry connector)
  ↓
Action: Delay (30 seconds)
  ↓
Action: Get Run (Foundry connector)
  ↓
Action: List Messages (Foundry connector)
  ↓
Action: Send Email (Office 365 connector)
```

**Configuration Steps**:

1. **Add Foundry Agent Service Connector**:
   - Search for "Agent Service" in Logic Apps actions
   - Select "Create Thread", "Create Run", "Get Run", "List Messages"

2. **Create Connection**:
   - Connection name: `foundry-agent-connection`
   - Project endpoint: `https://anfoundy3lsww.services.ai.azure.com/api/projects/<project-id>`
   - Authentication: Managed Identity or Service Principal

3. **Configure Actions**:
   - **Create Thread**: No parameters needed
   - **Create Run**: Use thread ID from previous step
   - **Get Run**: Poll for completion status
   - **List Messages**: Retrieve agent responses

**Example: Daily Weather Report**:

```json
{
  "definition": {
    "$schema": "https://schema.management.azure.com/providers/Microsoft.Logic/schemas/2016-06-01/workflowdefinition.json#",
    "triggers": {
      "Recurrence": {
        "type": "Recurrence",
        "recurrence": {
          "frequency": "Day",
          "interval": 1,
          "schedule": {
            "hours": ["9"]
          }
        }
      }
    },
    "actions": {
      "Create_Thread": {
        "type": "ApiConnection",
        "inputs": {
          "host": {
            "connection": {
              "name": "@parameters('$connections')['foundryagent']['connectionId']"
            }
          },
          "method": "post",
          "path": "/agents/weather-clothing-advisor/threads"
        }
      },
      "Create_Run": {
        "type": "ApiConnection",
        "inputs": {
          "host": {
            "connection": {
              "name": "@parameters('$connections')['foundryagent']['connectionId']"
            }
          },
          "method": "post",
          "path": "/agents/weather-clothing-advisor/threads/@{body('Create_Thread')?['id']}/runs",
          "body": {
            "message": "What's the weather forecast for today in New York?"
          }
        },
        "runAfter": {
          "Create_Thread": ["Succeeded"]
        }
      },
      "Send_Email": {
        "type": "ApiConnection",
        "inputs": {
          "host": {
            "connection": {
              "name": "@parameters('$connections')['office365']['connectionId']"
            }
          },
          "method": "post",
          "path": "/v2/Mail",
          "body": {
            "To": "user@example.com",
            "Subject": "Daily Weather Report",
            "Body": "@{body('List_Messages')?['data'][0]?['content'][0]?['text']?['value']}"
          }
        }
      }
    }
  }
}
```

**Pros**:
- Visual designer, no code required
- Built-in connectors for 1000+ services
- Automatic retry and error handling
- Managed authentication

**Cons**:
- Less flexible than code
- Vendor lock-in to Azure Logic Apps
- Can be expensive for high-volume scenarios

**Use Cases**:
- Scheduled daily/weekly reports
- Email automation with AI insights
- Event-driven processing (new file → analyze → respond)
- Multi-system integration (CRM → Agent → Database)

---

### Pattern 3: Foundry Workflow Builder (UI-based)

**Best For**: Visual workflow orchestration, multi-agent collaboration, rapid prototyping

**How It Works**:
1. Create workflow in Foundry portal (Sequential, Concurrent, or Group Chat)
2. Add agents as "Invoke agent" nodes
3. Configure data flow between agents
4. Deploy and test in playground
5. Invoke via API or integrate with applications

**Workflow Types**:

| Type | Description | Use Case |
|------|-------------|----------|
| **Sequential** | Agents execute in order | Multi-step processing pipeline |
| **Concurrent** | Agents run in parallel | Gather multiple perspectives simultaneously |
| **Group Chat** | Dynamic agent selection | Collaborative problem-solving |
| **Human-in-Loop** | Pause for user input | Approval workflows, clarification |

**Example: Sequential Workflow**:

```
Input: User query
  ↓
Agent 1: Parse zip code
  ↓
Agent 2: Get weather data (Weather Clothing Advisor)
  ↓
Agent 3: Format response
  ↓
Output: Formatted recommendation
```

**Creating in Portal**:

1. Navigate to https://ai.azure.com
2. Select **Build** → **Create new workflow** → **Sequential**
3. Add agents to each node
4. Configure transitions and data mapping
5. Save and run workflow

**Pros**:
- Visual design, intuitive UI
- Built into Foundry platform
- Supports complex orchestration patterns
- Native multi-agent coordination

**Cons**:
- Requires Foundry portal access
- Limited programmatic control
- May not fit all integration scenarios

**Use Cases**:
- Multi-agent collaboration workflows
- Rapid prototyping of agent interactions
- Human-in-the-loop approval processes
- Complex decision trees with multiple agents

---

### Pattern 4: Microsoft Agent Framework Workflows (Code)

**Best For**: Advanced orchestration, custom logic, programmatic control, .NET/Python applications

**How It Works**:
1. Define workflow in Python or .NET code
2. Use `WorkflowBuilder` to configure orchestration pattern
3. Execute with `workflow.run_stream()` for streaming results
4. Handle events and process agent responses

**Python Example (Sequential Workflow)**:

```python
from agent_framework import (
    SequentialBuilder,
    ChatAgent,
    WorkflowOutputEvent,
    ChatMessage
)
from azure.identity import DefaultAzureCredential

# Create agents
weather_agent = ChatAgent(
    name="WeatherClothingAdvisor",
    instructions="Provide clothing recommendations based on weather"
)

formatter_agent = ChatAgent(
    name="ResponseFormatter",
    instructions="Format responses in friendly, conversational style"
)

# Build sequential workflow
workflow = (
    SequentialBuilder()
    .participants([weather_agent, formatter_agent])
    .build()
)

# Execute workflow
async def run_workflow(query: str):
    output_event = None
    async for event in workflow.run_stream(query):
        if isinstance(event, WorkflowOutputEvent):
            output_event = event
    
    if output_event:
        messages = output_event.data
        for msg in messages:
            print(f"[{msg.author_name}]: {msg.text}")

# Run
import asyncio
asyncio.run(run_workflow("What should I wear in 10001?"))
```

**Concurrent Workflow Example**:

```python
from agent_framework import ConcurrentBuilder

# Multiple agents working in parallel
workflow = (
    ConcurrentBuilder()
    .participants([weather_agent, traffic_agent, events_agent])
    .with_aggregator(summarize_results)  # Custom function to combine results
    .build()
)

# Execute - all agents run concurrently
async for event in workflow.run_stream("Plan my day in NYC"):
    if isinstance(event, WorkflowOutputEvent):
        print(event.data)
```

**Pros**:
- Full programmatic control
- Advanced orchestration patterns
- Streaming support
- Multi-language (.NET, Python)

**Cons**:
- Requires coding skills
- More complex setup
- Need to manage deployment and hosting

**Use Cases**:
- Complex multi-agent systems
- Custom orchestration logic
- Real-time streaming workflows
- High-performance scenarios

---

## 🎯 Choosing the Right Pattern

| Scenario | Recommended Pattern | Why |
|----------|---------------------|-----|
| **Web app backend** | Direct API (Threads/Runs) | Full control, stateful conversations |
| **Scheduled tasks** | Logic Apps | No code, built-in scheduling |
| **Multi-agent workflow** | Foundry Workflow Builder | Visual design, native orchestration |
| **Custom orchestration** | Agent Framework | Advanced control, streaming |
| **Event-driven** | Logic Apps + API | Combine triggers with agent calls |
| **Batch processing** | Direct API (Python/PowerShell) | Programmatic loops and error handling |

---

## 📚 Example Use Cases

### Use Case 1: Daily Weather Email Report

**Pattern**: Logic Apps

**Workflow**:
1. Timer trigger (daily at 6 AM)
2. Loop through list of cities
3. For each city: Create thread → Invoke agent → Get recommendation
4. Aggregate results into email
5. Send via Office 365 connector

**Benefits**: Automated, no code, reliable

---

### Use Case 2: Customer Service Chatbot

**Pattern**: Direct API (Threads/Runs)

**Architecture**:
```
User → Web App → API Gateway → Foundry Agent (Threads/Runs) → Response
                                       ↓
                               Weather API Container
```

**Benefits**: Stateful conversations, custom UI, real-time

---

### Use Case 3: Multi-Agent Research System

**Pattern**: Agent Framework Workflows

**Workflow**:
```python
# Concurrent execution
researchers = [weather_agent, climate_agent, fashion_agent]
workflow = ConcurrentBuilder().participants(researchers).build()

# All agents work in parallel on the same query
results = await workflow.run("Sustainable clothing for rainy climates")
```

**Benefits**: Parallel execution, custom aggregation logic

---

### Use Case 4: Approval Workflow

**Pattern**: Foundry Workflow Builder (Human-in-Loop)

**Workflow**:
1. User submits request
2. Agent analyzes and generates recommendation
3. **Pause for human approval**
4. If approved, execute action
5. Send confirmation

**Benefits**: Built-in human approval, visual design

---

## 🔗 References

### Microsoft Documentation
- [Trigger an agent using Logic Apps](https://learn.microsoft.com/en-us/azure/ai-foundry/agents/how-to/triggers)
- [Build a workflow in Microsoft Foundry](https://learn.microsoft.com/en-us/azure/ai-foundry/agents/concepts/workflow)
- [Threads, runs, and messages](https://learn.microsoft.com/en-us/azure/ai-foundry/agents/concepts/threads-runs-messages)
- [Agent Framework Workflows](https://learn.microsoft.com/en-us/agent-framework/user-guide/workflows/orchestrations/overview)

### API Documentation
- [Azure AI Projects Python SDK](https://azuresdkdocs.z19.web.core.windows.net/python/azure-ai-projects/2.0.0b2/)
- [OpenAI Assistants API](https://platform.openai.com/docs/assistants/overview) (compatible pattern)

### Code Samples
- [azure-ai-foundry-samples](https://github.com/Azure-Samples/azure-ai-foundry-samples)
- [microsoft/agent-framework](https://github.com/microsoft/agent-framework)

---

## ✅ Implementation Checklist

For the Weather Clothing Advisor sprint, we will:

- [x] **Research complete**: Document all invocation patterns
- [ ] **Pattern 1**: Create PowerShell script for direct API calls
- [ ] **Pattern 2**: Optional - Set up Logic Apps example
- [ ] **Testing**: Validate agent responses via API
- [ ] **Documentation**: Update sprint docs with invocation examples

---

**Last Updated**: 2026-01-21  
**Author**: Development Team  
**Status**: Ready for Implementation
