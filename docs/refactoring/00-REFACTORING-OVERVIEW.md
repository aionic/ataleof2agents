# Codebase Refactoring Plan: Unified Responses API Architecture

**Date:** January 23, 2026
**Status:** Planning
**Goal:** Unify deployment methods to use a single container image with Foundry Responses API

---

## Executive Summary

Refactor the codebase to support **three deployment methods** using a **single unified container image** that exposes the **Foundry Responses API** (`/responses` endpoint on port 8088).

### Current State (Before)

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         CURRENT: Fragmented Architecture                     │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  src/agent-container/          src/agent-foundry/                          │
│  ├── app.py (FastAPI)          ├── register_agent.py                       │
│  ├── agent_service.py          ├── deploy_workflow.py                      │
│  └── workflow_orchestrator.py  ├── register_external_agent.py              │
│                                ├── compare_agents.py                        │
│  Dockerfile.container-app      ├── test_agent.py                           │
│  Port: 8000                    └── workflow_patterns.py                    │
│  Endpoint: /chat                                                            │
│                                (No container - Foundry native runtime)      │
│                                                                             │
│  deploy/container-app/         deploy/foundry/ (empty)                     │
│  └── deploy.ps1                deploy/scripts/                             │
│                                ├── azure_agent_manager.py                  │
│                                └── Invoke-AzureCapabilityHost.ps1          │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Target State (After)

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                      TARGET: Unified Responses API Architecture              │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  src/agent/                    (UNIFIED agent code)                        │
│  ├── core/                                                                  │
│  │   ├── agent_service.py      (Core agent logic)                          │
│  │   ├── clothing_logic.py     (Business logic - moved from shared)        │
│  │   ├── models.py             (Data models)                               │
│  │   └── constants.py          (Configuration)                             │
│  ├── hosting/                                                              │
│  │   ├── responses_server.py   (Hosting adapter - /responses endpoint)     │
│  │   └── legacy_fastapi.py     (Optional: /chat for backwards compat)      │
│  └── tools/                                                                │
│      └── weather_tool.py       (Weather API tool)                          │
│                                                                             │
│  src/weather-api/              (Unchanged - external service)              │
│                                                                             │
│  Dockerfile                    (Single unified Dockerfile)                 │
│  Port: 8088                                                                │
│  Endpoint: /responses                                                      │
│                                                                             │
├─────────────────────────────────────────────────────────────────────────────┤
│                           THREE DEPLOYMENT PATHS                            │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  1. Container Apps (Self-Hosted)     deploy/container-apps/                │
│     └── Same image, you manage       └── deploy.ps1                        │
│                                                                             │
│  2. Foundry Hosted (Image-Based)     deploy/foundry-hosted/                │
│     └── Same image, Azure manages    └── deploy.ps1                        │
│                                       └── Uses azure_agent_manager.py       │
│                                                                             │
│  3. Foundry Native (Legacy/Archive)  archive/foundry-native/               │
│     └── No container, YAML config    └── register_agent.py (archived)      │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Task Breakdown

| Phase | Description | Tasks | Est. Effort |
|-------|-------------|-------|-------------|
| **Phase 1** | Restructure source code | 1.1-1.5 | 2-3 hours |
| **Phase 2** | Create unified hosting adapter | 2.1-2.3 | 1-2 hours |
| **Phase 3** | Update Dockerfile & dependencies | 3.1-3.3 | 30 min |
| **Phase 4** | Refactor deployment scripts | 4.1-4.4 | 1-2 hours |
| **Phase 5** | Archive legacy code | 5.1-5.3 | 30 min |
| **Phase 6** | Update documentation | 6.1-6.4 | 1 hour |
| **Phase 7** | Testing & validation | 7.1-7.4 | 1-2 hours |

**Total Estimated Effort:** 7-11 hours

---

## Phase Details

See individual task files:
- [01-SOURCE-RESTRUCTURE.md](01-SOURCE-RESTRUCTURE.md)
- [02-HOSTING-ADAPTER.md](02-HOSTING-ADAPTER.md)
- [03-DOCKERFILE-DEPS.md](03-DOCKERFILE-DEPS.md)
- [04-DEPLOYMENT-SCRIPTS.md](04-DEPLOYMENT-SCRIPTS.md)
- [05-ARCHIVE-LEGACY.md](05-ARCHIVE-LEGACY.md)
- [06-DOCUMENTATION.md](06-DOCUMENTATION.md)
- [07-TESTING.md](07-TESTING.md)

---

## Key Decisions

### 1. Single Container Image
All deployment methods use the **exact same Docker image**. The only difference is who runs it (you vs Azure).

### 2. Foundry Responses API
The `/responses` endpoint becomes the **primary API**. This is the Foundry standard protocol.

### 3. Legacy Support
The old `/chat` FastAPI endpoint can be kept as an optional wrapper for backwards compatibility, but it will call the same underlying agent.

### 4. Archive vs Delete
Legacy Foundry-native code (register_agent.py, etc.) will be **archived** to `archive/` directory, not deleted. This preserves history and allows reference.

### 5. Weather API Unchanged
The Weather API container remains separate and unchanged. It's an external service called by the agent.

---

## File Movement Summary

### Files to Move/Rename

| From | To | Action |
|------|-----|--------|
| `src/agent-container/` | `src/agent/` | Rename & restructure |
| `src/shared/` | `src/agent/core/` | Merge into agent |
| `src/agent-container/app.py` | `src/agent/hosting/legacy_fastapi.py` | Move (optional) |
| `deploy/scripts/` | `deploy/shared/` | Rename |

### Files to Create

| File | Purpose |
|------|---------|
| `src/agent/hosting/responses_server.py` | Hosting adapter entry point |
| `src/agent/__init__.py` | Package init |
| `src/agent/core/__init__.py` | Package init |
| `deploy/foundry-hosted/deploy.ps1` | Foundry hosted deployment |

### Files to Archive

| File | Reason |
|------|--------|
| `src/agent-foundry/register_agent.py` | Replaced by image-based hosting |
| `src/agent-foundry/deploy_workflow.py` | Replaced by image-based hosting |
| `src/agent-foundry/register_external_agent.py` | Replaced by unified approach |
| `src/agent-foundry/compare_agents.py` | Test utility - archive |
| `src/agent-foundry/workflow_patterns.py` | Research code - archive |
| `src/agent-foundry/test_agent.py` | Test utility - archive |

---

## Success Criteria

- [ ] Single Docker image works in both Container Apps and Foundry Hosted
- [ ] `/responses` endpoint functional with Foundry protocol
- [ ] All three deployment methods documented and tested
- [ ] Legacy code archived (not deleted)
- [ ] Tests pass for all deployment methods
- [ ] Documentation updated

---

## Next Steps

1. Review this plan
2. Approve/modify phases
3. Execute Phase 1 (source restructure)
4. Iterate through remaining phases
