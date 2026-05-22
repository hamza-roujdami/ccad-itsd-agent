// ============================================================================
// Cosmos DB NoSQL — conversation history + workflow checkpoints
// ============================================================================

@description('Cosmos DB account name')
param cosmosAccountName string

@description('Azure region')
param location string

@description('Principal ID for RBAC role assignment')
param principalId string

@description('Principal type for RBAC role assignment')
@allowed(['User', 'ServicePrincipal', 'Group'])
param principalType string = 'User'

// ----------------------------------------------------------------------
// Cosmos DB Account (Serverless — cheapest for dev/test)
// ----------------------------------------------------------------------

resource cosmosAccount 'Microsoft.DocumentDB/databaseAccounts@2024-11-15' = {
  name: cosmosAccountName
  location: location
  kind: 'GlobalDocumentDB'
  properties: {
    databaseAccountOfferType: 'Standard'
    capabilities: [
      { name: 'EnableServerless' }
    ]
    locations: [
      {
        locationName: location
        failoverPriority: 0
      }
    ]
    consistencyPolicy: {
      defaultConsistencyLevel: 'Session'
    }
    disableLocalAuth: false
  }
}

// ----------------------------------------------------------------------
// Database
// ----------------------------------------------------------------------

resource database 'Microsoft.DocumentDB/databaseAccounts/sqlDatabases@2024-11-15' = {
  parent: cosmosAccount
  name: 'agent-framework'
  properties: {
    resource: {
      id: 'agent-framework'
    }
  }
}

// ----------------------------------------------------------------------
// Container — chat-history (partitioned by session_id)
// ----------------------------------------------------------------------

resource chatHistoryContainer 'Microsoft.DocumentDB/databaseAccounts/sqlDatabases/containers@2024-11-15' = {
  parent: database
  name: 'chat-history'
  properties: {
    resource: {
      id: 'chat-history'
      partitionKey: {
        paths: ['/session_id']
        kind: 'Hash'
        version: 2
      }
      defaultTtl: 2592000 // 30 days
    }
  }
}

// ----------------------------------------------------------------------
// RBAC — Cosmos DB Built-in Data Contributor
// ----------------------------------------------------------------------

// Built-in role: Cosmos DB Built-in Data Contributor
var cosmosDataContributorRoleId = '00000000-0000-0000-0000-000000000002'

resource cosmosRoleAssignment 'Microsoft.DocumentDB/databaseAccounts/sqlRoleAssignments@2024-11-15' = {
  parent: cosmosAccount
  name: guid(cosmosAccount.id, principalId, cosmosDataContributorRoleId)
  properties: {
    roleDefinitionId: '${cosmosAccount.id}/sqlRoleDefinitions/${cosmosDataContributorRoleId}'
    principalId: principalId
    scope: cosmosAccount.id
  }
}

// ----------------------------------------------------------------------
// Outputs
// ----------------------------------------------------------------------

output cosmosAccountEndpoint string = cosmosAccount.properties.documentEndpoint
output cosmosAccountName string = cosmosAccount.name
output databaseName string = database.name
output containerName string = chatHistoryContainer.name
