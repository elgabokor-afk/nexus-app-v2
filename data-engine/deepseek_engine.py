
import os
from openai import OpenAI
from dotenv import load_dotenv

# Load env from parent directory
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
load_dotenv(dotenv_path=os.path.join(parent_dir, '.env.local'))

class DeepSeekEngine:
    def __init__(self):
        self.api_key = os.getenv("DEEPSEEK_API_KEY")
        self.client = None
        if self.api_key:
            # DeepSeek is OpenAI compatible
            self.client = OpenAI(
                api_key=self.api_key,
                base_url="https://api.deepseek.com"
            )
            print("   [DEEPSEEK] Engine Initialized.")
        else:
            print("   [DEEPSEEK] Warning: DEEPSEEK_API_KEY missing in .env.local")

    def generate_deep_reasoning(self, symbol, signal_type, features):
        """
        Generates advanced trading reasoning using DeepSeek AI.
        """
        if not self.client:
            return None

        try:
            # Prepare context for the AI
            prompt = f"""
            Act as a Senior Quant Trader at a top hedge fund. 
            Analyze this signal for {symbol} and provide a concise, professional narrative (max 150 characters).
            
            Signal: {signal_type}
            Price: {features.get('price', 'N/A')}
            RSI: {features.get('rsi_value', 'N/A')}
            Trend: {features.get('trend', 'N/A')}
            Order Book Imbalance: {features.get('imbalance_ratio', 'N/A')}
            Volatility (ATR): {features.get('atr_value', 'N/A')}
            
            Context: The bot uses a Random Forest classifier combined with SMA/Volume filters.
            
            Provide a direct, high-conviction institutional reasoning.
            """

            response = self.client.chat.completions.create(
                model="deepseek-chat", # Use deepseek-reasoner for R1 if supported/needed
                messages=[
                    {"role": "system", "content": "You are a professional crypto analyst providing short, sharp trading insights."},
                    {"role": "user", "content": prompt},
                ],
                max_completion_tokens=100,
                temperature=0.7
            )

            reasoning = response.choices[0].message.content.strip()
            # Remove quotes if AI included them
            reasoning = reasoning.replace('"', '').replace("'", "")
            return reasoning

        except Exception as e:
            print(f"   [DEEPSEEK ERROR] {e}")
            return None

deepseek_engine = DeepSeekEngine()

if __name__ == "__main__":
    # Test call
    test_features = {"price": 50000, "rsi_value": 35, "trend": "BULLISH", "imbalance_ratio": 0.45}
    res = deepseek_engine.generate_deep_reasoning("BTC/USDT", "BUY", test_features)
    print(f"Test Reasoning: {res}")
