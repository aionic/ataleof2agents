# Phase 3: Dockerfile & Dependencies

**Phase:** 3 of 7
**Status:** Not Started
**Estimated Effort:** 30 minutes
**Depends On:** Phase 2

---

## Objective

Update the Dockerfile and dependencies to support the unified Responses API architecture.

---

## Tasks

### Task 3.1: Update pyproject.toml
**Status:** [ ] Not Started

Add the hosting adapter dependency and update project metadata:

```toml
[project]
name = "agentdemo"
version = "2.0.0"
description = "Weather-Based Clothing Advisor - Unified deployment (Container Apps + Foundry Hosted)"
readme = "README.md"
requires-python = ">=3.11"
dependencies = [
    # Azure Agent Framework
    "agent-framework-core",
    "agent-framework-azure-ai",

    # NEW: Foundry Hosting Adapter (enables /responses endpoint)
    "azure-ai-agentserver-agentframework>=0.1.0",

    # Azure AI Foundry
    "azure-ai-projects>=1.0.0",
    "azure-identity>=1.15.0",

    # HTTP client (for weather tool)
    "requests>=2.31.0",

    # Pydantic (for tool definitions)
    "pydantic>=2.0.0",

    # Telemetry
    "azure-monitor-opentelemetry>=1.2.0",
    "opentelemetry-api>=1.22.0",
    "opentelemetry-sdk>=1.22.0",

    # YAML parsing (for configuration)
    "pyyaml>=6.0.1",

    # Optional: Legacy FastAPI support
    "fastapi>=0.109.0",
    "uvicorn[standard]>=0.27.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=7.4.0",
    "pytest-asyncio>=0.21.0",
    "black>=23.12.0",
    "ruff>=0.1.9",
]

legacy = [
    # Only needed if using legacy /chat endpoint
    "fastapi>=0.109.0",
    "uvicorn[standard]>=0.27.0",
]
```

---

### Task 3.2: Create Unified Dockerfile
**Status:** [ ] Not Started

Replace `Dockerfile.container-app` with a unified `Dockerfile`:

```dockerfile
# Unified Dockerfile for Weather Clothing Advisor Agent
# Supports both Container Apps and Foundry Hosted deployments
#
# Exposes: /responses endpoint on port 8088 (Foundry Responses API)

FROM python:3.11-slim AS builder

# Install uv for fast dependency installation
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

WORKDIR /app

# Copy dependency files
COPY pyproject.toml ./

# Install dependencies (production only)
RUN uv pip install --system --no-cache --prerelease=allow -r pyproject.toml


FROM python:3.11-slim

WORKDIR /app

# Copy installed packages from builder
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages

# Copy application code
COPY src/agent/ ./src/agent/
COPY specs/ ./specs/

# Set Python path
ENV PYTHONPATH=/app/src:/app

# Expose Foundry Responses API port
EXPOSE 8088

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=10s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:8088/health', timeout=2)" || exit 1

# Run the Responses API server
CMD ["python", "-m", "agent.hosting.responses_server"]
```

---

### Task 3.3: Keep Weather API Dockerfile
**Status:** [ ] Not Started

`Dockerfile.weather-api` remains unchanged. Rename if desired for consistency:

```powershell
# Optional: Rename for clarity
# mv Dockerfile.weather-api Dockerfile.weather-api  (no change needed)
```

The weather API is an independent service and doesn't need modification.

---

### Task 3.4: Update .dockerignore
**Status:** [ ] Not Started

Update `.dockerignore` for new structure:

```
# Git
.git
.gitignore

# Python
__pycache__
*.pyc
*.pyo
.pytest_cache
.mypy_cache
.ruff_cache
*.egg-info
.venv
venv

# IDE
.vscode
.idea
*.swp
*.swo

# Archives (don't include legacy code in image)
archive/

# Tests (not needed in production image)
tests/

# Documentation (not needed in production image)
docs/

# Local environment
.env
.env.*
!.env.example

# Build artifacts
build/
dist/
*.whl

# Samples (not needed in production image)
samples/
```

---

## Validation Checklist

- [ ] `pyproject.toml` updated with hosting adapter dependency
- [ ] New unified `Dockerfile` created
- [ ] `.dockerignore` updated
- [ ] Docker build succeeds: `docker build -t weather-advisor:test .`
- [ ] Container starts and exposes port 8088
- [ ] Health check passes

---

## Testing Commands

```powershell
# Build the image
docker build -t weather-advisor:test .

# Run locally (need to set env vars)
docker run -p 8088:8088 `
  -e WEATHER_API_URL=http://host.docker.internal:8001 `
  -e AZURE_FOUNDRY_ENDPOINT=https://your-endpoint.azure.com `
  weather-advisor:test

# Test health
curl http://localhost:8088/health

# Test responses endpoint
curl -X POST http://localhost:8088/responses `
  -H "Content-Type: application/json" `
  -d '{"input": {"messages": [{"role": "user", "content": "What should I wear in 10001?"}]}}'
```

---

## Notes

### Why Port 8088?

Port 8088 is the **standard port** for Foundry Hosted Agents. The hosting adapter defaults to this port. Using this port ensures compatibility with Foundry's expected configuration.

### Why Remove FastAPI from Base?

FastAPI is moved to `[project.optional-dependencies]` because:
- The primary endpoint is now `/responses` via hosting adapter
- FastAPI is only needed for legacy `/chat` endpoint
- Reduces image size if legacy support not needed

---

## Dependencies

- Phase 2 completed (hosting adapter created)
- `azure-ai-agentserver-agentframework` available in PyPI

---

## Next Phase

[Phase 4: Deployment Scripts](04-DEPLOYMENT-SCRIPTS.md)
