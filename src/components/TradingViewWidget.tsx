"use client";

import React, { useEffect, useRef, memo } from 'react';

interface TradingViewWidgetProps {
    symbol: string;
    theme?: 'light' | 'dark';
    autosize?: boolean;
}

function TradingViewWidget({ symbol, theme = 'dark', autosize = true }: TradingViewWidgetProps) {
    const container = useRef<HTMLDivElement>(null);

    useEffect(() => {
        if (!container.current) return;

        // Clear previous if any (though React handles unmount, the script appends raw DOM)
        container.current.innerHTML = "";

        const script = document.createElement("script");
        script.src = "https://s3.tradingview.com/external-embedding/embed-widget-advanced-chart.js";
        script.type = "text/javascript";
        script.async = true;

        // Map Symbol to TradingView format
        // e.g. BTC/USDT -> BINANCE:BTCUSDT
        // If no slash, assume BINANCE default
        let tvSymbol = symbol.replace('/', '');
        if (!tvSymbol.includes(':')) {
            tvSymbol = `BINANCE:${tvSymbol}`;
        }

        script.innerHTML = JSON.stringify({
            "autosize": true,
            "symbol": tvSymbol,
            "interval": "15",
            "timezone": "Etc/UTC",
            "theme": theme,
            "style": "1",
            "locale": "en",
            "enable_publishing": false,
            "allow_symbol_change": true,
            "hide_side_toolbar": false,
            "calendar": false,
            "support_host": "https://www.tradingview.com"
        });

        container.current.appendChild(script);

    }, [symbol, theme]);

    return (
        <div className="tradingview-widget-container" ref={container} style={{ height: "100%", width: "100%" }}>
            <div className="tradingview-widget-container__widget" style={{ height: "100%", width: "100%" }}></div>
        </div>
    );
}

export default memo(TradingViewWidget);
