# Quick Start: Weather-Based Clothing Advisor

**Purpose**: Manual testing guide and usage documentation for the Weather-Based Clothing Advisor POC

**Audience**: Developers, testers, and demo participants

**Date**: 2026-01-20

## Overview

This guide provides step-by-step instructions for testing the Weather-Based Clothing Advisor application manually. Per POC Constitution Principle III (Rapid Validation), all testing is manual with clear acceptance criteria for each user story.

## Prerequisites

Before testing, ensure you have:

1. **OpenWeatherMap API Key**: Sign up at <https://openweathermap.org/appid> (free tier)
2. **Azure Subscription**: With access to Sweden Central region
3. **Azure CLI**: Installed and authenticated (`az login`)
4. **Python 3.11**: Installed locally for testing
5. **Deployed Resources**:
   - Weather API service deployed and accessible
   - Agent deployment (either Container Apps OR Azure AI Foundry)

## Test Scenarios

### User Story 1 (P1): Basic Weather Lookup

**Goal**: Verify weather data retrieval works correctly

**Manual Test Steps**:

1. **Test Case 1.1: Valid Zip Code (NYC)**
   - Input: `10001`
   - Expected Output:
     - Temperature displayed (numeric value in °F)
     - Weather conditions shown (e.g., "clear sky", "rain")
     - Humidity displayed (0-100%)
     - Wind speed shown (mph)
   - Pass Criteria: All weather fields present and reasonable values
   - Test: Enter zip code, verify all data appears within 5 seconds (SC-001)

2. **Test Case 1.2: Valid Zip Code (LA)**
   - Input: `90210`
   - Expected Output: Similar to 1.1 but different values (warmer climate)
   - Pass Criteria: Weather data reflects typical LA weather patterns

3. **Test Case 1.3: Invalid Zip Code**
   - Input: `00000`
   - Expected Output: User-friendly error message (e.g., "Invalid zip code" or "Zip code not found")
   - Pass Criteria: Error message is clear and actionable (FR-007)

4. **Test Case 1.4: Network Failure Simulation**
   - Setup: Temporarily disable weather API key or endpoint
   - Input: `10001`
   - Expected Output: "Service unavailable" type message
   - Pass Criteria: App doesn't crash, error message displayed (FR-008)

**Verification Checklist**:

- [ ] Weather data displays within 5 seconds (SC-001)
- [ ] Temperature in Fahrenheit
- [ ] Conditions text is readable
- [ ] Humidity shows percentage
- [ ] Wind speed in mph
- [ ] Invalid zip shows error message
- [ ] API failure handled gracefully

---

### User Story 2 (P2): Clothing Recommendations

**Goal**: Verify appropriate clothing suggestions based on weather

**Manual Test Steps**:

1. **Test Case 2.1: Cold Weather (<32°F)**
   - Setup: Find or wait for cold weather location
   - Input: Zip code with temp <32°F (e.g., `60601` in winter)
   - Expected Recommendations:
     - Heavy coat or winter jacket
     - Warm layers (sweater, thermal)
     - Winter accessories (hat, gloves, scarf)
     - Insulated footwear
     - Minimum 3-5 items total (SC-002)
   - Pass Criteria: All items appropriate for freezing weather (FR-005)

2. **Test Case 2.2: Hot Weather (>85°F)**
   - Input: Zip code with temp >85°F (e.g., `85001` in summer)
   - Expected Recommendations:
     - Light clothing (shorts, t-shirt)
     - Sun protection (sunglasses, sunscreen)
     - Breathable fabrics
     - Minimum 3-5 items (SC-002)
   - Pass Criteria: All items appropriate for hot weather (FR-005)

3. **Test Case 2.3: Rainy Conditions**
   - Input: Zip code with rain (check weather, then test)
   - Expected Recommendations:
     - Raincoat or waterproof jacket
     - Umbrella
     - Water-resistant footwear
     - Additional temperature-appropriate items
   - Pass Criteria: Rain gear included regardless of temperature (FR-006)

4. **Test Case 2.4: Snowy Conditions**
   - Input: Zip code with snow (e.g., `80202` in winter)
   - Expected Recommendations:
     - Winter coat
     - Waterproof boots
     - Warm layers
     - Winter accessories
   - Pass Criteria: Snow-appropriate gear included (FR-006)

5. **Test Case 2.5: High Wind Conditions**
   - Input: Zip code with wind >15 mph
   - Expected Recommendations:
     - Windbreaker or wind-resistant layer mentioned
     - Other temperature-appropriate items
   - Pass Criteria: Wind protection addressed (FR-006)

**Temperature Range Validation**:

Test each temperature range per FR-005:

- [ ] Below 32°F: Winter clothing recommended
- [ ] 32-50°F: Cool weather clothing
- [ ] 50-70°F: Moderate clothing
- [ ] 70-85°F: Light clothing
- [ ] Above 85°F: Hot weather gear

**Recommendation Quality Checklist** (SC-004):

- [ ] At least 3-5 recommendations displayed (SC-002)
- [ ] Items are specific (e.g., "heavy winter coat" not "coat")
- [ ] Organized by category (outerwear, layers, accessories, footwear)
- [ ] Reasons provided for each item
- [ ] Language is clear and actionable (no jargon)
- [ ] Understandable without additional explanation

---

### User Story 3 (P3): Quick Re-lookup

**Goal**: Verify multiple lookups work without errors

**Manual Test Steps**:

1. **Test Case 3.1: Sequential Different Zip Codes**
   - Step 1: Enter `10001` → verify weather + recommendations
   - Step 2: Enter `90210` → verify different weather + recommendations
   - Step 3: Enter `60601` → verify different weather + recommendations
   - Pass Criteria: Each lookup shows fresh data, no cached results from previous lookup

2. **Test Case 3.2: Same Zip Code Repeated**
   - Step 1: Enter `10001` → note temperature/conditions
   - Step 2: Wait 1 minute
   - Step 3: Enter `10001` again → verify data may differ (fresh fetch)
   - Pass Criteria: Fresh data fetched, not stale cached data

3. **Test Case 3.3: Invalid Then Valid**
   - Step 1: Enter `00000` → verify error displayed
   - Step 2: Enter `10001` → verify works correctly
   - Pass Criteria: App recovers from error, subsequent lookup works

**Multi-Lookup Checklist**:

- [ ] Can perform multiple lookups in one session (FR-009)
- [ ] Previous results cleared when new lookup begins
- [ ] Fresh weather data fetched each time
- [ ] No errors after multiple consecutive requests
- [ ] Response times remain consistent (<5 sec per SC-001)

---

## Sample Test Zip Codes

Use these zip codes for comprehensive testing:

| Zip Code | Location | Typical Weather | Test Purpose |
|----------|----------|-----------------|--------------|
| `10001` | New York, NY | Varied/Four seasons | General testing |
| `90210` | Beverly Hills, CA | Warm/sunny | Hot weather testing |
| `60601` | Chicago, IL | Cold winters | Cold weather testing |
| `33139` | Miami Beach, FL | Hot/humid | Hot + humid testing |
| `98101` | Seattle, WA | Rainy/moderate | Rain testing |
| `80202` | Denver, CO | Variable/snow | Snow + elevation testing |
| `02134` | Boston, MA | Cold/variable | Cold + rain testing |
| `85001` | Phoenix, AZ | Very hot/dry | Extreme heat testing |
| `00000` | Invalid | N/A | Error handling |
| `12345` | Schenectady, NY | Varied | Valid edge case zip |

---

## Success Criteria Verification

### SC-001: Response Time (<5 seconds)

**How to Test**:
1. Use browser developer tools (F12) → Network tab
2. Enter zip code
3. Measure time from request to display
4. Pass if <5 seconds

**Expected**:
- Weather API cold start: 2-3 seconds
- Weather API call: 1-2 seconds
- Agent processing: 1-2 seconds
- **Total: 4-6 seconds typical (within 5s goal for most cases)**

### SC-002: 3-5 Recommendations

**How to Test**:
1. Get recommendations for any zip code
2. Count number of clothing items suggested
3. Pass if count >= 3

**Expected**: Most weather conditions produce 4-5 recommendations

### SC-003: 95% Zip Code Success Rate

**How to Test**:
1. Test with 20 randomly selected valid US zip codes
2. Count successes (weather data returned + recommendations generated)
3. Calculate: (successes / 20) × 100
4. Pass if >= 95% (i.e., 19+ out of 20 successful)

**Expected**: Nearly 100% success for valid zip codes (API-dependent)

### SC-004: Understandable Recommendations

**How to Test** (Qualitative):
1. Get recommendations for any zip code
2. Review with non-technical person
3. Ask: "Do you understand what to wear and why?"
4. Pass if they can act on recommendations without questions

**Expected**: Clear, specific language with explanations

### SC-005: Extreme Conditions

**How to Test**:
1. Find zip codes with extreme temperatures:
   - Below 0°F: Use weather from Alaska or northern states in winter
   - Above 100°F: Use desert locations in summer (Phoenix, Death Valley)
2. Verify appropriate extreme weather gear recommended
3. Pass if recommendations are sensible for the conditions

**Expected**: Extra emphasis on protection in extreme conditions

---

## Deployment Testing

### Test Both Deployment Options

Per user requirements, test BOTH deployment methods:

#### Option 1: Azure Container Apps Deployment

**Access**:
- URL: `https://<container-app-name>.swedencentral.azurecontainerapps.io`
- Provided after deployment

**Test Steps**:
1. Navigate to Container App URL
2. Enter zip code
3. Verify weather + recommendations display
4. Test all user stories above

**Container-Specific Checks**:
- [ ] Application responds on expected port
- [ ] Environment variables loaded correctly (API keys work)
- [ ] Logs visible in Container Apps console
- [ ] Can scale to zero when idle (check after 5 minutes)

#### Option 2: Azure AI Foundry Agent Service

**Access**:
- Via Azure AI Foundry portal agent chat interface
- OR via API endpoint provided during deployment

**Test Steps**:
1. Open agent chat interface or call API
2. Send message: "What should I wear? Zip code 10001"
3. Verify agent calls weather API tool
4. Verify recommendations display
5. Test all user stories above

**Foundry-Specific Checks**:
- [ ] Agent thread persists across multiple messages
- [ ] Weather API tool calls visible in Foundry dashboard
- [ ] Agent instructions followed correctly
- [ ] Model responses are consistent with prompts

**Comparison Test**:
- [ ] Both deployments produce same recommendations for same zip code
- [ ] Response times are comparable (<5 sec)
- [ ] Error handling works identically

### Telemetry & Observability Testing

**Goal**: Verify both deployments integrate with Azure AI Foundry telemetry

**Prerequisites**:
- Access to Azure Portal
- Application Insights resource deployed
- Both deployments configured with telemetry

#### Container Apps Telemetry Validation

**Access**: Azure Portal → Application Insights → Logs (KQL query interface)

**Test Steps**:

1. **Verify Request Logging**:
   ```kql
   requests
   | where timestamp > ago(1h)
   | where customDimensions["deployment_type"] == "container-app"
   | project timestamp, name, duration, success
   | order by timestamp desc
   | take 10
   ```
   - Expected: See recent requests with durations
   - Pass: Requests logged after testing Container Apps deployment

2. **Verify Agent Operations**:
   ```kql
   traces
   | where timestamp > ago(1h)
   | where customDimensions["deployment_type"] == "container-app"
   | where message contains "agent" or message contains "get_weather"
   | project timestamp, message, severityLevel
   | order by timestamp desc
   ```
   - Expected: Traces showing agent initialization and tool calls
   - Pass: Agent operations visible in telemetry

3. **Verify Weather API Tool Calls**:
   ```kql
   dependencies
   | where timestamp > ago(1h)
   | where name contains "get_weather" or target contains "openweathermap"
   | project timestamp, name, target, duration, success
   | order by timestamp desc
   ```
   - Expected: HTTP calls to weather API and OpenWeatherMap API
   - Pass: Distributed tracing captures full request path

#### Foundry Agent Telemetry Validation

**Access**: Azure AI Foundry portal → Agent dashboard → Telemetry tab

**Test Steps**:

1. **Verify Agent Threads**:
   - Navigate to agent's thread history
   - Expected: See conversation threads with timestamps
   - Pass: Each test creates a new thread visible in dashboard

2. **Verify Tool Invocations**:
   - Open a thread → expand messages → look for tool calls
   - Expected: `get_weather` tool calls with zip code parameters
   - Pass: Tool calls logged with input/output

3. **Verify Cross-Platform Correlation**:
   ```kql
   // In Application Insights
   requests
   | where timestamp > ago(1h)
   | where customDimensions["deployment_type"] == "foundry-agent"
   | project timestamp, name, duration
   ```
   - Expected: Foundry agent requests also logged to shared App Insights
   - Pass: Both deployments visible in same telemetry backend

#### Telemetry Comparison Checklist

- [ ] Container Apps requests visible in Application Insights
- [ ] Foundry Agent requests visible in Application Insights
- [ ] Both deployments distinguishable via custom dimensions
- [ ] Tool calls (get_weather) tracked in both deployments
- [ ] OpenWeatherMap API calls visible as dependencies
- [ ] Error scenarios logged with proper severity levels
- [ ] Response times match observed user experience (<5 sec)

#### Telemetry Demo Validation

**For POC demonstration, verify you can show**:

1. **Real-time Monitoring**:
   - Execute test request
   - Show request appear in Application Insights within 1-2 minutes
   - Demonstrate telemetry lag is acceptable for POC

2. **Deployment Comparison**:
   - Run same zip code through both deployments
   - Show both appear in telemetry with different `deployment_type` tags
   - Compare response times via duration metric

3. **Error Tracking**:
   - Trigger an error (invalid zip code)
   - Show error logged in telemetry
   - Demonstrate error message aligns with user experience

4. **Distributed Tracing** (Container Apps only):
   - Execute request through Container Apps
   - Show end-to-end trace: agent → weather API → external API
   - Verify trace correlation IDs link operations

**Telemetry Troubleshooting**:

**Issue**: No telemetry appearing in Application Insights

- Check: Application Insights connection string configured correctly
- Check: `APPLICATIONINSIGHTS_CONNECTION_STRING` environment variable set
- Check: Telemetry packages installed (`azure-monitor-opentelemetry` for Container Apps)
- Check: Wait 2-5 minutes for telemetry ingestion lag

**Issue**: Can't distinguish between deployments

- Check: Custom dimensions set with `deployment_type` property
- Fix: Add tags during agent initialization or request processing

**Issue**: Weather API calls not visible in telemetry

- Check: Weather API app has Application Insights enabled
- Check: Weather API integration successful (test Weather API logs)
- Check: Dependencies tracked (HTTP client instrumentation enabled)

---

## Manual Testing Checklist

Complete this checklist for each deployment:

### Basic Functionality

- [ ] Application starts successfully
- [ ] Can enter zip code
- [ ] Weather data displays
- [ ] Clothing recommendations appear
- [ ] Recommendations are specific and organized
- [ ] At least 3-5 items recommended

### Error Handling

- [ ] Invalid zip code shows clear error
- [ ] API failure handled gracefully
- [ ] No application crashes observed
- [ ] Error messages are user-friendly

### Weather Conditions

- [ ] Cold weather (<32°F) recommendations appropriate
- [ ] Hot weather (>85°F) recommendations appropriate
- [ ] Rainy conditions include rain gear
- [ ] Snowy conditions include winter gear
- [ ] Windy conditions addressed

### User Experience

- [ ] Response time <5 seconds (SC-001)
- [ ] Recommendations understandable (SC-004)
- [ ] Can perform multiple lookups (US3)
- [ ] Clear layout and formatting

### Deployment-Specific

- [ ] Container Apps version works
- [ ] Foundry version works
- [ ] Both produce same results
- [ ] Environment variables configured correctly
- [ ] Telemetry visible in Application Insights for both deployments
- [ ] Custom dimensions distinguish between deployment types
- [ ] Tool calls tracked in telemetry
- [ ] Distributed tracing works (Container Apps)

---

## Troubleshooting

### Issue: Weather data not appearing

**Possible Causes**:
- Weather API key not configured
- Weather API not deployed or not running
- Network connectivity issues

**Resolution Steps**:
1. Check Weather API logs in Azure portal
2. Verify API key is valid: `curl "https://api.openweathermap.org/data/2.5/weather?zip=10001,US&appid={YOUR_KEY}"`
3. Test Weather API endpoint directly (if exposed)
4. Check environment variables in deployment

### Issue: Recommendations seem incorrect

**Possible Causes**:
- Agent instructions not loaded correctly
- Model temperature setting too high (too creative)
- Tool response format incorrect

**Resolution Steps**:
1. Review agent instructions in deployment
2. Check tool response format matches data model
3. Verify temperature classification logic
4. Test with known weather data

### Issue: Slow response times (>5 seconds)

**Possible Causes**:
- Weather API cold start
- Weather API slow response
- Agent model processing delay

**Resolution Steps**:
1. Check Weather API cold start time (first request vs subsequent)
2. Test weather API directly for response time
3. Consider using faster model (gpt-4o-mini)
4. Check network latency to Sweden Central

### Issue: Application crashes or errors

**Possible Causes**:
- Missing dependencies
- Configuration errors
- Resource limits exceeded

**Resolution Steps**:
1. Check application logs (Container Apps or Weather API logs)
2. Verify all dependencies installed correctly
3. Review environment variable configuration
4. Check resource quota limits

---

## Demo Script

Use this script for demonstrating the POC:

### Introduction (1 minute)

"This is the Weather-Based Clothing Advisor - an AI agent that tells you what to wear based on current weather conditions. It demonstrates Azure's Agent Framework SDK with a real-world weather API integration. Let me show you how it works."

### Demo Flow (3-4 minutes)

1. **Basic Lookup** (NYC - varied weather)
   - "Let's check New York City - zip code 10001"
   - [Enter 10001, wait for results]
   - "You can see it retrieved the current weather and provided specific clothing recommendations based on the temperature and conditions"

2. **Different Climate** (LA - hot weather)
   - "Now let's try somewhere warmer - Beverly Hills, 90210"
   - [Enter 90210]
   - "Notice how the recommendations changed - lighter clothing for the hotter weather"

3. **Adverse Weather** (Rainy or cold location)
   - "Let's see how it handles bad weather - Chicago, 60601"
   - [Enter 60601]
   - "See how it added rain gear / winter items based on the conditions"

4. **Error Handling** (Optional)
   - "And if you enter an invalid zip code like 00000"
   - [Enter 00000]
   - "It handles errors gracefully with a clear message"

### Deployment Showcase (2 minutes)

"This same application is deployed two ways:
1. **Container Apps** - Containerized deployment with auto-scaling
2. **Azure AI Foundry** - Managed agent service with built-in hosting

Both use the same weather API tool and produce identical recommendations, showcasing Azure's flexibility for agent deployment."

### Closing

"This demonstrates how Azure's Agent Framework makes it easy to build intelligent agents that integrate with external APIs and provide contextual, actionable recommendations."

---

## Next Steps

After successful manual testing:

1. **Document Results**: Note any issues or unexpected behavior
2. **Capture Screenshots**: For demonstration purposes
3. **Record Response Times**: Verify SC-001 compliance
4. **Test Edge Cases**: Try unusual but valid zip codes
5. **Gather Feedback**: From test participants on recommendation quality

**Ready for Production?** NO - This is a POC. See [spec.md](spec.md) "Out of Scope" section for production requirements.

---

## References

- Feature Spec: [spec.md](spec.md)
- Implementation Plan: [plan.md](plan.md)
- Agent Instructions: [contracts/agent-prompts.md](contracts/agent-prompts.md)
- Data Model: [data-model.md](data-model.md)
- Research: [research.md](research.md)
