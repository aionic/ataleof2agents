#!/usr/bin/env pwsh
# Build and push Docker image to Azure Container Registry
# Run this script ONCE from project root before deployment

param(
    [Parameter(Mandatory=$false)]
    [string]$RegistryName = "",

    [Parameter(Mandatory=$false)]
    [string]$ImageTag = "latest"
)

$ErrorActionPreference = "Stop"

Write-Host "🏗️  Building and Pushing Weather Advisor Container Image" -ForegroundColor Cyan
Write-Host ""

# Load environment variables if .env exists
if (Test-Path ".env") {
    Write-Host "📄 Loading environment from .env..." -ForegroundColor Yellow
    Get-Content .env | ForEach-Object {
        if ($_ -match '^([^#][^=]+)=(.*)$') {
            $varName = $matches[1].Trim()
            $varValue = $matches[2].Trim()
            Set-Variable -Name $varName -Value $varValue -Scope Script
            if ($varName -eq "CONTAINER_REGISTRY_NAME") {
                Write-Host "   Found registry: $varValue" -ForegroundColor Green
            }
        }
    }
}

# Use parameter or environment variable
if (!$RegistryName -and $env:CONTAINER_REGISTRY_NAME) {
    $RegistryName = $env:CONTAINER_REGISTRY_NAME
}
elseif (!$RegistryName -and $CONTAINER_REGISTRY_NAME) {
    $RegistryName = $CONTAINER_REGISTRY_NAME
}

if (!$RegistryName) {
    Write-Host "❌ Registry name is required" -ForegroundColor Red
    Write-Host "   Usage: ./build-and-push.ps1 -RegistryName 'myregistry'" -ForegroundColor Yellow
    Write-Host "   Or set CONTAINER_REGISTRY_NAME in .env file" -ForegroundColor Yellow
    exit 1
}

$imageName = "weather-advisor"
$fullImageName = "$RegistryName.azurecr.io/${imageName}:${ImageTag}"

# Verify we're in project root (check for Dockerfile)
if (!(Test-Path "Dockerfile.container-app")) {
    Write-Host "❌ Dockerfile.container-app not found!" -ForegroundColor Red
    Write-Host "   Please run this script from the project root directory" -ForegroundColor Yellow
    exit 1
}

# Build image
Write-Host "🔨 Building Docker image: $fullImageName" -ForegroundColor Yellow
Write-Host "   This may take a few minutes..." -ForegroundColor Gray
Write-Host ""

docker build -t "${imageName}:${ImageTag}" -f Dockerfile.container-app .

if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Docker build failed" -ForegroundColor Red
    exit 1
}

# Tag for registry
Write-Host ""
Write-Host "🏷️  Tagging image for ACR..." -ForegroundColor Yellow
docker tag "${imageName}:${ImageTag}" $fullImageName

if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Docker tag failed" -ForegroundColor Red
    exit 1
}

# Login to ACR
Write-Host ""
Write-Host "🔐 Logging in to Azure Container Registry..." -ForegroundColor Yellow
az acr login --name $RegistryName

if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ ACR login failed" -ForegroundColor Red
    Write-Host "   Make sure:" -ForegroundColor Yellow
    Write-Host "   1. You're logged in to Azure (az login)" -ForegroundColor Yellow
    Write-Host "   2. The registry exists: az acr show --name $RegistryName" -ForegroundColor Yellow
    Write-Host "   3. You have permission to access the registry" -ForegroundColor Yellow
    exit 1
}

# Push image
Write-Host ""
Write-Host "📤 Pushing image to ACR..." -ForegroundColor Yellow
Write-Host "   $fullImageName" -ForegroundColor Gray
Write-Host ""

docker push $fullImageName

if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Docker push failed" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "✅ Image successfully built and pushed!" -ForegroundColor Green
Write-Host ""
Write-Host "📦 Image: $fullImageName" -ForegroundColor Cyan
Write-Host ""
Write-Host "Next step: Run deployment script" -ForegroundColor Yellow
Write-Host "   cd deploy/container-app" -ForegroundColor White
Write-Host "   ./deploy.ps1 -ResourceGroupName <rg-name> -OpenWeatherMapApiKey <key>" -ForegroundColor White
Write-Host ""
