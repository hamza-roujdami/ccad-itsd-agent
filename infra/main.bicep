// ============================================================================
// CCAD ITSD Agent – Dev Infrastructure
// Provisions: Foundry Account + Project + GPT-4o, AI Search, Key Vault, Monitoring
// Region: Sweden Central
// ============================================================================

targetScope = 'resourceGroup'

// ----------------------------------------------------------------------
// Parameters
// ----------------------------------------------------------------------

@description('Environment name used for resource naming')
param environmentName string

@description('Azure region for all resources')
param location string = 'swedencentral'

@description('Principal ID of the deploying user (for role assignments)')
param principalId string

@description('Principal type for role assignments')
@allowed(['User', 'ServicePrincipal', 'Group'])
param principalType string = 'User'

@description('Unique token for deterministic resource naming')
param resourceToken string = toLower(uniqueString(subscription().id, environmentName, location))

// ----------------------------------------------------------------------
// Resource Names
// ----------------------------------------------------------------------

var names = {
  foundryAccount: 'ai-${resourceToken}'
  foundryProject: 'aiproj-${resourceToken}'
  search: 'search-${resourceToken}'
  keyVault: 'kv-${resourceToken}'
  logAnalytics: 'log-${resourceToken}'
  appInsights: 'appi-${resourceToken}'
}

// ----------------------------------------------------------------------
// Modules
// ----------------------------------------------------------------------

module monitoring 'modules/monitoring.bicep' = {
  name: 'monitoring'
  params: {
    logAnalyticsName: names.logAnalytics
    appInsightsName: names.appInsights
    location: location
  }
}

module keyVault 'modules/key-vault.bicep' = {
  name: 'keyVault'
  params: {
    keyVaultName: names.keyVault
    location: location
    principalId: principalId
    principalType: principalType
    logAnalyticsWorkspaceId: monitoring.outputs.logAnalyticsWorkspaceId
  }
}

module aiSearch 'modules/ai-search.bicep' = {
  name: 'aiSearch'
  params: {
    searchServiceName: names.search
    location: location
    principalId: principalId
    principalType: principalType
  }
}

module aiFoundry 'modules/ai-foundry.bicep' = {
  name: 'aiFoundry'
  params: {
    foundryAccountName: names.foundryAccount
    foundryProjectName: names.foundryProject
    location: location
    principalId: principalId
    principalType: principalType
    searchServiceId: aiSearch.outputs.searchServiceId
    searchServiceEndpoint: aiSearch.outputs.searchServiceEndpoint
    keyVaultId: keyVault.outputs.keyVaultId
    appInsightsId: monitoring.outputs.appInsightsId
  }
}

// ----------------------------------------------------------------------
// Outputs
// ----------------------------------------------------------------------

output AZURE_OPENAI_ENDPOINT string = aiFoundry.outputs.foundryAccountEndpoint
output AZURE_OPENAI_DEPLOYMENT string = 'gpt-4o'
output AZURE_EMBEDDING_DEPLOYMENT string = 'text-embedding-3-large'
output AZURE_SEARCH_ENDPOINT string = aiSearch.outputs.searchServiceEndpoint
output AZURE_SEARCH_INDEX string = 'itsd-kb'
output AZURE_KEY_VAULT_NAME string = keyVault.outputs.keyVaultName
output AZURE_APPINSIGHTS_CONNECTION_STRING string = monitoring.outputs.appInsightsConnectionString
output AZURE_FOUNDRY_PROJECT_NAME string = aiFoundry.outputs.foundryProjectName
