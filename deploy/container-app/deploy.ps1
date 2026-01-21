#!/usr/bin/env pwsh
# Deployment script for Container Apps deployment
# Prerequisites:
#   1. Run this script to build and push both images
#   2. Have .env file configured in project root

param(
    [Parameter(Mandatory=$true)]
    [string]$ResourceGroupName,

    [Parameter(Mandatory=$true)]
    [string]$OpenWeatherMapApiKey,

    [Parameter(Mandatory=$false)]
    [string]$Location = "swedencentral",

    [Parameter(Mandatory=$false)]
    [string]$Environment = "dev",

    [Parameter(Mandatory=$false)]
    [string]$ContainerRegistry = "",

    [Parameter(Mandatory=$false)]
    [string]$ImageTag = "latest",

    [Parameter(Mandatory=$false)]
    [switch]$SkipBuild
)

$ErrorActionPreference = "Stop"

Write-Host "🚀 Deploying Weather Advisor to Container Apps..." -ForegroundColor Cyan
Write-Host ""

# Load environment variables from project root .env if exists
$envPath = "../../.env"
if (Test-Path $envPath) {
    Write-Host "📄 Loading environment from .env..." -ForegroundColor Yellow
    Get-Content $envPath | ForEach-Object {
        if ($_ -match '^([^#][^=]+)=(.*)$') {
            $varName = $matches[1].Trim()
            $varValue = $matches[2].Trim()
            Set-Variable -Name $varName -Value $varValue -Scope Script
            if ($varName -eq "CONTAINER_REGISTRY_NAME") {
                Write-Host "   Found registry: $varValue" -ForegroundColor Green
            }
            if ($varName -eq "AZURE_FOUNDRY_ENDPOINT") {
                Write-Host "   Found Foundry endpoint: $varValue" -ForegroundColor Green
            }
            if ($varName -eq "AZURE_AI_MODEL_DEPLOYMENT_NAME") {
                Write-Host "   Found model deployment: $varValue" -ForegroundColor Green
            }
        }
    }
}

# Use parameter or environment variable for registry
if (!$ContainerRegistry -and $CONTAINER_REGISTRY_NAME) {
    $ContainerRegistry = $CONTAINER_REGISTRY_NAME
}

if (!$ContainerRegistry) {
    Write-Host "❌ Container registry name is required" -ForegroundColor Red
    Write-Host "   Either:" -ForegroundColor Yellow
    Write-Host "   1. Set CONTAINER_REGISTRY_NAME in .env file, or" -ForegroundColor Yellow
    Write-Host "   2. Pass -ContainerRegistry parameter" -ForegroundColor Yellow
    exit 1
}

# Generate unique build hash (git commit hash + timestamp)
$gitHash = git rev-parse --short HEAD 2>$null
if ($LASTEXITCODE -ne 0 -or !$gitHash) {
    $gitHash = "nogit"
}
$timestamp = Get-Date -Format "yyyyMMdd-HHmmss"
$buildHash = "$gitHash-$timestamp"

Write-Host "📦 Build version: $buildHash" -ForegroundColor Cyan

# Construct full image names with hash
$ContainerImage = "$ContainerRegistry.azurecr.io/weather-advisor:$buildHash"
$WeatherApiImage = "$ContainerRegistry.azurecr.io/weather-api:$buildHash"

# Build and push images unless skipped
if (!$SkipBuild) {
    Write-Host ""
    Write-Host "🔨 Building and pushing images..." -ForegroundColor Yellow

    # Build weather API image
    Write-Host "   Building weather-api..." -ForegroundColor Gray
    docker build -f ../../Dockerfile.weather-api -t $WeatherApiImage ../..
    if ($LASTEXITCODE -ne 0) {
        Write-Host "❌ Failed to build weather-api image" -ForegroundColor Red
        exit 1
    }

    # Also tag as latest
    docker tag $WeatherApiImage "$ContainerRegistry.azurecr.io/weather-api:latest"

    Write-Host "   Pushing weather-api..." -ForegroundColor Gray
    docker push $WeatherApiImage
    docker push "$ContainerRegistry.azurecr.io/weather-api:latest"
    if ($LASTEXITCODE -ne 0) {
        Write-Host "❌ Failed to push weather-api image" -ForegroundColor Red
        exit 1
    }

    # Build agent container image
    Write-Host "   Building weather-advisor..." -ForegroundColor Gray
    docker build -f ../../Dockerfile.container-app -t $ContainerImage ../..
    if ($LASTEXITCODE -ne 0) {
        Write-Host "❌ Failed to build weather-advisor image" -ForegroundColor Red
        exit 1
    }

    # Also tag as latest
    docker tag $ContainerImage "$ContainerRegistry.azurecr.io/weather-advisor:latest"

    Write-Host "   Pushing weather-advisor..." -ForegroundColor Gray
    docker push $ContainerImage
    docker push "$ContainerRegistry.azurecr.io/weather-advisor:latest"
    if ($LASTEXITCODE -ne 0) {
        Write-Host "❌ Failed to push weather-advisor image" -ForegroundColor Red
        exit 1
    }

    Write-Host "   ✓ Both images built and pushed successfully" -ForegroundColor Green
    Write-Host "   Weather API: $WeatherApiImage" -ForegroundColor Gray
    Write-Host "   Agent: $ContainerImage" -ForegroundColor Gray
}

# Get registry credentials
Write-Host "🔐 Getting registry credentials..." -ForegroundColor Yellow
$credsJson = az acr credential show --name $ContainerRegistry 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Failed to get registry credentials" -ForegroundColor Red
    Write-Host "   Make sure:" -ForegroundColor Yellow
    Write-Host "   1. Registry exists: az acr show --name $ContainerRegistry" -ForegroundColor Yellow
    Write-Host "   2. Admin access is enabled: az acr update --name $ContainerRegistry --admin-enabled true" -ForegroundColor Yellow
    Write-Host "   Error: $credsJson" -ForegroundColor Red
    exit 1
}

$creds = $credsJson | ConvertFrom-Json
$RegistryUsername = $creds.username
$RegistryPassword = $creds.passwords[0].value

# Verify images exist in registry (if not built in this run)
if ($SkipBuild) {
    Write-Host "📦 Verifying images exist in registry..." -ForegroundColor Yellow

    # When skipping build, use the ImageTag parameter (allows deploying specific versions)
    $ContainerImage = "$ContainerRegistry.azurecr.io/weather-advisor:$ImageTag"
    $WeatherApiImage = "$ContainerRegistry.azurecr.io/weather-api:$ImageTag"

    Write-Host "   Checking: weather-api:$ImageTag" -ForegroundColor Gray
    try {
        $null = az acr repository show --name $ContainerRegistry --image "weather-api:$ImageTag" --query "name" -o tsv 2>&1
        if ($LASTEXITCODE -ne 0) {
            throw "Image not found"
        }
        Write-Host "   ✓ Image found: $WeatherApiImage" -ForegroundColor Green
    }
    catch {
        Write-Host "❌ Image not found in registry: $WeatherApiImage" -ForegroundColor Red
        Write-Host "   Run without -SkipBuild to build images" -ForegroundColor Yellow
        exit 1
    }

    Write-Host "   Checking: weather-advisor:$ImageTag" -ForegroundColor Gray
    try {
        $null = az acr repository show --name $ContainerRegistry --image "weather-advisor:$ImageTag" --query "name" -o tsv 2>&1
        if ($LASTEXITCODE -ne 0) {
            throw "Image not found"
        }
        Write-Host "   ✓ Image found: $ContainerImage" -ForegroundColor Green
    }
    catch {
        Write-Host "❌ Image not found in registry: $ContainerImage" -ForegroundColor Red
        Write-Host "   Run without -SkipBuild to build images" -ForegroundColor Yellow
        exit 1
    }
}

# Check if resource group exists
Write-Host ""
Write-Host "📦 Checking resource group: $ResourceGroupName" -ForegroundColor Yellow
$rg = az group show --name $ResourceGroupName 2>$null | ConvertFrom-Json
if (!$rg) {
    Write-Host "   Creating resource group: $ResourceGroupName in $Location" -ForegroundColor Green
    az group create --name $ResourceGroupName --location $Location
}
else {
    Write-Host "   ✓ Resource group exists" -ForegroundColor Green
}

# Validate Foundry configuration
if (!$AZURE_FOUNDRY_ENDPOINT) {
    Write-Host "❌ AZURE_FOUNDRY_ENDPOINT not found in .env" -ForegroundColor Red
    exit 1
}

if (!$AZURE_AI_MODEL_DEPLOYMENT_NAME) {
    $AZURE_AI_MODEL_DEPLOYMENT_NAME = "gpt-4.1"
    Write-Host "⚠️  Using default model deployment: $AZURE_AI_MODEL_DEPLOYMENT_NAME" -ForegroundColor Yellow
}

# Deploy Bicep template
Write-Host ""
Write-Host "📋 Deploying infrastructure..." -ForegroundColor Yellow

$deployment = az deployment group create `
    --resource-group $ResourceGroupName `
    --template-file main.bicep `
    --parameters location=$Location `
    --parameters environment=$Environment `
    --parameters openWeatherMapApiKey=$OpenWeatherMapApiKey `
    --parameters containerImage=$ContainerImage `
    --parameters weatherApiImage=$WeatherApiImage `
    --parameters containerRegistry="$ContainerRegistry.azurecr.io" `
    --parameters containerRegistryUsername=$RegistryUsername `
    --parameters containerRegistryPassword=$RegistryPassword `
    --parameters azureFoundryEndpoint=$AZURE_FOUNDRY_ENDPOINT `
    --parameters modelDeploymentName=$AZURE_AI_MODEL_DEPLOYMENT_NAME `
    --output json | ConvertFrom-Json

if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Deployment failed" -ForegroundColor Red
    exit 1
}

# Extract outputs
$containerAppUrl = $deployment.properties.outputs.containerAppUrl.value
$weatherApiUrl = $deployment.properties.outputs.weatherApiUrl.value

Write-Host ""
Write-Host "✅ Deployment completed successfully!" -ForegroundColor Green
Write-Host ""
Write-Host "📍 Endpoints:" -ForegroundColor Cyan
Write-Host "   Agent App: $containerAppUrl" -ForegroundColor White
Write-Host "   Weather API: $weatherApiUrl (external access enabled)" -ForegroundColor White
Write-Host ""
Write-Host "🏷️  Image Versions:" -ForegroundColor Cyan
Write-Host "   Agent: $ContainerImage" -ForegroundColor White
Write-Host "   Weather API: $WeatherApiImage" -ForegroundColor White
Write-Host ""
Write-Host "🧪 Test the deployment:" -ForegroundColor Cyan
Write-Host "   # Test agent (end-to-end with weather API)" -ForegroundColor Gray
Write-Host "   Invoke-RestMethod -Uri '$containerAppUrl/chat' -Method POST -ContentType 'application/json' -Body '{\"message\": \"What should I wear in 10001?\"}' | ConvertTo-Json -Depth 10" -ForegroundColor White
Write-Host ""
Write-Host "   # Test weather API directly" -ForegroundColor Gray
Write-Host "   Invoke-RestMethod -Uri '$weatherApiUrl/api/weather?zip_code=10001' -Method GET | ConvertTo-Json" -ForegroundColor White
Write-Host ""
