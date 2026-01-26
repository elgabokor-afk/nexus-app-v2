'use client';

import React, { useEffect, useRef } from 'react';

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

declare global {
    interface Window {
        TradingView: any;
    }
}

export const SmartChart: React.FC<SmartChartProps> = ({ symbol, signalData }) => {
    const containerRef = useRef<HTMLDivElement>(null);

    // Defensive: Return placeholder if no symbol
    if (!symbol) return <div className="w-full h-full flex items-center justify-center text-gray-700 text-xs">Waiting for Signal...</div>;

    useEffect(() => {
        // Dynamic Translation of Symbols (Standardizing for TV)
        // BTC/USD -> KRAKEN:XBTUSD
        // ETH/USD -> KRAKEN:ETHUSD
        // if no slash, assume crypto

        let tvSymbol = "KRAKEN:BTCUSD"; // Default

        if (symbol) {
            let clean = symbol.replace('/', '');
            if (clean.startsWith('BTC')) clean = clean.replace('BTC', 'XBT');
            if (clean.endsWith('USDT')) clean = clean.replace('USDT', 'USDT');

            tvSymbol = `KRAKEN:${clean}`;
        }

        const script = document.createElement('script');
        script.src = 'https://s3.tradingview.com/tv.js';
        script.async = true;
        script.onload = () => {
            if (window.TradingView && containerRef.current) {
                new window.TradingView.widget({
                    "autosize": true,
                    "symbol": tvSymbol,
                    "interval": "60",
                    "timezone": "Etc/UTC",
                    "theme": "dark",
                    "style": "1",
                    "locale": "en",
                    "enable_publishing": false,
                    "allow_symbol_change": true,
                    "container_id": containerRef.current.id,
                    "toolbar_bg": "#0a0a0c",
                    "hide_side_toolbar": false,
                    "studies": [
                        "RSI@tv-basicstudies",
                        "MASimple@tv-basicstudies"
                    ]
                });
            }
        };
        document.head.appendChild(script);

        return () => {
            // Cleanup schema if needed, though TV widget is heavy and self-contained
            if (script.parentNode) script.parentNode.removeChild(script);
        };
    }, [symbol]);

    return (
        <div className="relative w-full h-full border border-[#222] rounded-2xl overflow-hidden bg-[#050505] shadow-2xl">
            <div id={`tv_chart_container_${symbol.replace('/', '_')}`} ref={containerRef} className="w-full h-full" />
        </div>
    );
};
