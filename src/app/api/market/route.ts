import { NextResponse } from 'next/server';

export async function GET() {
    const API_KEY = process.env.CMC_PRO_API_KEY;

    if (!API_KEY) {
        return NextResponse.json({ error: 'API Key missing' }, { status: 500 });
    }

    try {
        const res = await fetch('https://pro-api.coinmarketcap.com/v1/cryptocurrency/listings/latest?start=1&limit=100&convert=USD', {
            headers: {
                'X-CMC_PRO_API_KEY': API_KEY,
            },
            next: { revalidate: 60 } // Cache for 60 seconds
        });

        if (!res.ok) {
            const errorData = await res.json();
            return NextResponse.json(errorData, { status: res.status });
        }

        const data = await res.json();
        return NextResponse.json(data);
    } catch (error) {
        return NextResponse.json({ error: 'Internal Server Error' }, { status: 500 });
    }
}
