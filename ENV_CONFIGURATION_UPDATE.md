# Environment Configuration Update

## Summary

Updated the deployment documentation to use `.env` file for environment variables instead of inline PowerShell variable definitions. This improves security, consistency, and ease of deployment.

## Changes Made

### 1. Updated `.env.example`

Enhanced the template with comprehensive deployment variables:

```env
# =============================================================================
# DEPLOYMENT CONFIGURATION
# =============================================================================
AZURE_RESOURCE_GROUP=rg-weather-advisor-dev
AZURE_LOCATION=swedencentral
ENVIRONMENT_NAME=dev

# =============================================================================
# API KEYS & CREDENTIALS
# =============================================================================
OPENWEATHERMAP_API_KEY=your_api_key_here

# =============================================================================
# AZURE OPENAI (for Container Apps Agent)
# =============================================================================
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/
AZURE_OPENAI_DEPLOYMENT_NAME=gpt-4
AZURE_OPENAI_API_KEY=your-api-key-here

# =============================================================================
# AZURE SERVICES (auto-populated after deployment)
# =============================================================================
WEATHER_FUNCTION_URL=https://your-function-app.azurewebsites.net/api/get_weather
APPLICATIONINSIGHTS_CONNECTION_STRING=InstrumentationKey=your-key-here

# =============================================================================
# AZURE AI FOUNDRY (for Foundry agent deployment)
# =============================================================================
AZURE_AI_PROJECT_ENDPOINT=https://your-project.azure.ai
AZURE_AI_MODEL_DEPLOYMENT_NAME=gpt-4o-mini
AZURE_SUBSCRIPTION_ID=your-subscription-id

# =============================================================================
# CONTAINER APPS CONFIGURATION
# =============================================================================
CONTAINER_REGISTRY_NAME=your-acr-name
CONTAINER_APP_NAME=weather-advisor-app
CONTAINER_APP_ENVIRONMENT=your-environment-name
```

### 2. Updated `DEPLOYMENT.md`

#### Added Step 1: Configure Environment Variables

```bash
# From project root
cp .env.example .env

# Edit .env and fill in your values:
# - AZURE_RESOURCE_GROUP (e.g., rg-weather-advisor-dev)
# - AZURE_LOCATION (e.g., swedencentral)
# - OPENWEATHERMAP_API_KEY (from https://openweathermap.org/appid)
# - AZURE_OPENAI_ENDPOINT and AZURE_OPENAI_DEPLOYMENT_NAME
```

#### Added PowerShell Script to Load .env

For all deployment sections, added:

```powershell
# Load environment variables from .env file
Get-Content ../../.env | ForEach-Object {
    if ($_ -match '^([^#][^=]+)=(.*)$') {
        [Environment]::SetEnvironmentVariable($matches[1], $matches[2], "Process")
    }
}
```

#### Replaced Inline Variables with .env References

**Before:**
```powershell
$RESOURCE_GROUP = "rg-weather-advisor-dev"
$LOCATION = "swedencentral"
$OPENWEATHERMAP_API_KEY = "your-api-key-here"

az group create --name $RESOURCE_GROUP --location $LOCATION
```

**After:**
```powershell
# Variables loaded from .env
az group create --name $env:AZURE_RESOURCE_GROUP --location $env:AZURE_LOCATION
```

#### Added Auto-Save of Generated Values

Deployment commands now save generated URLs and connection strings back to .env:

```powershell
# Get Application Insights connection string
$APP_INSIGHTS_CS = az monitor app-insights component show `
    --resource-group $env:AZURE_RESOURCE_GROUP `
    --query connectionString -o tsv

# Save to .env file for future use
Add-Content ../../.env "`nAPPLICATIONINSIGHTS_CONNECTION_STRING=$APP_INSIGHTS_CS"

# Get Weather Function URL
$WEATHER_FUNCTION_URL = az functionapp show `
    --resource-group $env:AZURE_RESOURCE_GROUP `
    --query defaultHostName -o tsv

# Save to .env
Add-Content ../../.env "`nWEATHER_FUNCTION_URL=$WEATHER_FUNCTION_URL"
```

### 3. Verified `.gitignore`

Confirmed that `.env` is already properly excluded from git at line 40:

```ignore
# Environment variables
.env
.env.local
*.env
```

## Benefits

### Security
- ✅ Sensitive values (API keys, connection strings) never committed to git
- ✅ `.env` excluded via `.gitignore`
- ✅ `.env.example` provides template without sensitive data

### Consistency
- ✅ Single source of truth for configuration values
- ✅ Same `.env` file used for both Container Apps and Foundry deployments
- ✅ Eliminates copy-paste errors across deployment steps

### Ease of Use
- ✅ Configure once, deploy anywhere
- ✅ Generated values auto-saved to `.env` for reuse
- ✅ Clear documentation of required variables

### Maintainability
- ✅ Easy to update configuration without editing scripts
- ✅ Team members can have different `.env` files for different environments
- ✅ CI/CD pipelines can inject environment variables easily

## Usage Guide

### First Time Setup

1. **Copy the template:**
   ```bash
   cp .env.example .env
   ```

2. **Fill in required values:**
   - `AZURE_RESOURCE_GROUP` - Your Azure resource group name
   - `AZURE_LOCATION` - Azure region (e.g., swedencentral)
   - `OPENWEATHERMAP_API_KEY` - Get from https://openweathermap.org/appid
   - `AZURE_OPENAI_ENDPOINT` - Your Azure OpenAI endpoint
   - `AZURE_OPENAI_DEPLOYMENT_NAME` - Your GPT-4 deployment name
   - `CONTAINER_REGISTRY_NAME` - Your Azure Container Registry name

3. **Deploy:**
   ```powershell
   cd deploy/container-app
   # The deployment scripts will automatically load .env
   ```

### During Deployment

Deployment scripts will automatically:
- Load variables from `.env`
- Use them in Azure CLI commands
- Save generated values (URLs, connection strings) back to `.env`

### After Deployment

Your `.env` file will be updated with generated values:
- `APPLICATIONINSIGHTS_CONNECTION_STRING`
- `WEATHER_FUNCTION_URL`

These can be reused for subsequent deployments or local development.

## Environment Variables Reference

### Required (Manual Setup)
| Variable | Purpose | Example |
|----------|---------|---------|
| `AZURE_RESOURCE_GROUP` | Resource group name | `rg-weather-advisor-dev` |
| `AZURE_LOCATION` | Azure region | `swedencentral` |
| `ENVIRONMENT_NAME` | Environment identifier | `dev` |
| `OPENWEATHERMAP_API_KEY` | Weather API key | `your-api-key-here` |
| `AZURE_OPENAI_ENDPOINT` | OpenAI endpoint URL | `https://your-resource.openai.azure.com/` |
| `AZURE_OPENAI_DEPLOYMENT_NAME` | Model deployment | `gpt-4` |
| `CONTAINER_REGISTRY_NAME` | ACR name | `youracrname` |

### Auto-Generated (Deployment)
| Variable | Purpose | Generated By |
|----------|---------|--------------|
| `WEATHER_FUNCTION_URL` | Function endpoint | Function deployment |
| `APPLICATIONINSIGHTS_CONNECTION_STRING` | Telemetry | App Insights deployment |

### Optional
| Variable | Purpose | Default |
|----------|---------|---------|
| `CONTAINER_APP_NAME` | Custom app name | `weather-advisor-app` |
| `FUNCTION_APP_NAME` | Custom function name | `func-weather-advisor-{env}` |

## Migration from Old Approach

If you have existing deployments using inline variables:

1. **Create .env file:**
   ```bash
   cp .env.example .env
   ```

2. **Transfer your existing values:**
   ```env
   AZURE_RESOURCE_GROUP=your-existing-rg
   AZURE_LOCATION=your-existing-location
   OPENWEATHERMAP_API_KEY=your-existing-key
   ```

3. **Query existing resources for URLs:**
   ```powershell
   # Get existing Weather Function URL
   $WEATHER_FUNCTION_URL = az functionapp show `
       --resource-group your-rg `
       --name your-function `
       --query defaultHostName -o tsv

   # Add to .env
   Add-Content .env "`nWEATHER_FUNCTION_URL=https://$WEATHER_FUNCTION_URL/api/get_weather"
   ```

4. **Use updated deployment commands:**
   Follow the updated DEPLOYMENT.md instructions.

## Best Practices

### Development
- ✅ Each developer maintains their own `.env` file
- ✅ Never commit `.env` to version control
- ✅ Keep `.env.example` updated with new variables
- ✅ Document required variables in `.env.example` comments

### Production
- ✅ Use Azure Key Vault for sensitive values
- ✅ CI/CD pipelines inject environment variables
- ✅ Rotate API keys regularly
- ✅ Use managed identities instead of API keys where possible

### Team Collaboration
- ✅ Share `.env.example` updates via git
- ✅ Document variable changes in pull requests
- ✅ Provide onboarding guide for new team members
- ✅ Keep variable names consistent across environments

## Troubleshooting

### Variables Not Loading

**Problem:** Deployment fails with "variable not set" error

**Solution:**
```powershell
# Verify .env file exists
Test-Path .env

# Manually load .env
Get-Content .env | ForEach-Object {
    if ($_ -match '^([^#][^=]+)=(.*)$') {
        [Environment]::SetEnvironmentVariable($matches[1], $matches[2], "Process")
    }
}

# Verify variable is loaded
echo $env:AZURE_RESOURCE_GROUP
```

### Generated Values Missing

**Problem:** Deployment succeeds but .env not updated

**Solution:**
```powershell
# Manually query and save
$FUNCTION_URL = az functionapp show `
    --resource-group $env:AZURE_RESOURCE_GROUP `
    --name "func-weather-$env:ENVIRONMENT_NAME" `
    --query defaultHostName -o tsv

Add-Content .env "`nWEATHER_FUNCTION_URL=$FUNCTION_URL"
```

### Variable Name Conflicts

**Problem:** Variable names conflict with system variables

**Solution:** Use project-specific prefixes in `.env`:
```env
WEATHER_ADVISOR_RESOURCE_GROUP=rg-weather-advisor-dev
```

## Related Files

- [`.env.example`](.env.example) - Environment variable template
- [`DEPLOYMENT.md`](DEPLOYMENT.md) - Deployment instructions
- [`.gitignore`](.gitignore) - Git ignore patterns (includes .env)
- [`README.md`](README.md) - Project overview

## Next Steps

1. ✅ `.env.example` updated with all deployment variables
2. ✅ `DEPLOYMENT.md` updated to use .env
3. ✅ `.gitignore` verified (already contains .env)
4. 🔄 Test deployment with new .env workflow
5. 🔄 Update CI/CD pipelines to inject environment variables

## Questions?

If you encounter issues with the .env configuration:
1. Check `.env.example` for required variables
2. Verify `.env` exists and contains values
3. Ensure PowerShell can read the file (no encoding issues)
4. Check that variables are properly loaded (`echo $env:VARIABLE_NAME`)
