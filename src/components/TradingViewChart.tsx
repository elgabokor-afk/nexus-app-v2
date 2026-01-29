"use client";

import { useEffect, useRef } from 'react';
import { createChart, ColorType, CrosshairMode, IChartApi, CandlestickSeries } from 'lightweight-charts';

interface ChartProps {
    data: { time: string; open: number; high: number; low: number; close: number }[];
    entryPrice?: number;
    tpPrice?: number;
    slPrice?: number;
    height?: number;
}

export default function TradingViewChart({ data, entryPrice, tpPrice, slPrice, height = 300 }: ChartProps) {
    const chartContainerRef = useRef<HTMLDivElement>(null);
    const chartRef = useRef<IChartApi | null>(null);

    useEffect(() => {
        if (!chartContainerRef.current) return;

        // Initialize Chart
        const chart = createChart(chartContainerRef.current, {
            layout: {
                background: { type: ColorType.Solid, color: '#000000' },
                textColor: '#d1d5db',
            },
            width: chartContainerRef.current.clientWidth,
            height: height,
            grid: {
                vertLines: { color: '#333333' },
                horzLines: { color: '#333333' },
            },
            crosshair: {
                mode: CrosshairMode.Normal,
            },
            rightPriceScale: {
                borderColor: '#485c7b',
            },
            timeScale: {
                borderColor: '#485c7b',
                timeVisible: true,
            },
        });

        chartRef.current = chart;

        // Add Candlestick Series (v5 Syntax)
        const candleSeries = chart.addSeries(CandlestickSeries, {
            upColor: '#00ffa3', // Nexus Green
            downColor: '#ef4444', // Red
            borderVisible: false,
            wickUpColor: '#00ffa3',
            wickDownColor: '#ef4444',
        });

        if (data && data.length > 0) {
            // Sort data by time just in case
            const sortedData = [...data].sort((a, b) => new Date(a.time).getTime() - new Date(b.time).getTime());
            candleSeries.setData(sortedData);
        }

        // Add Lines (Entry, TP, SL)
        // We use PriceLines for this
        if (entryPrice) {
            candleSeries.createPriceLine({
                price: entryPrice,
                color: '#fbbf24', // Amber
                lineWidth: 2,
                lineStyle: 1, // Dotted
                axisLabelVisible: true,
                title: 'ENTRY',
            });
        }

        if (tpPrice) {
            candleSeries.createPriceLine({
                price: tpPrice,
                color: '#00ffa3', // Green
                lineWidth: 2,
                lineStyle: 0, // Solid
                axisLabelVisible: true,
                title: 'TP',
            });
        }

        if (slPrice) {
            candleSeries.createPriceLine({
                price: slPrice,
                color: '#ef4444', // Red
                lineWidth: 2,
                lineStyle: 0, // Solid
                axisLabelVisible: true,
                title: 'SL',
            });
        }

        // Resize Observer
        const handleResize = () => {
            if (chartContainerRef.current) {
                chart.applyOptions({ width: chartContainerRef.current.clientWidth });
            }
        };

        window.addEventListener('resize', handleResize);

        return () => {
            window.removeEventListener('resize', handleResize);
            chart.remove();
        };
    }, [data, entryPrice, tpPrice, slPrice, height]);

    return (
        <div className="relative w-full border border-white/10 rounded-lg overflow-hidden shadow-2xl">
            {/* Watermark */}
            <div className="absolute top-4 left-4 z-10 opacity-20 pointer-events-none">
                <span className="text-4xl font-black text-white tracking-tighter">NEXUS</span>
            </div>
            <div ref={chartContainerRef} />
        </div>
    );
}
