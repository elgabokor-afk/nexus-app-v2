
'use client';

import React from 'react';
import {
    LineChart,
    Line,
    XAxis,
    YAxis,
    CartesianGrid,
    Tooltip,
    ResponsiveContainer,
    Area,
    AreaChart
} from 'recharts';

interface LearningCurveProps {
    data: any[]; // Array of historical performance points
}

const LearningCurve: React.FC<LearningCurveProps> = ({ data }) => {
    if (!data || data.length === 0) {
        return (
            <div className="flex h-full items-center justify-center text-gray-500">
                <p className="text-sm">No performance data yet</p>
            </div>
        );
    }

    // Format data for chart if needed, or assume it's passed correctly
    // Expecting: { timestamp: string, equity: number }

    return (
        <div className="h-full w-full p-2">
            <ResponsiveContainer width="100%" height="100%">
                <AreaChart data={data}>
                    <defs>
                        <linearGradient id="colorEquity" x1="0" y1="0" x2="0" y2="1">
                            <stop offset="5%" stopColor="#10B981" stopOpacity={0.3} />
                            <stop offset="95%" stopColor="#10B981" stopOpacity={0} />
                        </linearGradient>
                    </defs>
                    <CartesianGrid strokeDasharray="3 3" stroke="#374151" opacity={0.5} />
                    <XAxis
                        dataKey="timestamp"
                        hide={true}
                    />
                    <YAxis
                        domain={['auto', 'auto']}
                        orientation="right"
                        tick={{ fill: '#9CA3AF', fontSize: 10 }}
                        tickFormatter={(value) => `$${value}`}
                        stroke="#374151"
                    />
                    <Tooltip
                        contentStyle={{ backgroundColor: '#1F2937', borderColor: '#374151' }}
                        itemStyle={{ color: '#E5E7EB' }}
                        formatter={(value: number) => [`$${value.toFixed(2)}`, 'Equity']}
                    />
                    <Area
                        type="monotone"
                        dataKey="equity"
                        stroke="#10B981"
                        fillOpacity={1}
                        fill="url(#colorEquity)"
                    />
                </AreaChart>
            </ResponsiveContainer>
        </div>
    );
};

export default LearningCurve;
