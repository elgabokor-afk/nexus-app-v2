"""
NEXUS AI - Ollama Deep Reasoning Engine
Replaces DeepSeek for advanced reasoning using local Ollama
"""
import os
import requests
from dotenv import load_dotenv

# Load env from parent directory
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
load_dotenv(dotenv_path=os.path.join(parent_dir, '.env.local'))

class DeepSeekEngine:
    """
    Renamed to maintain compatibility with existing imports.
    Now uses Ollama instead of DeepSeek API.
    """
    def __init__(self):
        self.ollama_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
        self.model = "llama3.2:3b"  # Fast, efficient model
        self.client = self  # For compatibility
        
        # Test connection
        try:
            response = requests.get(f"{self.ollama_url}/api/tags", timeout=5)
            if response.status_code == 200:
                print(f"   [OLLAMA] Deep reasoning engine connected")
            else:
                print(f"   [OLLAMA] Warning: Connection issue")
        except Exception as e:
            print(f"   [OLLAMA] Warning: Could not connect: {e}")

    def generate_deep_reasoning(self, symbol, signal_type, features):
        """
        Generates advanced trading reasoning using local Ollama.
        """
        try:
            prompt = f"""Act as a Senior Quant Trader at a top hedge fund. 
Analyze this signal for {symbol} and provide a concise, professional narrative (max 150 characters).

Signal: {signal_type}
Price: {features.get('price', 'N/A')}
RSI: {features.get('rsi_value', 'N/A')}
Trend: {features.get('trend', 'N/A')}
Order Book Imbalance: {features.get('imbalance_ratio', 'N/A')}
Volatility (ATR): {features.get('atr_value', 'N/A')}

Context: The bot uses a Random Forest classifier combined with SMA/Volume filters.

Provide a direct, high-conviction institutional reasoning."""

            response = requests.post(
                f"{self.ollama_url}/api/generate",
                json={
                    "model": self.model,
                    "prompt": prompt,
                    "stream": False,
                    "options": {
                        "temperature": 0.7,
                        "num_predict": 100
                    }
                },
                timeout=30
            )

            if response.status_code == 200:
                data = response.json()
                reasoning = data.get("response", "").strip()
                # Clean up
                reasoning = reasoning.replace('"', '').replace("'", "")
                # Truncate to 150 chars
                if len(reasoning) > 150:
                    reasoning = reasoning[:147] + "..."
                return reasoning
            else:
                print(f"   [OLLAMA ERROR] Status {response.status_code}")
                return None

        except Exception as e:
            print(f"   [OLLAMA ERROR] {e}")
            return None

# Singleton
deepseek_engine = DeepSeekEngine()

if __name__ == "__main__":
    # Test call
    test_features = {"price": 50000, "rsi_value": 35, "trend": "BULLISH", "imbalance_ratio": 0.45}
    res = deepseek_engine.generate_deep_reasoning("BTC/USDT", "BUY", test_features)
    print(f"Test Reasoning: {res}")
