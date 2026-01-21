# Container Apps Deployment

This directory contains the deployment configuration for the Weather-Based Clothing Advisor agent running on Azure Container Apps.

## Architecture

```
Container Apps Deployment
├── Container App (FastAPI + Azure Agent Framework)
│   └── Calls Weather Function via HTTP
├── Azure Function (Weather API)
│   └── Calls OpenWeatherMap API
└── Application Insights
    └── Unified telemetry for both components
```

## Prerequisites

- Azure CLI installed and authenticated
- Docker installed (for building container image)
- Azure Container Registry (or Docker Hub)
- OpenWeatherMap API key
- PowerShell (for deployment script)

## Quick Start

### 1. Set Up Environment

```powershell
# Login to Azure
az login

# Set subscription
az account set --subscription "Your Subscription Name"

# Login to your container registry (example with Azure Container Registry)
az acr login --name yourregistry
```

### 2. Deploy

```powershell
# Basic deployment
./deploy.ps1 `
    -ResourceGroupName "rg-weather-advisor-dev" `
    -OpenWeatherMapApiKey "your-api-key" `
    -ContainerImage "yourregistry.azurecr.io/weather-advisor:latest" `
    -ContainerRegistry "yourregistry.azurecr.io" `
    -RegistryUsername "yourregistry" `
    -RegistryPassword "your-password"

# Custom location and environment
./deploy.ps1 `
    -ResourceGroupName "rg-weather-advisor-prod" `
    -OpenWeatherMapApiKey "your-api-key" `
    -Location "swedencentral" `
    -Environment "prod" `
    -ContainerImage "yourregistry.azurecr.io/weather-advisor:v1.0.0"
```

### 3. Test Deployment

```bash
# Health check
curl https://your-container-app.azurecontainerapps.io/health

# Chat with agent
curl -X POST https://your-container-app.azurecontainerapps.io/chat \
    -H "Content-Type: application/json" \
    -d '{"message": "What should I wear in 10001?"}'
```

## Configuration

### Environment Variables

The Container App is configured with:

- `WEATHER_FUNCTION_URL`: URL of the weather function (auto-configured)
- `APPLICATIONINSIGHTS_CONNECTION_STRING`: Telemetry connection string (auto-configured)
- `ENVIRONMENT`: Deployment environment (dev/staging/prod)

### Scaling

Default scaling configuration:

- **Min replicas**: 1
- **Max replicas**: 3
- **Scale rule**: HTTP concurrent requests (10 per instance)

Modify in [main.bicep](main.bicep) under `template.scale`.

### Resources

Default container resources:

- **CPU**: 0.5 cores
- **Memory**: 1 GB

Adjust in [main.bicep](main.bicep) under `template.containers[0].resources`.

## Monitoring

### Application Insights

Access telemetry:

```bash
# Get Application Insights resource
az monitor app-insights component show \
    --resource-group rg-weather-advisor-dev \
    --query "[?contains(name, 'appi-weather')]"
```

View in Azure Portal:
1. Navigate to Application Insights resource
2. Check:
   - **Live Metrics**: Real-time request/response monitoring
   - **Failures**: Error rates and exceptions
   - **Performance**: Response times and dependencies
   - **Logs**: Custom queries on telemetry data

### Custom Dimensions

All telemetry includes:

- `deployment_type`: "container-app"
- `service.name`: "weather-clothing-advisor"
- `service.version`: "1.0.0"
- `deployment.environment`: Current environment (dev/staging/prod)

### Log Analytics Queries

```kusto
// Recent requests
requests
| where customDimensions.deployment_type == "container-app"
| order by timestamp desc
| take 100

// Average response time
requests
| where customDimensions.deployment_type == "container-app"
| summarize avg(duration) by bin(timestamp, 1h)

// Error rate
requests
| where customDimensions.deployment_type == "container-app"
| summarize ErrorRate=100.0*countif(success == false)/count() by bin(timestamp, 5m)
```

## Troubleshooting

### Container App Logs

```bash
# Stream logs
az containerapp logs show \
    --name ca-weather-advisor-dev-SUFFIX \
    --resource-group rg-weather-advisor-dev \
    --follow

# Query specific time range
az monitor log-analytics query \
    --workspace "log-weather-advisor-dev-SUFFIX" \
    --analytics-query "ContainerAppConsoleLogs_CL | where TimeGenerated > ago(1h)"
```

### Common Issues

1. **Image pull errors**:
   - Verify container registry credentials
   - Check image exists: `docker pull YOUR_IMAGE`

2. **Function timeout**:
   - Check weather function logs
   - Verify OpenWeatherMap API key
   - Check network connectivity

3. **Agent errors**:
   - Review Application Insights failures
   - Check environment variables are set
   - Verify agent-prompts.md is included in image

## Cleanup

```powershell
# Delete resource group (removes all resources)
az group delete --name rg-weather-advisor-dev --yes --no-wait
```

## Cost Optimization

For POC/development:

- Use Consumption plan for Function App (pay-per-execution)
- Set Container App min replicas to 0 for dev environments
- Use Log Analytics 30-day retention (configurable in monitoring.bicep)

## Related

- [Foundry Deployment](../foundry/README.md)
- [Main README](../../README.md)
- [Manual Testing Guide](../../specs/001-weather-clothing-advisor/quickstart.md)
