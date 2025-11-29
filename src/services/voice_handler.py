import os
import azure.cognitiveservices.speech as speechsdk
from src.config import settings
import base64
import tempfile
import asyncio
import re
from src.utils.logger import app_logger

class VoiceHandler:
    def __init__(self):
        if not settings.SPEECH_KEY or not settings.SPEECH_REGION:
            app_logger.warning("⚠️ Speech Service no configurado.")
            self.speech_config = None
        else:
            try:
                self.speech_config = speechsdk.SpeechConfig(
                    subscription=settings.SPEECH_KEY, 
                    region=settings.SPEECH_REGION
                )
                # Configurar voz en español
                self.speech_config.speech_synthesis_voice_name = "es-MX-JorgeNeural"
                self.speech_config.speech_recognition_language = "es-ES"
                app_logger.info("✅ Speech Service configurado correctamente")
            except Exception as e:
                app_logger.error(f"❌ Error configurando Speech Service: {e}")
                self.speech_config = None

    def _clean_text_for_tts(self, text: str) -> str:
        """
        Limpia el texto de formato markdown para que el TTS lo lea naturalmente.
        """
        if not text:
            return ""
        
        # 1. Remover encabezados markdown (###, ##, #)
        text = re.sub(r'#+\s*', '', text)
        
        # 2. Remover negritas e itálicas (**texto**, *texto*)
        text = re.sub(r'\*\*(.*?)\*\*', r'\1', text)
        text = re.sub(r'\*(.*?)\*', r'\1', text)
        text = re.sub(r'_(.*?)_', r'\1', text)
        
        # 3. Remover código inline (`codigo`)
        text = re.sub(r'`(.*?)`', r'\1', text)
        
        # 4. Remover enlaces [texto](url) -> mantener solo el texto
        text = re.sub(r'\[(.*?)\]\(.*?\)', r'\1', text)
        
        # 5. Remover listas con asteriscos o guiones
        text = re.sub(r'^\s*[\*\-]\s*', '', text, flags=re.MULTILINE)
        
        # 6. Remover bloques de código (```language\ncode\n```)
        text = re.sub(r'```[\s\S]*?```', '', text)
        
        # 7. Reemplazar saltos de línea múltiples por puntos
        text = re.sub(r'\n\s*\n', '. ', text)
        
        # 8. Reemplazar saltos de línea simples por espacios
        text = re.sub(r'\n', ' ', text)
        
        # 9. Limpiar espacios múltiples
        text = re.sub(r'\s+', ' ', text)
        
        # 10. Limpiar caracteres especiales problemáticos
        text = re.sub(r'[<>]', '', text)
        
        # 11. Asegurar que termina con un punto si es una oración larga
        text = text.strip()
        if len(text) > 10 and not text.endswith(('.', '!', '?')):
            text += '.'
            
        app_logger.info(f"🔧 Texto limpio para TTS: {text[:100]}...")
        return text

    async def transcribe_audio(self, audio_file_path: str) -> str:
        """STT: Convierte archivo de audio (WAV) a Texto"""
        if not self.speech_config:
            return "Servicio de voz no configurado"

        try:
            audio_config = speechsdk.audio.AudioConfig(filename=audio_file_path)
            speech_recognizer = speechsdk.SpeechRecognizer(
                speech_config=self.speech_config, 
                audio_config=audio_config,
                language="es-ES"
            )

            app_logger.info("🎙️ Transcribiendo audio desde archivo...")
            result = speech_recognizer.recognize_once_async().get()
            
            if result.reason == speechsdk.ResultReason.RecognizedSpeech:
                text = result.text.strip()
                app_logger.info(f"✅ Texto reconocido: {text}")
                return text
            elif result.reason == speechsdk.ResultReason.NoMatch:
                app_logger.warning("❌ No se pudo reconocer el audio")
                return "No pude entender el audio. ¿Podrías intentarlo de nuevo?"
            else:
                cancellation_details = result.cancellation_details
                error_msg = f"Error en reconocimiento: {cancellation_details.reason}"
                if cancellation_details.reason == speechsdk.CancellationReason.Error:
                    error_msg += f" - {cancellation_details.error_details}"
                app_logger.error(error_msg)
                return "Error procesando el audio. Por favor intenta de nuevo."

        except Exception as e:
            app_logger.error(f"💥 Error en STT: {e}")
            return "Error interno procesando audio"

    async def text_to_speech(self, text: str) -> str:
        """TTS: Convierte texto a audio Base64"""
        if not self.speech_config or not text.strip():
            return ""

        try:
            # Limpiar el texto de markdown antes de sintetizar
            clean_text = self._clean_text_for_tts(text)
            
            if not clean_text.strip():
                app_logger.warning("⚠️ Texto vacío después de limpiar, no se genera audio")
                return ""
                
            # Sintetizador
            synthesizer = speechsdk.SpeechSynthesizer(
                speech_config=self.speech_config, 
                audio_config=None
            )

            app_logger.info(f"🔊 Sintetizando audio (limpio): {clean_text[:50]}...")
            result = synthesizer.speak_text_async(clean_text).get()

            if result.reason == speechsdk.ResultReason.SynthesizingAudioCompleted:
                audio_base64 = base64.b64encode(result.audio_data).decode('utf-8')
                app_logger.info("✅ Audio sintetizado correctamente")
                return audio_base64
            else:
                cancellation_details = result.cancellation_details
                error_msg = f"Error en síntesis: {cancellation_details.reason}"
                if cancellation_details.reason == speechsdk.CancellationReason.Error:
                    error_msg += f" - {cancellation_details.error_details}"
                app_logger.error(error_msg)
                return ""

        except Exception as e:
            app_logger.error(f"💥 Error en TTS: {e}")
            return ""

voice_handler = VoiceHandler()