
import os
from openai import OpenAI
from dotenv import load_dotenv

# Load env from parent directory
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
load_dotenv(dotenv_path=os.path.join(parent_dir, '.env.local'))

class OpenAIEngine:
    def __init__(self):
        self.api_key = os.getenv("OPENAI_API_KEY")
        self.client = None
        if self.api_key:
            self.client = OpenAI(api_key=self.api_key)
            print("   [OPENAI] Engine Initialized.")
        else:
            print("   [OPENAI] Warning: OPENAI_API_KEY missing in .env.local")

    def generate_trade_narrative(self, symbol, signal_type, features):
        """
        Generates high-fidelity trading reasoning using OpenAI GPT-4o-mini.
        """
        if not self.client:
            return None

        try:
            prompt = f"""
            Act as a Lead Strategy Quant in a global macro fund.
            Interpret this crypto signal for {symbol} with institutional precision.
            Maximum length: 140 characters. No fluff.
            
            Signal: {signal_type}
            Price: {features.get('price', 'N/A')}
            RSI: {features.get('rsi_value', 'N/A')}
            EMA 200 Position: {features.get('trend', 'N/A')}
            Order Book Imbalance: {features.get('imbalance_ratio', 'N/A')}
            SMC Details: {features.get('smc_details', 'Detecting...')}
            
            Provide a direct, high-conviction institutional thesis.
            """

            try:
                response = self.client.chat.completions.create(
                    model="gpt-5-nano",
                    messages=[
                        {"role": "system", "content": "You provide sharp, concise crypto trading insights like a Bloomberg terminal."},
                        {"role": "user", "content": prompt},
                    ],
                    max_completion_tokens=60,
                    temperature=0.5
                )
            except Exception as ml_err:
                 print(f"   [OPENAI WARN] GPT-5 Nano unavailable ({ml_err}). Falling back to GPT-4o-mini.")
                 response = self.client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[
                        {"role": "system", "content": "You provide sharp, concise crypto trading insights like a Bloomberg terminal."},
                        {"role": "user", "content": prompt},
                    ],
                    max_completion_tokens=60,
                    temperature=0.5
                )

            narrative = response.choices[0].message.content.strip()
            return narrative.replace('"', '').replace("'", "")

        except Exception as e:
            print(f"   [OPENAI ERROR] {e}")
            return None

openai_engine = OpenAIEngine()

if __name__ == "__main__":
    # Test call
    test_features = {"price": 105000, "rsi_value": 28, "trend": "BULLISH", "imbalance_ratio": 0.55}
    res = openai_engine.generate_trade_narrative("BTC/USDT", "STRONG BUY", test_features)
    print(f"Test Narrative: {res}")
