# Microsoft Agent Framework Update

**Date**: January 20, 2026
**Status**: ✅ Updated to use official Microsoft Agent Framework

---

## Summary of Changes

Updated the project to use the **official Microsoft Agent Framework** from https://github.com/microsoft/agent-framework with proper package management via **uv**.

---

## 1. Package Dependencies Fixed

### ❌ Before (Incorrect)
```toml
# Wrong package names - these don't exist in PyPI
"azure-ai-agent>=1.0.0",
"azure-ai-agent-azure>=1.0.0",
```

### ✅ After (Correct)
```toml
# Correct Microsoft Agent Framework packages
"agent-framework-core",
"agent-framework-azure-ai",
"pydantic>=2.0.0",  # Required for tool definitions
```

**Installation**: Run `uv sync --prerelease=allow` from the repo root.

**Note**: The Microsoft Agent Framework is currently in **preview/pre-release** (beta versions like 1.0.0b260116), so you must allow pre-release packages.

---

## 2. Agent Framework Code Updated

### Import Changes

**Before**:
```python
from azure.ai.agent import ChatAgent, ToolFunction
from azure.ai.agent.models import Message
```

**After** (using official Microsoft Agent Framework):
```python
from agent_framework import ChatAgent
from agent_framework.azure import AzureOpenAIChatClient
from azure.identity import DefaultAzureCredential
```

### Tool Definition Changes

**Before** (using non-existent ToolFunction):
```python
get_weather_tool = ToolFunction(
    name="get_weather",
    description="Retrieve current weather data for a US zip code",
    parameters={...},
    function=self._call_weather_function
)
```

**After** (using Agent Framework's Python function pattern):
```python
from typing import Annotated
from pydantic import Field

def get_weather(
    zip_code: Annotated[str, Field(description="5-digit US zip code")]
) -> str:
    """Retrieve current weather data for a US zip code."""
    result = self._call_weather_function(zip_code)
    return json.dumps(result)
```

### Agent Initialization Changes

**Before**:
```python
agent = ChatAgent(
    instructions=self.instructions,
    tools=[get_weather_tool],
    name="WeatherClothingAdvisor"
)
```

**After** (with proper chat client):
```python
# Create Azure OpenAI chat client
chat_client = AzureOpenAIChatClient(
    endpoint=azure_endpoint,
    deployment_name=deployment_name,
    credential=DefaultAzureCredential()
)

# Create agent
agent = ChatAgent(
    name="WeatherClothingAdvisor",
    instructions=self.instructions,
    chat_client=chat_client,
    tools=[get_weather]  # Python function, not ToolFunction
)
```

### Message Processing Changes

**Before**:
```python
response = await self.agent.process_message(message)
response_text = response.content
```

**After** (using Agent Framework's run method):
```python
response_text = await self.agent.run(message)
```

---

## 3. Development Tools Updated

### Azure Functions Core Tools

**❌ Before** (using npm):
```bash
npm install -g azure-functions-core-tools@4
```

**✅ After** (platform-specific native installers):

**Windows**:
```powershell
winget install Microsoft.Azure.FunctionsCoreTools
# or
choco install azure-functions-core-tools
```

**macOS**:
```bash
brew tap azure/functions
brew install azure-functions-core-tools@4
```

**Linux**: Download from https://github.com/Azure/azure-functions-core-tools/releases

**Why**: Native installers are preferred over npm for system tools. npm is still valid but not required.

---

## 4. Package Management Standardized

### ❌ Before (mixing pip and uv):
```bash
uv sync
pip install azure-ai-projects azure-identity pyyaml  # Wrong!
```

### ✅ After (uv only):
```bash
# All dependencies managed in pyproject.toml
uv sync
```

**All Python dependencies are now managed exclusively through uv and pyproject.toml.**

---

## 5. Required Environment Variables

The Container Apps agent now requires Azure OpenAI configuration:

```bash
# .env file
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/
AZURE_OPENAI_DEPLOYMENT_NAME=gpt-4
WEATHER_FUNCTION_URL=https://your-function.azurewebsites.net/api/get_weather
APPLICATIONINSIGHTS_CONNECTION_STRING=InstrumentationKey=your-key
```

**Note**: Authentication uses `DefaultAzureCredential()` which supports:
- Azure CLI: `az login`
- Managed Identity (in Azure)
- Environment variables
- Visual Studio Code
- And more...

---

## 6. Files Updated

### Core Code
- ✅ `pyproject.toml` - Fixed package names, added pydantic
- ✅ `src/agent-container/agent_service.py` - Updated to use Microsoft Agent Framework patterns

### Documentation
- ✅ `README.md` - Added link to microsoft/agent-framework repo
- ✅ `DEPLOYMENT.md` - Updated tool installation instructions, removed pip commands
- ✅ `src/agent-foundry/README.md` - Standardized to uv sync
- ✅ `CODE_CONSISTENCY_VALIDATION.md` - Updated code examples

---

## 7. How to Use

### Install Dependencies
```bash
# From repo root - allow pre-release packages
uv sync --prerelease=allow
```

**Why `--prerelease=allow`?** The Microsoft Agent Framework is currently in preview (beta versions), so pre-release packages must be allowed.

### Run Container Apps Agent Locally
```bash
# Set environment variables in .env file
cd src/agent-container
uvicorn app:app --reload
```

### Deploy to Azure
Follow the deployment guides - no changes needed for deployment procedures.

---

## 8. Key Benefits

✅ **Using official Microsoft framework** - Not non-existent packages
✅ **Simpler tool definitions** - Python functions with type hints
✅ **Better patterns** - Following microsoft/agent-framework examples
✅ **Proper package management** - All via uv, no pip mixing
✅ **Platform-native tools** - Using system package managers

---

## 9. Validation

### Test Installation
```bash
# This should now work (note: pre-release flag required)
uv sync --prerelease=allow

# Verify packages installed
uv pip list | grep agent-framework
```

Expected output:
```
agent-framework-azure-ai    1.0.0b260116
agent-framework-core        1.0.0b260116
azure-ai-agents             1.2.0b5
```

### Test Agent Service
```python
# Should import without errors
from agent_framework import ChatAgent
from agent_framework.azure import AzureOpenAIChatClient
```

---

## References

- **Microsoft Agent Framework**: https://github.com/microsoft/agent-framework
- **Python Docs**: https://github.com/microsoft/agent-framework/tree/main/python
- **Examples**: https://github.com/microsoft/agent-framework/tree/main/python/samples

---

## Next Steps

1. ✅ Run `uv sync --prerelease=allow` to install correct packages
2. ✅ Set Azure OpenAI environment variables in `.env`
3. ✅ Test Container Apps agent locally
4. ✅ Verify tool calling works with get_weather function
5. ✅ Deploy to Azure following existing deployment guides

---

## Note on Pre-Release Packages

The Microsoft Agent Framework is actively being developed and is currently in **preview/beta**. This means:

- Package versions include beta markers (e.g., `1.0.0b260116`)
- API may change between releases
- Perfect for POCs and early adoption
- Production use should wait for stable 1.0.0 release

**For production**: Monitor https://github.com/microsoft/agent-framework/releases for stable releases.
