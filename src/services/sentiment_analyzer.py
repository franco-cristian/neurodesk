from azure.core.credentials import AzureKeyCredential
from azure.ai.textanalytics import TextAnalyticsClient
from src.config import settings

class SentimentAnalyzer:
    def __init__(self):
        if not settings.LANGUAGE_ENDPOINT or not settings.LANGUAGE_KEY:
            print("⚠️ Azure Language no configurado. Sentimiento será 'Neutral' por defecto.")
            self.client = None
        else:
            try:
                self.client = TextAnalyticsClient(
                    endpoint=settings.LANGUAGE_ENDPOINT, 
                    credential=AzureKeyCredential(settings.LANGUAGE_KEY)
                )
                print("✅ Sentiment Analyzer conectado.")
            except Exception as e:
                print(f"❌ Error conectando Sentiment Analyzer: {e}")
                self.client = None

    def analyze(self, text: str) -> dict:
        """
        Devuelve: { 'sentiment': 'positive'|'neutral'|'negative'|'mixed', 'confidence': 0.99 }
        """
        if not self.client or not text:
            return {"sentiment": "Neutral", "confidence": 1.0}

        try:
            # Analizamos el sentimiento
            response = self.client.analyze_sentiment(documents=[text])[0]
            
            # Mapeamos al formato que queremos
            # response.sentiment puede ser "positive", "neutral", "negative", "mixed"
            
            # Obtenemos el score del sentimiento dominante
            scores = response.confidence_scores
            confidence = 0.0
            
            if response.sentiment == "positive": confidence = scores.positive
            elif response.sentiment == "negative": confidence = scores.negative
            elif response.sentiment == "neutral": confidence = scores.neutral
            else: confidence = max(scores.positive, scores.negative) # Mixed

            print(f"❤️ Análisis de Sentimiento: {response.sentiment} ({confidence:.2f})")
            
            return {
                "sentiment": response.sentiment.capitalize(), # "Negative"
                "confidence": confidence
            }

        except Exception as e:
            print(f"❌ Error analizando sentimiento: {e}")
            return {"sentiment": "Neutral", "confidence": 0.0}

sentiment_analyzer = SentimentAnalyzer()