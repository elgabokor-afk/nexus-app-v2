'use client';

import { useEffect, useState } from 'react';
import { createClient } from '@supabase/supabase-js';
import { AreaChart, Area, XAxis, YAxis, Tooltip, ResponsiveContainer } from 'recharts';
import { TrendingUp, TrendingDown, Activity, DollarSign } from 'lucide-react';

// Initialize Supabase Client
const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL!;
const supabaseKey = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!;
const supabase = createClient(supabaseUrl, supabaseKey);

interface Stats {
    total_trades: number;
    winning_trades: number;
    losing_trades: number;
    total_pnl: number;
    win_rate: number;
}

interface Trade {
    id: number;
    realized_pnl: number;
    created_at: string;
}

export default function PerformanceStats() {
    const [stats, setStats] = useState<Stats | null>(null);
    const [maxDrawdown, setMaxDrawdown] = useState<number>(0);
    const [chartData, setChartData] = useState<any[]>([]);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        fetchStats();
        // Subscribe to changes for real-time updates
        const channel = supabase
            .channel('performance_updates')
            .on('postgres_changes', { event: 'INSERT', schema: 'public', table: 'paper_trades' }, () => {
                fetchStats();
            })
            .on('postgres_changes', { event: 'UPDATE', schema: 'public', table: 'paper_trades' }, () => {
                fetchStats();
            })
            .subscribe();

        return () => {
            supabase.removeChannel(channel);
        };
    }, []);

    const fetchStats = async () => {
        try {
            // 1. Fetch Summary View
            const { data: viewData, error: viewError } = await supabase
                .from('performance_stats')
                .select('*')
                .single();

            if (viewError) throw viewError;
            setStats(viewData);

            // 2. Fetch Recent Trades for Drawdown & Chart
            const { data: trades, error: tradesError } = await supabase
                .from('paper_trades')
                .select('id, realized_pnl, created_at')
                .eq('bot_status', 'CLOSED')
                .order('created_at', { ascending: true }) // Ascending for chart build
                .limit(100);

            if (tradesError) throw tradesError;

            if (trades && trades.length > 0) {
                // Calculate Max Consecutive Loss Streak
                let maxStreak = 0;
                let currentStreak = 0;

                trades.forEach(t => {
                    if (t.realized_pnl < 0) {
                        currentStreak++;
                        if (currentStreak > maxStreak) maxStreak = currentStreak;
                    } else {
                        currentStreak = 0;
                    }
                });
                setMaxDrawdown(maxStreak);

                // Build Chart Data (Cumulative PnL)
                let cumulative = 0;
                const history = trades.map(t => {
                    cumulative += t.realized_pnl;
                    return {
                        id: t.id,
                        pnl: cumulative,
                        date: new Date(t.created_at).toLocaleTimeString()
                    };
                });
                setChartData(history);
            }
        } catch (err) {
            console.error("Error fetching stats:", err);
        } finally {
            setLoading(false);
        }
    };

    if (loading) return <div className="p-6 text-center text-gray-500 animate-pulse">Loading Analytics...</div>;

    return (
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4 p-6 w-full">
            {/* WIN RATE */}
            <div className="bg-black/40 border border-white/5 rounded-2xl p-4 flex flex-col justify-between">
                <div className="flex items-center gap-2 mb-2">
                    <Activity size={16} className="text-[#00ffa3]" />
                    <span className="text-[10px] font-black text-gray-500 uppercase tracking-widest">Win Rate</span>
                </div>
                <div className="text-2xl font-black text-white font-mono">
                    {stats?.win_rate ?? 0}%
                </div>
                <div className="text-[10px] text-gray-400 mt-1">
                    {stats?.winning_trades} Wins / {stats?.total_trades} Total
                </div>
            </div>

            {/* TOTAL PROFIT */}
            <div className="bg-black/40 border border-white/5 rounded-2xl p-4 flex flex-col justify-between">
                <div className="flex items-center gap-2 mb-2">
                    <DollarSign size={16} className="text-[#00ffa3]" />
                    <span className="text-[10px] font-black text-gray-500 uppercase tracking-widest">Total Profit</span>
                </div>
                <div className={`text-2xl font-black font-mono ${(stats?.total_pnl || 0) >= 0 ? 'text-[#00ffa3]' : 'text-red-500'}`}>
                    ${stats?.total_pnl?.toLocaleString(undefined, { minimumFractionDigits: 2 }) ?? '0.00'}
                </div>
                <div className="text-[10px] text-gray-400 mt-1">
                    Realized PnL
                </div>
            </div>

            {/* MAX DRAWDOWN (STREAK) */}
            <div className="bg-black/40 border border-white/5 rounded-2xl p-4 flex flex-col justify-between">
                <div className="flex items-center gap-2 mb-2">
                    <TrendingDown size={16} className="text-orange-500" />
                    <span className="text-[10px] font-black text-gray-500 uppercase tracking-widest">Max Loss Streak</span>
                </div>
                <div className="text-2xl font-black text-white font-mono">
                    {maxDrawdown} <span className="text-sm text-gray-500 font-bold">Trades</span>
                </div>
                <div className="text-[10px] text-gray-400 mt-1">
                    Consecutive Losses
                </div>
            </div>

            {/* CHART */}
            <div className="bg-black/40 border border-white/5 rounded-2xl p-2 relative h-[100px] md:h-auto overflow-hidden">
                <div className="absolute top-2 left-4 flex items-center gap-2 z-10">
                    <TrendingUp size={14} className="text-[#00ffa3]" />
                    <span className="text-[9px] font-black text-gray-500 uppercase tracking-widest">Growth Curve</span>
                </div>
                <ResponsiveContainer width="100%" height="100%">
                    <AreaChart data={chartData}>
                        <defs>
                            <linearGradient id="colorPv" x1="0" y1="0" x2="0" y2="1">
                                <stop offset="5%" stopColor="#00ffa3" stopOpacity={0.3} />
                                <stop offset="95%" stopColor="#00ffa3" stopOpacity={0} />
                            </linearGradient>
                        </defs>
                        <Tooltip
                            contentStyle={{ backgroundColor: '#000', border: '1px solid #333', borderRadius: '8px' }}
                            itemStyle={{ color: '#00ffa3', fontSize: '12px', fontFamily: 'monospace' }}
                            labelStyle={{ display: 'none' }}
                        />
                        <Area
                            type="monotone"
                            dataKey="pnl"
                            stroke="#00ffa3"
                            strokeWidth={2}
                            fillOpacity={1}
                            fill="url(#colorPv)"
                        />
                    </AreaChart>
                </ResponsiveContainer>
            </div>
        </div>
    );
}
