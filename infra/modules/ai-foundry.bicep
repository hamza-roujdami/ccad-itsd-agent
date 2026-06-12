// ============================================================================
// AI Foundry – Account + Project + Model Deployments (GPT-4o + Embeddings)
// Uses the new Foundry model: Account (no hub) → Project → Model Deployments
// ============================================================================

@description('Name of the Foundry Account (AI Services)')
param foundryAccountName string

@description('Name of the Foundry Project')
param foundryProjectName string

@description('Azure region')
param location string

@description('Principal ID for role assignments')
param principalId string

@description('Principal type')
param principalType string = 'User'

@description('AI Search resource ID for connection')
param searchServiceId string

@description('AI Search endpoint for connection')
param searchServiceEndpoint string

@description('Key Vault resource ID')
param keyVaultId string

@description('Application Insights resource ID')
param appInsightsId string

// ----------------------------------------------------------------------
// Foundry Account (Microsoft.CognitiveServices/accounts, kind: AIServices)
// ----------------------------------------------------------------------

resource foundryAccount 'Microsoft.CognitiveServices/accounts@2025-04-01-preview' = {
  name: foundryAccountName
  location: location
  kind: 'AIServices'
  sku: {
    name: 'S0'
  }
  identity: {
    type: 'SystemAssigned'
  }
  properties: {
    customSubDomainName: foundryAccountName
    publicNetworkAccess: 'Enabled'
    disableLocalAuth: false
    allowProjectManagement: true
    networkAcls: {
      defaultAction: 'Allow'
    }
  }
}

// ----------------------------------------------------------------------
// Model Deployments (sequential to avoid conflicts)
// ----------------------------------------------------------------------

resource gpt4oDeployment 'Microsoft.CognitiveServices/accounts/deployments@2024-10-01' = {
  parent: foundryAccount
  name: 'gpt-4o'
  sku: {
    name: 'Standard'
    capacity: 30
  }
  properties: {
    model: {
      format: 'OpenAI'
      name: 'gpt-4o'
      version: '2024-11-20'
    }
  }
}

resource embeddingDeployment 'Microsoft.CognitiveServices/accounts/deployments@2024-10-01' = {
  parent: foundryAccount
  name: 'text-embedding-3-large'
  dependsOn: [gpt4oDeployment]
  sku: {
    name: 'Standard'
    capacity: 30
  }
  properties: {
    model: {
      format: 'OpenAI'
      name: 'text-embedding-3-large'
      version: '1'
    }
  }
}

// ----------------------------------------------------------------------
// Foundry Project (uses preview API for project support)
// ----------------------------------------------------------------------

resource foundryProject 'Microsoft.CognitiveServices/accounts/projects@2025-04-01-preview' = {
  parent: foundryAccount
  name: foundryProjectName
  location: location
  identity: {
    type: 'SystemAssigned'
  }
  properties: {
    displayName: 'Clinical ITSD Agent'
    description: 'ITSM agent for clinical environments — KB triage + ManageEngine ticketing'
  }
  dependsOn: [embeddingDeployment]
}

// ----------------------------------------------------------------------
// Connection: AI Search → Foundry Account
// ----------------------------------------------------------------------

resource searchConnection 'Microsoft.CognitiveServices/accounts/connections@2025-04-01-preview' = {
  parent: foundryAccount
  name: 'ai-search-connection'
  dependsOn: [foundryProject]
  properties: {
    category: 'CognitiveSearch'
    target: searchServiceEndpoint
    authType: 'AAD'
    isSharedToAll: true
    metadata: {
      ApiType: 'Azure'
      ResourceId: searchServiceId
    }
  }
}

// ----------------------------------------------------------------------
// Role Assignments – deploying user gets Cognitive Services OpenAI User
// on the account, and project MI gets Search Index Data Contributor on search
// ----------------------------------------------------------------------

// Deploying user → Cognitive Services OpenAI User on Foundry Account
resource userOpenAIRole 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(foundryAccount.id, principalId, 'CognitiveServicesOpenAIUser')
  scope: foundryAccount
  properties: {
    principalId: principalId
    principalType: principalType
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', '5e0bd9bd-7b93-4f28-af87-19fc36ad61bd')
  }
}

// Deploying user → Cognitive Services Contributor (manage project, deployments)
resource userContributorRole 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(foundryAccount.id, principalId, 'CognitiveServicesContributor')
  scope: foundryAccount
  properties: {
    principalId: principalId
    principalType: principalType
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', '25fbc0a9-bd7c-42a3-aa1a-3b75d497ee68')
  }
}

// Project MI → Search Index Data Contributor on AI Search
resource projectSearchRole 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(searchServiceId, foundryProject.id, 'SearchIndexDataContributor')
  scope: foundryAccount
  properties: {
    principalId: foundryProject.identity.principalId
    principalType: 'ServicePrincipal'
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', '8ebe5a00-799e-43f5-93ac-243d3dce84a7')
  }
}

// ----------------------------------------------------------------------
// Outputs
// ----------------------------------------------------------------------

output foundryAccountEndpoint string = foundryAccount.properties.endpoint
output foundryAccountName string = foundryAccount.name
output foundryProjectName string = foundryProject.name
output foundryProjectId string = foundryProject.id
output foundryProjectPrincipalId string = foundryProject.identity.principalId
output embeddingDeploymentName string = embeddingDeployment.name
