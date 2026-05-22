// ============================================================================
// Azure AI Search – Service for KB index (FAQs, troubleshooting, known issues)
// ============================================================================

@description('Name of the AI Search service')
param searchServiceName string

@description('Azure region')
param location string

@description('Principal ID for role assignments')
param principalId string

@description('Principal type')
param principalType string = 'User'

// ----------------------------------------------------------------------
// AI Search Service
// ----------------------------------------------------------------------

resource searchService 'Microsoft.Search/searchServices@2024-06-01-preview' = {
  name: searchServiceName
  location: location
  sku: {
    name: 'basic'
  }
  identity: {
    type: 'SystemAssigned'
  }
  properties: {
    hostingMode: 'default'
    publicNetworkAccess: 'enabled'
    partitionCount: 1
    replicaCount: 1
    semanticSearch: 'free'
    authOptions: {
      aadOrApiKey: {
        aadAuthFailureMode: 'http401WithBearerChallenge'
      }
    }
  }
}

// ----------------------------------------------------------------------
// Role Assignments – deploying user
// ----------------------------------------------------------------------

// Search Service Contributor (manage indexes)
resource userSearchContributor 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(searchService.id, principalId, 'SearchServiceContributor')
  scope: searchService
  properties: {
    principalId: principalId
    principalType: principalType
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', '7ca78c08-252a-4471-8644-bb5ff32d4ba0')
  }
}

// Search Index Data Contributor (read/write index data)
resource userSearchDataContributor 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(searchService.id, principalId, 'SearchIndexDataContributor')
  scope: searchService
  properties: {
    principalId: principalId
    principalType: principalType
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', '8ebe5a00-799e-43f5-93ac-243d3dce84a7')
  }
}

// ----------------------------------------------------------------------
// Outputs
// ----------------------------------------------------------------------

output searchServiceId string = searchService.id
output searchServiceName string = searchService.name
output searchServiceEndpoint string = 'https://${searchService.name}.search.windows.net'
