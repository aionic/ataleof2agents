# Refactoring Task Tracker

**Project:** Weather Clothing Advisor - Unified Architecture
**Started:** January 23, 2026
**Target:** v2.0.0

---

## Progress Overview

| Phase | Description | Status | Est. Hours |
|-------|-------------|--------|------------|
| 1 | [Source Restructure](01-SOURCE-RESTRUCTURE.md) | ⬜ Not Started | 2-3 |
| 2 | [Hosting Adapter](02-HOSTING-ADAPTER.md) | ⬜ Not Started | 1-2 |
| 3 | [Dockerfile & Deps](03-DOCKERFILE-DEPS.md) | ⬜ Not Started | 0.5 |
| 4 | [Deployment Scripts](04-DEPLOYMENT-SCRIPTS.md) | ⬜ Not Started | 1-2 |
| 5 | [Archive Legacy](05-ARCHIVE-LEGACY.md) | ⬜ Not Started | 0.5 |
| 6 | [Documentation](06-DOCUMENTATION.md) | ⬜ Not Started | 1 |
| 7 | [Testing](07-TESTING.md) | ⬜ Not Started | 1-2 |
| **Total** | | | **7-11** |

Legend: ⬜ Not Started | 🔄 In Progress | ✅ Complete | ❌ Blocked

---

## Quick Reference

### Key Decisions Made
1. ✅ Single container image for all deployments
2. ✅ Foundry Responses API (`/responses`) as primary endpoint
3. ✅ Port 8088 as standard
4. ✅ Archive (not delete) legacy code
5. ✅ Weather API remains separate service

### Deployment Methods (After Refactor)

| Method | Type | Deploy Script |
|--------|------|---------------|
| Container Apps | Self-hosted | `deploy/container-apps/deploy.ps1` |
| Foundry Hosted | Managed | `deploy/foundry-hosted/deploy.ps1` |
| Foundry Native | Legacy/Archived | N/A (see `archive/`) |

### New File Structure

```
src/agent/                    # Unified agent
├── core/                     # Business logic
├── hosting/                  # Server implementations
├── tools/                    # Agent tools
└── telemetry/                # Observability

deploy/
├── container-apps/           # Self-hosted deployment
├── foundry-hosted/           # Managed deployment
├── foundry-native/           # Legacy (README only)
└── shared/                   # Shared scripts

archive/                      # Preserved legacy code
├── foundry-native/
└── legacy-fastapi/
```

---

## Execution Instructions

### Phase 1: Source Restructure
```powershell
# Read the detailed plan
code docs/refactoring/01-SOURCE-RESTRUCTURE.md

# Execute tasks 1.1-1.5
# Mark complete when done
```

### Phase 2-7: Continue Sequentially
Each phase has dependencies on previous phases. Complete in order.

---

## Notes & Issues

### Blocking Issues
(None currently)

### Open Questions
(None currently)

### Decisions Needed
(None currently)

---

## Changelog

| Date | Update |
|------|--------|
| 2026-01-23 | Created refactoring plan (Phases 1-7) |

---

## Sign-off

- [ ] Phase 1 complete - Reviewed by: _______
- [ ] Phase 2 complete - Reviewed by: _______
- [ ] Phase 3 complete - Reviewed by: _______
- [ ] Phase 4 complete - Reviewed by: _______
- [ ] Phase 5 complete - Reviewed by: _______
- [ ] Phase 6 complete - Reviewed by: _______
- [ ] Phase 7 complete - Reviewed by: _______
- [ ] **v2.0.0 Released** - Approved by: _______
