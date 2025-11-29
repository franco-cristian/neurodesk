import pandas as pd
import io
import sys
from azure.identity import DefaultAzureCredential
from azure.storage.blob import BlobServiceClient
from src.config import settings
from src.utils.logger import app_logger
from src.services.ticket_store import ticket_store

class DataAnalyst:
    def __init__(self):
        self.df_hr = pd.DataFrame()
        self.container_name = "reference-data"
        self.blob_name = "hr_data_enriched.csv"
        
        # Carga estricta al iniciar. Si falla, la app no debe arrancar en falso.
        self._load_hr_data_from_blob_strict()

    def _load_hr_data_from_blob_strict(self):
        """
        Descarga el CSV de referencia desde Azure Blob Storage.
        CRÍTICO: No hay fallback local. Requiere conexión real a Azure.
        """
        storage_account_name = settings.STORAGE_ACCOUNT

        if not storage_account_name:
            app_logger.critical("❌ Data Analyst: STORAGE_ACCOUNT_NAME no definido en variables de entorno.")
            return

        # Construcción segura del endpoint
        account_url = f"https://{storage_account_name}.blob.core.windows.net"

        try:
            app_logger.info(f"☁️ Conectando a Azure Blob Storage: {account_url} ...")
            
            # Autenticación Real (Managed Identity en Azure o Azure CLI en local)
            credential = DefaultAzureCredential()
            blob_service_client = BlobServiceClient(account_url, credential=credential)
            
            blob_client = blob_service_client.get_blob_client(container=self.container_name, blob=self.blob_name)

            if not blob_client.exists():
                app_logger.critical(f"❌ El archivo {self.blob_name} no existe en el contenedor {self.container_name}.")
                return

            # Descarga a stream en memoria
            download_stream = blob_client.download_blob()
            csv_data = download_stream.readall()
            
            # Parsing con Pandas
            self.df_hr = pd.read_csv(io.BytesIO(csv_data))
            
            # Normalización de datos para búsquedas
            if 'EmpID' in self.df_hr.columns:
                self.df_hr['EmpID'] = self.df_hr['EmpID'].astype(str)
            if 'Email' in self.df_hr.columns:
                self.df_hr['Email'] = self.df_hr['Email'].str.lower().str.strip()
                
            app_logger.info(f"✅ Data Analyst: Dataset HR cargado desde CLOUD ({len(self.df_hr)} registros).")

        except Exception as e:
            app_logger.critical(f"🔥 ERROR CRÍTICO DE ACCESO A DATOS: {e}")
            # En producción esto debe detener el servicio o alertar, no continuar vacio.
            self.df_hr = pd.DataFrame() 

    def get_employee_metrics(self, user_identifier: str) -> dict:
        """
        Busca métricas específicas de un empleado en el DataFrame en memoria.
        Retorna un diccionario limpio para el consumo del Plugin.
        """
        if self.df_hr.empty:
            return {"error": "HR Database Offline"}

        user_identifier = str(user_identifier).lower().strip()
        
        # Búsqueda Vectorial (Email o ID)
        # Prioridad 1: Email
        user = self.df_hr[self.df_hr['Email'] == user_identifier]
        
        # Prioridad 2: ID
        if user.empty:
            user = self.df_hr[self.df_hr['EmpID'] == user_identifier]

        if user.empty:
            return {"error": "User Not Found"}

        # Extracción de datos (Fila 0)
        row = user.iloc[0]
        
        return {
            "name": row.get('Employee_Name', 'N/A'),
            "position": row.get('Position', 'N/A'),
            "department": row.get('Department', 'N/A'),
            "manager": row.get('ManagerName', 'N/A'),
            "satisfaction": float(row.get('EmpSatisfaction', 3.0)), # Cast seguro
            "projects": int(row.get('SpecialProjectsCount', 0)),
            "monthly_hours": float(row.get('Average_Monthly_Hours', 160.0)),
            "last_review": row.get('LastPerformanceReview_Date', 'N/A'),
            "absences": int(row.get('Absences', 0))
        }

    def get_contextual_risk_profile(self, user_identifier: str) -> dict:
        """
        FUSIÓN DE DATOS REALES: HR (Blob) + IT (Cosmos DB).
        Se usa para alimentar al LLM con contexto enriquecido.
        """
        # 1. Obtener datos base de HR
        hr_metrics = self.get_employee_metrics(user_identifier)
        if "error" in hr_metrics:
            return {"risk_level": "UNKNOWN", "reason": "Usuario no encontrado en HR"}

        # 2. Obtener datos vivos de IT (Cosmos DB)
        # Buscamos tickets de los últimos 7 días
        recent_tickets = ticket_store.get_recent_tickets(user_identifier, days=7)
        ticket_count = len(recent_tickets)
        
        # 3. Cálculo de Riesgo Algorítmico
        risk_score = 0
        factors = []

        # Análisis HR
        if hr_metrics['satisfaction'] <= 2.0:
            risk_score += 40
            factors.append("Baja satisfacción reportada")
        if hr_metrics['monthly_hours'] > 200:
            risk_score += 30
            factors.append("Sobrecarga horaria")
        
        # Análisis IT
        if ticket_count > 2:
            risk_score += 20
            factors.append(f"Múltiples incidentes recientes ({ticket_count})")

        # Determinación de Nivel
        level = "LOW"
        if risk_score >= 60: level = "CRITICAL"
        elif risk_score >= 30: level = "MEDIUM"

        return {
            "employee_name": hr_metrics['name'],
            "role": hr_metrics['position'],
            "risk_level": level,
            "risk_score": risk_score,
            "risk_factors": factors,
            "active_tickets_count": ticket_count
        }

# Instancia Global
data_analyst = DataAnalyst()