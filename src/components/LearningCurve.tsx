
"use client";
import React, { useEffect, useState } from 'react';
import { supabase } from '@/lib/supabase';
import { Target, TrendingUp, Zap, AlertCircle } from 'lucide-react';

export default function LearningCurve() {
    const [stats, setStats] = useState({ winRate: 0, count: 0, target: 60, sampleSize: 50 });
    const [history, setHistory] = useState<number[]>([]);

    useEffect(() => {
        const fetchStats = async () => {
            const { data } = await supabase
                .from('paper_positions')
                .select('pnl')
                .eq('status', 'CLOSED')
                .order('closed_at', { ascending: false })
                .limit(50);

            if (data && data.length > 0) {
                const wins = data.filter(t => (t.pnl || 0) > 0).length;
                const wr = (wins / data.length) * 100;
                setStats(s => ({ ...s, winRate: wr, count: data.length }));

                // Create a rolling win rate for the history (simplified)
                const rolling = data.map((t, i, arr) => {
                    const slice = arr.slice(i, i + 10);
                    return (slice.filter(x => x.pnl > 0).length / slice.length) * 100;
                }).reverse();
                setHistory(rolling);
            }
        };

        fetchStats();
        const sub = supabase.channel('learning_sync')
            .on('postgres_changes', { event: '*', schema: 'public', table: 'paper_positions' }, fetchStats)
            .subscribe();

        return () => { supabase.removeChannel(sub); };
    }, []);

    const isReady = stats.winRate >= stats.target && stats.count >= stats.sampleSize;

    return (
        <div className="bg-gradient-to-br from-black/40 to-white/[0.02] border border-white/10 rounded-3xl p-6 backdrop-blur-xl mb-6 overflow-hidden relative group">
            <div className="absolute -top-24 -right-24 w-48 h-48 bg-blue-500/10 blur-[100px] rounded-full group-hover:bg-blue-500/20 transition-all duration-1000" />

            <div className="flex justify-between items-start mb-6 relative z-10">
                <div>
                    <h3 className="text-xs font-black uppercase tracking-[0.3em] text-blue-400 mb-1 flex items-center gap-2">
                        <Zap size={14} className="animate-pulse" />
                        Cosmos Learning Curve
                    </h3>
                    <p className="text-[10px] text-gray-500 font-bold uppercase tracking-widest">
                        Training Status: {stats.count}/{stats.sampleSize} Operations
                    </p>
                </div>
                {isReady ? (
                    <div className="bg-[#00ffa3]/10 border border-[#00ffa3]/20 px-3 py-1 rounded-full flex items-center gap-2 animate-bounce">
                        <div className="w-1.5 h-1.5 bg-[#00ffa3] rounded-full" />
                        <span className="text-[10px] font-black text-[#00ffa3] uppercase tracking-tighter">Ready for Live</span>
                    </div>
                ) : (
                    <div className="bg-yellow-500/10 border border-yellow-500/20 px-3 py-1 rounded-full flex items-center gap-2">
                        <div className="w-1.5 h-1.5 bg-yellow-500 rounded-full animate-pulse" />
                        <span className="text-[10px] font-black text-yellow-500 uppercase tracking-tighter">In Training</span>
                    </div>
                )}
            </div>

            <div className="grid grid-cols-2 gap-4 mb-6 relative z-10">
                <div className="bg-black/40 p-4 rounded-2xl border border-white/5 flex flex-col items-center">
                    <span className="text-[9px] font-black text-gray-500 uppercase tracking-widest mb-1">Win Rate</span>
                    <span className={`text-3xl font-black tracking-tighter ${stats.winRate >= stats.target ? 'text-[#00ffa3]' : 'text-white'}`}>
                        {Math.round(stats.winRate)}%
                    </span>
                    <div className="w-full h-1 bg-white/5 rounded-full mt-2 overflow-hidden">
                        <div
                            className={`h-full transition-all duration-1000 ${stats.winRate >= stats.target ? 'bg-[#00ffa3]' : 'bg-blue-500'}`}
                            style={{ width: `${stats.winRate}%` }}
                        />
                    </div>
                </div>
                <div className="bg-black/40 p-4 rounded-2xl border border-white/5 flex flex-col items-center">
                    <span className="text-[9px] font-black text-gray-500 uppercase tracking-widest mb-1">Target</span>
                    <span className="text-3xl font-black tracking-tighter text-white/40">
                        {stats.target}%
                    </span>
                    <span className="text-[8px] font-bold text-gray-600 uppercase mt-2">Required for Live Mode</span>
                </div>
            </div>

            {/* Micro Sparkline */}
            <div className="h-12 flex items-end gap-1 px-1 relative z-10 grayscale hover:grayscale-0 transition-all duration-500">
                {history.map((val, i) => (
                    <div
                        key={i}
                        className={`group/bar relative flex-1 rounded-t-sm transition-all duration-300 ${val >= 60 ? 'bg-[#00ffa3]/40 hover:bg-[#00ffa3]' : 'bg-blue-500/20 hover:bg-blue-500/60'}`}
                        style={{ height: `${val}%` }}
                    >
                        <div className="absolute -top-6 left-1/2 -translate-x-1/2 bg-black border border-white/10 px-1 py-0.5 rounded text-[8px] font-black opacity-0 group-hover/bar:opacity-100 transition-opacity">
                            {Math.round(val)}%
                        </div>
                    </div>
                ))}
            </div>

            {!isReady && stats.count > 0 && (
                <div className="mt-4 p-3 bg-white/[0.03] rounded-xl border border-white/5 flex items-center gap-3">
                    <AlertCircle size={14} className="text-blue-400" />
                    <p className="text-[9px] text-gray-400 font-bold leading-tight uppercase tracking-wider">
                        The AI needs {stats.sampleSize - stats.count > 0 ? stats.sampleSize - stats.count : 0} more trades to stabilize its perception before going Live.
                    </p>
                </div>
            )}
        </div>
    );
}
