# Test Docker image locally before deploying
param(
    [string]$WeatherApiUrl = "",
    [string]$AppInsightsCs = ""
)

Write-Host "🧪 Testing Docker image locally..." -ForegroundColor Cyan
Write-Host ""

# Stop any existing test container
docker stop test-weather 2>$null
docker rm test-weather 2>$null

# Run container with environment variables
Write-Host "🚀 Starting container..." -ForegroundColor Yellow
$containerId = docker run -d `
    -p 8000:8000 `
    --name test-weather `
    -e WEATHER_API_URL=$WeatherApiUrl `
    -e APPLICATIONINSIGHTS_CONNECTION_STRING=$AppInsightsCs `
    anacr123321.azurecr.io/weather-advisor:latest

if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Failed to start container" -ForegroundColor Red
    exit 1
}

Write-Host "✓ Container started: $($containerId.Substring(0,12))" -ForegroundColor Green
Write-Host ""
Write-Host "⏳ Waiting for application to start..." -ForegroundColor Yellow
Start-Sleep 5

# Check health endpoint
Write-Host ""
Write-Host "🏥 Testing /health endpoint..." -ForegroundColor Yellow
try {
    $health = Invoke-RestMethod -Uri "http://localhost:8000/health" -TimeoutSec 5
    Write-Host "✅ Health check passed!" -ForegroundColor Green
    Write-Host "   Response: $($health | ConvertTo-Json -Compress)" -ForegroundColor White
}
catch {
    Write-Host "❌ Health check failed" -ForegroundColor Red
    Write-Host ""
    Write-Host "📋 Container logs:" -ForegroundColor Yellow
    docker logs test-weather
    docker stop test-weather
    docker rm test-weather
    exit 1
}

# Test chat endpoint
Write-Host ""
Write-Host "💬 Testing /chat endpoint..." -ForegroundColor Yellow
try {
    $body = @{ message = "What should I wear in 10001?" } | ConvertTo-Json
    $response = Invoke-RestMethod -Uri "http://localhost:8000/chat" `
        -Method Post `
        -ContentType "application/json" `
        -Body $body `
        -TimeoutSec 30

    Write-Host "✅ Chat endpoint works!" -ForegroundColor Green
    Write-Host "   Response:" -ForegroundColor White
    Write-Host "   $($response.response)" -ForegroundColor Gray
}
catch {
    Write-Host "⚠️  Chat endpoint failed (may need valid API key)" -ForegroundColor Yellow
    Write-Host "   Error: $($_.Exception.Message)" -ForegroundColor Gray
}

# Cleanup
Write-Host ""
Write-Host "🧹 Cleaning up..." -ForegroundColor Yellow
docker stop test-weather
docker rm test-weather

Write-Host ""
Write-Host "✅ Local test completed!" -ForegroundColor Green
Write-Host ""
Write-Host "Next step: Deploy to Azure" -ForegroundColor Cyan
Write-Host "   cd deploy/container-app" -ForegroundColor White
Write-Host "   pwsh -File .\deploy.ps1 -ResourceGroupName foundry -OpenWeatherMapApiKey YOUR_KEY" -ForegroundColor White
