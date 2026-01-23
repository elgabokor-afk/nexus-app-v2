import { NextResponse } from 'next/server';

export async function GET(request: Request) {
    const { searchParams } = new URL(request.url);
    const symbol = searchParams.get('symbol');

    if (!symbol) {
        return NextResponse.json({ error: 'Symbol required' }, { status: 400 });
    }

    try {
        // Map Symbol to Kraken Pair
        let pair = symbol.replace('/', '');
        if (pair.startsWith('BTC')) pair = pair.replace('BTC', 'XBT');
        if (pair.endsWith('USDT')) pair = pair.replace('USDT', 'USDT');

        // Fetch from Kraken (Server-side, no CORS issues)
        const response = await fetch(`https://api.kraken.com/0/public/OHLC?pair=${pair}&interval=60`, {
            headers: {
                'User-Agent': 'NexusAI/1.0'
            },
            next: { revalidate: 60 } // Cache for 60 seconds
        });

        const data = await response.json();

        return NextResponse.json(data);
    } catch (error) {
        console.error("Proxy Error:", error);
        return NextResponse.json({ error: 'Failed to fetch data' }, { status: 500 });
    }
}
