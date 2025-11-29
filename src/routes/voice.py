from fastapi import APIRouter, UploadFile, File, HTTPException
from src.services.voice_handler import voice_handler
from src.services.chat_orchestrator import orchestrator
from src.models.messages import ChatRequest
from src.utils.logger import app_logger

router = APIRouter()

@router.post("/chat/voice")
async def voice_chat(
    file: UploadFile = File(...), 
    user_id: str = "unknown", 
    conversation_id: str = "default"
):
    try:
        app_logger.info("🎙️ Endpoint de voz recibiendo solicitud...")
        
        # 1. Validar archivo
        if not file.content_type or not file.content_type.startswith('audio/'):
            raise HTTPException(status_code=400, detail="Formato de archivo no soportado")
        
        # 2. Leer contenido del audio
        audio_content = await file.read()
        app_logger.info(f"📊 Audio recibido: {len(audio_content)} bytes")
        
        if len(audio_content) < 100:  # Archivo muy pequeño
            raise HTTPException(status_code=400, detail="Archivo de audio demasiado pequeño")
        
        # 3. STT - Convertir audio a texto
        user_text = await voice_handler.transcribe_audio(audio_content)
        
        if not user_text or user_text.startswith("Error") or user_text.startswith("No pude"):
            app_logger.warning(f"⚠️ STT falló o resultado vacío: {user_text}")
            return {
                "user_text": user_text or "No se detectó speech",
                "response": "Lo siento, no pude entender el audio. ¿Podrías intentarlo de nuevo o escribir tu mensaje?",
                "ai_audio_base64": None,
                "risk_level": "Low",
                "sentiment": "Neutral",
                "actions_taken": ["STT Falló"],
                "ui_component": None
            }
        
        # 4. Procesar con el orchestrator
        chat_request = ChatRequest(
            user_id=user_id,
            message=user_text,
            conversation_id=conversation_id
        )
        
        chat_response = await orchestrator.process_message(chat_request)
        
        # 5. TTS - Convertir respuesta a audio (solo si hay texto significativo)
        ai_audio_base64 = None
        if chat_response.response and len(chat_response.response.strip()) > 10:
            ai_audio_base64 = await voice_handler.text_to_speech(chat_response.response)
        
        # 6. Retornar respuesta
        return {
            "user_text": user_text,
            "response": chat_response.response,
            "ai_audio_base64": ai_audio_base64,
            "risk_level": chat_response.risk_level,
            "sentiment": chat_response.sentiment,
            "actions_taken": chat_response.actions_taken,
            "ui_component": chat_response.ui_component
        }
        
    except HTTPException:
        raise
    except Exception as e:
        app_logger.error(f"💥 Error crítico en voice endpoint: {str(e)}")
        raise HTTPException(
            status_code=500, 
            detail=f"Error interno procesando audio: {str(e)}"
        )