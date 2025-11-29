import uuid
from datetime import datetime
from azure.cosmos import CosmosClient, PartitionKey
from src.config import settings
from src.utils.logger import app_logger

class AuditLedger:
    def __init__(self):
        if not settings.COSMOS_CONN_STR:
            app_logger.warning("⚠️ Cosmos DB no configurado. La auditoría no se guardará.")
            self.container = None
            return

        try:
            # Cliente Cosmos DB
            self.client = CosmosClient.from_connection_string(settings.COSMOS_CONN_STR)
            self.database = self.client.create_database_if_not_exists(id=settings.COSMOS_DB_NAME)
            
            # Contenedor de Logs (Partition Key: /user_id para búsquedas rápidas por empleado)
            self.container = self.database.create_container_if_not_exists(
                id=settings.COSMOS_CONTAINER_LOGS,
                partition_key=PartitionKey(path="/user_id")
            )
            app_logger.info("✅ Audit Ledger conectado (Cosmos DB).")
        except Exception as e:
            app_logger.error(f"❌ Error conectando Audit Ledger: {e}")
            self.container = None

    def log_transaction(self, user_id: str, request_text: str, response_obj: object, context_id: str = None):
        """
        Guarda una transacción inmutable en el Ledger.
        """
        if not self.container: return

        # Extraemos datos del objeto Pydantic ChatResponse
        response_text = getattr(response_obj, "response", str(response_obj))
        risk_level = getattr(response_obj, "risk_level", "Unknown")
        actions = getattr(response_obj, "actions_taken", [])
        is_safe = getattr(response_obj, "is_safe", True)

        record = {
            "id": str(uuid.uuid4()),
            "user_id": str(user_id),
            "conversation_id": context_id or "session-unknown",
            "timestamp": datetime.utcnow().isoformat(),
            "request_hash": str(hash(request_text)), # Privacidad simple
            "request_content": request_text[:1000],  # Truncar para ahorrar espacio si es enorme
            "response_summary": response_text[:1000],
            "risk_level": risk_level,
            "ai_actions": actions,
            "safety_check": "PASS" if is_safe else "BLOCKED",
            "audit_version": "2.0"
        }

        try:
            self.container.create_item(body=record)
            app_logger.info(f"📝 Transacción auditada en Cosmos DB: {record['id']}")
        except Exception as e:
            app_logger.error(f"❌ Fallo al escribir en Ledger: {e}")

audit_ledger = AuditLedger()