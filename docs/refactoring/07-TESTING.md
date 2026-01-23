# Phase 7: Testing & Validation

**Phase:** 7 of 7
**Status:** Not Started
**Estimated Effort:** 1-2 hours
**Depends On:** Phase 6

---

## Objective

Validate the refactored codebase works correctly across all deployment methods.

---

## Tasks

### Task 7.1: Update Test Files
**Status:** [ ] Not Started

Update `tests/test_container_agent.py` to use `/responses` endpoint:

```python
#!/usr/bin/env python3
"""
Test Unified Agent Deployment

Tests the agent using the Foundry Responses API (/responses endpoint).
Works for both Container Apps and Foundry Hosted deployments.
"""

import os
import requests
import time
from typing import Dict, List
from dotenv import load_dotenv

load_dotenv()

# Configuration - works for both deployments
AGENT_URL = os.getenv("AGENT_URL", "http://localhost:8088")

# Test cases
TEST_CASES = [
    {
        "name": "Cold weather (NYC)",
        "message": "What should I wear in 10001?",
        "expected_keywords": ["coat", "warm", "layer"],
    },
    {
        "name": "Warm weather (LA)",
        "message": "What should I wear in 90210?",
        "expected_keywords": ["light", "short"],
    },
]


def format_responses_request(message: str) -> dict:
    """Format message for Foundry Responses API."""
    return {
        "input": {
            "messages": [
                {"role": "user", "content": message}
            ]
        }
    }


def test_health_check() -> bool:
    """Test agent health endpoint."""
    print("\n" + "=" * 60)
    print("TEST: Health Check")
    print("=" * 60)

    try:
        response = requests.get(f"{AGENT_URL}/health", timeout=10)
        if response.status_code == 200:
            print("✓ Agent is healthy")
            return True
        else:
            print(f"✗ Health check failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"✗ Health check error: {str(e)}")
        return False


def test_responses_endpoint(test_case: Dict) -> Dict:
    """Test agent with Responses API."""
    print("\n" + "=" * 60)
    print(f"TEST: {test_case['name']}")
    print("=" * 60)
    print(f"Message: {test_case['message']}")

    start_time = time.time()

    try:
        response = requests.post(
            f"{AGENT_URL}/responses",
            json=format_responses_request(test_case["message"]),
            headers={"Content-Type": "application/json"},
            timeout=60
        )

        duration = time.time() - start_time

        if response.status_code != 200:
            print(f"✗ Request failed: {response.status_code}")
            print(f"  Response: {response.text}")
            return {"success": False, "duration": duration}

        data = response.json()

        # Extract response from Foundry format
        output = data.get("output", {})
        messages = output.get("messages", [])

        agent_response = ""
        for msg in messages:
            if msg.get("role") == "assistant":
                agent_response = msg.get("content", "")
                break

        print(f"\nResponse ({duration:.2f}s):")
        print(f"  {agent_response[:300]}...")

        # Check for expected keywords
        found_keywords = []
        missing_keywords = []

        for keyword in test_case.get("expected_keywords", []):
            if keyword.lower() in agent_response.lower():
                found_keywords.append(keyword)
            else:
                missing_keywords.append(keyword)

        if found_keywords:
            print(f"\n✓ Found keywords: {', '.join(found_keywords)}")
        if missing_keywords:
            print(f"✗ Missing keywords: {', '.join(missing_keywords)}")

        success = len(missing_keywords) == 0
        return {"success": success, "duration": duration, "response": agent_response}

    except Exception as e:
        duration = time.time() - start_time
        print(f"✗ Error: {str(e)}")
        return {"success": False, "duration": duration, "error": str(e)}


def run_all_tests():
    """Run all tests."""
    print("=" * 60)
    print("UNIFIED AGENT TEST SUITE")
    print(f"Target: {AGENT_URL}")
    print("API: Foundry Responses (/responses)")
    print("=" * 60)

    results = []

    # Health check
    if not test_health_check():
        print("\n⚠️  Health check failed - agent may not be running")
        return

    # Run test cases
    for test_case in TEST_CASES:
        result = test_responses_endpoint(test_case)
        results.append({"test": test_case["name"], **result})

    # Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)

    passed = sum(1 for r in results if r["success"])
    failed = len(results) - passed
    avg_time = sum(r["duration"] for r in results) / len(results)

    print(f"Passed: {passed}/{len(results)}")
    print(f"Failed: {failed}/{len(results)}")
    print(f"Average Response Time: {avg_time:.2f}s")

    if failed == 0:
        print("\n✅ All tests passed!")
    else:
        print("\n❌ Some tests failed")


if __name__ == "__main__":
    run_all_tests()
```

---

### Task 7.2: Create Local Test Script
**Status:** [ ] Not Started

Create `test-local.ps1` in project root:

```powershell
#!/usr/bin/env pwsh
# Local testing script for unified agent

param(
    [Parameter(Mandatory=$false)]
    [switch]$StartWeatherApi,

    [Parameter(Mandatory=$false)]
    [switch]$StartAgent,

    [Parameter(Mandatory=$false)]
    [switch]$RunTests
)

$ErrorActionPreference = "Stop"

Write-Host "🧪 Local Testing for Weather Clothing Advisor" -ForegroundColor Cyan

# Load .env
if (Test-Path ".env") {
    Get-Content .env | ForEach-Object {
        if ($_ -match '^([^#][^=]+)=(.*)$') {
            $env:($matches[1].Trim()) = $matches[2].Trim()
        }
    }
}

if ($StartWeatherApi) {
    Write-Host ""
    Write-Host "🌤️  Starting Weather API on port 8001..." -ForegroundColor Yellow
    Start-Process -FilePath "python" -ArgumentList "-m", "uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8001" -WorkingDirectory "src/weather-api" -NoNewWindow
    Start-Sleep -Seconds 2
    Write-Host "   Weather API started" -ForegroundColor Green
}

if ($StartAgent) {
    Write-Host ""
    Write-Host "🤖 Starting Agent (Responses API) on port 8088..." -ForegroundColor Yellow

    # Set required env vars
    if (!$env:WEATHER_API_URL) {
        $env:WEATHER_API_URL = "http://localhost:8001"
    }

    Start-Process -FilePath "python" -ArgumentList "-m", "agent.hosting.responses_server" -WorkingDirectory "src" -NoNewWindow
    Start-Sleep -Seconds 3
    Write-Host "   Agent started" -ForegroundColor Green
}

if ($RunTests) {
    Write-Host ""
    Write-Host "🧪 Running tests..." -ForegroundColor Yellow

    $env:AGENT_URL = "http://localhost:8088"
    python tests/test_container_agent.py
}

if (!$StartWeatherApi -and !$StartAgent -and !$RunTests) {
    Write-Host ""
    Write-Host "Usage:" -ForegroundColor Yellow
    Write-Host "  ./test-local.ps1 -StartWeatherApi    # Start weather API"
    Write-Host "  ./test-local.ps1 -StartAgent         # Start agent"
    Write-Host "  ./test-local.ps1 -RunTests           # Run tests"
    Write-Host ""
    Write-Host "  # Full local test:"
    Write-Host "  ./test-local.ps1 -StartWeatherApi -StartAgent -RunTests"
}
```

---

### Task 7.3: Test Container Apps Deployment
**Status:** [ ] Not Started

Manual testing checklist for Container Apps:

```markdown
## Container Apps Deployment Test

### Prerequisites
- [ ] Image built and pushed to ACR
- [ ] Container Apps deployed

### Tests

1. **Health Check**
   ```bash
   curl https://<app-url>/health
   ```
   Expected: `{"status": "healthy"}`

2. **Responses Endpoint**
   ```bash
   curl -X POST https://<app-url>/responses \
     -H "Content-Type: application/json" \
     -d '{"input": {"messages": [{"role": "user", "content": "What should I wear in 10001?"}]}}'
   ```
   Expected: Clothing recommendations for NYC weather

3. **Response Time**
   - Should respond within 10 seconds
   - Target: < 5 seconds for typical requests

4. **Error Handling**
   ```bash
   curl -X POST https://<app-url>/responses \
     -H "Content-Type: application/json" \
     -d '{"input": {"messages": [{"role": "user", "content": "What should I wear in 00000?"}]}}'
   ```
   Expected: Graceful error handling for invalid zip

### Sign-off
- [ ] All tests pass
- [ ] Logs visible in Application Insights
- [ ] No errors in container logs
```

---

### Task 7.4: Test Foundry Hosted Deployment
**Status:** [ ] Not Started

Manual testing checklist for Foundry Hosted:

```markdown
## Foundry Hosted Deployment Test

### Prerequisites
- [ ] Image built and pushed to ACR
- [ ] Agent registered with Foundry
- [ ] Capability Host enabled

### Tests

1. **Portal Test**
   - Navigate to Azure AI Foundry portal
   - Find your agent
   - Use playground to test: "What should I wear in 10001?"
   Expected: Clothing recommendations

2. **API Test**
   ```bash
   # Get token
   TOKEN=$(az account get-access-token --query accessToken -o tsv)

   # Call agent
   curl -X POST https://<foundry-endpoint>/agents/<agent-id>/responses \
     -H "Authorization: Bearer $TOKEN" \
     -H "Content-Type: application/json" \
     -d '{"input": {"messages": [{"role": "user", "content": "What should I wear in 90210?"}]}}'
   ```
   Expected: Clothing recommendations for LA weather

3. **List Agents**
   ```bash
   curl https://<foundry-endpoint>/agents \
     -H "Authorization: Bearer $TOKEN"
   ```
   Expected: Your agent in the list

### Sign-off
- [ ] Portal playground works
- [ ] API calls work
- [ ] Same responses as Container Apps
```

---

## Validation Checklist

### Code Validation
- [ ] All imports resolve correctly
- [ ] No circular dependencies
- [ ] `python -c "from agent.core import AgentService"` works
- [ ] Docker build succeeds
- [ ] Container starts and serves `/responses`

### Deployment Validation
- [ ] Container Apps deployment works
- [ ] Foundry Hosted deployment works
- [ ] Both return identical responses for same input

### Documentation Validation
- [ ] README accurately describes architecture
- [ ] Deployment guides are accurate
- [ ] No broken links

---

## Final Acceptance Criteria

| Criterion | Status |
|-----------|--------|
| Single Docker image works in Container Apps | [ ] |
| Single Docker image works in Foundry Hosted | [ ] |
| `/responses` endpoint functional | [ ] |
| Weather tool fetches real data | [ ] |
| Clothing recommendations generated | [ ] |
| Response time < 10s typical | [ ] |
| Error handling graceful | [ ] |
| Telemetry flowing to App Insights | [ ] |
| Documentation accurate | [ ] |
| Legacy code archived | [ ] |

---

## Completion

Once all tasks pass:

1. Commit all changes
2. Create PR with summary
3. Update CHANGELOG.md
4. Tag release (v2.0.0)

```powershell
git add .
git commit -m "Refactor: Unified Responses API architecture (v2.0.0)

- Single container image for all deployments
- /responses endpoint as primary API
- Support for Container Apps + Foundry Hosted
- Legacy code archived to archive/"

git tag v2.0.0
git push origin main --tags
```

---

## Congratulations! 🎉

The refactoring is complete. You now have:

- **One codebase** serving all deployment methods
- **One Docker image** that works everywhere
- **One API** (Foundry Responses) as the standard
- **Clean architecture** with clear separation of concerns
- **Archived history** of legacy approaches
