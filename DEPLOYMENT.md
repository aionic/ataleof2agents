# Deployment Guide

Choose your deployment approach:

| Deployment | Best For | Guide |
|------------|----------|-------|
| **Container Apps** | High-volume, fastest responses (2.3x faster) | [Container Apps Guide](docs/guides/DEPLOYMENT-CONTAINER-APPS.md) |
| **Azure AI Foundry** | Managed service, rapid development | [Foundry Guide](docs/guides/DEPLOYMENT-FOUNDRY.md) |
| **Quick Start** | 5-minute overview | [QUICKSTART.md](QUICKSTART.md) |

---

## Prerequisites (Both Deployments)

```powershell
# Required tools
az --version      # Azure CLI 2.50+
docker --version  # Docker 20.10+
python --version  # Python 3.11+
uv --version      # uv package manager

# Azure login
az login
az account set --subscription <subscription-id>
```

**API Keys Needed:**
- [OpenWeatherMap API Key](https://openweathermap.org/appid) (free, 1000 calls/day)
- Azure OpenAI deployment (GPT-4 or GPT-4o)

---

## Quick Deploy

### Container Apps (Recommended)
```powershell
cd deploy/container-app
./deploy.ps1 -ResourceGroupName foundry -OpenWeatherMapApiKey <your-key>
```

### Azure AI Foundry
```powershell
cd src/agent-foundry
python register_agent.py
```

---

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│            Weather Clothing Advisor - Dual Deploy           │
└─────────────────────────────────────────────────────────────┘

Container Apps Path:                    Foundry Path:
User → Agent Container                  User → Foundry Agent Runtime
         ↓                                        ↓
    WorkflowOrchestrator                    OpenAPI Tool Call
         ↓                                        ↓
    Weather API (Container)              Weather API (Container)
         ↓                                        ↓
    OpenWeatherMap                         OpenWeatherMap
         ↓                                        ↓
    Recommendations                        Recommendations

Shared: Weather API, App Insights, OpenWeatherMap
```

---

## Testing

```powershell
# Container Apps
Invoke-RestMethod -Uri 'https://<your-app>.azurecontainerapps.io/chat' `
  -Method Post -ContentType 'application/json' `
  -Body '{"message": "What should I wear in 10001?"}'

# Foundry - use Azure AI Foundry Portal playground
```

---

## Monitoring (Application Insights)

### Key Queries

**Response Time (KQL):**
```kql
traces
| where customDimensions.deployment_type in ("container-app", "foundry-agent")
| extend responseTime = todouble(customDimensions.response_time)
| summarize avg(responseTime), percentile(responseTime, 95) by bin(timestamp, 1h)
```

**Weather API Calls:**
```kql
dependencies
| where name == "get_weather"
| summarize count(), avg(duration) by tostring(customDimensions.zip_code)
```

---

## Cost Estimates (Monthly)

| Component | Container Apps | Foundry |
|-----------|----------------|---------|
| Compute | $5-20 | $10-50 |
| App Insights | $2-10 | $2-10 |
| Container Registry | $5 | - |
| **Total** | **~$15-40** | **~$15-65** |

*Varies by usage volume and model (GPT-4 vs GPT-4o)*

---

## Troubleshooting

| Issue | Solution |
|-------|----------|
| Container not starting | Check `az containerapp logs show --name <app> -g <rg> --follow` |
| 503 errors | Scale up: `az containerapp update --min-replicas 2` |
| Weather API errors | Verify API key activated (wait 15 min after signup) |
| Foundry agent not found | Re-run `python register_agent.py` |
| Slow responses | Check cold starts, increase resources |

---

## Cleanup

```powershell
# Delete everything
az group delete --name foundry --yes --no-wait
```

---

## More Info

- [Container Apps Deep Dive](docs/guides/DEPLOYMENT-CONTAINER-APPS.md)
- [Foundry Deep Dive](docs/guides/DEPLOYMENT-FOUNDRY.md)
- [Architecture Patterns](docs/architecture/)
