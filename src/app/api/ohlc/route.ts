import { NextResponse } from 'next/server';

export async function GET(request: Request) {
    const { searchParams } = new URL(request.url);
    const symbol = searchParams.get('symbol'); // e.g., BTC/USDT

    if (!symbol) {
        return NextResponse.json({ error: 'Symbol required' }, { status: 400 });
    }

    try {
        // 1. Try Binance (Preferred for accuracy)
        // If Vercel region is blocked, this will fail fast.
        try {
            const cleanSymbol = symbol.replace('/', '');
            const binUrl = `https://api.binance.com/api/v3/klines?symbol=${cleanSymbol}&interval=1h&limit=100`;
            const binRes = await fetch(binUrl, { next: { revalidate: 60 } });

            if (binRes.ok) {
                const data = await binRes.json();
                // [time, open, high, low, close, vol, ...]
                // Map to Chart Format: { time: 'yyyy-mm-dd', open, high, low, close }
                const formatted = data.map((d: any) => ({
                    time: new Date(d[0]).toISOString().split('T')[0], // Lightweight charts likes YYYY-MM-DD or Unix
                    // Actually, for Intraday, timestamp is better?
                    // Lightweight charts handles Unix timestamp if we pass it as 'number' type time
                    // But here we return standard structure.
                    // Let's stick to simple mapping.
                    open: parseFloat(d[1]),
                    high: parseFloat(d[2]),
                    low: parseFloat(d[3]),
                    close: parseFloat(d[4]),
                }));
                // Add timestamp to each
                const final = formatted.map((item: any, i: number) => ({
                    ...item,
                    time: new Date(data[i][0]).toISOString().slice(0, 10), // Daily format for now, or use unix
                }));
                // Fix: Lightweight Charts expects specific time format. 
                // If 1h candles, YYYY-MM-DD isn't enough?
                // Actually passing UNIX timestamp (seconds) is best for intraday.
                const unixFormatted = data.map((d: any) => ({
                    time: d[0] / 1000, // Seconds
                    open: parseFloat(d[1]),
                    high: parseFloat(d[2]),
                    low: parseFloat(d[3]),
                    close: parseFloat(d[4]),
                }));

                return NextResponse.json(unixFormatted);
            }
        } catch (e) {
            console.warn("Binance OHLC failed:", e);
        }

        // 2. Fallback: CoinGecko (Reliable, no Geo-Block)
        try {
            // Map Symbol -> ID
            let id = 'bitcoin';
            const base = symbol.split('/')[0].toLowerCase();
            if (base === 'eth') id = 'ethereum';
            if (base === 'sol') id = 'solana';
            if (base === 'bnb') id = 'binance-coin';
            if (base === 'xrp') id = 'ripple';
            if (base === 'doge') id = 'dogecoin';
            if (base === 'ada') id = 'cardano';
            if (base === 'avax') id = 'avalanche-2';

            // OHLC Endpoint: Days = 1 (30 min Interval approx) or Days = 7 (4h)
            const cgUrl = `https://api.coingecko.com/api/v3/coins/${id}/ohlc?vs_currency=usd&days=1`;
            const cgRes = await fetch(cgUrl, {
                headers: { 'User-Agent': 'NexusAI/1.0' },
                next: { revalidate: 120 }
            });

            if (cgRes.ok) {
                const data = await cgRes.json();
                // [time(ms), open, high, low, close]
                const formatted = data.map((d: any) => ({
                    time: d[0] / 1000,
                    open: d[1],
                    high: d[2],
                    low: d[3],
                    close: d[4]
                }));
                return NextResponse.json(formatted);
            }
        } catch (e) {
            console.warn("CoinGecko OHLC failed:", e);
        }

        return NextResponse.json({ error: 'All data sources failed' }, { status: 500 });
    } catch (error) {
        return NextResponse.json({ error: 'Internal Server Error' }, { status: 500 });
    }
}
