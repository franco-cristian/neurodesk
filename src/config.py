import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

class Settings:
    # --- DEFINICIÓN DE RUTAS ---
    BASE_DIR: Path = Path(__file__).resolve().parent.parent 
    DATA_DIR: Path = BASE_DIR / "src" / "data"

    # --- INFRAESTRUCTURA GENERAL ---
    PROJECT_NAME: str = "NeuroDesk AI"
    VERSION: str = "1.0.0"
    DEBUG: bool = os.getenv("DEBUG_MODE", "False").lower() == "true"
    
    # --- RUTAS DE DATOS ---
    HR_DATA_PATH: Path = DATA_DIR / "hr_data_enriched.csv"
    TICKETS_DATA_PATH: Path = DATA_DIR / "synthetic_tickets.csv"
    POLICIES_PATH: Path = DATA_DIR / "policies.txt"

    # --- AZURE OPENAI ---
    AOAI_ENDPOINT: str = os.getenv("AZURE_OPENAI_ENDPOINT", "")
    AOAI_KEY: str = os.getenv("AZURE_OPENAI_API_KEY", "")
    AOAI_DEPLOYMENT: str = os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME", "gpt-5-chat")
    AOAI_EMBEDDING: str = os.getenv("AZURE_OPENAI_EMBEDDING_NAME", "text-embedding-3-small")
    
    # --- AZURE AI SEARCH (RAG) ---
    SEARCH_ENDPOINT: str = os.getenv("AZURE_SEARCH_ENDPOINT", "")
    SEARCH_KEY: str = os.getenv("AZURE_SEARCH_API_KEY", "")
    SEARCH_INDEX_NAME: str = "neurodesk-policies-vector"
    
    # --- AZURE DOCUMENT INTELLIGENCE (OCR) ---
    DOC_INT_ENDPOINT: str = os.getenv("AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT", "")
    DOC_INT_KEY: str = os.getenv("AZURE_DOCUMENT_INTELLIGENCE_KEY", "")

    # --- AZURE COSMOS DB ---
    COSMOS_CONN_STR: str = os.getenv("AZURE_COSMOS_CONNECTION_STRING", "")
    COSMOS_DB_NAME: str = "NeuroDeskDB"
    COSMOS_CONTAINER_LOGS: str = "AuditLogs"
    COSMOS_CONTAINER_TICKETS: str = "Tickets"

    # --- AZURE CONTENT SAFETY ---
    SAFETY_ENDPOINT: str = os.getenv("CONTENT_SAFETY_ENDPOINT", "")
    SAFETY_KEY: str = os.getenv("CONTENT_SAFETY_KEY", "")

    # --- AZURE SPEECH & LANGUAGE ---
    SPEECH_KEY: str = os.getenv("AZURE_SPEECH_KEY", "")
    SPEECH_REGION: str = os.getenv("AZURE_SPEECH_REGION", "eastus2")
    LANGUAGE_ENDPOINT: str = os.getenv("AZURE_LANGUAGE_ENDPOINT", "")
    LANGUAGE_KEY: str = os.getenv("AZURE_LANGUAGE_KEY", "")

    # --- AZURE AUTOMATION ---
    SUBSCRIPTION_ID: str = os.getenv("AZURE_SUBSCRIPTION_ID", "")
    AUTOMATION_RG: str = os.getenv("AUTOMATION_RESOURCE_GROUP", "")
    AUTOMATION_ACCOUNT: str = os.getenv("AUTOMATION_ACCOUNT_NAME", "")
    STORAGE_ACCOUNT: str = os.getenv("STORAGE_ACCOUNT_NAME", "")
    LOGIC_APP_URL: str = os.getenv("LOGIC_APP_URL", "")

    def validate(self):
        """Validación estricta de arranque"""
        missing = []
        if not self.AOAI_KEY: missing.append("AZURE_OPENAI_API_KEY")
        if not self.SEARCH_KEY: missing.append("AZURE_SEARCH_API_KEY")
        if not self.COSMOS_CONN_STR: missing.append("AZURE_COSMOS_CONNECTION_STRING")
        
        # Validar existencia de directorio de datos
        if not self.DATA_DIR.exists():
            # Intentar crearlo si no existe para evitar crashes, aunque debería tener datos
            try:
                os.makedirs(self.DATA_DIR, exist_ok=True)
                print(f"⚠️ Directorio {self.DATA_DIR} creado automáticamente.")
            except Exception as e:
                missing.append(f"Directorio DATA_DIR no accesible: {e}")

        if missing:
            raise ValueError(f"❌ ERROR CRÍTICO: Faltan configuraciones: {', '.join(missing)}")

settings = Settings()
# Validamos al importar para asegurar Fail Fast
try:
    settings.validate()
except Exception as e:
    print(e)