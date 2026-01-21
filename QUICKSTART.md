# Weather Advisor - Quick Start Guide

Simple 3-step deployment process for Azure Container Apps.

## Prerequisites

1. **Azure CLI** installed and logged in (`az login`)
2. **Docker Desktop** running
3. **Azure Container Registry** created:
   ```powershell
   az acr create --resource-group foundry --name anacr123321 --sku Basic
   az acr update --name anacr123321 --admin-enabled true
   ```
4. **OpenWeatherMap API Key** from https://openweathermap.org/appid (free tier)

## Step 1: Configure Environment

```powershell
# Copy and edit .env file
Copy-Item .env.example .env

# Edit .env with your values:
# - AZURE_RESOURCE_GROUP=foundry
# - AZURE_LOCATION=swedencentral
# - OPENWEATHERMAP_API_KEY=your_key_here
# - CONTAINER_REGISTRY_NAME=anacr123321
```

## Step 2: Build and Push Image

```powershell
# Run from project root
./build-and-push.ps1

# This handles everything:
# ✓ Builds Docker image from correct directory
# ✓ Tags for your ACR
# ✓ Logs in to ACR
# ✓ Pushes image
```

## Step 3: Deploy to Azure

```powershell
# Navigate to deployment folder
Set-Location deploy/container-app

# Load environment variables
Get-Content ../../.env | ForEach-Object {
    if ($_ -match '^([^#][^=]+)=(.*)$') {
        $varName = $matches[1].Trim()
        $varValue = $matches[2].Trim()
        Set-Variable -Name $varName -Value $varValue -Scope Global
    }
}

# Deploy
./deploy.ps1 `
    -ResourceGroupName $AZURE_RESOURCE_GROUP `
    -OpenWeatherMapApiKey $OPENWEATHERMAP_API_KEY

# The script will:
# ✓ Verify image exists in ACR
# ✓ Deploy shared infrastructure (App Insights, Weather Function)
# ✓ Deploy Container App
# ✓ Output the Container App URL
```

## Test Your Deployment

```powershell
# Get Container App URL
$CONTAINER_APP_NAME = az containerapp list `
    --resource-group foundry `
    --query "[?starts_with(name, 'ca-weather-advisor')].name | [0]" -o tsv

$CONTAINER_APP_URL = az containerapp show `
    --resource-group foundry `
    --name $CONTAINER_APP_NAME `
    --query properties.configuration.ingress.fqdn -o tsv

# Test health endpoint
Invoke-RestMethod -Uri "https://$CONTAINER_APP_URL/health"

# Test chat endpoint
$body = @{ message = "What should I wear in 10001?" } | ConvertTo-Json
Invoke-RestMethod -Uri "https://$CONTAINER_APP_URL/chat" `
    -Method Post `
    -ContentType "application/json" `
    -Body $body
```

## That's It!

You now have a working weather-based clothing advisor with:
- ✅ Workflow orchestration (4-step: Parse → Get Weather → Generate → Format)
- ✅ Application Insights telemetry
- ✅ Azure Functions integration
- ✅ Production-ready container deployment

## Troubleshooting

**Image not found in registry?**
```powershell
# Verify image exists
az acr repository show --name anacr123321 --image weather-advisor:latest

# If missing, run build-and-push.ps1 again
```

**Deployment fails?**
```powershell
# Check Azure CLI is logged in
az account show

# Verify resource group exists
az group show --name foundry

# Check container app logs
az containerapp logs show `
    --resource-group foundry `
    --name $CONTAINER_APP_NAME `
    --follow
```

**Need to rebuild?**
```powershell
# Just run build-and-push.ps1 again from project root
./build-and-push.ps1

# Then redeploy (it will use the new image)
Set-Location deploy/container-app
./deploy.ps1 -ResourceGroupName foundry -OpenWeatherMapApiKey $OPENWEATHERMAP_API_KEY
```

## For More Details

See [DEPLOYMENT.md](DEPLOYMENT.md) for comprehensive documentation including:
- Azure AI Foundry deployment option
- Monitoring and observability setup
- Cost optimization strategies
- Security hardening
- CI/CD pipeline setup

## Clean Up

```powershell
# Remove everything
az group delete --name foundry --yes --no-wait
```
