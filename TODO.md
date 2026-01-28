# Agent Refactoring TODO

## Goal
Simplify the agent to use only the `/responses` API (remove legacy `/chat`), optimize Docker build, and deploy cleanly to both ACA and Foundry.

---

## Phase 1: Code Cleanup
- [x] **1.1** Remove legacy `/chat` mode from `src/agent/main.py`
- [x] **1.2** Simplify `src/agent/main.py` to only support responses mode
- [x] **1.3** Remove unused mode switching logic
- [x] **1.4** Update `responses_server.py` if needed

## Phase 2: Dockerfile Optimization
- [x] **2.1** Use multi-stage build properly (builder + runtime)
- [x] **2.2** Optimize layer caching (deps before code)
- [x] **2.3** Remove multi-target complexity (single unified image)
- [x] **2.4** Add proper labels and metadata
- [x] **2.5** Minimize final image size (non-root user, cleanup)

## Phase 3: ACR Cleanup
- [x] **3.1** Delete all old images from `weather-advisor` repo
- [x] **3.2** Delete all old images from `weather-api` repo
- [x] **3.3** Build fresh `weather-advisor:v1` image
- [x] **3.4** Verify image size and layers

## Phase 4: ACA Testing
- [x] **4.1** Update ACA to use new image
- [x] **4.2** Test `/health` endpoint
- [x] **4.3** Test `/responses` endpoint end-to-end
- [x] **4.4** Verify response quality and timing

## Phase 5: Foundry Capability Host Fix
- [ ] **5.1** Delete existing Capability Host
- [ ] **5.2** Recreate with `enablePublicAgentEnvironment: true`
- [ ] **5.3** Verify Capability Host status

## Phase 6: Foundry Agent Deployment
- [ ] **6.1** Delete existing agent (if any)
- [ ] **6.2** Create new agent with clean image
- [ ] **6.3** Start the agent
- [ ] **6.4** Test agent invocation end-to-end

## Phase 7: Final Cleanup
- [ ] **7.1** Commit all changes
- [ ] **7.2** Push to remote
- [ ] **7.3** Update documentation if needed

---

## Progress Log

| Phase | Status | Notes |
|-------|--------|-------|
| 1 | ✅ Complete | Simplified main.py to ~50 lines |
| 2 | ✅ Complete | Multi-stage build, uv, non-root user |
| 3 | ✅ Complete | ACR cleaned, fresh v1 image built |
| 4 | ✅ Complete | ACA health + responses working |
| 5 | In Progress | Need to fix Capability Host |
| 7 | Not Started | |
