'use client';

import { createChart, ColorType, ISeriesApi, AreaSeries } from 'lightweight-charts';
import React, { useEffect, useRef } from 'react';

interface ChartProps {
    data: { time: string; value: number }[];
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
        data,
        colors: {
            backgroundColor = 'transparent',
            lineColor = '#00ffa3',
            textColor = '#DDD',
            areaTopColor = 'rgba(0, 255, 163, 0.4)',
            areaBottomColor = 'rgba(0, 255, 163, 0.0)',
        } = {},
    } = props;

    const chartContainerRef = useRef<HTMLDivElement>(null);

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

        // Format data for chart
        // Note: Lightweight charts expects time as string 'yyyy-mm-dd' or unix timestamp
        // For this MVP demo, we assume data is formatted correctly or we might need to map it.
        // If data comes as full timestamp strings, we might need to convert.
        // For simplicity, let's assume the parent passes correct data or we just pass it through.
        if (data && data.length > 0) {
            newSeries.setData(data as any);
        }

        const resizeObserver = new ResizeObserver(handleResize);
        resizeObserver.observe(chartContainerRef.current);

        return () => {
            resizeObserver.disconnect();
            chart.remove();
        };
    }, [data, backgroundColor, lineColor, textColor, areaTopColor, areaBottomColor]);

    return <div ref={chartContainerRef} className="w-full h-[300px]" />;
};
