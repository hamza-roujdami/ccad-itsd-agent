// ============================================================================
// CCAD ITSD Agent — Backend hosting on Azure Container Apps
// Runs the agent INSIDE the lab tenant so its system-assigned managed identity
// can reach Foundry + AI Search (no device-compliance / Conditional Access block).
//
// Provisions:
//   - Log Analytics workspace + Container Apps managed environment
//   - Container App with 2 containers (agent + mock MCP sidecar, shared localhost)
//   - System-assigned managed identity
//   - Role assignments on the EXISTING Foundry account + Search service
//
// ACR is created by the deploy script (az acr create + az acr build) and its
// credentials are passed in as parameters.
// ============================================================================

targetScope = 'resourceGroup'

// ---------------------------------------------------------------------------
// Parameters
// ---------------------------------------------------------------------------

@description('Azure region')
param location string = resourceGroup().location

@description('Base name used for the Container Apps environment and app')
param baseName string = 'ccad-itsd'

@description('Full container image reference, e.g. myacr.azurecr.io/ccad-itsd-agent:latest')
param containerImage string

@description('ACR login server, e.g. myacr.azurecr.io')
param acrServer string

@description('ACR admin username')
param acrUsername string

@description('ACR admin password')
@secure()
param acrPassword string

@description('Name of the EXISTING Azure AI Foundry (Cognitive Services) account')
param foundryAccountName string

@description('Name of the EXISTING Azure AI Search service')
param searchServiceName string

@description('Foundry project/account endpoint')
param foundryEndpoint string

@description('Foundry model deployment name')
param foundryModel string = 'gpt-4o'

@description('Azure AI Search endpoint')
param searchEndpoint string

@description('Azure AI Search index name')
param searchIndexName string = 'itsd-kb'

@description('ACS cognitive services endpoint (for STT/TTS in calls). Leave empty for text-only.')
param acsCognitiveServicesEndpoint string = ''

@description('ACS connection string. Leave empty for text-only (disables voice channel).')
@secure()
param acsConnectionString string = ''

@description('Application Insights connection string (optional)')
param appInsightsConnectionString string = ''

var voiceEnabled = !empty(acsConnectionString)

// ---------------------------------------------------------------------------
// Names & role definition IDs
// ---------------------------------------------------------------------------

var appName = '${baseName}-agent'
var envName = '${baseName}-env'
var logName = '${baseName}-aca-logs'

// Built-in role definition IDs
var roleCognitiveServicesOpenAIUser = '5e0bd9bd-7b93-4f28-af87-19fc36ad61bd'
var roleCognitiveServicesUser = 'a97b65f3-24c7-4388-baec-2e87618995b6'
var roleSearchIndexDataReader = '1407120a-92aa-4202-b7e9-c0e197c71c8f'

// Public FQDN is deterministic from the env default domain, so we can wire the
// ACS callback URL at deploy time (no second pass needed).
var publicFqdn = '${appName}.${managedEnv.properties.defaultDomain}'

// ---------------------------------------------------------------------------
// Log Analytics + Container Apps environment
// ---------------------------------------------------------------------------

resource logAnalytics 'Microsoft.OperationalInsights/workspaces@2023-09-01' = {
  name: logName
  location: location
  properties: {
    sku: {
      name: 'PerGB2018'
    }
    retentionInDays: 30
  }
}

resource managedEnv 'Microsoft.App/managedEnvironments@2024-03-01' = {
  name: envName
  location: location
  properties: {
    appLogsConfiguration: {
      destination: 'log-analytics'
      logAnalyticsConfiguration: {
        customerId: logAnalytics.properties.customerId
        sharedKey: logAnalytics.listKeys().primarySharedKey
      }
    }
  }
}

// ---------------------------------------------------------------------------
// Container App
// ---------------------------------------------------------------------------

resource containerApp 'Microsoft.App/containerApps@2024-03-01' = {
  name: appName
  location: location
  identity: {
    type: 'SystemAssigned'
  }
  properties: {
    managedEnvironmentId: managedEnv.id
    configuration: {
      ingress: {
        external: true
        targetPort: 8000
        transport: 'auto'
        allowInsecure: false
      }
      registries: [
        {
          server: acrServer
          username: acrUsername
          passwordSecretRef: 'acr-password'
        }
      ]
      secrets: concat([
        {
          name: 'acr-password'
          value: acrPassword
        }
      ], voiceEnabled ? [
        {
          name: 'acs-connection-string'
          value: acsConnectionString
        }
      ] : [])
    }
    template: {
      containers: [
        {
          name: 'agent'
          image: containerImage
          resources: {
            cpu: json('1.0')
            memory: '2Gi'
          }
          env: concat([
            { name: 'FOUNDRY_PROJECT_ENDPOINT', value: foundryEndpoint }
            { name: 'FOUNDRY_MODEL', value: foundryModel }
            { name: 'AZURE_SEARCH_ENDPOINT', value: searchEndpoint }
            { name: 'AZURE_SEARCH_INDEX_NAME', value: searchIndexName }
            { name: 'MCP_SERVER_URL', value: 'http://localhost:8001/mcp' }
            { name: 'APPLICATIONINSIGHTS_CONNECTION_STRING', value: appInsightsConnectionString }
          ], voiceEnabled ? [
            { name: 'ACS_COGNITIVE_SERVICES_ENDPOINT', value: acsCognitiveServicesEndpoint }
            { name: 'ACS_CALLBACK_BASE_URL', value: 'https://${publicFqdn}' }
            { name: 'ACS_CONNECTION_STRING', secretRef: 'acs-connection-string' }
          ] : [])
        }
        {
          name: 'mock-mcp'
          image: containerImage
          command: ['python', '-m', 'mock_mcp.server']
          resources: {
            cpu: json('0.5')
            memory: '1Gi'
          }
        }
      ]
      scale: {
        minReplicas: 1
        maxReplicas: 1
      }
    }
  }
}

// ---------------------------------------------------------------------------
// Role assignments — grant the app's managed identity access to Foundry + Search
// ---------------------------------------------------------------------------

resource foundryAccount 'Microsoft.CognitiveServices/accounts@2023-05-01' existing = {
  name: foundryAccountName
}

resource searchService 'Microsoft.Search/searchServices@2023-11-01' existing = {
  name: searchServiceName
}

resource foundryOpenAIUserAssignment 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(foundryAccount.id, containerApp.id, roleCognitiveServicesOpenAIUser)
  scope: foundryAccount
  properties: {
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', roleCognitiveServicesOpenAIUser)
    principalId: containerApp.identity.principalId
    principalType: 'ServicePrincipal'
  }
}

resource foundryCognitiveUserAssignment 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(foundryAccount.id, containerApp.id, roleCognitiveServicesUser)
  scope: foundryAccount
  properties: {
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', roleCognitiveServicesUser)
    principalId: containerApp.identity.principalId
    principalType: 'ServicePrincipal'
  }
}

resource searchReaderAssignment 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(searchService.id, containerApp.id, roleSearchIndexDataReader)
  scope: searchService
  properties: {
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', roleSearchIndexDataReader)
    principalId: containerApp.identity.principalId
    principalType: 'ServicePrincipal'
  }
}

// ---------------------------------------------------------------------------
// Outputs
// ---------------------------------------------------------------------------

output appFqdn string = publicFqdn
output appUrl string = 'https://${publicFqdn}'
output eventGridWebhook string = 'https://${publicFqdn}/api/calls/incoming'
output principalId string = containerApp.identity.principalId
