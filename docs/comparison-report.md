# Agent Comparison Test Results

**Test Date**: 2026-01-21 11:37:09

**Agents Tested**:
- Foundry-native: asst_52uP9hfMXCf2bKDIuSTBzZdz
- Container Apps: https://ca-weather-dev-ezbvua.mangomushroom-3560f614.swedencentral.azurecontainerapps.io

## Summary

| Test Case | Foundry Success | Container Success | Foundry Time | Container Time |
|-----------|-----------------|-------------------|--------------|----------------|
| Cold Weather (NYC) | ✅ | ✅ | 19.84s | 5.39s |
| Warm Weather (LA) | ✅ | ✅ | 7.94s | 5.10s |
| Rainy Weather (Seattle) | ✅ | ✅ | 7.23s | 4.28s |
| Hot Weather (Miami) | ✅ | ✅ | 8.97s | 5.79s |
| Invalid Zip Code | ✅ | ✅ | 5.41s | 1.03s |
| Conversational Query | ✅ | ✅ | 10.43s | 5.58s |
| Multiple Locations | ✅ | ✅ | 16.37s | 5.61s |

## Detailed Results

### Test Case 1: Cold Weather (NYC)

**Query**: `What should I wear in 10001?`

**Expected**: Winter clothing recommendations for cold weather

#### Foundry-Native Agent
- **Status**: ✅ Success
- **Duration**: 19.84s
- **Response**: New York (10001) is experiencing clear skies with a current temperature of about 26°F and a "feels like" temperature of 17°F. Here’s what I recommend for this winter weather:

**Outerwear:**
- Heavy i...

#### Container Apps Agent
- **Status**: ✅ Success
- **Duration**: 5.39s
- **Response**: Current Weather in 10001 (New York):
- Temperature: 26°F (feels like 17°F)
- Condition: Clear sky
- Wind: 9 mph

Here’s what you should wear:

Outerwear:
- Insulated winter coat: The low temperature a...
- **Workflow Duration**: 4.54s

#### Comparison
- **Both succeeded** ✅
- **Time difference**: 14.45s (Container faster)
- **Quality match**: Manual review required

### Test Case 2: Warm Weather (LA)

**Query**: `What should I wear in 90210?`

**Expected**: Light clothing for mild/warm weather

#### Foundry-Native Agent
- **Status**: ✅ Success
- **Duration**: 7.94s
- **Response**: Beverly Hills (90210) is currently 56°F with misty conditions and light wind. Here’s what I recommend:

**Outerwear:**
- Light jacket or windbreaker (temperatures are moderate, and mist may make it fe...

#### Container Apps Agent
- **Status**: ✅ Success
- **Duration**: 5.10s
- **Response**: Here are clothing recommendations for Beverly Hills (90210) based on the current misty conditions and temperature around 56°F:

Outerwear:
- Light Jacket or Windbreaker: Misty conditions and cool temp...
- **Workflow Duration**: 4.14s

#### Comparison
- **Both succeeded** ✅
- **Time difference**: 2.84s (Container faster)
- **Quality match**: Manual review required

### Test Case 3: Rainy Weather (Seattle)

**Query**: `What should I wear in 98101?`

**Expected**: Rain gear and waterproof clothing

#### Foundry-Native Agent
- **Status**: ✅ Success
- **Duration**: 7.23s
- **Response**: Seattle (98101) is foggy and chilly today at around 33°F with high humidity. Here’s what I recommend you wear:

**Outerwear:**
- Warm insulated coat or puffer jacket (temperature just above freezing, ...

#### Container Apps Agent
- **Status**: ✅ Success
- **Duration**: 4.28s
- **Response**: Here's what you should wear today in 98101 (Seattle):

Outerwear:

- Insulated jacket or warm coat: The temperature is just above freezing (33°F, feels like 29°F), so a warm outer layer is essential.
...
- **Workflow Duration**: 3.39s

#### Comparison
- **Both succeeded** ✅
- **Time difference**: 2.95s (Container faster)
- **Quality match**: Manual review required

### Test Case 4: Hot Weather (Miami)

**Query**: `What should I wear in 33101?`

**Expected**: Summer clothing for hot humid weather

#### Foundry-Native Agent
- **Status**: ✅ Success
- **Duration**: 8.97s
- **Response**: Miami (33101) is currently 70°F with overcast clouds, 72% humidity, a gentle breeze (15 mph), and no precipitation. Here’s what I recommend:

**Layers:**
- Lightweight long-sleeve shirt or T-shirt (co...

#### Container Apps Agent
- **Status**: ✅ Success
- **Duration**: 5.79s
- **Response**: Here are outfit recommendations for Miami (33101) based on the current weather—around 70°F, overcast skies, mild humidity, and a moderate breeze:

Outerwear:
- Lightweight windbreaker or casual jacket...
- **Workflow Duration**: 4.93s

#### Comparison
- **Both succeeded** ✅
- **Time difference**: 3.18s (Container faster)
- **Quality match**: Manual review required

### Test Case 5: Invalid Zip Code

**Query**: `What should I wear in 00000?`

**Expected**: Error handling - invalid zip code

#### Foundry-Native Agent
- **Status**: ✅ Success
- **Duration**: 5.41s
- **Response**: I couldn't find weather data for zip code 00000. This doesn't appear to be a valid US zip code. Please double-check and provide a 5-digit US zip code (for example, 10001 for New York City or 90210 for...

#### Container Apps Agent
- **Status**: ✅ Success
- **Duration**: 1.03s
- **Response**: I encountered an error processing your request. Please try again....

#### Comparison
- **Both succeeded** ✅
- **Time difference**: 4.38s (Container faster)
- **Quality match**: Manual review required

### Test Case 6: Conversational Query

**Query**: `I'm visiting New York tomorrow (10001), what clothes do I need?`

**Expected**: Weather-based recommendations with conversational response

#### Foundry-Native Agent
- **Status**: ✅ Success
- **Duration**: 10.43s
- **Response**: Here's the current weather for New York (10001): it's 26°F with clear skies and light wind.

Here are my clothing recommendations:

**Outerwear:**
- Heavy insulated winter coat (temperatures are well ...

#### Container Apps Agent
- **Status**: ✅ Success
- **Duration**: 5.58s
- **Response**: Here are clothing recommendations for New York (10001) tomorrow, based on current weather conditions:

Outerwear:
- Light Jacket or Windbreaker: The temperature is cool at around 26°F, and there’s a l...
- **Workflow Duration**: 4.70s

#### Comparison
- **Both succeeded** ✅
- **Time difference**: 4.85s (Container faster)
- **Quality match**: Manual review required

### Test Case 7: Multiple Locations

**Query**: `Compare weather in 10001 and 90210`

**Expected**: Should handle or clarify multiple locations

#### Foundry-Native Agent
- **Status**: ✅ Success
- **Duration**: 16.37s
- **Response**: Here's a comparison of the current weather in 10001 (New York) and 90210 (Beverly Hills):

---

**New York (10001):**
- Temperature: 26°F (feels like 17°F)
- Condition: Clear sky
- Humidity: 43%
- Win...

#### Container Apps Agent
- **Status**: ✅ Success
- **Duration**: 5.61s
- **Response**: Here's a comparison of weather-based clothing recommendations for zip codes 10001 (New York, NY) and 90210 (Beverly Hills, CA):

10001 (New York, NY)
- Temperature: 26°F (feels like 17°F), clear sky, ...
- **Workflow Duration**: 4.83s

#### Comparison
- **Both succeeded** ✅
- **Time difference**: 10.75s (Container faster)
- **Quality match**: Manual review required

## Overall Assessment

**Success Rates**:
- Foundry-native: 7/7 (100.0%)
- Container Apps: 7/7 (100.0%)

**Average Response Times**:
- Foundry-native: 10.88s
- Container Apps: 4.68s

## Conclusions

- **Portability**: ✅ Same workflow code works in both environments
- **Reliability**: Both agents completed all tests
- **Performance**: Container agent was faster on average