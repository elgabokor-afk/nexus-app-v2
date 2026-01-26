'use client';

import { createChart, ColorType, ISeriesApi, AreaSeries } from 'lightweight-charts';
import React, { useEffect, useRef, useState } from 'react';
import { useLiveStream } from '@/hooks/useLiveStream'; // V900

interface ChartProps {
    data: { time: string | number; value: number }[];
    colors?: {
        backgroundColor?: string;
        lineColor?: string;
        textColor?: string;
        areaTopColor?: string;
        areaBottomColor?: string;
    };
}

export const ChartComponent: React.FC<ChartProps> = (props) => {
    const {
        data = [], // Defensive default
        colors: {
            backgroundColor = 'transparent',
            lineColor = '#00ffa3',
            textColor = '#DDD',
            areaTopColor = 'rgba(0, 255, 163, 0.4)',
            areaBottomColor = 'rgba(0, 255, 163, 0.0)',
        } = {},
    } = props;

    const chartContainerRef = useRef<HTMLDivElement>(null);
    const seriesRef = useRef<ISeriesApi<"Area"> | null>(null);
    const { lastMessage } = useLiveStream(["live_prices"]);

    useEffect(() => {
        if (lastMessage && lastMessage.channel === "live_prices" && seriesRef.current) {
            const { price, time } = lastMessage.data;
            // Append new point
            seriesRef.current.update({
                time: time,
                value: price
            });
        }
    }, [lastMessage]);

    useEffect(() => {
        if (!chartContainerRef.current) return;

        const handleResize = () => {
            chart.applyOptions({ width: chartContainerRef.current!.clientWidth });
        };

        const chart = createChart(chartContainerRef.current, {
            layout: {
                background: { type: ColorType.Solid, color: backgroundColor },
                textColor,
            },
            width: chartContainerRef.current.clientWidth,
            height: 300,
            grid: {
                vertLines: { color: 'rgba(42, 46, 57, 0.5)' },
                horzLines: { color: 'rgba(42, 46, 57, 0.5)' },
            },
        });

        chart.timeScale().fitContent();

        const newSeries = chart.addSeries(AreaSeries, {
            lineColor,
            topColor: areaTopColor,
            bottomColor: areaBottomColor,
        });

        seriesRef.current = newSeries;

        if (data && data.length > 0) {
            newSeries.setData(data as any);
        }

        const resizeObserver = new ResizeObserver(handleResize);
        resizeObserver.observe(chartContainerRef.current);

        return () => {
            resizeObserver.disconnect();
            chart.remove();
            seriesRef.current = null;
        };
    }, [data, backgroundColor, lineColor, textColor, areaTopColor, areaBottomColor]);

    return <div ref={chartContainerRef} className="w-full h-[300px]" />;
};
