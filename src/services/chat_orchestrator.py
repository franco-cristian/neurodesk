from semantic_kernel import Kernel
from semantic_kernel.connectors.ai.open_ai import AzureChatCompletion, AzureChatPromptExecutionSettings
from semantic_kernel.connectors.ai.function_choice_behavior import FunctionChoiceBehavior
from semantic_kernel.contents import ChatHistory
from semantic_kernel.exceptions import ServiceResponseException
from semantic_kernel.functions import KernelArguments
import re
from typing import Dict

from src.config import settings
from src.services.safety_guard import safety_guard
from src.services.sentiment_analyzer import sentiment_analyzer
from src.models.messages import ChatRequest, ChatResponse
from src.utils.logger import app_logger

# Plugins
from src.services.plugins.hr_plugin import HRAgentPlugin
from src.services.plugins.it_plugin import ITAgentPlugin
from src.services.plugins.policy_plugin import PolicyAgentPlugin

class ChatOrchestrator:
    def __init__(self):
        self.kernel = Kernel()
        
        # Diccionario en memoria para mantener el historial de conversaciones
        # Key: conversation_id (o user_id si no hay conv_id), Value: ChatHistory
        self._memories: Dict[str, ChatHistory] = {}
        
        chat_service = AzureChatCompletion(
            service_id="chat-gpt",
            deployment_name=settings.AOAI_DEPLOYMENT,
            endpoint=settings.AOAI_ENDPOINT,
            api_key=settings.AOAI_KEY,
        )
        self.kernel.add_service(chat_service)
        
        # Registrar Plugins
        self.kernel.add_plugin(HRAgentPlugin(), plugin_name="HRAgent")
        self.kernel.add_plugin(ITAgentPlugin(), plugin_name="ITAgent")
        self.kernel.add_plugin(PolicyAgentPlugin(), plugin_name="PolicyAgent")

    def _detect_critical_intent(self, message: str) -> dict:
        """
        Detección heurística para logging y cálculo de riesgo, 
        pero NO para forzar al LLM (evita alucinaciones).
        """
        message_lower = message.lower()
        
        restart_patterns = [
            r'\blento\b', r'\breiniciar\b', r'\bno funciona\b', r'\bbloqueado\b',
            r'\bcongelado\b', r'\bcaído\b', r'\bhang\b', r'\bfreeze\b', 
            r'\bslow\b', r'\brestart\b', r'\bcaido\b', r'\bno responde\b'
        ]
        
        upload_patterns = [
            r'\blogs\b', r'\bsubir\b', r'\barchivo\b', r'\bevidencia\b',
            r'\bcaptura\b', r'\bscreenshot\b', r'\bupload\b', r'\bfoto\b'
        ]
        
        audit_patterns = [
            r'\bauditoría\b', r'\bquién tocó\b', r'\bcambios\b', r'\bseguridad\b',
            r'\bactividad\b', r'\bhistorial\b', r'\bquien hizo\b'
        ]
        
        human_patterns = [
            r'\bhumano\b', r'\bpersona\b', r'\bagente\b', r'\boperador\b',
            r'\bsupervisor\b', r'\bgerente\b', r'\bhablar con\b'
        ]
        
        detected_intent = {
            "needs_restart": any(re.search(pattern, message_lower) for pattern in restart_patterns),
            "needs_upload": any(re.search(pattern, message_lower) for pattern in upload_patterns),
            "needs_audit": any(re.search(pattern, message_lower) for pattern in audit_patterns),
            "needs_human": any(re.search(pattern, message_lower) for pattern in human_patterns),
            "urgency": "high" if any(word in message_lower for word in ["urgente", "crítico", "critico", "emergencia", "ya", "inmediato"]) else "normal"
        }
        
        return detected_intent

    def _get_or_create_history(self, session_key: str, user_name: str) -> ChatHistory:
        """
        Recupera el historial existente o crea uno nuevo con el System Prompt.
        """
        if session_key in self._memories:
            return self._memories[session_key]
        
        # Inicializar nuevo historial con System Prompt optimizado
        history = ChatHistory()
        
        system_prompt = f"""Eres NeuroDesk, un asistente de resiliencia operativa autónomo.
        
        OBJETIVO:
        Resolver incidentes técnicos y cuidar el bienestar del empleado ({user_name}) usando las herramientas disponibles.
        
        TUS HERRAMIENTAS (PLUGINS):
        Tienes acceso a funciones reales en la nube. ÚSALAS. No simules que las usas.
        
        1. 'ITAgent-generate_upload_link': Para subir logs, capturas o archivos.
        2. 'ITAgent-get_activity_logs': Para auditoría, seguridad o ver cambios recientes.
        3. 'ITAgent-self_heal_restart': Para problemas de lentitud, bloqueos o reinicio de servicios.
        4. 'ITAgent-escalate_to_human': Si el usuario pide un humano, está muy frustrado o no puedes resolverlo.
        5. 'HRAgent-analyze_workload_metrics': EJECUTA ESTO SIEMPRE AL INICIO para entender el contexto del usuario.
        6. 'PolicyAgent-check_corporate_policy': Si hay dudas sobre normas, horarios o derechos.

        REGLAS DE COMPORTAMIENTO:
        - Si detectas un problema técnico claro, invoca la herramienta correspondiente inmediatamente.
        - Si ejecutas una herramienta, TU RESPUESTA FINAL debe basarse en el resultado de esa herramienta.
        - Mantén un tono profesional pero empático.
        - NO inventes resultados. Si la herramienta falla, dilo.
        - Recuerda el contexto de la conversación anterior.
        """
        
        history.add_system_message(system_prompt)
        self._memories[session_key] = history
        return history

    async def process_message(self, request: ChatRequest) -> ChatResponse:
        app_logger.info(f"📨 Procesando mensaje de {request.user_id} (ConvID: {request.conversation_id})")

        # 1. Identificador de Sesión
        # Usamos conversation_id si existe, sino user_id (memoria persistente por usuario)
        session_key = request.conversation_id if request.conversation_id else request.user_id

        # 2. FILTRO DE RUIDO
        if len(request.message.strip()) < 2:
             return ChatResponse(response="Hola, soy NeuroDesk. ¿En qué puedo ayudarte hoy?", is_safe=True)

        # 3. SENTINEL (Safety Guard)
        safety = safety_guard.is_safe(request.message)
        if not safety["safe"]:
            app_logger.warning(f"🛑 Bloqueo Sentinel: {safety['reason']}")
            return ChatResponse(
                response=f"🛑 El mensaje ha sido bloqueado por protocolos de seguridad ética: {safety['reason']}",
                is_safe=False,
                sentiment="Negative",
                risk_level="High",
                actions_taken=["Bloqueado por Sentinel"]
            )

        # 4. SENTIMENT & INTENT (Heurística)
        sentiment_result = sentiment_analyzer.analyze(request.message)
        user_sentiment = sentiment_result["sentiment"]
        intent = self._detect_critical_intent(request.message)
        
        app_logger.info(f"❤️ Sentimiento: {user_sentiment} | 🎯 Intención Heurística: {intent}")

        # 5. GESTIÓN DE MEMORIA Y ORQUESTACIÓN
        chat_service = self.kernel.get_service("chat-gpt")
        
        # Recuperar historial
        history = self._get_or_create_history(session_key, request.user_id)
        
        # Añadir mensaje del usuario al historial
        history.add_user_message(request.message)

        # Configuración de ejecución con Auto Function Calling
        execution_settings = AzureChatPromptExecutionSettings(
            service_id="chat-gpt",
            temperature=0.5, # Bajamos temperatura para ser más precisos con las herramientas
            max_tokens=800,
            function_choice_behavior=FunctionChoiceBehavior.Auto()
        )

        try:
            # Invocar al LLM con el historial completo
            result = await chat_service.get_chat_message_content(
                chat_history=history,
                settings=execution_settings,
                kernel=self.kernel 
            )

            # Añadir la respuesta del asistente al historial para el siguiente turno
            history.add_message(result)
            
            final_response = str(result)
            ui_data = None

            # LÓGICA DE EXTRACCIÓN DE PAYLOAD (Rich UI)
            # Buscamos si en el historial reciente hay un output de herramienta con nuestro formato JSON
            # Nota: Semantic Kernel guarda el resultado de las funciones en el chat history.
            
            # Iteramos los mensajes recientes en busca de "system_data"
            for msg in reversed(history.messages):
                if msg.role == "tool": # Mensajes que vienen de las herramientas
                    try:
                        import json
                        content_str = str(msg.content)
                        if "system_data" in content_str:
                            data = json.loads(content_str)
                            if "system_data" in data:
                                ui_data = data["system_data"]
                                app_logger.info(f"🎨 UI Component detectado: {ui_data['type']}")
                                break
                    except:
                        continue

            # --- Lógica de Auditoría de Ejecución ---
            # Verificamos si Semantic Kernel reporta uso de herramientas en este turno
            
            execution_indicators = [
                "he ejecutado", "he reiniciado", "he generado", "he consultado",
                "proceso ejecutado", "ticket creado", "escalado realizado", "enlace generado",
                "datos de rrhh", "análisis de carga"
            ]
            
            is_real_execution = any(indicator in final_response.lower() for indicator in execution_indicators)
            
            # Cálculo de Riesgo Post-Ejecución
            calculated_risk = "Low"
            actions_taken = ["Análisis Contextual"]
            
            if intent["urgency"] == "high":
                calculated_risk = "Medium"
            
            if is_real_execution:
                actions_taken.append("Tool Execution (Semantic Kernel)")
            elif intent["needs_restart"] or intent["needs_human"]:
                # Si necesitaba acción crítica y no hay evidencia de ejecución, subimos riesgo
                calculated_risk = "High"
                actions_taken.append("⚠️ Alerta: Posible inacción en solicitud crítica")

            app_logger.info(f"📊 Respuesta generada. Riesgo: {calculated_risk}. Acciones: {actions_taken}")

            return ChatResponse(
                response=final_response,
                is_safe=True,
                sentiment=user_sentiment,
                risk_level=calculated_risk,
                actions_taken=actions_taken,
                ui_component=ui_data,
                next_steps=["Esperar feedback usuario"]
            )

        except ServiceResponseException as e:
            app_logger.error(f"❌ Error de servicio Azure OpenAI: {e}")
            return ChatResponse(
                response="Error temporal del servicio de IA. Mi memoria está intacta, pero no puedo procesar la respuesta ahora.",
                is_safe=True,
                risk_level="Medium"
            )
        except Exception as e:
            app_logger.error(f"❌ Error crítico Orchestrator: {e}")
            return ChatResponse(
                response="Error interno del sistema al procesar la solicitud.",
                is_safe=True,
                risk_level="Unknown"
            )

orchestrator = ChatOrchestrator()