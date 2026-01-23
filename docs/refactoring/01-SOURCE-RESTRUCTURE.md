# Phase 1: Source Code Restructure

**Phase:** 1 of 7
**Status:** Not Started
**Estimated Effort:** 2-3 hours

---

## Objective

Reorganize source code from fragmented `agent-container` and `agent-foundry` directories into a unified `agent` package structure.

---

## Current Structure

```
src/
├── agent-container/           # Container Apps specific
│   ├── agent.yaml
│   ├── agent_service.py       # KEEP - core agent logic
│   ├── app.py                 # MOVE - FastAPI server
│   ├── telemetry.py           # KEEP - telemetry utilities
│   ├── workflow.yaml
│   └── workflow_orchestrator.py  # KEEP - workflow logic
├── agent-foundry/             # Foundry native specific
│   ├── agent.yaml
│   ├── compare_agents.py      # ARCHIVE
│   ├── deploy_workflow.py     # ARCHIVE
│   ├── external-agent-openapi.json  # ARCHIVE
│   ├── README.md              # ARCHIVE
│   ├── register_agent.py      # ARCHIVE
│   ├── register_external_agent.py  # ARCHIVE
│   ├── test_agent.py          # ARCHIVE
│   ├── workflow.yaml
│   └── workflow_patterns.py   # ARCHIVE
├── shared/                    # Shared utilities
│   ├── __init__.py
│   ├── clothing_logic.py      # MOVE to agent/core
│   ├── constants.py           # MOVE to agent/core
│   └── models.py              # MOVE to agent/core
└── weather-api/               # UNCHANGED
    ├── app.py
    ├── openapi.json
    └── weather_service.py
```

---

## Target Structure

```
src/
├── agent/                     # UNIFIED agent package
│   ├── __init__.py
│   ├── agent.yaml             # Combined configuration
│   ├── workflow.yaml          # Workflow definition
│   │
│   ├── core/                  # Core business logic
│   │   ├── __init__.py
│   │   ├── agent_service.py   # Main agent service
│   │   ├── clothing_logic.py  # Clothing recommendations
│   │   ├── constants.py       # Configuration constants
│   │   ├── models.py          # Data models
│   │   └── workflow_orchestrator.py  # Workflow logic
│   │
│   ├── hosting/               # Server/hosting implementations
│   │   ├── __init__.py
│   │   ├── responses_server.py   # NEW: Foundry Responses API
│   │   └── legacy_fastapi.py     # Optional: /chat endpoint
│   │
│   ├── tools/                 # Agent tools
│   │   ├── __init__.py
│   │   └── weather_tool.py    # Weather API tool
│   │
│   └── telemetry/             # Observability
│       ├── __init__.py
│       └── telemetry.py
│
├── weather-api/               # UNCHANGED
│   ├── app.py
│   ├── openapi.json
│   └── weather_service.py
│
└── shared/                    # DEPRECATED - redirect imports
    └── __init__.py            # Backwards compat imports
```

---

## Tasks

### Task 1.1: Create New Directory Structure
**Status:** [ ] Not Started

Create the new `src/agent/` directory structure:

```powershell
# From project root
New-Item -ItemType Directory -Path "src/agent" -Force
New-Item -ItemType Directory -Path "src/agent/core" -Force
New-Item -ItemType Directory -Path "src/agent/hosting" -Force
New-Item -ItemType Directory -Path "src/agent/tools" -Force
New-Item -ItemType Directory -Path "src/agent/telemetry" -Force
```

---

### Task 1.2: Move Core Files
**Status:** [ ] Not Started

Move files from `agent-container/` and `shared/` to new locations:

| Source | Destination |
|--------|-------------|
| `src/agent-container/agent_service.py` | `src/agent/core/agent_service.py` |
| `src/agent-container/workflow_orchestrator.py` | `src/agent/core/workflow_orchestrator.py` |
| `src/agent-container/telemetry.py` | `src/agent/telemetry/telemetry.py` |
| `src/shared/clothing_logic.py` | `src/agent/core/clothing_logic.py` |
| `src/shared/models.py` | `src/agent/core/models.py` |
| `src/shared/constants.py` | `src/agent/core/constants.py` |

**Update imports** in each moved file to reflect new paths.

---

### Task 1.3: Create Package Init Files
**Status:** [ ] Not Started

Create `__init__.py` files for each package:

**src/agent/__init__.py:**
```python
"""
Unified Weather Clothing Advisor Agent.

Supports deployment to:
- Azure Container Apps (self-hosted)
- Azure AI Foundry Hosted Agents (managed)
"""

from .core.agent_service import AgentService
from .core.clothing_logic import ClothingAdvisor
from .core.models import WeatherData, ClothingRecommendation

__all__ = ["AgentService", "ClothingAdvisor", "WeatherData", "ClothingRecommendation"]
__version__ = "2.0.0"
```

**src/agent/core/__init__.py:**
```python
"""Core agent business logic."""

from .agent_service import AgentService
from .clothing_logic import ClothingAdvisor
from .models import WeatherData, ClothingRecommendation, ClothingItem
from .constants import *

__all__ = [
    "AgentService",
    "ClothingAdvisor",
    "WeatherData",
    "ClothingRecommendation",
    "ClothingItem",
]
```

**src/agent/hosting/__init__.py:**
```python
"""Hosting server implementations."""

from .responses_server import create_responses_server

__all__ = ["create_responses_server"]
```

**src/agent/tools/__init__.py:**
```python
"""Agent tools for external API integration."""
```

**src/agent/telemetry/__init__.py:**
```python
"""Telemetry and observability utilities."""

from .telemetry import configure_telemetry

__all__ = ["configure_telemetry"]
```

---

### Task 1.4: Update Import Paths
**Status:** [ ] Not Started

Update all import statements in moved files:

**Old imports:**
```python
from shared.constants import SC_001_RESPONSE_TIME_SECONDS
from shared.models import WeatherData
from shared.clothing_logic import ClothingAdvisor
```

**New imports:**
```python
from agent.core.constants import SC_001_RESPONSE_TIME_SECONDS
from agent.core.models import WeatherData
from agent.core.clothing_logic import ClothingAdvisor
```

Files to update:
- [ ] `agent_service.py`
- [ ] `workflow_orchestrator.py`
- [ ] `clothing_logic.py`
- [ ] `models.py`

---

### Task 1.5: Create Backwards Compatibility Shim
**Status:** [ ] Not Started

Update `src/shared/__init__.py` to redirect imports (temporary, for transition):

```python
"""
DEPRECATED: Import from agent.core instead.

This module exists for backwards compatibility only.
Will be removed in a future version.
"""

import warnings

warnings.warn(
    "Importing from 'shared' is deprecated. Import from 'agent.core' instead.",
    DeprecationWarning,
    stacklevel=2
)

# Re-export for backwards compatibility
from agent.core.models import *
from agent.core.constants import *
from agent.core.clothing_logic import *
```

---

## Validation Checklist

- [ ] All files moved to new locations
- [ ] All `__init__.py` files created
- [ ] All imports updated
- [ ] No circular import errors
- [ ] Can import `from agent.core import AgentService`
- [ ] Weather API unchanged and functional

---

## Dependencies

- None (first phase)

---

## Next Phase

[Phase 2: Create Hosting Adapter](02-HOSTING-ADAPTER.md)
