@description('Nombre base para los recursos (ej: neurodesk)')
param appName string = 'neurodesk-${uniqueString(resourceGroup().id)}'

@description('Ubicación de los recursos (ej: eastus2)')
param location string = resourceGroup().location

// --- 1. ALMACENAMIENTO (Blob Storage) ---
resource storage 'Microsoft.Storage/storageAccounts@2023-01-01' = {
  name: 'st${replace(appName, '-', '')}' // Solo letras y numeros
  location: location
  sku: {
    name: 'Standard_LRS'
  }
  kind: 'StorageV2'
  properties: {
    accessTier: 'Hot'
    minimumTlsVersion: 'TLS1_2'
  }
}

// --- 2. BASE DE DATOS (Cosmos DB Serverless) ---
resource cosmosAccount 'Microsoft.DocumentDB/databaseAccounts@2023-11-15' = {
  name: 'cosmos-${appName}'
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
  }
}

resource cosmosDb 'Microsoft.DocumentDB/databaseAccounts/sqlDatabases@2023-11-15' = {
  parent: cosmosAccount
  name: 'NeuroDeskDB'
  properties: {
    resource: {
      id: 'NeuroDeskDB'
    }
  }
}

// --- 3. INTELIGENCIA ARTIFICIAL (Azure OpenAI) ---
resource openai 'Microsoft.CognitiveServices/accounts@2023-05-01' = {
  name: 'aoai-${appName}'
  location: location
  kind: 'OpenAI'
  sku: {
    name: 'S0'
  }
  properties: {
    customSubDomainName: 'aoai-${appName}'
  }
}

// --- 4. BÚSQUEDA (AI Search) ---
resource search 'Microsoft.Search/searchServices@2023-11-01' = {
  name: 'search-${appName}'
  location: location
  sku: {
    name: 'basic' // O 'free' si está disponible
  }
  properties: {
    replicaCount: 1
    partitionCount: 1
  }
}

// --- 5. SERVICIOS COGNITIVOS (Multi-Service: Speech, Language, Vision) ---
resource cognitiveServices 'Microsoft.CognitiveServices/accounts@2023-05-01' = {
  name: 'ai-${appName}'
  location: location
  kind: 'CognitiveServices' 
  sku: {
    name: 'S0'
  }
  properties: {
    apiProperties: {
      statisticsEnabled: false
    }
  }
}

// --- 6. SEGURIDAD DE CONTENIDOS (Content Safety) ---
resource contentSafety 'Microsoft.CognitiveServices/accounts@2023-05-01' = {
  name: 'safety-${appName}'
  location: location
  kind: 'ContentSafety'
  sku: {
    name: 'S0'
  }
}

// --- 7. AUTOMATIZACIÓN (Automation Account) ---
resource automation 'Microsoft.Automation/automationAccounts@2023-11-01' = {
  name: 'auto-${appName}'
  location: location
  sku: {
    name: 'Basic'
  }
  identity: {
    type: 'SystemAssigned'
  }
}

// --- 8. LOGIC APP (Serverless Workflow) ---
resource logicApp 'Microsoft.Logic/workflows@2019-05-01' = {
  name: 'logic-${appName}'
  location: location
  properties: {
    state: 'Enabled'
    definition: { 
      '$schema': 'https://schema.management.azure.com/providers/Microsoft.Logic/schemas/2016-06-01/workflowdefinition.json#'
      contentVersion: '1.0.0.0'
      triggers: {
        manual: {
          type: 'Request'
          kind: 'Http'
          inputs: {}
        }
      }
      actions: {}
      outputs: {}
    }
  }
}

// --- OUTPUTS ---
output STORAGE_ACCOUNT_NAME string = storage.name
output COSMOS_DB_ENDPOINT string = cosmosAccount.properties.documentEndpoint
output OPENAI_ENDPOINT string = openai.properties.endpoint
output SEARCH_ENDPOINT string = 'https://${search.name}.search.windows.net'
output COGNITIVE_ENDPOINT string = cognitiveServices.properties.endpoint
