// ============================================================================
// Azure Communication Services — for telephony (PSTN voice calls)
// ============================================================================

@description('Name of the Communication Services resource')
param communicationServiceName string

@description('Azure region — ACS is a global resource, location is for metadata only')
param location string = 'global'

resource communicationService 'Microsoft.Communication/communicationServices@2023-04-01' = {
  name: communicationServiceName
  location: location
  properties: {
    dataLocation: 'United States'  // Data residency for ACS
  }
}

output communicationServiceId string = communicationService.id
output communicationServiceName string = communicationService.name
