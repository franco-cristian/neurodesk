@description('Nombre base para los recursos (ej: neurodesk)')
param appName string = 'neurodesk-${uniqueString(resourceGroup().id)}'

@description('Ubicación de los recursos (ej: eastus2)')
param location string = resourceGroup().location

// Variable para generar nombres únicos y seguros (alfanuméricos)
var uniqueSuffix = uniqueString(resourceGroup().id, appName)

// --- 1. ALMACENAMIENTO (Blob Storage) ---
resource storage 'Microsoft.Storage/storageAccounts@2023-01-01' = {
  name: 'st${uniqueSuffix}' 
  location: location
  sku: {
    name: 'Standard_LRS'
  }
  kind: 'StorageV2'
  properties: {
    accessTier: 'Hot'
    minimumTlsVersion: 'TLS1_2'
    allowBlobPublicAccess: true
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
    name: 'basic' 
  }
  properties: {
    replicaCount: 1
    partitionCount: 1
  }
}

// --- 5. SERVICIOS COGNITIVOS (Speech & Language) ---
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

// --- 7. DOCUMENT INTELLIGENCE (OCR) ---
resource formRecognizer 'Microsoft.CognitiveServices/accounts@2023-05-01' = {
  name: 'doc-${appName}'
  location: location
  kind: 'FormRecognizer'
  #disable-next-line BCP187
  sku: {
    name: 'S0'
  }
  properties: {
    networkAcls: {
      defaultAction: 'Allow'
      virtualNetworkRules: []
      ipRules: []
    }
    publicNetworkAccess: 'Enabled'
  }
}

// --- 8. AUTOMATIZACIÓN (Automation Account) ---
resource automation 'Microsoft.Automation/automationAccounts@2023-11-01' = {
  name: 'auto-${appName}'
  location: location
  #disable-next-line BCP187
  sku: {
    name: 'Basic'
  }
  identity: {
    type: 'SystemAssigned'
  }
}

// --- 9. LOGIC APP (Serverless Workflow) ---
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

// --- 10. CONTAINER REGISTRY (ACR) ---
resource acr 'Microsoft.ContainerRegistry/registries@2023-01-01-preview' = {
  name: 'acr${uniqueSuffix}'
  location: location
  sku: {
    name: 'Basic'
  }
  properties: {
    adminUserEnabled: true
  }
}

// --- 11. APP SERVICE PLAN (Hosting Linux) ---
resource appServicePlan 'Microsoft.Web/serverfarms@2022-09-01' = {
  name: 'plan-${appName}'
  location: location
  properties: {
    reserved: true
  }
  sku: {
    name: 'B1'
    tier: 'Basic'
  }
  kind: 'linux'
}

// --- 12. WEB APP FOR CONTAINERS (Backend Python) ---
resource webApp 'Microsoft.Web/sites@2022-09-01' = {
  name: 'web-${appName}'
  location: location
  kind: 'app,linux,container'
  properties: {
    serverFarmId: appServicePlan.id
    siteConfig: {
      // Dejamos esto genérico. Luego al hacer 'az acr build' y conectar, se actualiza.
      linuxFxVersion: 'DOCKER|${acr.properties.loginServer}/neurodesk-backend:latest'
      appSettings: [
        {
          name: 'WEBSITES_PORT'
          value: '8000'
        }
      ]
    }
  }
  identity: {
    type: 'SystemAssigned'
  }
}

// --- 13. STATIC WEB APP (Frontend React) ---
resource staticWebApp 'Microsoft.Web/staticSites@2022-09-01' = {
  name: 'stapp-${appName}'
  location: 'eastus2'
  sku: {
    name: 'Free'
    tier: 'Free'
  }
  // Se creará el recurso "desconectado" y el usuario lo conectará en el Portal.
}

// --- OUTPUTS ---
output STORAGE_ACCOUNT_NAME string = storage.name
output COSMOS_DB_ENDPOINT string = cosmosAccount.properties.documentEndpoint
output OPENAI_ENDPOINT string = openai.properties.endpoint
output SEARCH_ENDPOINT string = 'https://${search.name}.search.windows.net'
output COGNITIVE_ENDPOINT string = cognitiveServices.properties.endpoint
output CONTENT_SAFETY_ENDPOINT string = contentSafety.properties.endpoint
output DOC_INTELLIGENCE_ENDPOINT string = formRecognizer.properties.endpoint
output ACR_LOGIN_SERVER string = acr.properties.loginServer
output WEB_APP_NAME string = webApp.name
output STATIC_WEB_APP_NAME string = staticWebApp.name
