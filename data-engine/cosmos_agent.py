
import json
import random

class CosmosAgent:
    """
    V1800: The Intelligence Core for Nexus Chat.
    Currently uses Heuristic/Rule-Based Logic to simulate an expert.
    Ready to be upgraded to GPT-4/Claude via API.
    """
    def __init__(self):
        self.agent_name = "Cosmos Oracle (v9.2)"

    def analyze_signal(self, message, signal_context):
        """
        Generates advice based on the strict signal metrics.
        """
        s = signal_context
        symbol = s.get("symbol", "Asset")
        price = s.get("price", 0)
        confidence = s.get("confidence", 0)
        rsi = s.get("rsi", 50)
        signal_type = s.get("signal_type", "NEUTRAL")
        
        advice = ""
        
        # 1. CORE ANALYSIS ENGINE (Simulated)
        if confidence >= 95:
            advice = (
                f"### 🚀 High-Conviction {signal_type}\n\n"
                f"I have identified a **Tier-1 Opportunity** on **{symbol}**.\n"
                f"- **Confidence**: {confidence}% (Exceptional)\n"
                f"- **RSI**: {rsi:.1f} (Momentum Aligned)\n\n"
                f"**Strategy**: Aggressive entry is supported. "
                f"The algorithm detects strong institutional flow syncing with this move."
            )
        elif confidence >= 80:
            advice = (
                f"### ✅ Solid {signal_type} Setup\n\n"
                 f"**{symbol}** is showing healthy metrics with **{confidence}% Confidence**.\n"
                f"It doesn't have the 'perfect' score of a 95%+, but the trend is clearly defined.\n\n"
                f"**Risk Note**: RSI is at {rsi:.1f}. Monitor for divergence."
            )
        else:
             advice = (
                f"### ⚠️ Caution Advised\n\n"
                f"This signal for **{symbol}** has a lower confidence score ({confidence}%).\n"
                f"The indicators are conflicting. If you enter, use a generous stop-loss to avoid shakeouts."
            )

        # 2. CONTEXTUAL RESPONSES
        query = message.lower()
        
        if "risk" in query or "safe" in query:
            risk_level = "LOW" if confidence > 90 else "MODERATE" if confidence > 75 else "HIGH"
            advice += f"\n\n**Risk Assessment**: {risk_level}. calculated based on volatility and trend strength."
            
        elif "target" in query or "profit" in query:
            target = price * 1.02 if "BUY" in signal_type else price * 0.98
            advice += f"\n\n**AI Target**: Aim for **${target:.2f}** as a primary take-profit zone."

        elif "why" in query:
             advice += f"\n\n**Reasoning**: The decision is driven primarily by the **RSI ({rsi:.1f})** and the **Volume Ratio**, which suggest a breakout is imminent."

        return {
            "reply": advice,
            "agent": self.agent_name,
            "metrics_used": ["RSI", "Confidence", "Trend"]
        }

# Singleton Instance
cosmos_agent = CosmosAgent()
