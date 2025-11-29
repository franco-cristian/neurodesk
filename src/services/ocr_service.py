import os
from azure.core.credentials import AzureKeyCredential
from azure.ai.documentintelligence import DocumentIntelligenceClient
from azure.ai.documentintelligence.models import AnalyzeResult
from src.config import settings
from src.utils.logger import app_logger


# Mapeo simple de content-types para mejor precisión; octet-stream funciona como fallback
CONTENT_TYPES = {
    ".pdf": "application/pdf",
    ".png": "image/png",
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".tiff": "image/tiff",
}


class OcrService:
    def __init__(self):
        self.endpoint = settings.DOC_INT_ENDPOINT
        self.key = settings.DOC_INT_KEY

        if not self.endpoint or not self.key:
            app_logger.warning("⚠️ OCR Service: AZURE_DOCUMENT_INTELLIGENCE_* no configurado.")
            self.client = None
            return

        try:
            self.client = DocumentIntelligenceClient(
                endpoint=self.endpoint,
                credential=AzureKeyCredential(self.key)
            )
            app_logger.info("✅ OCR Service (Document Intelligence) conectado.")
        except Exception as e:
            app_logger.error(f"❌ Error conectando OCR Service: {e}")
            self.client = None

    def _guess_content_type(self, file_path: str) -> str:
        ext = os.path.splitext(file_path)[1].lower()
        return CONTENT_TYPES.get(ext, "application/octet-stream")

    def extract_text_from_file(self, file_path: str) -> str:
        """
        Extrae texto de documentos complejos usando el modelo 'prebuilt-read'.
        Compatible con azure-ai-documentintelligence==1.0.2.
        """
        if not self.client:
            return ""

        filename = os.path.basename(file_path)
        app_logger.info(f"👁️ Procesando documento: {filename}")

        content_type = self._guess_content_type(file_path)

        try:
            with open(file_path, "rb") as f:
                # Firma correcta en 1.0.2: segundo argumento POSICIONAL = body (stream binario)
                poller = self.client.begin_analyze_document(
                    "prebuilt-read",          # model_id
                    f,                        # body (stream del archivo)
                    content_type=content_type
                )
                result: AnalyzeResult = poller.result()

            if result and getattr(result, "content", None):
                app_logger.info(f"✅ OCR Exitoso ({len(result.content)} chars).")
                return result.content

            app_logger.warning(f"⚠️ OCR finalizado pero sin texto en {filename}")
            return ""

        except Exception as e:
            error_msg = str(e)
            if "404" in error_msg:
                app_logger.error(
                    f"❌ Error 404: Verifica que el endpoint '{self.endpoint}' sea correcto y que el recurso de Document Intelligence soporte 'prebuilt-read'."
                )
            else:
                app_logger.error(f"❌ Fallo crítico OCR: {e}")
            return ""


# Instancia global del servicio
ocr_service = OcrService()
