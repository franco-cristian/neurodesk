from azure.core.credentials import AzureKeyCredential
from azure.search.documents import SearchClient
from azure.search.documents.indexes import SearchIndexClient
from azure.search.documents.indexes.models import (
    SearchIndex, 
    SimpleField, 
    SearchableField,
    SearchField,
    SearchFieldDataType,
    VectorSearch,
    HnswAlgorithmConfiguration,
    VectorSearchProfile
)
from azure.search.documents.models import VectorizedQuery
from src.config import settings
from src.utils.logger import app_logger
from openai import AzureOpenAI

class SearchEngine:
    def __init__(self):
        self.endpoint = settings.SEARCH_ENDPOINT
        self.key = settings.SEARCH_KEY
        self.index_name = settings.SEARCH_INDEX_NAME
        
        # Configuración del Modelo de Embeddings (Azure AI Foundry)
        self.embedding_deployment = settings.AOAI_EMBEDDING # ej: text-embedding-3-small

        if not self.endpoint or not self.key:
            app_logger.critical("❌ Azure AI Search no configurado.")
            return

        self.credential = AzureKeyCredential(self.key)
        
        # Cliente Search (Búsquedas)
        self.search_client = SearchClient(self.endpoint, self.index_name, self.credential)
        
        # Cliente Admin (Crear Índices)
        self.admin_client = SearchIndexClient(self.endpoint, self.credential)

        # Cliente Azure OpenAI para generar vectores (Directo a la fuente)
        try:
            self.openai_client = AzureOpenAI(
                api_key=settings.AOAI_KEY,
                api_version="2023-05-15",
                azure_endpoint=settings.AOAI_ENDPOINT
            )
            app_logger.info("✅ Search Engine: Cliente Azure OpenAI conectado para vectorización.")
        except Exception as e:
            app_logger.error(f"❌ Error conectando OpenAI Client: {e}")
            self.openai_client = None

    def generate_embedding(self, text: str) -> list:
        """
        Genera el vector usando el modelo desplegado en Azure AI Foundry.
        Usa el SDK nativo 'openai' para máxima estabilidad.
        """
        if not text or not self.openai_client: 
            return []
        
        try:
            # Limpieza básica para evitar tokens corruptos
            text = text.replace("\n", " ")
            
            # Llamada a Azure OpenAI Embeddings
            response = self.openai_client.embeddings.create(
                input=text,
                model=self.embedding_deployment
            )
            
            # Extraer el vector (lista de floats)
            return response.data[0].embedding
            
        except Exception as e:
            app_logger.error(f"❌ Error generando embedding: {e}")
            return []

    def create_vector_index(self):
        """Crea un índice con soporte VECTORIAL (HNSW) en Azure AI Search"""
        if not self.admin_client: return

        try:
            app_logger.info(f"⚙️ Configurando índice vectorial: {self.index_name}...")
            
            # 1. Configuración del Algoritmo Vectorial (HNSW)
            vector_search = VectorSearch(
                algorithms=[HnswAlgorithmConfiguration(name="myHnsw")],
                profiles=[VectorSearchProfile(name="myHnswProfile", algorithm_configuration_name="myHnsw")]
            )

            # 2. Definición de Campos
            fields = [
                SimpleField(name="id", type="Edm.String", key=True),
                
                # Campo de Texto (Búsqueda por palabras clave)
                SearchableField(name="content", type="Edm.String", analyzer_name="es.microsoft"),
                
                # Campo Vectorial (1536 dimensiones es el estándar para text-embedding-3-small)
                SearchField(
                    name="contentVector", 
                    type=SearchFieldDataType.Collection(SearchFieldDataType.Single),
                    searchable=True,
                    vector_search_dimensions=1536,
                    vector_search_profile_name="myHnswProfile"
                ),
                
                # Metadatos para filtrado
                SimpleField(name="category", type="Edm.String", filterable=True, facetable=True),
                SimpleField(name="source", type="Edm.String")
            ]
            
            # 3. Crear o Actualizar Índice
            index = SearchIndex(name=self.index_name, fields=fields, vector_search=vector_search)
            self.admin_client.create_or_update_index(index)
            app_logger.info(f"✅ Índice VECTORIAL '{self.index_name}' listo.")
            
        except Exception as e:
            app_logger.error(f"❌ Error creando índice vectorial: {e}")

    def upload_documents(self, documents: list):
        """Sube documentos (que ya incluyen el campo 'contentVector')"""
        if not self.search_client: return
        try:
            self.search_client.upload_documents(documents)
            app_logger.info(f"📤 {len(documents)} documentos subidos a Azure AI Search.")
        except Exception as e:
            app_logger.error(f"❌ Error subiendo documentos: {e}")

    def search_hybrid(self, query: str, top: int = 3) -> str:
        """
        Realiza una búsqueda HÍBRIDA (Semántica + Keywords).
        """
        if not self.search_client:
            return "Error: Servicio de búsqueda no disponible."

        try:
            # 1. Vectorizar la consulta del usuario en tiempo real
            query_vector = self.generate_embedding(query)
            if not query_vector:
                return "Error: No se pudo vectorizar la consulta."

            # 2. Configurar la consulta vectorial
            vector_query = VectorizedQuery(
                vector=query_vector, 
                k_nearest_neighbors=top, 
                fields="contentVector"
            )

            # 3. Ejecutar búsqueda híbrida en Azure AI Search
            results = self.search_client.search(
                search_text=query,
                vector_queries=[vector_query],
                top=top,
                select=["content", "category", "source"] # No traemos el vector de vuelta
            )
            
            context_parts = []
            for res in results:
                # Filtrado por score de relevancia (ajustable)
                if res['@search.score'] < 0.03: continue

                context_parts.append(
                    f"[Fuente: {res['source']} | Categoría: {res['category']}]\n"
                    f"{res['content']}\n"
                )

            if not context_parts:
                return "No encontré información relevante en las políticas corporativas."
            
            return "\n".join(context_parts)

        except Exception as e:
            app_logger.error(f"❌ Fallo en Búsqueda Híbrida: {e}")
            return "Error técnico al recuperar información."

# Instancia global
search_engine = SearchEngine()