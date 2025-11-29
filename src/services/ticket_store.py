import uuid
from datetime import datetime, timedelta
from typing import List, Dict, Any
from azure.cosmos import CosmosClient, PartitionKey
from src.config import settings
from src.utils.logger import app_logger

class TicketStore:
    def __init__(self):
        if not settings.COSMOS_CONN_STR:
            app_logger.error("❌ Cosmos DB no configurado. TicketStore inactivo.")
            self.container = None
            return

        try:
            client = CosmosClient.from_connection_string(settings.COSMOS_CONN_STR)
            database = client.create_database_if_not_exists(id=settings.COSMOS_DB_NAME)
            
            self.container = database.create_container_if_not_exists(
                id=settings.COSMOS_CONTAINER_TICKETS,
                partition_key=PartitionKey(path="/user_id")
            )
            app_logger.info("✅ Cosmos DB TicketStore conectado (Serverless).")
        except Exception as e:
            app_logger.error(f"❌ Error conectando TicketStore: {e}")
            self.container = None

    def create_ticket(self, ticket_data: Dict[str, Any]) -> bool:
        """Crea un nuevo ticket en la base de datos"""
        if not self.container: return False

        # Aseguramos que tenga ID único y timestamp
        if "id" not in ticket_data:
            ticket_data["id"] = str(uuid.uuid4())
        if "created_at" not in ticket_data:
            ticket_data["created_at"] = datetime.utcnow().isoformat()
        
        # Si no viene ticket_id, generamos uno legible
        if "ticket_id" not in ticket_data:
            import random
            ticket_data["ticket_id"] = f"INC-{random.randint(10000, 99999)}"
            
        # Asegurar que user_id sea string (Cosmos DB requirement para partition key)
        if "user_id" in ticket_data:
            ticket_data["user_id"] = str(ticket_data["user_id"])

        try:
            self.container.create_item(body=ticket_data)
            app_logger.info(f"💾 Ticket guardado en nube: {ticket_data.get('ticket_id', 'N/A')}")
            return True
        except Exception as e:
            # Si ya existe (idempotencia), no es un error crítico para el script de init
            if "409" in str(e):
                app_logger.info(f"ℹ️ El ticket {ticket_data.get('ticket_id')} ya existe.")
                return True
            app_logger.error(f"❌ Fallo al guardar ticket en Cosmos: {e}")
            return False

    def get_tickets_by_user(self, user_id: str) -> List[Dict[str, Any]]:
        """Obtiene el historial de un usuario"""
        if not self.container: return []

        query = "SELECT * FROM c WHERE c.user_id = @user_id ORDER BY c.created_at DESC"
        parameters = [{"name": "@user_id", "value": str(user_id)}]

        try:
            items = list(self.container.query_items(
                query=query,
                parameters=parameters,
                enable_cross_partition_query=False
            ))
            return items
        except Exception as e:
            app_logger.error(f"❌ Error leyendo tickets: {e}")
            return []

    def get_recent_tickets(self, user_identifier: str, days: int = 7) -> List[Dict[str, Any]]:
        """Alias para get_tickets_by_user filtrando por fecha (lógica simplificada)"""
        # Para simplificar en serverless, traemos todos y filtramos en Python si son pocos,
        # o usamos query con fecha. Usaremos query con fecha.
        if not self.container: return []
        
        date_limit = (datetime.utcnow() - timedelta(days=days)).isoformat()
        query = "SELECT * FROM c WHERE c.user_id = @user_id AND c.created_at > @date_limit"
        parameters = [
            {"name": "@user_id", "value": str(user_identifier)},
            {"name": "@date_limit", "value": date_limit}
        ]
        
        try:
            items = list(self.container.query_items(
                query=query,
                parameters=parameters,
                enable_cross_partition_query=False
            ))
            return items
        except Exception as e:
            app_logger.error(f"❌ Error consultando recientes: {e}")
            return []

ticket_store = TicketStore()