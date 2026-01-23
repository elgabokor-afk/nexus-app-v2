
'use client';

import { createChart, ColorType, IChartApi, ISeriesApi } from 'lightweight-charts';
import React, { useEffect, useRef, useState } from 'react';

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
    const chartContainerRef = useRef<HTMLDivElement>(null);
    const chartRef = useRef<IChartApi | null>(null);
    const seriesRef = useRef<ISeriesApi<"Candlestick"> | null>(null);

    // Fetch Data from Kraken
    useEffect(() => {
        if (!symbol) return;

        const fetchData = async () => {
            try {
                // Map Symbol to Kraken Pair
                // BTC/USD -> XBTUSD, ETH/USD -> ETHUSD
                let pair = symbol.replace('/', '');
                if (pair.startsWith('BTC')) pair = pair.replace('BTC', 'XBT');
                if (pair.endsWith('USDT')) pair = pair.replace('USDT', 'USDT'); // Kraken uses USDT sometimes

                const response = await fetch(`https://api.kraken.com/0/public/OHLC?pair=${pair}&interval=60`);
                const result = await response.json();

                if (result.error && result.error.length > 0) {
                    console.error("Kraken Error:", result.error);
                    return;
                }

                // Extract OHLC
                const keys = Object.keys(result.result);
                const key = keys.find(k => k !== 'last');
                if (!key) return;

                const candles = result.result[key].map((item: any) => ({
                    time: item[0], // Unix timestamp
                    open: parseFloat(item[1]),
                    high: parseFloat(item[2]),
                    low: parseFloat(item[3]),
                    close: parseFloat(item[4]),
                }));

                // Update Series
                if (seriesRef.current) {
                    seriesRef.current.setData(candles);
                }
            } catch (err) {
                console.error("Chart Data Fetch Error:", err);
            }
        };

        fetchData();
        const interval = setInterval(fetchData, 60000); // Live update
        return () => clearInterval(interval);

    }, [symbol]);

    // Initialize Chart
    useEffect(() => {
        if (!chartContainerRef.current) return;

        const chart = createChart(chartContainerRef.current, {
            layout: {
                background: { type: ColorType.Solid, color: '#050505' },
                textColor: '#999',
            },
            grid: {
                vertLines: { color: '#111' },
                horzLines: { color: '#111' },
            },
            width: chartContainerRef.current.clientWidth,
            height: 500,
            timeScale: {
                timeVisible: true,
                secondsVisible: false,
            },
        });

        const newSeries = chart.addCandlestickSeries({
            upColor: '#00ffa3', // Green
            downColor: '#ff4d4d', // Red
            borderVisible: false,
            wickUpColor: '#00ffa3',
            wickDownColor: '#ff4d4d',
        });

        chartRef.current = chart;
        seriesRef.current = newSeries;

        const handleResize = () => {
            chart.applyOptions({ width: chartContainerRef.current?.clientWidth });
        };

        window.addEventListener('resize', handleResize);

        return () => {
            window.removeEventListener('resize', handleResize);
            chart.remove();
        };
    }, []);

    // Draw Signal Lines
    useEffect(() => {
        if (!seriesRef.current || !signalData) return;

        // Clear existing lines (not directly supported by API easily without keeping track, 
        // but creating a new series or resetting logic is complex. 
        // Lightweight charts keeps lines until manually removed. 
        // For V1 simplicty, we rely on the chart re-render if needed or just add them.
        // Actually, best way is to remove primitive, but we don't have refs to them easily here.
        // Let's rely on component unmount/remount for totally clean state if symbol changes drastically, 
        // but here we just add lines.)

        // Note: In a production app, we would track the priceLines objects to remove() them.
        // For now, simpler to just add them. 

        // 1. ENTRY PRICE
        seriesRef.current.createPriceLine({
            price: signalData.entry,
            color: '#ffffff',
            lineWidth: 2,
            lineStyle: 2, // Dashed
            axisLabelVisible: true,
            title: 'ENTRY',
        });

        // 2. STOP LOSS
        if (signalData.stop_loss) {
            seriesRef.current.createPriceLine({
                price: signalData.stop_loss,
                color: '#ff4d4d',
                lineWidth: 2,
                lineStyle: 0, // Solid
                axisLabelVisible: true,
                title: 'STOP LOSS',
            });
        }

        // 3. TAKE PROFIT
        if (signalData.take_profit) {
            seriesRef.current.createPriceLine({
                price: signalData.take_profit,
                color: '#00ffa3',
                lineWidth: 2,
                lineStyle: 0, // Solid
                axisLabelVisible: true,
                title: 'TAKE PROFIT',
            });
        }

    }, [signalData]); // Re-run when signal data changes

    return (
        <div className="relative w-full h-[500px] border border-[#222] rounded-2xl overflow-hidden bg-[#050505]">
            {/* Confidence Overlay */}
            {signalData && (
                <div className="absolute top-4 left-4 z-20 bg-[#111]/90 backdrop-blur border border-[#333] px-4 py-2 rounded-lg shadow-xl">
                    <p className="text-xs text-gray-400 font-mono">SIGNAL CONFIDENCE</p>
                    <div className="flex items-center gap-2">
                        <div className={`w-2 h-2 rounded-full ${signalData.confidence > 80 ? 'bg-[#00ffa3]' : 'bg-yellow-500'}`}></div>
                        <span className="text-xl font-bold text-white">{signalData.confidence}%</span>
                    </div>
                </div>
            )}
            <div ref={chartContainerRef} className="w-full h-full" />
        </div>
    );
};
