# Agent Framework + Foundry Integration Guide

**Date:** January 20, 2026
**Status:** Research Complete - Implementation Pending

---

## Executive Summary

This document captures research findings on how to build agents using **Microsoft Agent Framework** that can be deployed to **both Azure Container Apps AND Azure AI Foundry Hosted Agents** with minimal code changes.

### Key Finding

**YES - It's possible to run the same agent code in both environments using Azure's hosting adapter pattern.**

---

## Table of Contents

1. [Understanding the Ecosystem](#understanding-the-ecosystem)
2. [Two Deployment Patterns](#two-deployment-patterns)
3. [The Hosting Adapter Solution](#the-hosting-adapter-solution)
4. [Architecture Comparison](#architecture-comparison)
5. [Current Project Status](#current-project-status)
6. [Implementation Strategy](#implementation-strategy)
7. [Technical Details](#technical-details)
8. [References](#references)

---

## Understanding the Ecosystem

### What We Have Now

Our current project uses:
- **Microsoft Agent Framework** (`agent-framework-core`, `agent-framework-azure-ai`)
- **Azure AI Foundry Models** (GPT-4.1 deployment)
- **Azure Container Apps** (self-hosted)
- **FastAPI** for HTTP endpoints

### The Confusion We Had

We were mixing two different concepts:

1. **Azure AI Foundry Models** - The AI models hosted in Foundry (what we should use)
2. **Azure AI Foundry Agent Service** - Managed runtime for hosting agents (optional, but powerful)

### The Correct Understanding

```
┌─────────────────────────────────────────────────────────────┐
│                    Microsoft Agent Framework                 │
│                  (Your agent code - SHARED)                  │
└──────────────────────┬──────────────────┬───────────────────┘
                       │                  │
          ┌────────────▼─────────┐   ┌───▼────────────────────┐
          │   Container Apps     │   │  Foundry Hosted Agents │
          │   (Self-Hosted)      │   │  (Managed Service)     │
          │                      │   │                        │
          │  FastAPI + uvicorn   │   │  Hosting Adapter       │
          │  Custom endpoints    │   │  Standard API          │
          │  Full control        │   │  Auto-scaling          │
          └──────────┬───────────┘   └───────────┬────────────┘
                     │                           │
                     └───────────┬───────────────┘
                                 │
                    ┌────────────▼─────────────┐
                    │ Azure AI Foundry Models  │
                    │  (GPT-4.1, etc.)         │
                    └──────────────────────────┘
```

---

## Two Deployment Patterns

### Pattern 1: Container Apps (Self-Hosted)

**What you control:**
- Container infrastructure
- HTTP server implementation (FastAPI)
- API endpoints
- Scaling configuration
- Observability setup

**Code pattern:**
```python
from agent_framework import ChatAgent
from fastapi import FastAPI

agent = ChatAgent(...)
app = FastAPI()

@app.post("/chat")
async def chat(request: ChatRequest):
    response = await agent.run(request.message)
    return response
```

**Pros:**
- Full control over APIs
- Custom integration points
- Flexible architecture

**Cons:**
- You manage infrastructure
- Manual scaling setup
- More operational overhead

### Pattern 2: Foundry Hosted Agents (Managed)

**What Foundry manages:**
- Container hosting
- HTTP server implementation
- Standard Foundry Responses API
- Auto-scaling
- State management
- Observability (Application Insights integration)

**Code pattern:**
```python
from agent_framework import ChatAgent
from azure.ai.agentserver.agentframework import from_agent_framework

agent = ChatAgent(...)

if __name__ == "__main__":
    # One line - automatically creates HTTP server on localhost:8088
    from_agent_framework(agent).run()
```

**Pros:**
- Zero infrastructure management
- Auto-scaling included
- Built-in observability
- Standard Foundry API
- Enterprise security

**Cons:**
- Foundry Responses API only
- Less flexibility for custom endpoints

---

## The Hosting Adapter Solution

### What is the Hosting Adapter?

The **hosting adapter** is Microsoft's framework abstraction layer that converts agent code into Foundry-compatible HTTP services.

### Key Packages

| Language | Package | Purpose |
|----------|---------|---------|
| Python | `azure-ai-agentserver-agentframework` | Wraps Agent Framework agents |
| Python | `azure-ai-agentserver-langgraph` | Wraps LangGraph agents |
| .NET | `Azure.AI.AgentServer.AgentFramework` | Wraps .NET agents |

### What It Provides

1. **One-line deployment**: `from_agent_framework(agent).run()`
2. **Automatic protocol translation**: Converts Foundry requests ↔ agent framework formats
3. **Built-in features**:
   - OpenTelemetry tracing
   - CORS support
   - SSE streaming
   - Structured logging
4. **Foundry Responses API compatibility**

### Local Testing

```python
# Your agent code
agent = ChatAgent(...)

# Start local server
from_agent_framework(agent).run()  # Runs on http://localhost:8088
```

Test with REST:
```http
POST http://localhost:8088/responses
Content-Type: application/json

{
    "input": {
        "messages": [
            {
                "role": "user",
                "content": "What should I wear in 10001?"
            }
        ]
    }
}
```

---

## Architecture Comparison

### Current State (Container Apps Only)

```
┌──────────────────────┐
│   Agent Framework    │
│   - ChatAgent        │
│   - Tools            │
└──────────┬───────────┘
           │
┌──────────▼───────────┐
│   FastAPI Server     │
│   - /health          │
│   - /chat            │
└──────────┬───────────┘
           │
┌──────────▼───────────┐
│  Azure Container Apps│
│  - uvicorn           │
│  - Custom scaling    │
└──────────┬───────────┘
           │
┌──────────▼───────────┐
│ Foundry Models API   │
│  - GPT-4.1           │
└──────────────────────┘
```

### Target State (Dual Deployment)

```
                    ┌──────────────────────┐
                    │   Agent Framework    │
                    │   - ChatAgent        │
                    │   - Tools (SHARED)   │
                    └──────────┬───────────┘
                               │
                ┌──────────────┴──────────────┐
                │                             │
    ┌───────────▼─────────┐       ┌──────────▼──────────┐
    │  Entry Point 1      │       │  Entry Point 2      │
    │  container_app.py   │       │  foundry_hosted.py  │
    │                     │       │                     │
    │  FastAPI + uvicorn  │       │  Hosting Adapter    │
    │  Custom endpoints   │       │  from_agent_framework()│
    └───────────┬─────────┘       └──────────┬──────────┘
                │                            │
    ┌───────────▼─────────┐       ┌──────────▼──────────┐
    │ Container Apps      │       │ Foundry Hosted      │
    │ (Self-managed)      │       │ (Fully managed)     │
    └───────────┬─────────┘       └──────────┬──────────┘
                │                            │
                └────────────┬───────────────┘
                             │
                ┌────────────▼─────────────┐
                │   Foundry Models API     │
                │   - GPT-4.1              │
                └──────────────────────────┘
```

---

## Current Project Status

### What's Working ✅
- Agent Framework code structure
- FastAPI server implementation
- Docker containerization
- Local development environment
- Azure resource provisioning

### What's Broken ❌
- **Endpoint configuration**: Using wrong endpoint format
  - Current: `https://anfoundy3lsww.services.ai.azure.com/api/projects/weatheragentlsww`
  - Should be: `https://anfoundy3lsww.services.ai.azure.com/`
- **Authentication**: DefaultAzureCredential failing in container
- **Model client**: Using wrong SDK pattern for Agent Framework + Foundry Models

### Root Causes

1. **Endpoint confusion**: We're using the "Agent Service" endpoint instead of "Models" endpoint
2. **Missing Managed Identity**: Container App needs system-assigned identity with RBAC roles
3. **SDK pattern**: Should use Azure OpenAI SDK with Foundry Models endpoint, not direct project client

---

## Implementation Strategy

### Phase-Based Approach

```
Phase 1: Fix Container Apps Deployment
├── 1.1 Fix endpoint configuration (.env + agent_service.py)
├── 1.2 Enable Managed Identity on Container App
├── 1.3 Assign RBAC roles (Cognitive Services OpenAI User)
├── 1.4 Update Bicep templates with correct env vars
├── 1.5 Test locally with Docker
├── 1.6 Deploy and validate in Azure
└── ✓ Container Apps fully functional

Phase 2: Add Foundry Hosted Support
├── 2.1 Install hosting adapter: azure-ai-agentserver-agentframework
├── 2.2 Create foundry_hosted.py entry point
├── 2.3 Create Dockerfile.foundry
├── 2.4 Update azure.yaml for dual deployment
├── 2.5 Test locally (localhost:8088)
├── 2.6 Deploy with azd up
└── ✓ Both deployment targets working

Phase 3: Unified Deployment Pipeline
├── 3.1 Create deployment matrix
├── 3.2 Update documentation
├── 3.3 Create comparison guide
└── ✓ Production-ready dual deployment
```

---

## Technical Details

### Correct Endpoint Pattern

According to Agent Framework documentation, when using Azure AI Foundry **Models** (not Agent Service):

| Service | SDK | Endpoint Format |
|---------|-----|----------------|
| Azure AI Foundry Models | Azure.AI.OpenAI | `https://<resource>.services.ai.azure.com/` |
| Azure AI Foundry Models | OpenAI SDK | `https://<resource>.services.ai.azure.com/openai/v1/` |

**Our values:**
- Resource: `anfoundy3lsww`
- Correct endpoint: `https://anfoundy3lsww.services.ai.azure.com/`
- Model deployment: `gpt-4.1`

### Authentication Pattern

**For Container Apps:**
```python
from azure.identity import DefaultAzureCredential
from agent_framework.azure import AzureOpenAIChatClient

credential = DefaultAzureCredential()
chat_client = AzureOpenAIChatClient(
    endpoint="https://anfoundy3lsww.services.ai.azure.com/",
    deployment_name="gpt-4.1",
    credential=credential
)
```

**Required RBAC:**
- Role: `Cognitive Services OpenAI User`
- Scope: Foundry resource
- Assignee: Container App managed identity

### Project Structure

```
agentdemo/
├── src/
│   ├── agent-container/
│   │   ├── agent_service.py        # Core agent (SHARED)
│   │   ├── app.py                  # FastAPI entry (Container Apps)
│   │   └── foundry_hosted.py       # Adapter entry (Foundry) - NEW
│   ├── agent-function/
│   └── shared/
├── deploy/
│   ├── container-app/
│   │   ├── Dockerfile              # Container Apps
│   │   └── main.bicep
│   └── foundry-hosted/             # NEW
│       ├── Dockerfile.foundry
│       └── azure.yaml
├── docs/
│   └── AGENT-FRAMEWORK-FOUNDRY-INTEGRATION.md
└── .env
```

---

## References

### Microsoft Documentation

1. **Agent Framework Types**: https://learn.microsoft.com/en-us/agent-framework/user-guide/agents/agent-types/
2. **Foundry Agent Service Overview**: https://learn.microsoft.com/en-us/azure/ai-foundry/agents/overview
3. **Foundry Hosted Agents**: https://learn.microsoft.com/en-us/azure/ai-foundry/agents/concepts/hosted-agents
4. **Container Apps AI Integration**: https://learn.microsoft.com/en-us/azure/container-apps/ai-integration

### Key Insights from Documentation

#### From Agent Framework Docs

> "Agent Framework makes it easy to create simple agents based on many different inference services. Any inference service that provides a Microsoft.Extensions.AI.IChatClient implementation can be used to build these agents."

**Azure AI Foundry Models Support:**
- **Azure OpenAI SDK**: `https://<resource>.services.ai.azure.com/`
- **OpenAI SDK**: `https://<resource>.services.ai.azure.com/openai/v1/`
- **Can use DefaultAzureCredential or API keys**

#### From Foundry Hosted Agents Docs

> "The hosting adapter is a framework abstraction layer that automatically converts popular agent frameworks into Microsoft Foundry-compatible HTTP services."

**One-line deployment:**
```python
from_langgraph(my_agent).run()  # LangGraph
from_agent_framework(my_agent).run()  # Agent Framework
```

**Automatic features:**
- OpenTelemetry tracing
- CORS support
- SSE streaming
- Structured logging
- Foundry Responses API compatibility

#### From Container Apps AI Integration Docs

> "Azure Container Apps integrates with Azure AI Foundry, which enables you to deploy curated AI models directly into your containerized environments."

**Sample projects demonstrate:**
- OpenAI integration with Container Apps
- Multi-agent coordination (MCP)
- RAG with Azure AI Search

---

## Decision Matrix

### When to Use Container Apps

✅ **Use Container Apps when:**
- Need custom API endpoints beyond standard chat
- Require specific integration patterns
- Want full control over HTTP server behavior
- Need to integrate with existing microservices
- Have custom observability requirements
- Want to optimize infrastructure costs yourself

### When to Use Foundry Hosted Agents

✅ **Use Foundry Hosted when:**
- Standard agent chat interface is sufficient
- Want zero infrastructure management
- Need auto-scaling without configuration
- Prefer pay-as-you-go pricing
- Want built-in Foundry integration (tools, models, etc.)
- Need enterprise security out-of-the-box

### When to Use BOTH

✅ **Use both when:**
- **Development/Staging**: Test with Foundry Hosted (fast iteration)
- **Production**: Run on Container Apps (cost optimization)

OR

- **Internal**: Container Apps with custom integrations
- **External API**: Foundry Hosted with standard interface

---

## Next Steps

### Immediate (Phase 1)

1. ✅ Capture this research in markdown
2. ⏳ Fix endpoint configuration in `.env` and `agent_service.py`
3. ⏳ Enable Container App managed identity
4. ⏳ Assign RBAC roles
5. ⏳ Test deployment end-to-end

### Future (Phase 2)

6. ⏳ Install `azure-ai-agentserver-agentframework`
7. ⏳ Create `foundry_hosted.py` entry point
8. ⏳ Test locally on port 8088
9. ⏳ Deploy with `azd up`
10. ⏳ Compare both deployments

---

## Conclusion

**Microsoft Agent Framework provides a unified development experience for building agents that can be deployed to multiple targets.**

By leveraging:
- **Shared agent code** (agent_service.py)
- **Different entry points** (FastAPI vs Hosting Adapter)
- **Common models backend** (Foundry Models)

We can achieve **one codebase, two deployment targets** with minimal code duplication.

**The hosting adapter is the key** - it bridges the gap between custom agent code and Foundry's managed service, allowing teams to start with Container Apps for flexibility and add Foundry Hosted for simplicity.

---

**Document Owner:** GitHub Copilot
**Last Updated:** January 20, 2026
**Status:** Ready for Phase 1 Implementation
