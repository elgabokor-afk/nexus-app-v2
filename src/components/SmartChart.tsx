"use client";

import React from 'react';
import TradingViewWidget from './TradingViewWidget';

interface SmartChartProps {
    symbol: string;
    signalData?: any; // Kept for interface compatibility, though Widget handles data itself
}

export const SmartChart: React.FC<SmartChartProps> = ({ symbol, signalData }) => {
    // Basic symbol sanitation just in case
    const cleanSymbol = symbol || "BTC/USDT";

    return (
        <div className="w-full h-full relative group bg-black rounded-lg overflow-hidden border border-[#2f3336]">
            {/* V1500: Replaced custom chart with TradingView Widget for 100% Reliability */}
            <TradingViewWidget symbol={cleanSymbol} theme="dark" />

            {/* Optional: Overlay Signal Info if needed */}
            {signalData && (
                <div className="absolute top-4 right-4 z-20 pointer-events-none bg-black/50 backdrop-blur-md px-3 py-1.5 rounded-lg border border-white/10">
                    <div className="flex flex-col items-end">
                        <span className={`text-xs font-bold ${signalData.signal_type === 'BUY' ? 'text-[#00ffa3]' : 'text-[#ff4d4d]'}`}>
                            {signalData.signal_type} @ {signalData.entry}
                        </span>
                        {signalData.take_profit && (
                            <span className="text-[10px] text-gray-400">TP: {signalData.take_profit}</span>
                        )}
                    </div>
                </div>
            )}
        </div>
    );
};

