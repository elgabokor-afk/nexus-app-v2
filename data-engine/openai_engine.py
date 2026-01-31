"""
NEXUS AI - Ollama Text Generation Engine
Replaces OpenAI for trade narrative generation using local Ollama
"""
import os
import requests
from dotenv import load_dotenv

# Load env from parent directory
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
load_dotenv(dotenv_path=os.path.join(parent_dir, '.env.local'))

class OpenAIEngine:
    """
    Renamed to maintain compatibility with existing imports.
    Now uses Ollama instead of OpenAI.
    """
    def __init__(self):
        self.ollama_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
        self.model = "llama3.2:3b"  # Fast, efficient model for trade narratives
        self.client = self  # For compatibility
        
        # Test connection
        try:
            response = requests.get(f"{self.ollama_url}/api/tags", timeout=5)
            if response.status_code == 200:
                print(f"   [OLLAMA] Text generation engine connected to {self.ollama_url}")
            else:
                print(f"   [OLLAMA] Warning: Connection issue (status {response.status_code})")
        except Exception as e:
            print(f"   [OLLAMA] Warning: Could not connect to {self.ollama_url}: {e}")

    def generate_trade_narrative(self, symbol, signal_type, features):
        """
        Generates high-fidelity trading reasoning using local Ollama.
        """
        try:
            prompt = f"""Act as a Lead Strategy Quant in a global macro fund.
Interpret this crypto signal for {symbol} with institutional precision.
Maximum length: 140 characters. No fluff.

Signal: {signal_type}
Price: {features.get('price', 'N/A')}
RSI: {features.get('rsi_value', 'N/A')}
EMA 200 Position: {features.get('trend', 'N/A')}
Order Book Imbalance: {features.get('imbalance_ratio', 'N/A')}
SMC Details: {features.get('smc_details', 'Detecting...')}

Provide a direct, high-conviction institutional thesis."""

            response = requests.post(
                f"{self.ollama_url}/api/generate",
                json={
                    "model": self.model,
                    "prompt": prompt,
                    "stream": False,
                    "options": {
                        "temperature": 0.5,
                        "num_predict": 60  # Limit tokens for concise response
                    }
                },
                timeout=30
            )

            if response.status_code == 200:
                data = response.json()
                narrative = data.get("response", "").strip()
                # Clean up narrative
                narrative = narrative.replace('"', '').replace("'", "")
                # Truncate to 140 chars
                if len(narrative) > 140:
                    narrative = narrative[:137] + "..."
                return narrative
            else:
                print(f"   [OLLAMA ERROR] Status {response.status_code}: {response.text}")
                return None

        except requests.exceptions.RequestException as e:
            print(f"   [OLLAMA CONNECTION ERROR] {e}")
            return None
        except Exception as e:
            print(f"   [OLLAMA ERROR] {e}")
            return None

# Singleton instance
openai_engine = OpenAIEngine()

if __name__ == "__main__":
    # Test call
    test_features = {"price": 105000, "rsi_value": 28, "trend": "BULLISH", "imbalance_ratio": 0.55}
    res = openai_engine.generate_trade_narrative("BTC/USDT", "STRONG BUY", test_features)
    print(f"Test Narrative: {res}")
