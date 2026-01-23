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
    The operation to perform: 'Enable' (PUT) or 'GetStatus' (GET). Defaults to 'Enable'.

.PARAMETER OperationId
    Required for 'GetStatus' operation. The operation ID to check status for.

.PARAMETER Location
    Required for 'GetStatus' operation. The Azure region location.

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
        [ValidateSet("Enable", "GetStatus")]
        [string]$Operation = "Enable",

        [Parameter(Mandatory = $false)]
        [string]$OperationId,

        [Parameter(Mandatory = $false)]
        [string]$Location
    )

    # Validate parameters based on operation
    if ($Operation -eq "Enable" -and (-not $ResourceGroupName -or -not $AccountName)) {
        throw "ResourceGroupName and AccountName are required for 'Enable' operation."
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

# Export the function when loaded as a module
Export-ModuleMember -Function Invoke-AzureCapabilityHost
