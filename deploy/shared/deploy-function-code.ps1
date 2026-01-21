#!/usr/bin/env pwsh
# Deploy function code using managed identity
# Run this after Bicep deployment completes

param(
    [Parameter(Mandatory=$true)]
    [string]$FunctionAppName,

    [Parameter(Mandatory=$true)]
    [string]$ResourceGroupName,

    [Parameter(Mandatory=$true)]
    [string]$StorageAccountName,

    [Parameter(Mandatory=$false)]
    [string]$FunctionCodePath = "../../src/function"
)

$ErrorActionPreference = "Stop"

Write-Host "📦 Deploying Function Code with Managed Identity" -ForegroundColor Cyan
Write-Host ""

# Navigate to function code directory
$originalPath = Get-Location
Set-Location $FunctionCodePath

try {
    # Create deployment package
    Write-Host "Creating deployment package..." -ForegroundColor Yellow
    $zipPath = "function.zip"
    if (Test-Path $zipPath) {
        Remove-Item $zipPath
    }

    Compress-Archive -Path function_app.py,host.json,requirements.txt,weather_service.py -DestinationPath $zipPath -Force
    Write-Host "✓ Package created: $zipPath" -ForegroundColor Green

    # Create container if it doesn't exist
    Write-Host "`nCreating deployments container..." -ForegroundColor Yellow
    az storage container create `
        --name deployments `
        --account-name $StorageAccountName `
        --auth-mode login `
        --only-show-errors | Out-Null
    Write-Host "✓ Container ready" -ForegroundColor Green

    # Upload package
    Write-Host "`nUploading package to blob storage..." -ForegroundColor Yellow
    az storage blob upload `
        --account-name $StorageAccountName `
        --container-name deployments `
        --name function.zip `
        --file $zipPath `
        --auth-mode login `
        --overwrite `
        --only-show-errors | Out-Null
    Write-Host "✓ Package uploaded" -ForegroundColor Green

    # Configure function app to run from package
    Write-Host "`nConfiguring function app..." -ForegroundColor Yellow
    $blobUrl = "https://$StorageAccountName.blob.core.windows.net/deployments/function.zip"
    az functionapp config appsettings set `
        --name $FunctionAppName `
        --resource-group $ResourceGroupName `
        --settings "WEBSITE_RUN_FROM_PACKAGE=$blobUrl" `
        --only-show-errors | Out-Null
    Write-Host "✓ Function app configured" -ForegroundColor Green

    # Restart function app
    Write-Host "`nRestarting function app..." -ForegroundColor Yellow
    az functionapp restart `
        --name $FunctionAppName `
        --resource-group $ResourceGroupName `
        --only-show-errors
    Write-Host "✓ Function app restarted" -ForegroundColor Green

    Write-Host "`nWaiting for function to become available..." -ForegroundColor Yellow
    Start-Sleep -Seconds 20

    Write-Host ""
    Write-Host "✅ Function code deployment complete!" -ForegroundColor Green
    Write-Host ""
    Write-Host "Test the function:" -ForegroundColor Cyan
    Write-Host "  curl 'https://$FunctionAppName.azurewebsites.net/api/get_weather?zip_code=10001'" -ForegroundColor White
    Write-Host ""

} finally {
    Set-Location $originalPath
}
