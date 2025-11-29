from fastapi import FastAPI, HTTPException, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from src.models.messages import ChatRequest, ChatResponse
from src.services.chat_orchestrator import orchestrator
from src.services.audit_ledger import audit_ledger
from src.services.voice_handler import voice_handler
from src.utils.logger import app_logger
import shutil
import os
import uuid

app = FastAPI(
    title="NeuroDesk API",
    description="Sistema Inmunológico Organizacional (AI Agent + RAG + Automation)",
    version="2.0.0"
)

# Configuración CORS (Permitir todo para Hackathon)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    return {
        "status": "NeuroDesk System Operational", 
        "mode": "Active Defense",
        "version": "2.0.0 (Vector + OCR + Memory)"
    }

@app.post("/chat", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest):
    """
    Endpoint principal de chat.
    Maneja texto, memoria conversacional y auditoría.
    """
    # 1. Generar ID de conversación si no viene
    if not request.conversation_id:
        request.conversation_id = str(uuid.uuid4())

    app_logger.info(f"📩 Mensaje recibido. User: {request.user_id} | Session: {request.conversation_id}")
    
    try:
        # 2. Procesar con el Orquestador (Cerebro)
        # El orquestador ya maneja RAG, Tools y HR internamente
        response = await orchestrator.process_message(request)
        
        # 3. Auditoría (Escribir en Cosmos DB)
        # Esto ocurre en segundo plano (fire & forget) idealmente, aquí síncrono para seguridad
        audit_ledger.log_transaction(
            user_id=request.user_id,
            request_text=request.message,
            response_obj=response,
            context_id=request.conversation_id
        )
        
        return response

    except Exception as e:
        app_logger.error(f"💥 Error no controlado en API: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/chat/voice")
async def voice_chat_endpoint(
    user_id: str = Form(...), 
    conversation_id: str = Form(None),
    file: UploadFile = File(...)
):
    """
    Recibe audio (.wav), transcribe, procesa y responde con audio + texto.
    """
    temp_filename = f"temp_{uuid.uuid4()}.wav"
    
    try:
        # 1. Guardar archivo temporalmente
        with open(temp_filename, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        # 2. STT: Audio -> Texto
        transcribed_text = await voice_handler.transcribe_audio(temp_filename)
        app_logger.info(f"🗣️ Audio transcrito: {transcribed_text}")

        if not transcribed_text or "No pude entender" in transcribed_text:
             return {
                 "response": "No pude escuchar bien el audio. ¿Podrías repetirlo?",
                 "user_text": "",
                 "ai_audio_base64": None
             }

        # 3. Crear Request estándar
        chat_req = ChatRequest(
            user_id=user_id, 
            message=transcribed_text,
            conversation_id=conversation_id or str(uuid.uuid4())
        )

        # 4. Procesar (Igual que endpoint de texto)
        chat_res = await orchestrator.process_message(chat_req)
        
        # 5. Auditoría
        audit_ledger.log_transaction(
            user_id=user_id,
            request_text=f"[VOICE] {transcribed_text}",
            response_obj=chat_res,
            context_id=chat_req.conversation_id
        )

        # 6. TTS: Respuesta Texto -> Audio
        audio_response_b64 = await voice_handler.text_to_speech(chat_res.response)

        return {
            "response": chat_res.response,
            "user_text": transcribed_text,
            "ai_audio_base64": audio_response_b64,
            "is_safe": chat_res.is_safe,
            "sentiment": chat_res.sentiment,
            "risk_level": chat_res.risk_level,
            "conversation_id": chat_req.conversation_id
        }

    except Exception as e:
        app_logger.error(f"❌ Error en voice endpoint: {e}")
        return {"error": str(e)}
    finally:
        # Limpieza
        if os.path.exists(temp_filename):
            os.remove(temp_filename)

# Comando de ejecución: uvicorn src.api.main:app --reload