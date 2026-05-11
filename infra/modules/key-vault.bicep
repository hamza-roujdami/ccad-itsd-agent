// ============================================================================
// Key Vault – Secrets storage (ManageEngine API key, APIM subscription key)
// ============================================================================

@description('Name of the Key Vault')
param keyVaultName string

@description('Azure region')
param location string

@description('Principal ID for role assignments')
param principalId string

@description('Principal type')
param principalType string = 'User'

@description('Log Analytics workspace ID for diagnostics')
param logAnalyticsWorkspaceId string

// ----------------------------------------------------------------------
// Key Vault
// ----------------------------------------------------------------------

resource keyVault 'Microsoft.KeyVault/vaults@2023-07-01' = {
  name: keyVaultName
  location: location
  properties: {
    tenantId: subscription().tenantId
    sku: {
      family: 'A'
      name: 'standard'
    }
    enableRbacAuthorization: true
    enableSoftDelete: true
    softDeleteRetentionInDays: 7
    publicNetworkAccess: 'Enabled'
  }
}

// ----------------------------------------------------------------------
// Diagnostics
// ----------------------------------------------------------------------

resource diagnostics 'Microsoft.Insights/diagnosticSettings@2021-05-01-preview' = {
  name: 'kv-diagnostics'
  scope: keyVault
  properties: {
    workspaceId: logAnalyticsWorkspaceId
    logs: [
      {
        categoryGroup: 'audit'
        enabled: true
      }
    ]
    metrics: [
      {
        category: 'AllMetrics'
        enabled: true
      }
    ]
  }
}

// ----------------------------------------------------------------------
// Role Assignments – deploying user gets Key Vault Secrets Officer
// ----------------------------------------------------------------------

resource userSecretsOfficer 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(keyVault.id, principalId, 'KeyVaultSecretsOfficer')
  scope: keyVault
  properties: {
    principalId: principalId
    principalType: principalType
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', 'b86a8fe4-44ce-4948-aee5-eccb2c155cd7')
  }
}

// ----------------------------------------------------------------------
// Outputs
// ----------------------------------------------------------------------

output keyVaultId string = keyVault.id
output keyVaultName string = keyVault.name
output keyVaultUri string = keyVault.properties.vaultUri
