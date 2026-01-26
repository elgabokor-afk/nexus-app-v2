
import { NextResponse } from 'next/server';

// V1600: Simulated "Deep Brain" Expert
// In a production env with API Keys, this would call OpenAI/Anthropic.
// For now, we simulate a sophisticated analysis based on the signal data.

export async function POST(req: Request) {
    try {
        const { message, signalContext } = await req.json();

        // mimic network latency for realism
        await new Promise(resolve => setTimeout(resolve, 1500));

        let advice = "";
        const s = signalContext;

        // 1. Context Awareness Logic
        if (s.confidence === 100) {
            advice = `This is a **High-Conviction Play**. The **${s.symbol}** signal has achieved a perfect **100% Confidence Score**, which is rare. 

**My Analysis:**
- **Trend**: The underlying trend is strongly **${s.signal_type.includes('BUY') ? 'BULLISH' : 'BEARISH'}**.
- **Timing**: RSI is at ${s.rsi.toFixed(1)}, suggesting decent momentum.
- **Risk**: While confidence is maxed, always use a **Stop Loss**.

**Recommendation**: This aligns with an aggressive entry strategy. Closely monitor for a breakout above ${s.price}.`;
        } else if (s.confidence > 80) {
            advice = `The setup for **${s.symbol}** looks solid with **${s.confidence}% Confidence**.

**Key Metrics:**
- **RSI**: ${s.rsi.toFixed(1)} (Neutral-Bullish)
- **Signal**: ${s.signal_type}
- **Volatility**: Average True Range is stable.

It's a good trade, but keep your position size moderate. It doesn't have the "perfect storm" indicators of a 100% signal, but the math favors this direction.`;
        } else {
            advice = `Exercise caution with **${s.symbol}** (Confidence: ${s.confidence}%).

The indicators are mixed. The algorithm sees potential, but there is significant noise in the price action. 
**Strategy**: If you enter, use a **tight stop loss** and take profit quickly. Do not hold this swing for too long.`;
        }

        // 2. Handle specific user questions (Simple Keyword Matching for V1)
        const lowerMsg = message.toLowerCase();
        if (lowerMsg.includes("risk") || lowerMsg.includes("safe")) {
            advice = `**Risk Assessment**:
Based on the current volatility (${s.symbol}), the risk factor is **${s.confidence > 90 ? 'LOW' : 'MODERATE'}**.
Suggest setting Stop Loss at **$${(s.price * 0.98).toFixed(2)}** (-2%).`;
        } else if (lowerMsg.includes("target") || lowerMsg.includes("profit")) {
            advice = `**Profit Targets**:
1. Conservative: **$${(s.price * 1.015).toFixed(2)}** (Scalp)
2. Extended: **$${(s.price * 1.04).toFixed(2)}** (Swing)
Manage your greed—take partial profits at target 1.`;
        }

        return NextResponse.json({
            reply: advice,
            agent: "Nexus Prime (v9.0)"
        });

    } catch (error) {
        console.error("AI Advisor Error:", error);
        return NextResponse.json(
            { error: "Neural Link Unstable. Try again." },
            { status: 500 }
        );
    }
}
