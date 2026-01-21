# Tests

Automated test scripts for validating agent deployments.

---

## Available Tests

### test_container_agent.py
Tests the Container Apps (self-hosted) agent deployment.

**Prerequisites**:
- Agent deployed to Container Apps
- `AGENT_URL` environment variable set (or will use default)

**Run**:
```powershell
.\.venv\Scripts\Activate.ps1
python tests/test_container_agent.py
```

**Tests**:
- Health check
- Cold weather recommendations (NYC 10001)
- Warm weather recommendations (LA 90210)
- Rainy weather recommendations (Seattle 98101)
- Invalid input handling (00000)

**Output**:
```
CONTAINER APPS AGENT TESTING
========================================
Agent URL: https://ca-weather-dev-<suffix>.azurecontainerapps.io

TEST: Health Check
✓ Agent is healthy

TEST: Cold weather (NYC)
Response (4.52s):
  Based on the current weather in New York...
✓ Found keywords: coat, warm, layer
✓ Test passed

...

TEST SUMMARY
========================================
Results: 4/4 passed (100%)
Average duration: 4.68s

✅ All tests passed!
```

---

### test_foundry_agent.py
Tests the Foundry (managed) agent deployment.

**Prerequisites**:
- Agent registered in Foundry
- `AI_PROJECT_CONNECTION_STRING` environment variable set
- `FOUNDRY_AGENT_ID` environment variable set (or will use default)

**Run**:
```powershell
.\.venv\Scripts\Activate.ps1
python tests/test_foundry_agent.py
```

**Tests**:
- Foundry connection
- Agent exists verification
- Cold weather recommendations (NYC 10001)
- Warm weather recommendations (LA 90210)
- Rainy weather recommendations (Seattle 98101)

**Output**:
```
FOUNDRY AGENT TESTING
========================================

TEST: Foundry Connection
✓ Connected to Foundry
  Available agents: 2

TEST: Agent Exists
Agent ID: asst_52uP9hfMXCf2bKDIuSTBzZdz
✓ Agent found: WeatherClothingAdvisor
  Model: gpt-4
  Tools: 1

...

TEST SUMMARY
========================================
Results: 3/3 passed (100%)
Average duration: 10.88s

✅ All tests passed!
```

---

## Environment Variables

Create `.env` file with:

```env
# For Container Apps tests
AGENT_URL=https://ca-weather-dev-<suffix>.azurecontainerapps.io

# For Foundry tests
AI_PROJECT_CONNECTION_STRING=<from-foundry-portal>
FOUNDRY_AGENT_ID=asst_52uP9hfMXCf2bKDIuSTBzZdz
```

---

## Running All Tests

```powershell
# Test Container Apps
python tests/test_container_agent.py

# Test Foundry
python tests/test_foundry_agent.py

# Compare both (if src/agent-foundry/compare_agents.py available)
cd src/agent-foundry
python compare_agents.py
```

---

## Test Cases Explained

### Cold Weather (NYC 10001)
- **Purpose**: Test cold weather clothing recommendations
- **Expected**: Heavy coat, warm layers, winter gear
- **Validates**: Agent handles temperature-based decisions

### Warm Weather (LA 90210)
- **Purpose**: Test warm weather clothing recommendations
- **Expected**: Light clothing, shorts, breathable fabrics
- **Validates**: Agent adapts to different climates

### Rainy Weather (Seattle 98101)
- **Purpose**: Test condition-based recommendations
- **Expected**: Umbrella, waterproof jacket, rain gear
- **Validates**: Agent considers weather conditions beyond temperature

### Invalid Input (00000)
- **Purpose**: Test error handling
- **Expected**: Graceful error response
- **Validates**: Agent handles bad data appropriately

---

## Success Criteria

✅ **All tests pass**: 100% success rate
✅ **Response time**: Container Apps <10s, Foundry <20s
✅ **Quality**: Relevant clothing recommendations
✅ **Keywords found**: Expected terms in responses
✅ **Error handling**: Invalid inputs handled gracefully

---

## Troubleshooting

### Test fails with connection error

**Container Apps**:
```powershell
# Verify agent is running
curl https://<agent-url>/health
```

**Foundry**:
```powershell
# Verify connection string
az account show
```

### Test fails with timeout

**Possible causes**:
- Cold start (first request is slower)
- Network issues
- Agent processing complex query

**Solution**: Re-run test. First test is always slower.

### Keywords not found but response seems correct

**Check**: Response might use synonyms
- "jacket" vs "coat"
- "umbrella" vs "rain gear"

**Solution**: Review test expectations, adjust keywords if needed

---

## Adding New Tests

```python
# Add to TEST_CASES list in either test file
TEST_CASES = [
    {
        "name": "My Test Case",
        "message": "User message to send",
        "expected_keywords": ["word1", "word2"],
    },
]
```

---

## Related Documentation

- **[Container Apps Deployment](../docs/DEPLOYMENT-CONTAINER-APPS.md)** - Deploy agent to test
- **[Foundry Deployment](../docs/DEPLOYMENT-FOUNDRY.md)** - Register agent
- **[Comparison Report](../docs/comparison-report.md)** - See baseline results

---

**Quick test**: `python tests/test_container_agent.py` or `python tests/test_foundry_agent.py`
