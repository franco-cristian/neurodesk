from semantic_kernel.functions import kernel_function
from typing import Annotated, Dict, Any, Optional, List
import time, uuid, json, random
from datetime import datetime

from azure.identity import DefaultAzureCredential
from azure.mgmt.automation import AutomationClient
from azure.core.credentials import AccessToken
import requests

from src.config import settings
from src.utils.logger import app_logger
from src.services.ticket_store import ticket_store


class ITAgentPlugin:
    def __init__(self):
        self.subscription_id = settings.SUBSCRIPTION_ID
        self.automation_rg = settings.AUTOMATION_RG
        self.automation_account = settings.AUTOMATION_ACCOUNT
        self.storage_account = getattr(settings, "STORAGE_ACCOUNT", None)
        self.logic_app_url = getattr(settings, "LOGIC_APP_URL", None)

        if not self.subscription_id or not self.automation_rg or not self.automation_account:
            app_logger.error("❌ Faltan variables de Azure Automation.")
            self.client = None
            self.credential = None
            return

        try:
            self.credential = DefaultAzureCredential()
            self.client = AutomationClient(self.credential, self.subscription_id)
            app_logger.info("✅ Azure Automation Client conectado.")
        except Exception as e:
            app_logger.error(f"❌ Error conectando Automation Client: {e}")
            self.client = None

    # --- Utilidades ---

    def _create_job(self, runbook_name: str, parameters: Dict[str, Any], job_id: str) -> None:
        self.client.job.create(
            self.automation_rg,
            self.automation_account,
            job_name=job_id,
            parameters={"runbook": {"name": runbook_name}, "parameters": parameters},
        )

    def _poll_job_status(self, job_id: str, max_wait_seconds: int = 120) -> Dict[str, Any]:
        start_ts = time.time()
        status = "New"
        attempts, delay = 0, 2.0
        terminal = {"Completed", "Failed", "Suspended", "Stopped"}

        while True:
            try:
                job_info = self.client.job.get(self.automation_rg, self.automation_account, job_id)
                status = job_info.status
            except Exception as e:
                app_logger.warning(f"⚠️ Fallo consultando estado Job {job_id}: {e}")
                status = "Unknown"

            attempts += 1
            if attempts % 3 == 0:
                app_logger.info(f"    ⏳ Job {job_id} estado: {status} (attempt={attempts})")

            if status in terminal:
                break

            if (time.time() - start_ts) >= max_wait_seconds:
                app_logger.error(f"⏱️ Timeout Job {job_id}. Último estado: {status}")
                break

            time.sleep(delay)
            delay = min(delay * 1.5, 6.0)

        end_ts = time.time()
        return {
            "status_final": status,
            "attempts": attempts,
            "duration_ms": int((end_ts - start_ts) * 1000),
            "started_at": datetime.utcfromtimestamp(start_ts).isoformat(),
            "completed_at": datetime.utcfromtimestamp(end_ts).isoformat(),
        }

    def _read_job_output_streams(self, job_id: str) -> Optional[str]:
        try:
            streams: List[Any] = list(
                self.client.job_stream.list_by_job(self.automation_rg, self.automation_account, job_id)
            )
            chunks = [
                s.stream_text
                for s in streams
                if getattr(s, "stream_type", "").lower() == "output"
                and getattr(s, "stream_text", None)
            ]
            text = "\n".join(chunks).strip() if chunks else ""
            return text or None
        except Exception as e:
            app_logger.warning(f"⚠️ Fallo leyendo Job Streams Output {job_id}: {e}")
            return None

    def _get_bearer_token(self) -> str:
        token: AccessToken = self.credential.get_token("https://management.azure.com/.default")
        return token.token

    def _read_job_output_rest(self, job_id: str) -> Optional[str]:
        try:
            time.sleep(2)
            url = (
                f"https://management.azure.com/subscriptions/{self.subscription_id}"
                f"/resourceGroups/{self.automation_rg}"
                f"/providers/Microsoft.Automation/automationAccounts/{self.automation_account}"
                f"/jobs/{job_id}/output?api-version=2023-11-01"
            )
            headers = {"Authorization": f"Bearer {self._get_bearer_token()}"}
            resp = requests.get(url, headers=headers, timeout=20)
            if resp.status_code == 200:
                text = (resp.text or "").strip()
                return text or None
            app_logger.warning(f"⚠️ Get-Output REST {job_id} status={resp.status_code} body={resp.text[:500]}")
            return None
        except Exception as e:
            app_logger.warning(f"⚠️ Fallo REST Get-Output {job_id}: {e}")
            return None

    def _normalize_output(self, raw_text: Optional[str]) -> str:
        if not raw_text:
            return "El Runbook finalizó con éxito (sin salida de texto)."
        s = raw_text.strip()
        if len(s) > 4000:
            s = s[:4000] + "…[truncated]"
        try:
            # Intentar parsear la cadena como JSON y luego volver a formatearla
            parsed = json.loads(s)
            return json.dumps(parsed, ensure_ascii=False)
        except Exception:
            return s

    def _persist_ticket(
        self,
        user_id: str,
        runbook_name: str,
        description: str,
        job_id: str,
        status_final: str,
        output_text: str,
        metrics: Dict[str, Any],
    ) -> Dict[str, Any]:
        record = {
            "ticket_id": f"AUTO-{random.randint(1000, 9999)}",
            "user_id": user_id,
            "category": "Automation",
            "subject": f"Ejecución de {runbook_name}",
            "description": description,
            "priority": "High",
            "status": "Resolved" if status_final == "Completed" else "Closed",
            "automation_job_id": job_id,
            "automation_status": status_final,
            "automation_output": (output_text or "")[:2000],
            "metrics": metrics,
            "created_at": datetime.utcnow().isoformat(),
        }
        try:
            ticket_store.create_ticket(record)
            app_logger.info(f"💾 Ticket guardado en nube: {record['ticket_id']}")
        except Exception as e:
            app_logger.warning(f"⚠️ No se pudo persistir el ticket {record['ticket_id']}: {e}")
        return record

    def _persist_escalation_ticket(
        self,
        user_id: str,
        reason: str,
        urgency: str,
        logic_app_response: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Persiste tickets de escalado a humano en Cosmos DB
        """
        escalation_id = f"ESC-{random.randint(1000, 9999)}"
        
        record = {
            "ticket_id": escalation_id,
            "user_id": user_id,
            "category": "Human Escalation",
            "subject": f"Escalado a Agente Humano - Prioridad {urgency}",
            "description": f"Razón: {reason}",
            "priority": "High" if urgency.lower() == "alta" else "Medium",
            "status": "Open",
            "escalation_reason": reason,
            "escalation_urgency": urgency,
            "logic_app_triggered": logic_app_response is not None,
            "logic_app_response": logic_app_response,
            "created_at": datetime.utcnow().isoformat(),
        }
        
        try:
            ticket_store.create_ticket(record)
            app_logger.info(f"💾 Ticket de escalado guardado: {escalation_id}")
            return record
        except Exception as e:
            app_logger.error(f"❌ Error crítico guardando ticket de escalado {escalation_id}: {e}")
            # Fallback: crear registro mínimo
            fallback_record = {
                "ticket_id": escalation_id,
                "user_id": user_id,
                "category": "Human Escalation",
                "subject": f"ESCALADO - {urgency}",
                "description": reason[:500],
                "priority": "High",
                "status": "Open",
                "created_at": datetime.utcnow().isoformat(),
                "error_persisting": str(e)
            }
            try:
                ticket_store.create_ticket(fallback_record)
                app_logger.info(f"💾 Ticket de escalado (fallback) guardado: {escalation_id}")
                return fallback_record
            except Exception as e2:
                app_logger.critical(f"💥 FALLO CRÍTICO: No se pudo guardar ticket de escalado: {e2}")
                return None

    def _trigger_runbook(
        self,
        runbook_name: str,
        parameters: Dict[str, Any],
        user_id: str,
        description: str,
        max_wait_seconds: int = 120,
    ) -> str:
        if not self.client:
            return "Error: Cliente de automatización no disponible."

        job_id = str(uuid.uuid4())
        app_logger.info(f"🚀 [AZURE] Iniciando Job {job_id} para Runbook '{runbook_name}'...")

        try:
            self._create_job(runbook_name, parameters, job_id)
            poll = self._poll_job_status(job_id, max_wait_seconds=max_wait_seconds)
            status_final = poll.get("status_final", "Unknown")

            if status_final != "Completed":
                output_text = f"El proceso en la nube finalizó con estado: {status_final}."
                self._persist_ticket(user_id, runbook_name, description, job_id, status_final, output_text, poll)
                return output_text

            output_text = self._read_job_output_streams(job_id) or self._read_job_output_rest(job_id)
            final_output = self._normalize_output(output_text)

            self._persist_ticket(user_id, runbook_name, description, job_id, status_final, final_output, poll)
            return final_output

        except Exception as e:
            app_logger.error(f"❌ Error crítico Runbook '{runbook_name}' (Job {job_id}): {e}")
            return f"Error de sistema al invocar automatización: {str(e)}"

    # --- Funciones expuestas ---

    @kernel_function(description="Genera enlace seguro para logs.", name="generate_upload_link")
    def generate_upload_link(self, user_email: Annotated[str, "Email del usuario"]) -> str:
        if not self.storage_account:
            return "Error: Storage no configurado."
        
        # 1. Ejecutar Runbook
        raw_output = self._trigger_runbook(
            "NeuroDesk-Generate-Upload-Link",
            {"UserEmail": user_email, "StorageAccountName": self.storage_account},
            user_id=user_email,
            description="Solicitud de subida de logs.",
        )

        import json
        try:
            data = json.loads(raw_output)
            
            # 1. 'human_text': NO contiene la URL. Instruye al LLM sobre qué decir.
            # 2. 'system_data': Contiene la URL para que el Frontend la use en el Widget.
            
            return json.dumps({
                "human_text": "He activado el protocolo de transferencia segura. Utiliza el panel visual que aparece abajo para seleccionar y cargar tus archivos de evidencia.",
                "system_data": {
                    "type": "upload_widget",
                    "payload": {
                        "upload_url": data.get("Url"), # URL Real corregida por el Runbook
                        "expires_at": data.get("ExpiresAt"),
                        "blob_path": data.get("BlobPath")
                    }
                }
            })
        except Exception:
            app_logger.warning("⚠️ Error parseando respuesta del Runbook.")
            return "Error técnico generando el control de carga."

    @kernel_function(description="Consulta logs de actividad.", name="get_activity_logs")
    def get_activity_logs(self, user_id: str = "system") -> str:
        return self._trigger_runbook(
            "NeuroDesk-Get-Activity-Logs",
            {"Hours": "4"},
            user_id=user_id,
            description="Consulta de auditoría.",
        )

    @kernel_function(
        description="Reinicia servicios web o aplicaciones críticas cuando están lentas o bloqueadas.", 
        name="self_heal_restart"
    )
    def self_heal_restart(
        self, 
        user_id: Annotated[str, "ID del usuario que reporta"],
        resource_name: Annotated[str, "Nombre del recurso (opcional)"] = "Nexo-Emprendedor" 
    ) -> str:
        """
        Ejecuta un reinicio real sobre la infraestructura de Azure (Web App).
        Target: Nexo-Emprendedor (Production).
        """
        # Si el LLM no especifica nombre, usamos uno por defecto
        target_resource = resource_name if resource_name else "Nexo-Emprendedor"
        
        return self._trigger_runbook(
            runbook_name="NeuroDesk-Self-Heal-Restart",
            parameters={
                "ResourceName": target_resource, 
                "ResourceType": "WebApp"
            },
            user_id=user_id,
            description=f"Reinicio de emergencia: {target_resource}",
            max_wait_seconds=180 # Dar tiempo al reinicio real
        )

    # --- ESCALADO REAL ---
    @kernel_function(
        description="Escala el caso a un agente humano cuando no hay solución automática o es una crisis.",
        name="escalate_to_human"
    )
    def escalate_to_human(
        self, 
        user_id: Annotated[str, "ID del usuario afectado"],
        reason: Annotated[str, "Razón del escalado"],
        urgency: Annotated[str, "Alta, Media, Baja"]
    ) -> str:
        """
        Envía una alerta real vía Logic App a los gerentes de soporte y persiste en Cosmos DB.
        """
        app_logger.info(f"🚨 ESCALANDO TICKET: {user_id} - {reason} - Urgencia: {urgency}")
        
        logic_app_response = None
        
        # 1. Llamar a Logic App si está configurada
        if self.logic_app_url:
            try:
                payload = {
                    "user_id": user_id,
                    "reason": reason,
                    "urgency": urgency,
                    "timestamp": datetime.utcnow().isoformat()
                }
                # Llamada HTTP a Logic App
                response = requests.post(self.logic_app_url, json=payload, timeout=10)
                
                if response.status_code in [200, 202]:
                    logic_app_response = {
                        "status_code": response.status_code,
                        "request_id": response.headers.get('x-ms-request-id', 'N/A'),
                        "triggered_at": datetime.utcnow().isoformat()
                    }
                    app_logger.info(f"✅ Logic App triggered successfully for user {user_id}")
                else:
                    app_logger.warning(f"⚠️ Logic App responded with status {response.status_code}: {response.text}")
                    logic_app_response = {
                        "status_code": response.status_code,
                        "error": response.text[:500] if response.text else "Empty response"
                    }
                    
            except requests.exceptions.Timeout:
                app_logger.error(f"⏱️ Timeout calling Logic App for user {user_id}")
                logic_app_response = {"error": "Timeout after 10 seconds"}
            except Exception as e:
                app_logger.error(f"❌ Exception calling Logic App for user {user_id}: {e}")
                logic_app_response = {"error": str(e)}
        else:
            app_logger.warning("⚠️ Logic App URL no configurada - solo persistencia local")

        # 2. PERSISTIR TICKET EN COSMOS DB
        ticket_record = self._persist_escalation_ticket(user_id, reason, urgency, logic_app_response)
        
        if ticket_record is None:
            app_logger.critical(f"💥 FALLO COMPLETO: No se pudo guardar ticket de escalado para {user_id}")
            return "❌ Error crítico: No se pudo registrar el escalado en el sistema. Por favor, contacte al administrador directamente."

        # 3. Construir respuesta al usuario
        ticket_id = ticket_record.get("ticket_id", "N/A")
        
        if logic_app_response and logic_app_response.get("status_code") in [200, 202]:
            return f"✅ TICKET ESCALADO: Se ha enviado una alerta prioritaria al equipo humano. Tu ticket es #{ticket_id}. Un agente se contactará contigo pronto."
        elif self.logic_app_url:
            return f"⚠️ TICKET REGISTRADO: Se ha creado el ticket #{ticket_id}, pero hubo un problema con la notificación automática. El equipo será notificado manualmente."
        else:
            return f"📝 TICKET CREADO: Se ha registrado tu solicitud con el número #{ticket_id}. El equipo de soporte revisará tu caso pronto."