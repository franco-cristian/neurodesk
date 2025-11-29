from semantic_kernel.functions import kernel_function
from typing import Annotated
from src.services.search_engine import search_engine
from src.utils.logger import app_logger

class PolicyAgentPlugin:
    """
    Plugin encargado de la normativa, compliance y manuales de empleado.
    Utiliza RAG (Retrieval Augmented Generation) sobre Azure AI Search.
    """

    @kernel_function(
        description="Busca en las políticas corporativas, manuales y normativas de seguridad.",
        name="check_corporate_policy"
    )
    def check_corporate_policy(
        self, 
        query: Annotated[str, "La pregunta específica sobre la política (ej: 'política de desconexión', 'días por mudanza')"]
    ) -> str:
        """
        Accede al motor de búsqueda vectorial/semántica para recuperar fragmentos de documentos.
        """
        app_logger.info(f"⚖️ [POLICY AGENT] Invocado por LLM. Query: '{query}'")
        
        search_result = search_engine.search_hybrid(query)
        
        # Retornamos el texto crudo para que el LLM lo sintetice
        return search_result