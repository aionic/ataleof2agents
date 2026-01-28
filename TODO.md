# Agent Refactoring TODO

## Goal
Simplify the agent to use only the `/responses` API (remove legacy `/chat`), optimize Docker build, and deploy cleanly to both ACA and Foundry.

---

## Phase 1: Code Cleanup ✅
- [x] **1.1** Remove legacy `/chat` mode from `src/agent/main.py`
- [x] **1.2** Simplify `src/agent/main.py` to only support responses mode
- [x] **1.3** Remove unused mode switching logic
- [x] **1.4** Update `responses_server.py` if needed

## Phase 2: Dockerfile Optimization ✅
- [x] **2.1** Use multi-stage build properly (builder + runtime)
- [x] **2.2** Optimize layer caching (deps before code)
- [x] **2.3** Remove multi-target complexity (single unified image)
- [x] **2.4** Add proper labels and metadata
- [x] **2.5** Minimize final image size (non-root user, cleanup)

## Phase 3: ACR Cleanup ✅
- [x] **3.1** Delete all old images from `weather-advisor` repo
- [x] **3.2** Delete all old images from `weather-api` repo
- [x] **3.3** Build fresh `weather-advisor:v1` image
- [x] **3.4** Verify image size and layers

## Phase 4: ACA Testing ✅
- [x] **4.1** Update ACA to use new image
- [x] **4.2** Test `/health` endpoint
- [x] **4.3** Test `/responses` endpoint end-to-end
- [x] **4.4** Verify response quality and timing

## Phase 5: Foundry Capability Host ✅
- [x] **5.1** Verified Capability Host already has `enablePublicHostingEnvironment: true`
- [x] **5.2** Granted AcrPull role to Foundry project managed identity
- [x] **5.3** Capability Host status confirmed active

## Phase 6: Foundry Agent Deployment 🔄 IN PROGRESS
- [x] **6.1** Deleted old agent versions
- [x] **6.2** Fixed auth in `agent_service.py` (use `ad_token_provider` not `credential`)
- [x] **6.3** Fixed input format in `responses_server.py` (support both `input` and `messages`)
- [x] **6.4** Built v3 image with fixes, pushed to ACR
- [ ] **6.5** Create agent v6 with v3 image
- [ ] **6.6** Test agent invocation end-to-end

## Phase 7: Final Cleanup
- [x] **7.1** WIP commit made
- [ ] **7.2** Final testing and cleanup
- [ ] **7.3** Push to remote
- [ ] **7.4** Update documentation if needed

---

## Current State (WIP Commit: 1526ebb)

### Images in ACR (`anacr123321.azurecr.io`)
| Image | Status | Notes |
|-------|--------|-------|
| `weather-advisor:v1` | ❌ Old | Original build, auth bug |
| `weather-advisor:v2` | ❌ Old | Auth fix only |
| `weather-advisor:v3` | ✅ Current | Auth + input format fixes |

### Agents in Foundry
Multiple test agents exist (v2-v5) - need cleanup after v6 works:
- `weather-clothing-advisor` - original, issues
- `weather-advisor-v2` through `v5` - various issues
- `weather-advisor-v6` - **TO CREATE** with v3 image

### Key Fixes Applied
1. **Auth Fix** (`src/agent/core/agent_service.py`):
   ```python
   # Changed from:
   credential=DefaultAzureCredential()
   # To:
   ad_token_provider=get_token  # where get_token returns credential.get_token(...).token
   ```

2. **Input Format Fix** (`src/agent/hosting/responses_server.py`):
   ```python
   # Support both Foundry v6 and legacy formats
   messages = body.get("input") or body.get("messages", [])
   if isinstance(messages, str):
       messages = [{"role": "user", "content": messages}]
   ```

---

## Next Steps (Resume Here)

### Step 1: Create Agent v6
```powershell
az cognitiveservices agent create `
  --account-name anfoundy3lsww `
  --project-name weatheragentlsww `
  --name weather-advisor-v6 `
  --image anacr123321.azurecr.io/weather-advisor:v3 `
  --protocol responses `
  --protocol-version v6 `
  --description "Weather clothing advisor agent" `
  --env WEATHER_API_URL=https://ca-weather-api-dev-ezbvua.mangomushroom-3560f614.swedencentral.azurecontainerapps.io AZURE_FOUNDRY_ENDPOINT=https://anfoundy3lsww.services.ai.azure.com AZURE_AI_MODEL_DEPLOYMENT_NAME=gpt-4.1
```

### Step 2: Test Invocation
```powershell
python deploy/scripts/invoke_hosted_agent.py `
  --endpoint https://anfoundy3lsww.services.ai.azure.com/api/projects/weatheragentlsww `
  --agent weather-advisor-v6 `
  --message "What should I wear in 10001?"
```

### Step 3: If Still Failing
- Check container logs in Foundry portal
- Verify env vars are being passed correctly
- Test container locally with same env vars:
  ```powershell
  docker run -p 8088:8088 `
    -e WEATHER_API_URL=https://ca-weather-api-dev-ezbvua.mangomushroom-3560f614.swedencentral.azurecontainerapps.io `
    -e AZURE_FOUNDRY_ENDPOINT=https://anfoundy3lsww.services.ai.azure.com `
    -e AZURE_AI_MODEL_DEPLOYMENT_NAME=gpt-4.1 `
    anacr123321.azurecr.io/weather-advisor:v3
  
  # Test with Foundry v6 format
  curl -X POST http://localhost:8088/responses `
    -H "Content-Type: application/json" `
    -d '{"input": "What should I wear in 10001?"}'
  ```

### Step 4: Cleanup Old Agents
Once v6 works, delete old agents:
```powershell
az cognitiveservices agent delete --account-name anfoundy3lsww --project-name weatheragentlsww --name weather-advisor-v2
az cognitiveservices agent delete --account-name anfoundy3lsww --project-name weatheragentlsww --name weather-advisor-v3
az cognitiveservices agent delete --account-name anfoundy3lsww --project-name weatheragentlsww --name weather-advisor-v4
az cognitiveservices agent delete --account-name anfoundy3lsww --project-name weatheragentlsww --name weather-advisor-v5
```

### Step 5: Cleanup Old Images
```powershell
az acr repository delete --name anacr123321 --image weather-advisor:v1 --yes
az acr repository delete --name anacr123321 --image weather-advisor:v2 --yes
# Keep v3 as production
```

---

## Azure Resources Reference

| Resource | Value |
|----------|-------|
| ACR | `anacr123321.azurecr.io` |
| Foundry Account | `anfoundy3lsww` |
| Foundry Project | `weatheragentlsww` |
| Resource Group | `foundry` |
| Region | Sweden Central |
| ACA Agent | `ca-weather-dev-ezbvua` |
| ACA Weather API | `ca-weather-api-dev-ezbvua` |
| Weather API URL | `https://ca-weather-api-dev-ezbvua.mangomushroom-3560f614.swedencentral.azurecontainerapps.io` |
| Foundry Endpoint | `https://anfoundy3lsww.services.ai.azure.com` |
| Model Deployment | `gpt-4.1` |
