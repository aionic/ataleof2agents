# Phase 4: Deployment Scripts

**Phase:** 4 of 7
**Status:** Not Started
**Estimated Effort:** 1-2 hours
**Depends On:** Phase 3

---

## Objective

Refactor deployment scripts to support all three deployment methods using the unified container image.

---

## Target Directory Structure

```
deploy/
├── shared/                           # Shared utilities
│   ├── Invoke-AzureCapabilityHost.ps1
│   └── azure_agent_manager.py
│
├── container-apps/                   # Method 1: Self-hosted
│   ├── deploy.ps1
│   ├── main.bicep
│   └── README.md
│
├── foundry-hosted/                   # Method 2: Foundry managed
│   ├── deploy.ps1
│   └── README.md
│
└── foundry-native/                   # Method 3: Legacy (archived)
    └── README.md                     # Points to archive/
```

---

## Tasks

### Task 4.1: Reorganize Deploy Directory
**Status:** [ ] Not Started

```powershell
# Rename scripts to shared
Rename-Item -Path "deploy/scripts" -NewName "shared"

# Create foundry-hosted directory
New-Item -ItemType Directory -Path "deploy/foundry-hosted" -Force

# Create foundry-native placeholder
New-Item -ItemType Directory -Path "deploy/foundry-native" -Force
```

---

### Task 4.2: Update Container Apps Deploy Script
**Status:** [ ] Not Started

Update `deploy/container-apps/deploy.ps1` to:
- Use the unified Dockerfile (not `Dockerfile.container-app`)
- Deploy on port 8088 (not 8000)
- Update health check path

Key changes:

```powershell
# Old
$ContainerImage = "$ContainerRegistry.azurecr.io/weather-advisor:$buildHash"

# Build from root Dockerfile
docker build -f ../../Dockerfile -t $ContainerImage ../..

# Update Bicep to use port 8088
# Update ingress to route to port 8088
```

**Full updated script:** See below

```powershell
#!/usr/bin/env pwsh
# deploy/container-apps/deploy.ps1
# Deploys Weather Advisor to Azure Container Apps using unified image

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
    [switch]$SkipBuild
)

$ErrorActionPreference = "Stop"
$ProjectRoot = Resolve-Path "$PSScriptRoot/../.."

Write-Host "🚀 Deploying Weather Advisor to Container Apps..." -ForegroundColor Cyan
Write-Host "   Using unified Responses API image (port 8088)" -ForegroundColor Gray

# Load .env
$envPath = "$ProjectRoot/.env"
if (Test-Path $envPath) {
    Get-Content $envPath | ForEach-Object {
        if ($_ -match '^([^#][^=]+)=(.*)$') {
            Set-Variable -Name $matches[1].Trim() -Value $matches[2].Trim() -Scope Script
        }
    }
}

# Use registry from parameter or env
if (!$ContainerRegistry -and $CONTAINER_REGISTRY_NAME) {
    $ContainerRegistry = $CONTAINER_REGISTRY_NAME
}

if (!$ContainerRegistry) {
    throw "Container registry required. Set CONTAINER_REGISTRY_NAME in .env or use -ContainerRegistry"
}

# Generate build version
$gitHash = git rev-parse --short HEAD 2>$null
if (!$gitHash) { $gitHash = "nogit" }
$buildHash = "$gitHash-$(Get-Date -Format 'yyyyMMdd-HHmmss')"

# Image names
$AgentImage = "$ContainerRegistry.azurecr.io/weather-advisor:$buildHash"
$WeatherApiImage = "$ContainerRegistry.azurecr.io/weather-api:$buildHash"

if (!$SkipBuild) {
    Write-Host ""
    Write-Host "🔨 Building images..." -ForegroundColor Yellow

    # Build weather API (unchanged)
    Write-Host "   Building weather-api..." -ForegroundColor Gray
    docker build -f "$ProjectRoot/Dockerfile.weather-api" -t $WeatherApiImage $ProjectRoot
    docker tag $WeatherApiImage "$ContainerRegistry.azurecr.io/weather-api:latest"
    docker push $WeatherApiImage
    docker push "$ContainerRegistry.azurecr.io/weather-api:latest"

    # Build agent (unified Dockerfile)
    Write-Host "   Building weather-advisor (unified)..." -ForegroundColor Gray
    docker build -f "$ProjectRoot/Dockerfile" -t $AgentImage $ProjectRoot
    docker tag $AgentImage "$ContainerRegistry.azurecr.io/weather-advisor:latest"
    docker push $AgentImage
    docker push "$ContainerRegistry.azurecr.io/weather-advisor:latest"

    Write-Host "   ✓ Images built and pushed" -ForegroundColor Green
}

# Deploy with Bicep
Write-Host ""
Write-Host "📦 Deploying to Container Apps..." -ForegroundColor Yellow

az deployment group create `
    --resource-group $ResourceGroupName `
    --template-file "$PSScriptRoot/main.bicep" `
    --parameters `
        environment=$Environment `
        containerImage=$AgentImage `
        weatherApiImage=$WeatherApiImage `
        containerRegistryName=$ContainerRegistry `
        openWeatherMapApiKey=$OpenWeatherMapApiKey `
        agentPort=8088  # Unified port

Write-Host ""
Write-Host "✅ Deployment complete!" -ForegroundColor Green
Write-Host ""
Write-Host "Test with:" -ForegroundColor Cyan
Write-Host "  POST https://<your-app>/responses" -ForegroundColor Gray
Write-Host '  Body: {"input": {"messages": [{"role": "user", "content": "What should I wear in 10001?"}]}}' -ForegroundColor Gray
```

---

### Task 4.3: Create Foundry Hosted Deploy Script
**Status:** [ ] Not Started

Create `deploy/foundry-hosted/deploy.ps1`:

```powershell
#!/usr/bin/env pwsh
# deploy/foundry-hosted/deploy.ps1
# Deploys Weather Advisor to Azure AI Foundry as a Hosted Agent

param(
    [Parameter(Mandatory=$false)]
    [string]$ContainerRegistry = "",

    [Parameter(Mandatory=$false)]
    [string]$ImageTag = "latest",

    [Parameter(Mandatory=$false)]
    [string]$AgentName = "WeatherClothingAdvisor",

    [Parameter(Mandatory=$false)]
    [switch]$SkipBuild
)

$ErrorActionPreference = "Stop"
$ProjectRoot = Resolve-Path "$PSScriptRoot/../.."

Write-Host "🚀 Deploying Weather Advisor to Foundry Hosted Agents..." -ForegroundColor Cyan

# Load .env
$envPath = "$ProjectRoot/.env"
if (Test-Path $envPath) {
    Get-Content $envPath | ForEach-Object {
        if ($_ -match '^([^#][^=]+)=(.*)$') {
            $name = $matches[1].Trim()
            $value = $matches[2].Trim()
            Set-Variable -Name $name -Value $value -Scope Script
            [Environment]::SetEnvironmentVariable($name, $value, "Process")
        }
    }
}

# Get registry
if (!$ContainerRegistry -and $CONTAINER_REGISTRY_NAME) {
    $ContainerRegistry = $CONTAINER_REGISTRY_NAME
}

if (!$ContainerRegistry) {
    throw "Container registry required. Set CONTAINER_REGISTRY_NAME in .env or use -ContainerRegistry"
}

$FullImage = "$ContainerRegistry.azurecr.io/weather-advisor:$ImageTag"

# Build if needed
if (!$SkipBuild) {
    Write-Host ""
    Write-Host "🔨 Building and pushing image..." -ForegroundColor Yellow

    docker build -f "$ProjectRoot/Dockerfile" -t $FullImage $ProjectRoot
    docker push $FullImage

    Write-Host "   ✓ Image pushed: $FullImage" -ForegroundColor Green
}

# Deploy to Foundry using Python script
Write-Host ""
Write-Host "📦 Registering agent with Foundry..." -ForegroundColor Yellow

$env:AGENT_NAME = $AgentName
$env:AGENT_IMAGE = $FullImage
$env:AGENT_CPU = "1"
$env:AGENT_MEMORY = "2Gi"

# Call the Python agent manager
python "$PSScriptRoot/../shared/azure_agent_manager.py"

Write-Host ""
Write-Host "✅ Deployment complete!" -ForegroundColor Green
Write-Host ""
Write-Host "Your agent is now hosted in Azure AI Foundry." -ForegroundColor Cyan
Write-Host "Test it in the Foundry Portal or via API." -ForegroundColor Gray
```

---

### Task 4.4: Enhance azure_agent_manager.py
**Status:** [ ] Not Started

Update `deploy/shared/azure_agent_manager.py` to support:
- Interactive mode (prompts for values)
- List existing agents
- Delete agents
- Better error handling

Add to the end of the file:

```python
def interactive_mode():
    """Run in interactive mode with prompts."""
    print("=== Azure AI Agent Manager ===")
    print("")

    # Get endpoint
    endpoint = os.environ.get("AZURE_AI_PROJECT_ENDPOINT")
    if not endpoint:
        endpoint = input("Enter Azure AI Project Endpoint: ").strip()

    print(f"Using endpoint: {endpoint}")
    print("")

    # Select operation
    print("Operations:")
    print("  1. Create/Update Agent")
    print("  2. List Agents")
    print("  3. Delete Agent")
    print("")

    choice = input("Select operation [1]: ").strip() or "1"

    project_config = ProjectConfig(endpoint=endpoint)

    with AzureAgentManager(project_config) as manager:
        if choice == "1":
            # Create agent
            agent_name = os.environ.get("AGENT_NAME") or input("Agent Name: ").strip()
            image = os.environ.get("AGENT_IMAGE") or input("Container Image: ").strip()
            cpu = os.environ.get("AGENT_CPU", "1")
            memory = os.environ.get("AGENT_MEMORY", "2Gi")

            agent_config = AgentConfig(
                agent_name=agent_name,
                image=image,
                cpu=cpu,
                memory=memory,
            )

            print(f"\nCreating agent '{agent_name}'...")
            agent = manager.create_agent_version(agent_config)
            print(f"✓ Agent created successfully!")
            print(f"  Agent: {agent}")

        elif choice == "2":
            # List agents
            print("\nListing agents...")
            agents = manager.client.agents.list_agents()
            for agent in agents:
                print(f"  - {agent.name} (ID: {agent.id})")

        elif choice == "3":
            # Delete agent
            agent_id = input("Agent ID to delete: ").strip()
            print(f"\nDeleting agent {agent_id}...")
            manager.client.agents.delete_agent(agent_id)
            print("✓ Agent deleted")


if __name__ == "__main__":
    # Check if running with env vars (non-interactive) or interactive
    if os.environ.get("AGENT_NAME") and os.environ.get("AGENT_IMAGE"):
        # Non-interactive: create from env
        create_agent_from_env()
    else:
        # Interactive mode
        interactive_mode()
```

---

### Task 4.5: Create Foundry Native README
**Status:** [ ] Not Started

Create `deploy/foundry-native/README.md`:

```markdown
# Foundry Native Deployment (Legacy)

> ⚠️ **This method is archived.** Use [Foundry Hosted](../foundry-hosted/) instead.

## What Was This?

The "Foundry Native" deployment ran your agent in Foundry's built-in runtime
without a container. It used:
- YAML configuration files
- OpenAPI tools calling external APIs
- Foundry's generic agent runtime

## Why Archived?

The **Foundry Hosted** (image-based) approach is superior because:
- Same code runs everywhere (Container Apps + Foundry)
- Full control over business logic (clothing_logic.py)
- Better performance
- Simpler deployment

## Archived Files

The legacy scripts are preserved in `archive/foundry-native/`:
- `register_agent.py`
- `deploy_workflow.py`
- `register_external_agent.py`
- And others...

## Migration

To migrate from Foundry Native to Foundry Hosted:

1. Build your container: `docker build -t myagent .`
2. Push to ACR: `docker push myacr.azurecr.io/myagent:latest`
3. Deploy: `./deploy/foundry-hosted/deploy.ps1`

Your agent will run with the same code in both environments.
```

---

## Validation Checklist

- [ ] `deploy/shared/` contains utility scripts
- [ ] `deploy/container-apps/deploy.ps1` updated for port 8088
- [ ] `deploy/foundry-hosted/deploy.ps1` created
- [ ] `azure_agent_manager.py` has interactive mode
- [ ] Both deployment scripts work end-to-end

---

## Testing Commands

```powershell
# Test Container Apps deployment
cd deploy/container-apps
./deploy.ps1 -ResourceGroupName mygroup -OpenWeatherMapApiKey xxx

# Test Foundry Hosted deployment
cd deploy/foundry-hosted
./deploy.ps1 -ContainerRegistry myacr -AgentName TestAgent
```

---

## Dependencies

- Phase 3 completed (Dockerfile ready)
- ACR access configured
- Azure AI Foundry project created with Capability Host enabled

---

## Next Phase

[Phase 5: Archive Legacy Code](05-ARCHIVE-LEGACY.md)
