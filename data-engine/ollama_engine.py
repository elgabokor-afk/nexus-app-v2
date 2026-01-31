import os
import requests
import json
import logging

# Configure Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("OllamaEngine")

class OllamaEngine:
    def __init__(self):
        # Base URL for Ollama (e.g., https://your-ngrok-url.io or http://localhost:11434)
        self.base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
        
        # Models configuration
        self.chat_model = os.getenv("OLLAMA_CHAT_MODEL", "llama3")
        self.embed_model = os.getenv("OLLAMA_EMBED_MODEL", "nomic-embed-text")
        
        self.is_active = self._check_connection()

    def _check_connection(self):
        """Verifies if Ollama is reachable."""
        try:
            # Simple check to tags endpoint
            res = requests.get(f"{self.base_url}/api/tags", timeout=3)
            if res.status_code == 200:
                logger.info(f"   [OLLAMA] Connected to {self.base_url}")
                return True
            return False
        except Exception:
            logger.warning(f"   [OLLAMA] Connection Failed. Is {self.base_url} reachable?")
            return False

    def generate_trade_narrative(self, symbol, signal_type, features):
        """
        Generates trade reasoning using local LLM.
        Compatible with OpenAI style prompt structure.
        """
        if not self.is_active: 
            return None

        prompt = f"""
        ACT AS AN EXPERT QUANTITATIVE ANALYST.
        Asset: {symbol}
        Signal: {signal_type}
        
        Market Data:
        - RSI: {features.get('rsi_value', 'N/A')}
        - Volume Ratio: {features.get('volume_ratio', 'N/A')}
        - Whale Sentiment: {features.get('whale_sentiment_score', 0)}
        - Academic Score: {features.get('academic_thesis_score', 0)}
        
        TASK:
        Write a 2-sentence professional analysis justifying this trade. 
        Focus on the confluence of Technicals and Quantitative data.
        """

        payload = {
            "model": self.chat_model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": 0.3, # Low temp for analytical precision
                "num_predict": 100
            }
        }

        try:
            url = f"{self.base_url}/api/generate"
            res = requests.post(url, json=payload, timeout=30)
            
            if res.status_code == 200:
                response_text = res.json().get('response', '').strip()
                return response_text
            else:
                logger.error(f"   [OLLAMA ERROR] Status: {res.status_code} - {res.text}")
                return None
                
        except Exception as e:
            logger.error(f"   [OLLAMA CRASH] {e}")
            return None

    def get_embedding(self, text):
        """
        Generates vector embeddings for RAG system using local model.
        Returns: Light list of floats (vector).
        """
        if not self.is_active: return None
        
        payload = {
            "model": self.embed_model,
            "prompt": text
        }
        
        try:
            url = f"{self.base_url}/api/embeddings"
            res = requests.post(url, json=payload, timeout=10)
            
            if res.status_code == 200:
                return res.json().get('embedding', [])
            return None
        except Exception as e:
            logger.error(f"   [OLLAMA EMBED ERROR] {e}")
            return None

# Singleton Instance
ollama_engine = OllamaEngine()
