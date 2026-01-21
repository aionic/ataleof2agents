# Demo & Customer Readiness Sprint

**Sprint Goal**: Transform codebase into demo/customer-ready reference implementation for Agent Framework with portable deployment (Container Apps + Azure AI Foundry)

**Target Audience**: Developers and architects evaluating Agent Framework and deciding where to host agents
**Key Message**: Same agent code, two deployment options - choose what fits your needs

**Sprint Duration**: 1-2 days
**Start Date**: 2026-01-21

---

## Sprint Objective

Create a clean, streamlined repository that developers can:
1. Clone and understand in 5 minutes
2. Deploy to either Container Apps or Foundry in 15 minutes
3. Use as reference for building their own agents
4. Port between deployment models without code rewrites

---

## Stories

### Story 1: Codebase Cleanup ✅

**Goal**: Remove unused code, organize structure, make repo clean

**Tasks**:
- ✅ Remove legacy weather service code (deprecated artifacts)
- ✅ Consolidate planning documents (move to `archive/` or remove)
- ✅ Move comparison reports to `docs/` folder
- ✅ Clean up root directory (keep only essential files)
- ✅ Remove empty directories (`deploy/foundry/`)
- ✅ Update `.gitignore` to prevent clutter

**Files to Remove**:
```
legacy weather service folder          → DELETE (not used)
legacy function Bicep template         → DELETE (not used)
FOUNDRY-DEPLOYMENT-SPRINT.md           → ARCHIVE (sprint doc)
SPRINT-COMPLETION-REPORT.md            → ARCHIVE (completed sprint)
comparison-report.md                   → MOVE to docs/
```

**Files to Keep**:
```
src/agent-container/                   → Core agent code
src/agent-foundry/                     → Foundry deployment code
deploy/container-app/                  → Container Apps deployment
docs/                                  → Documentation
specs/                                 → Specifications (reference)
```

**Acceptance Criteria**:
- Clean `git status` (only tracked files that matter)
- No unused code in `src/`
- Organized `docs/` folder
- Root directory has <10 files

---

### Story 2: Add MIT License

**Goal**: Add open-source license for customer use

**Tasks**:
- Create `LICENSE` file with MIT license
- Add license header reference to README

**Acceptance Criteria**:
- `LICENSE` file in root
- Standard MIT license text
- Year: 2026

---

### Story 3: Streamlined README

**Goal**: Create clear, concise README that gets developers to code fast

**Structure**:
```markdown
# Agent Framework Reference Implementation

Brief description (2-3 sentences)

## Quick Start (5 minutes)
- What you'll build
- Prerequisites
- Three commands to deploy

## Choose Your Deployment
[Container Apps] → Self-hosted, fast responses
[Foundry] → Managed service, built-in orchestration
[Both] → See comparison, decide later

## What's Inside
- Architecture overview (diagram)
- Key concepts (Agent Framework, external APIs)
- Link to detailed guides

## Documentation
- Agent Framework Basics
- Container Apps Deployment
- Foundry Deployment
- Porting Guide

## Example Use Case
Weather clothing advisor (throwaway example)

## License
MIT
```

**Acceptance Criteria**:
- README is <200 lines
- Clear navigation to next steps
- No walls of text
- Includes architecture diagram

---

### Story 4: Consolidate Deployment Guides

**Goal**: Create streamlined, accurate deployment guides for both models

**Structure**:
```
docs/
├─ DEPLOYMENT-CONTAINER-APPS.md    (Self-hosted path)
├─ DEPLOYMENT-FOUNDRY.md           (Managed path)
└─ PORTING-GUIDE.md                (Moving between)
```

**Each Guide Contains**:
1. **Overview** - What this deployment model provides
2. **Prerequisites** - What you need installed
3. **Step-by-Step Deployment** - Commands with explanations
4. **Verification** - How to test it works
5. **Architecture** - What was deployed
6. **Next Steps** - Links to advanced topics

**Acceptance Criteria**:
- Each guide is complete, standalone
- Commands are tested and work
- Clear when to use which deployment model
- Links between guides work

---

### Story 5: Agent Framework Tutorial

**Goal**: Level 2 tutorial showing how to build agents with external APIs

**File**: `docs/AGENT-FRAMEWORK-TUTORIAL.md`

**Structure**:
1. **What is Agent Framework?**
   - Key concepts
   - Why use it vs. direct LLM calls

2. **Building Your First Agent**
   - Define agent instructions
   - Add external API tools
   - Configure workflow
   - Code walkthrough with references to actual code

3. **External API Integration**
   - OpenAPI spec pattern
   - Authentication options
   - Tool invocation flow
   - Reference: Our weather API example

4. **Deployment Options**
   - Container Apps (self-hosted)
   - Foundry (managed)
   - Code differences (spoiler: minimal)

5. **Best Practices**
   - When to use agents vs. business logic
   - Error handling
   - Cost optimization (hybrid pattern)

**Acceptance Criteria**:
- Explained step-by-step (Level 2)
- Code snippets reference actual repo code
- Clear connection between concepts and implementation
- Developers can follow to build their own

---

### Story 6: Foundry Guide - External vs. Runtime

**Goal**: One comprehensive Foundry guide with two deployment patterns

**File**: `docs/DEPLOYMENT-FOUNDRY.md`

**Structure**:
```markdown
# Deploying Agents to Azure AI Foundry

## Overview
Two patterns for Foundry deployment:
1. Native Runtime Agent (recommended for new agents)
2. External Agent Registration (for existing Container Apps agents)

## Pattern 1: Native Runtime Agent
### What It Is
Agent runs in Foundry's managed runtime with OpenAPI tools

### When to Use
- New agent development
- Want managed service benefits
- Need built-in orchestration

### Deployment Steps
[Step-by-step with code references]

### Code References
- Agent definition: src/agent-foundry/agent.yaml
- Registration script: src/agent-foundry/register_agent.py
- OpenAPI spec: [reference to weather API spec]

## Pattern 2: External Agent Registration
### What It Is
Existing Container Apps agent registered as tool in Foundry

### When to Use
- Already have Container Apps agent
- Want Foundry orchestration without migration
- Hybrid deployment model

### Deployment Steps
[Step-by-step with code references]

### Code References
- External agent OpenAPI: src/agent-foundry/external-agent-openapi.json
- Registration script: src/agent-foundry/register_external_agent.py

## Comparison
[Table showing when to use each pattern]

## Testing Your Deployment
[Verification steps for both patterns]
```

**Acceptance Criteria**:
- Both patterns clearly explained
- Decision criteria provided
- Code references point to actual files
- Complete deployment instructions for each

---

### Story 7: Code Samples & Test Scripts

**Goal**: Provide working test examples that demonstrate both deployments

**Structure**:
```
tests/
├─ test_container_agent.py         (Test Container Apps deployment)
├─ test_foundry_agent.py           (Test Foundry native agent)
├─ test_external_agent.py          (Test Foundry external agent)
└─ test_workflow_patterns.py       (Test workflow orchestration)
```

**Each Test Includes**:
- Clear description of what it tests
- Prerequisites check
- Simple pass/fail output
- Example output shown in comments

**Additional Samples**:
```
samples/
├─ create_agent.py                 (Minimal agent creation example)
├─ add_openapi_tool.py             (Add external API tool)
├─ invoke_agent.py                 (Call agent from code)
└─ workflow_example.py             (Build simple workflow)
```

**Acceptance Criteria**:
- All tests run successfully
- Clear output showing success/failure
- Sample code is minimal, focused
- Easy to adapt for other use cases

---

### Story 8: Architecture & Porting Guide

**Goal**: Level 3 reference documentation for deeper understanding

**Files**:
1. `docs/ARCHITECTURE.md` - Deep dive into how everything works
2. `docs/PORTING-GUIDE.md` - Step-by-step porting between deployments

**ARCHITECTURE.md Structure**:
```markdown
# Architecture Reference

## System Overview
[Comprehensive architecture diagram]

## Components
- Agent Container
- Weather API Service
- Foundry Integration
- Workflow Orchestrator

## Data Flow
[Detailed flow diagrams]

## Deployment Models
- Container Apps architecture
- Foundry architecture
- Hybrid architecture

## Design Decisions
Why we chose this pattern (Level 3 depth)

## Performance Characteristics
Based on our testing (reference comparison report)

## Security Considerations
Authentication, authorization, network security

## Cost Analysis
Detailed breakdown from our tests
```

**PORTING-GUIDE.md Structure**:
```markdown
# Porting Guide: Moving Between Deployment Models

## Overview
Why and when to port

## Container Apps → Foundry
### What Stays the Same
- Agent instructions
- Business logic
- External API integration pattern

### What Changes
- Deployment configuration
- Tool registration method
- Invocation pattern

### Step-by-Step
1. Prepare Foundry environment
2. Create OpenAPI spec (if not exists)
3. Register agent with tools
4. Test in Foundry
5. Update client code

### Code Comparison
[Side-by-side code showing differences]

## Foundry → Container Apps
[Reverse direction]

## Hybrid Deployment
Running both simultaneously
```

**Acceptance Criteria**:
- Architecture diagram included
- Porting steps validated with actual code
- Design decisions explained
- Performance/cost data referenced

---

## Story 9: Documentation Polish & Cross-Links

**Goal**: Ensure all documentation is interconnected and flows well

**Tasks**:
- Add "Next Steps" links to each document
- Create navigation breadcrumbs
- Ensure consistent terminology
- Add table of contents to longer docs
- Review for typos/clarity
- Add timestamps/versions where appropriate

**Documentation Map**:
```
README.md
├─→ QUICKSTART.md
├─→ docs/AGENT-FRAMEWORK-TUTORIAL.md
│   └─→ docs/DEPLOYMENT-CONTAINER-APPS.md
│   └─→ docs/DEPLOYMENT-FOUNDRY.md
├─→ docs/PORTING-GUIDE.md
└─→ docs/ARCHITECTURE.md

docs/DEPLOYMENT-FOUNDRY.md
├─→ Section 1: Native Runtime
└─→ Section 2: External Registration
```

**Acceptance Criteria**:
- Every document links to related docs
- No broken links
- Consistent style and terminology
- Clear navigation path

---

## Story 10: Final Cleanup & Demo Verification

**Goal**: Ensure everything works end-to-end for demo

**Tasks**:
- Run all tests
- Verify all deployment steps
- Check all documentation links
- Create demo script/checklist
- Add troubleshooting section to docs
- Tag release version

**Demo Checklist**:
```markdown
## Demo Verification Checklist

### Prerequisites
- [ ] Azure subscription configured
- [ ] Azure CLI installed and authenticated
- [ ] Python 3.11+ with uv installed
- [ ] Git repository cloned

### Container Apps Deployment
- [ ] Weather API deployed
- [ ] Agent container deployed
- [ ] External ingress working
- [ ] Test script passes

### Foundry Deployment - Native
- [ ] Agent registered in Foundry
- [ ] OpenAPI tool configured
- [ ] Test calls working
- [ ] Response quality verified

### Foundry Deployment - External
- [ ] External agent registered
- [ ] Meta-agent invocation working
- [ ] Test script passes

### Documentation
- [ ] README accurate
- [ ] All links working
- [ ] Code samples tested
- [ ] Architecture diagram current

### Repository
- [ ] Clean git status
- [ ] No sensitive data
- [ ] LICENSE file present
- [ ] .gitignore complete
```

**Acceptance Criteria**:
- All checklist items pass
- Fresh clone and deploy works
- Demo can be delivered confidently

---

## Success Criteria

### Technical Success
- ✅ Clean, organized codebase
- ✅ All tests passing
- ✅ Both deployment models working
- ✅ Documentation complete and accurate

### Developer Experience Success
- ✅ Clone to working demo in <30 minutes
- ✅ Clear understanding of when to use each deployment
- ✅ Can adapt code for their own use case
- ✅ Confident in porting between models

### Demo Readiness Success
- ✅ Can demo both deployments side-by-side
- ✅ Clean repository (professional appearance)
- ✅ Working code samples
- ✅ Compelling architecture story

---

## Execution Plan

**Phase 1: Cleanup (Stories 1-2)** - 2 hours
- Remove unused code
- Add license
- Organize structure

**Phase 2: Core Documentation (Stories 3-4)** - 3 hours
- Streamlined README
- Deployment guides

**Phase 3: Tutorials (Stories 5-6)** - 3 hours
- Agent Framework tutorial
- Foundry dual-pattern guide

**Phase 4: Samples & References (Stories 7-8)** - 3 hours
- Test scripts
- Code samples
- Architecture docs
- Porting guide

**Phase 5: Polish (Stories 9-10)** - 2 hours
- Cross-links
- Final verification
- Demo checklist

**Total Estimate**: 13 hours (1.5-2 days)

---

## Let's Start!

Ready to begin with Story 1 (Codebase Cleanup)?
