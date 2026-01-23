# Phase 5: Archive Legacy Code

**Phase:** 5 of 7
**Status:** Not Started
**Estimated Effort:** 30 minutes
**Depends On:** Phase 4

---

## Objective

Archive legacy code that's been replaced by the unified architecture. This preserves history while cleaning up the active codebase.

---

## Files to Archive

### From `src/agent-foundry/`

| File | Reason |
|------|--------|
| `register_agent.py` | Replaced by image-based hosting |
| `deploy_workflow.py` | Replaced by image-based hosting |
| `register_external_agent.py` | Replaced by unified approach |
| `compare_agents.py` | Test utility - now obsolete |
| `test_agent.py` | Test utility - replaced by unified tests |
| `workflow_patterns.py` | Research code - reference only |
| `external-agent-openapi.json` | External agent spec - no longer used |
| `agent.yaml` | Configuration - superseded |
| `workflow.yaml` | Configuration - superseded |
| `.env.example` | Example config - superseded |
| `README.md` | Documentation - outdated |

### From `src/agent-container/`

| File | Reason |
|------|--------|
| `app.py` | Replaced by `responses_server.py` |
| `agent.yaml` | Configuration - consolidated |
| `workflow.yaml` | Configuration - consolidated |
| `.env.example` | Example config - consolidated |

---

## Tasks

### Task 5.1: Create Archive Directory
**Status:** [ ] Not Started

```powershell
# Create archive structure
New-Item -ItemType Directory -Path "archive" -Force
New-Item -ItemType Directory -Path "archive/foundry-native" -Force
New-Item -ItemType Directory -Path "archive/legacy-fastapi" -Force
```

---

### Task 5.2: Move Foundry Native Files
**Status:** [ ] Not Started

```powershell
# Move foundry-native files to archive
$filesToArchive = @(
    "src/agent-foundry/register_agent.py",
    "src/agent-foundry/deploy_workflow.py",
    "src/agent-foundry/register_external_agent.py",
    "src/agent-foundry/compare_agents.py",
    "src/agent-foundry/test_agent.py",
    "src/agent-foundry/workflow_patterns.py",
    "src/agent-foundry/external-agent-openapi.json",
    "src/agent-foundry/agent.yaml",
    "src/agent-foundry/workflow.yaml",
    "src/agent-foundry/.env.example",
    "src/agent-foundry/README.md"
)

foreach ($file in $filesToArchive) {
    if (Test-Path $file) {
        $destName = Split-Path $file -Leaf
        Move-Item -Path $file -Destination "archive/foundry-native/$destName"
        Write-Host "Archived: $file"
    }
}
```

---

### Task 5.3: Move Legacy FastAPI Files
**Status:** [ ] Not Started

```powershell
# Archive legacy container files
$legacyFiles = @(
    "src/agent-container/app.py",
    "src/agent-container/agent.yaml",
    "src/agent-container/workflow.yaml",
    "src/agent-container/.env.example"
)

foreach ($file in $legacyFiles) {
    if (Test-Path $file) {
        $destName = Split-Path $file -Leaf
        Move-Item -Path $file -Destination "archive/legacy-fastapi/$destName"
        Write-Host "Archived: $file"
    }
}
```

---

### Task 5.4: Create Archive README
**Status:** [ ] Not Started

Create `archive/README.md`:

```markdown
# Archived Code

This directory contains code that has been replaced by the unified architecture.
Files are preserved for reference but are no longer actively maintained.

## Directory Structure

### foundry-native/

Legacy "Foundry Native Runtime" deployment code. This approach ran agents
in Foundry's built-in runtime using YAML configuration and OpenAPI tools.

**Replaced by:** Foundry Hosted (image-based) deployment

**Key files:**
- `register_agent.py` - Agent registration script
- `deploy_workflow.py` - Workflow deployment
- `workflow_patterns.py` - Research on workflow patterns

### legacy-fastapi/

Original FastAPI-based server that exposed `/chat` endpoint on port 8000.

**Replaced by:** Unified Responses API server (`/responses` on port 8088)

**Key files:**
- `app.py` - Original FastAPI server
- `agent.yaml` / `workflow.yaml` - Original configuration

## Migration

If you need to restore any of this code:

1. Copy the relevant files back to `src/`
2. Update imports as needed
3. Consider why the unified approach doesn't meet your needs

## Archive Date

Archived: January 2026
Reason: Unified Responses API architecture
```

---

### Task 5.5: Remove Empty Directories
**Status:** [ ] Not Started

After archiving, clean up empty directories:

```powershell
# Remove src/agent-foundry if empty
if ((Get-ChildItem "src/agent-foundry" -File).Count -eq 0) {
    Remove-Item "src/agent-foundry" -Recurse -Force
    Write-Host "Removed empty: src/agent-foundry"
}

# Remove src/agent-container if empty (after moving core files in Phase 1)
if ((Get-ChildItem "src/agent-container" -File -Exclude "__pycache__").Count -eq 0) {
    Remove-Item "src/agent-container" -Recurse -Force
    Write-Host "Removed empty: src/agent-container"
}
```

---

### Task 5.6: Update .gitignore
**Status:** [ ] Not Started

Add archive to git (not ignore, we want to preserve history):

```gitignore
# Archive directory is tracked (preserved for history)
# !archive/
```

---

## Validation Checklist

- [ ] `archive/` directory created
- [ ] `archive/foundry-native/` contains legacy Foundry code
- [ ] `archive/legacy-fastapi/` contains legacy FastAPI code
- [ ] `archive/README.md` documents the archive
- [ ] Empty `src/agent-foundry/` removed
- [ ] Empty `src/agent-container/` removed
- [ ] Git history preserved via archive

---

## Final Source Structure

After archiving:

```
src/
├── agent/                     # Active agent code
│   ├── core/
│   ├── hosting/
│   ├── tools/
│   └── telemetry/
├── weather-api/               # Active weather service
└── shared/                    # Deprecated shim (backwards compat)

archive/
├── README.md
├── foundry-native/            # Legacy Foundry native code
└── legacy-fastapi/            # Legacy FastAPI server
```

---

## Dependencies

- Phase 1-4 completed (new code in place)
- All imports updated to use new paths

---

## Next Phase

[Phase 6: Update Documentation](06-DOCUMENTATION.md)
