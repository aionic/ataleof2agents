<#
.SYNOPSIS
    Manages Azure Cognitive Services Capability Hosts for AI Agents.

.DESCRIPTION
    This function enables or checks the status of capability hosts on Azure Cognitive Services accounts.
    It automatically retrieves the bearer token using Azure CLI.

.PARAMETER SubscriptionId
    The Azure subscription ID.

.PARAMETER ResourceGroupName
    The name of the resource group containing the Cognitive Services account.

.PARAMETER AccountName
    The name of the Cognitive Services account.

.PARAMETER CapabilityHostName
    The name of the capability host. Defaults to 'accountcaphost'.

.PARAMETER CapabilityHostKind
    The kind of capability host. Defaults to 'Agents'.

.PARAMETER EnablePublicHostingEnvironment
    Whether to enable public hosting environment. Defaults to $true.

.PARAMETER ApiVersion
    The API version to use. Defaults to '2025-10-01-preview'.

.PARAMETER Operation
    The operation to perform: 'Enable' (PUT), 'List' (GET), or 'GetStatus' (GET). Defaults to 'Enable'.

.PARAMETER OperationId
    Required for 'GetStatus' operation. The operation ID to check status for.

.PARAMETER Location
    Required for 'GetStatus' operation. The Azure region location.

.EXAMPLE
    # List existing capability hosts
    Invoke-AzureCapabilityHost -SubscriptionId "2800a07b-0813-4797-a519-b329df809545" `
        -ResourceGroupName "rg-petermessinaai" `
        -AccountName "petermessina-8930-resource" `
        -Operation "List"

.EXAMPLE
    # Enable capability host
    Invoke-AzureCapabilityHost -SubscriptionId "2800a07b-0813-4797-a519-b329df809545" `
        -ResourceGroupName "rg-petermessinaai" `
        -AccountName "petermessina-8930-resource"

.EXAMPLE
    # Check operation status
    Invoke-AzureCapabilityHost -SubscriptionId "2800a07b-0813-4797-a519-b329df809545" `
        -Operation "GetStatus" `
        -Location "northcentralus" `
        -OperationId "ch:81f8b4f9-099c-4f0f-8ccf-a8ff17f26964:baf195b3-bdeb-4951-a0a8-5ce4819b8541"
#>
function Invoke-AzureCapabilityHost {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory = $true)]
        [string]$SubscriptionId,

        [Parameter(Mandatory = $false)]
        [string]$ResourceGroupName,

        [Parameter(Mandatory = $false)]
        [string]$AccountName,

        [Parameter(Mandatory = $false)]
        [string]$CapabilityHostName = "accountcaphost",

        [Parameter(Mandatory = $false)]
        [string]$CapabilityHostKind = "Agents",

        [Parameter(Mandatory = $false)]
        [bool]$EnablePublicHostingEnvironment = $true,

        [Parameter(Mandatory = $false)]
        [string]$ApiVersion = "2025-10-01-preview",

        [Parameter(Mandatory = $false)]
        [ValidateSet("Enable", "List", "GetStatus")]
        [string]$Operation = "Enable",

        [Parameter(Mandatory = $false)]
        [string]$OperationId,

        [Parameter(Mandatory = $false)]
        [string]$Location
    )

    # Validate parameters based on operation
    if ($Operation -in @("Enable", "List") -and (-not $ResourceGroupName -or -not $AccountName)) {
        throw "ResourceGroupName and AccountName are required for '$Operation' operation."
    }
    if ($Operation -eq "GetStatus" -and (-not $OperationId -or -not $Location)) {
        throw "OperationId and Location are required for 'GetStatus' operation."
    }

    # Get bearer token using Azure CLI
    Write-Verbose "Retrieving bearer token from Azure CLI..."
    try {
        $token = az account get-access-token --resource https://management.azure.com/ --query accessToken -o tsv
        if (-not $token) {
            throw "Failed to retrieve access token. Ensure you are logged in with 'az login'."
        }
    }
    catch {
        throw "Error retrieving access token: $_"
    }

    # Build headers
    $headers = @{
        "Content-Type"  = "application/json"
        "Authorization" = "Bearer $token"
    }

    # Execute the appropriate operation
    switch ($Operation) {
        "Enable" {
            $uri = "https://management.azure.com/subscriptions/$SubscriptionId/resourceGroups/$ResourceGroupName/providers/Microsoft.CognitiveServices/accounts/$AccountName/capabilityHosts/$CapabilityHostName`?api-version=$ApiVersion"

            $body = @{
                properties = @{
                    capabilityHostKind             = $CapabilityHostKind
                    enablePublicHostingEnvironment = $EnablePublicHostingEnvironment
                }
            } | ConvertTo-Json -Depth 10

            Write-Verbose "Sending PUT request to: $uri"
            Write-Verbose "Request body: $body"

            try {
                $response = Invoke-RestMethod -Uri $uri -Method Put -Headers $headers -Body $body
                Write-Output "Capability host '$CapabilityHostName' enabled successfully."
                return $response
            }
            catch {
                $errorMessage = $_.Exception.Message
                if ($_.ErrorDetails.Message) {
                    $errorMessage = $_.ErrorDetails.Message
                }
                throw "Failed to enable capability host: $errorMessage"
            }
        }

        "List" {
            $uri = "https://management.azure.com/subscriptions/$SubscriptionId/resourceGroups/$ResourceGroupName/providers/Microsoft.CognitiveServices/accounts/$AccountName/capabilityHosts`?api-version=$ApiVersion"

            Write-Verbose "Sending GET request to: $uri"

            try {
                $response = Invoke-RestMethod -Uri $uri -Method Get -Headers $headers
                if ($response.value -and $response.value.Count -gt 0) {
                    Write-Output "Found $($response.value.Count) capability host(s):"
                    foreach ($capHost in $response.value) {
                        Write-Output "  - Name: $($capHost.name)"
                        Write-Output "    Kind: $($capHost.properties.capabilityHostKind)"
                        Write-Output "    State: $($capHost.properties.provisioningState)"
                        Write-Output "    Public Hosting: $($capHost.properties.enablePublicHostingEnvironment)"
                        Write-Output ""
                    }
                } else {
                    Write-Output "No capability hosts found for account '$AccountName'."
                }
                return $response
            }
            catch {
                $errorMessage = $_.Exception.Message
                if ($_.ErrorDetails.Message) {
                    $errorMessage = $_.ErrorDetails.Message
                }
                throw "Failed to list capability hosts: $errorMessage"
            }
        }

        "GetStatus" {
            $uri = "https://management.azure.com/subscriptions/$SubscriptionId/providers/Microsoft.MachineLearningServices/locations/$Location/mfeOperationsStatus/$OperationId`?api-version=$ApiVersion"

            Write-Verbose "Sending GET request to: $uri"

            try {
                $response = Invoke-RestMethod -Uri $uri -Method Get -Headers $headers
                return $response
            }
            catch {
                $errorMessage = $_.Exception.Message
                if ($_.ErrorDetails.Message) {
                    $errorMessage = $_.ErrorDetails.Message
                }
                throw "Failed to get operation status: $errorMessage"
            }
        }
    }
}

# If running as a script (not dot-sourced or imported as module), prompt for parameters and execute
if ($MyInvocation.InvocationName -ne '.') {
    Write-Host "=== Azure Capability Host Manager ===" -ForegroundColor Cyan
    Write-Host ""

    # Prompt for operation type
    $operationChoice = Read-Host "Select operation (1=List, 2=Enable, 3=GetStatus) [1]"
    if ([string]::IsNullOrWhiteSpace($operationChoice)) { $operationChoice = "1" }
    $operation = switch ($operationChoice) {
        "1" { "List" }
        "2" { "Enable" }
        "3" { "GetStatus" }
        default { "List" }
    }

    # Prompt for subscription ID
    Write-Host ""
    Write-Host "Fetching available subscriptions..." -ForegroundColor Yellow
    $subscriptions = az account list --query "[].{Name:name, Id:id}" -o json | ConvertFrom-Json
    if ($subscriptions.Count -gt 0) {
        Write-Host "Available subscriptions:" -ForegroundColor Green
        for ($i = 0; $i -lt $subscriptions.Count; $i++) {
            Write-Host "  [$($i + 1)] $($subscriptions[$i].Name) ($($subscriptions[$i].Id))"
        }
        $subChoice = Read-Host "Select subscription number or enter subscription ID"
        if ($subChoice -match '^\d+$' -and [int]$subChoice -le $subscriptions.Count) {
            $subscriptionId = $subscriptions[[int]$subChoice - 1].Id
        } else {
            $subscriptionId = $subChoice
        }
    } else {
        $subscriptionId = Read-Host "Enter Subscription ID"
    }

    $params = @{
        SubscriptionId = $subscriptionId
        Operation      = $operation
        Verbose        = $true
    }

    if ($operation -in @("List", "Enable")) {
        # List and select resource group
        Write-Host ""
        Write-Host "Fetching resource groups..." -ForegroundColor Yellow
        $resourceGroups = az group list --subscription $subscriptionId --query "[].{Name:name, Location:location}" -o json | ConvertFrom-Json
        if ($resourceGroups.Count -gt 0) {
            Write-Host "Available resource groups:" -ForegroundColor Green
            for ($i = 0; $i -lt $resourceGroups.Count; $i++) {
                Write-Host "  [$($i + 1)] $($resourceGroups[$i].Name) ($($resourceGroups[$i].Location))"
            }
            $rgChoice = Read-Host "Select resource group number or enter name"
            if ($rgChoice -match '^\d+$' -and [int]$rgChoice -le $resourceGroups.Count) {
                $resourceGroupName = $resourceGroups[[int]$rgChoice - 1].Name
            } else {
                $resourceGroupName = $rgChoice
            }
        } else {
            $resourceGroupName = Read-Host "Enter Resource Group Name"
        }

        # List and select Cognitive Services account
        Write-Host ""
        Write-Host "Fetching Cognitive Services accounts in '$resourceGroupName'..." -ForegroundColor Yellow
        $cogAccounts = az cognitiveservices account list --resource-group $resourceGroupName --subscription $subscriptionId --query "[].{Name:name, Kind:kind, Location:location}" -o json 2>$null | ConvertFrom-Json
        if ($cogAccounts -and $cogAccounts.Count -gt 0) {
            Write-Host "Available Cognitive Services accounts:" -ForegroundColor Green
            for ($i = 0; $i -lt $cogAccounts.Count; $i++) {
                Write-Host "  [$($i + 1)] $($cogAccounts[$i].Name) (Kind: $($cogAccounts[$i].Kind), Location: $($cogAccounts[$i].Location))"
            }
            $accChoice = Read-Host "Select account number or enter name"
            if ($accChoice -match '^\d+$' -and [int]$accChoice -le $cogAccounts.Count) {
                $accountName = $cogAccounts[[int]$accChoice - 1].Name
            } else {
                $accountName = $accChoice
            }
        } else {
            Write-Host "No Cognitive Services accounts found in resource group '$resourceGroupName'." -ForegroundColor Yellow
            $accountName = Read-Host "Enter Cognitive Services Account Name manually"
        }

        $params.ResourceGroupName = $resourceGroupName
        $params.AccountName = $accountName

        if ($operation -eq "Enable") {
            $capabilityHostName = Read-Host "Enter Capability Host Name [accountcaphost]"
            if ([string]::IsNullOrWhiteSpace($capabilityHostName)) { $capabilityHostName = "accountcaphost" }
            $params.CapabilityHostName = $capabilityHostName
        }
    }
    elseif ($operation -eq "GetStatus") {
        Write-Host ""
        $location = Read-Host "Enter Azure Region Location (e.g., northcentralus)"
        $operationId = Read-Host "Enter Operation ID"

        $params.Location = $location
        $params.OperationId = $operationId
    }

    Write-Host ""
    Write-Host "Executing $operation operation..." -ForegroundColor Yellow
    Write-Host ""

    try {
        $result = Invoke-AzureCapabilityHost @params
        Write-Host ""
        Write-Host "Operation completed successfully!" -ForegroundColor Green
        $result | ConvertTo-Json -Depth 10
    }
    catch {
        Write-Host ""
        Write-Host "Error: $_" -ForegroundColor Red
        exit 1
    }
}
