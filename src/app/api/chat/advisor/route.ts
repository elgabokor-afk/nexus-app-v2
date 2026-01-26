
import { NextResponse } from 'next/server';

// V1800: Proxy to Cosmos AI (Python Engine)
// The "Brain" has moved to data-engine/cosmos_agent.py

export async function POST(req: Request) {
    try {
        const body = await req.json();

        // 1. Forward request to Python Service (Localhost default)
        const pythonUrl = process.env.PYTHON_API_URL || 'http://127.0.0.1:8000';

        try {
            const res = await fetch(`${pythonUrl}/chat`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(body)
            });

            if (!res.ok) throw new Error(`Cosmos Error: ${res.statusText}`);

            const data = await res.json();
            return NextResponse.json(data);

        } catch (fetchError) {
            console.error("Cosmos Bridge Error:", fetchError);
            // Fallback response if Python is offline
            return NextResponse.json({
                reply: "⚠️ One moment - The Neural Link (Python Engine) is offline. Please start `websocket_bridge.py`.",
                agent: "System Monitor"
            });
        }

    } catch (error) {
        console.error("API Route Error:", error);
        return NextResponse.json(
            { error: "Internal Relay Error" },
            { status: 500 }
        );
    }
}
