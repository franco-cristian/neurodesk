from azure.core.credentials import AzureKeyCredential
from azure.ai.contentsafety import ContentSafetyClient
from azure.ai.contentsafety.models import AnalyzeTextOptions
from src.config import settings

class SafetyGuard:
    def __init__(self):
        if not settings.SAFETY_ENDPOINT or not settings.SAFETY_KEY:
            print("❌ ERROR CRÍTICO: Content Safety NO configurado en .env")
            self.client = None
        else:
            try:
                self.client = ContentSafetyClient(
                    settings.SAFETY_ENDPOINT, 
                    AzureKeyCredential(settings.SAFETY_KEY)
                )
                print("✅ Content Safety Client conectado.")
            except Exception as e:
                print(f"❌ Error conectando Content Safety: {e}")
                self.client = None

    def is_safe(self, text: str) -> dict:
        if not self.client:
            print("⚠️ Safety Guard inactivo (Bypassed)")
            return {"safe": True, "reason": "Safety Service Unreachable"}

        try:
            request = AnalyzeTextOptions(text=text)
            response = self.client.analyze_text(request)

            violations = []
            
            # Recorremos las categorías
            for category in response.categories_analysis:
                cat_name = category.category
                if hasattr(cat_name, 'name'):
                    cat_name = cat_name.name
                
                # Umbral
                if category.severity > 2: # Solo bloquea si la severidad es Media o Alta
                    severity_label = f"Nivel {category.severity}"
                    violations.append(f"{cat_name} ({severity_label})")

            if violations:
                return {
                    "safe": False, 
                    "reason": f"Violaciones detectadas: {', '.join(violations)}"
                }
            
            return {"safe": True, "reason": "Clean"}

        except Exception as e:
            print(f"❌ Error analizando texto en SafetyGuard: {e}")
            # En caso de duda, dejamos pasar para que OpenAI decida (Fail Open para demo)
            return {"safe": True, "reason": "Analysis Error"}

safety_guard = SafetyGuard()