// Main deployment for Container Apps agent
// Deploys shared infrastructure + Container App

@description('Location for all resources (default: Sweden Central)')
param location string = 'swedencentral'

@description('Environment name (dev, staging, prod)')
param environment string = 'dev'

@description('OpenWeatherMap API Key')
@secure()
param openWeatherMapApiKey string

@description('Container image for the agent')
param containerImage string

@description('Container image for the weather API')
param weatherApiImage string

@description('Container registry server')
param containerRegistry string = ''

@description('Container registry username')
@secure()
param containerRegistryUsername string = ''

@description('Container registry password')
@secure()
param containerRegistryPassword string = ''

@description('Azure Foundry endpoint for models')
param azureFoundryEndpoint string

@description('Azure AI model deployment name')
param modelDeploymentName string = 'gpt-4.1'

var resourceSuffix = uniqueString(resourceGroup().id)
var shortSuffix = substring(resourceSuffix, 0, 6)

// Deploy shared monitoring
module monitoring '../shared/monitoring.bicep' = {
  name: 'monitoring-deployment'
  params: {
    location: location
    environmentName: environment
    resourceSuffix: resourceSuffix
  }
}

// Reference the Log Analytics workspace created by monitoring module
resource logAnalyticsWorkspace 'Microsoft.OperationalInsights/workspaces@2022-10-01' existing = {
  name: 'log-weather-advisor-${environment}-${resourceSuffix}'
}

// Container Apps Environment
resource containerAppEnvironment 'Microsoft.App/managedEnvironments@2023-05-01' = {
  name: 'cae-weather-${environment}-${shortSuffix}'
  location: location
  properties: {
    appLogsConfiguration: {
      destination: 'log-analytics'
      logAnalyticsConfiguration: {
        customerId: logAnalyticsWorkspace.properties.customerId
        sharedKey: logAnalyticsWorkspace.listKeys().primarySharedKey
      }
    }
  }
  dependsOn: [
    monitoring
  ]
}

// Weather API Container App
resource weatherApiApp 'Microsoft.App/containerApps@2023-05-01' = {
  name: 'ca-weather-api-${environment}-${shortSuffix}'
  location: location
  identity: {
    type: 'SystemAssigned'
  }
  properties: {
    managedEnvironmentId: containerAppEnvironment.id
    configuration: {
      ingress: {
        external: true  // External access enabled for Foundry agent integration
        targetPort: 8080
        transport: 'auto'
        allowInsecure: false
      }
      registries: containerRegistry != '' ? [
        {
          server: containerRegistry
          username: containerRegistryUsername
          passwordSecretRef: 'registry-password'
        }
      ] : []
      secrets: containerRegistry != '' ? [
        {
          name: 'registry-password'
          value: containerRegistryPassword
        }
        {
          name: 'openweathermap-api-key'
          value: openWeatherMapApiKey
        }
      ] : [
        {
          name: 'openweathermap-api-key'
          value: openWeatherMapApiKey
        }
      ]
    }
    template: {
      containers: [
        {
          name: 'weather-api'
          image: weatherApiImage
          resources: {
            cpu: json('0.25')
            memory: '0.5Gi'
          }
          env: [
            {
              name: 'OPENWEATHERMAP_API_KEY'
              secretRef: 'openweathermap-api-key'
            }
          ]
        }
      ]
      scale: {
        minReplicas: 1
        maxReplicas: 2
      }
    }
  }
}

// Agent Container App
resource containerApp 'Microsoft.App/containerApps@2023-05-01' = {
  name: 'ca-weather-${environment}-${shortSuffix}'
  location: location
  identity: {
    type: 'SystemAssigned'
  }
  properties: {
    managedEnvironmentId: containerAppEnvironment.id
    configuration: {
      ingress: {
        external: true
        targetPort: 8000
        transport: 'http'
        allowInsecure: false
      }
      registries: containerRegistry != '' ? [
        {
          server: containerRegistry
          username: containerRegistryUsername
          passwordSecretRef: 'registry-password'
        }
      ] : []
      secrets: containerRegistry != '' ? [
        {
          name: 'registry-password'
          value: containerRegistryPassword
        }
        {
          name: 'app-insights-connection-string'
          value: monitoring.outputs.appInsightsConnectionString
        }
      ] : [
        {
          name: 'app-insights-connection-string'
          value: monitoring.outputs.appInsightsConnectionString
        }
      ]
    }
    template: {
      containers: [
        {
          name: 'weather-advisor-agent'
          image: containerImage
          resources: {
            cpu: json('0.5')
            memory: '1Gi'
          }
          env: [
            {
              name: 'WEATHER_API_URL'
              value: 'http://${weatherApiApp.properties.configuration.ingress.fqdn}'
            }
            {
              name: 'AZURE_FOUNDRY_ENDPOINT'
              value: azureFoundryEndpoint
            }
            {
              name: 'AZURE_AI_MODEL_DEPLOYMENT_NAME'
              value: modelDeploymentName
            }
            {
              name: 'APPLICATIONINSIGHTS_CONNECTION_STRING'
              secretRef: 'app-insights-connection-string'
            }
            {
              name: 'ENVIRONMENT'
              value: environment
            }
          ]
        }
      ]
      scale: {
        minReplicas: 1
        maxReplicas: 3
        rules: [
          {
            name: 'http-scaling'
            http: {
              metadata: {
                concurrentRequests: '10'
              }
            }
          }
        ]
      }
    }
  }
}

// Note: Managed identity role assignment (Cognitive Services OpenAI User)
// is configured via Azure CLI or portal. If not configured, run:
// az role assignment create --assignee <principal-id> --role "Cognitive Services OpenAI User" --scope <foundry-resource-id>

// Outputs
output containerAppUrl string = 'https://${containerApp.properties.configuration.ingress.fqdn}'
output weatherApiUrl string = 'http://${weatherApiApp.properties.configuration.ingress.fqdn}'
output appInsightsConnectionString string = monitoring.outputs.appInsightsConnectionString
output containerAppPrincipalId string = containerApp.identity.principalId
output weatherApiPrincipalId string = weatherApiApp.identity.principalId
