"use client";

import React, { useEffect, useState } from 'react';
import TradingViewChart from './TradingViewChart';

interface SmartChartProps {
    symbol: string;
    signalData?: {
        entry: number;
        stop_loss?: number;
        take_profit?: number;
        confidence: number;
        signal_type: string;
    } | null;
}

export const SmartChart: React.FC<SmartChartProps> = ({ symbol, signalData }) => {
    const [candleData, setCandleData] = useState<any[]>([]);
    const [loading, setLoading] = useState(false);

    useEffect(() => {
        if (!symbol) return;

        const fetchCandles = async () => {
            setLoading(true);
            try {
                // Convert symbol for Binance (BTC/USD -> BTCUSDT)
                let clean = symbol.replace('/', '').replace('USD', 'USDT');
                if (!clean.endsWith('USDT')) clean += 'USDT';

                const res = await fetch(`https://api.binance.com/api/v3/klines?symbol=${clean}&interval=15m&limit=100`);
                const data = await res.json();

                if (Array.isArray(data)) {
                    const formatted = data.map((d: any) => ({
                        time: new Date(d[0]).toISOString().split('T')[0], // Lightweight charts uses YYYY-MM-DD or Unix
                        value: d[0] / 1000,
                        open: parseFloat(d[1]),
                        high: parseFloat(d[2]),
                        low: parseFloat(d[3]),
                        close: parseFloat(d[4]),
                    })).map(c => ({
                        time: c.value as any, // Passing unix timestamp (number)
                        open: c.open,
                        high: c.high,
                        low: c.low,
                        close: c.close
                    }));
                    setCandleData(formatted);
                }
            } catch (err) {
                console.error("Failed to fetch candle data:", err);
            } finally {
                setLoading(false);
            }
        };

        fetchCandles();
        // Refresh every 60s
        const interval = setInterval(fetchCandles, 60000);
        return () => clearInterval(interval);

    }, [symbol]);

    if (loading && candleData.length === 0) {
        return (
            <div className="w-full h-full flex items-center justify-center bg-[#050505] border border-[#2f3336] rounded-2xl">
                <span className="text-[#00ffa3] font-mono text-xs animate-pulse">LOADING MARKET DATA...</span>
            </div>
        );
    }

    return (
        <div className="w-full h-full relative group">
            {/* Header Overlay */}
            <div className="absolute top-4 left-4 z-20 flex flex-col pointer-events-none">
                <h2 className="text-2xl font-black text-white tracking-tighter">{symbol}</h2>
                <span className="text-[10px] text-gray-500 font-bold uppercase tracking-widest">15M INTERVAL • LIVE</span>
            </div>

            <TradingViewChart
                data={candleData}
                entryPrice={signalData?.entry}
                tpPrice={signalData?.take_profit}
                slPrice={signalData?.stop_loss}
                height={500}
            />
        </div>
    );
};
