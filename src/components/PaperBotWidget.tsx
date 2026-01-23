
'use client';

import { useEffect, useState } from 'react';
import { supabase } from '@/lib/supabaseClient';
import { TrendingUp, RefreshCw, AlertCircle, CheckCircle, Activity } from 'lucide-react';

interface PaperPosition {
    id: number;
    symbol: string;
    entry_price: number;
    quantity: number;
    status: 'OPEN' | 'CLOSED';
    pnl: number | null;
    exit_price: number | null;
    exit_reason: string | null;
    opened_at: string;
    closed_at: string | null;
}

export default function PaperBotWidget() {
    const [positions, setPositions] = useState<PaperPosition[]>([]);
    const [stats, setStats] = useState({ totalPnl: 0, winRate: 0, activeCount: 0 });

    const fetchPositions = async () => {
        const { data } = await supabase
            .from('paper_positions')
            .select('*')
            .order('opened_at', { ascending: false })
            .limit(50);

        if (data) {
            setPositions(data);
            calculateStats(data);
        }
    };

    const calculateStats = (data: PaperPosition[]) => {
        const closed = data.filter(p => p.status === 'CLOSED');
        const active = data.filter(p => p.status === 'OPEN');

        const totalPnl = closed.reduce((acc, curr) => acc + (curr.pnl || 0), 0);
        const winners = closed.filter(p => (p.pnl || 0) > 0).length;
        const winRate = closed.length > 0 ? (winners / closed.length) * 100 : 0;

        setStats({
            totalPnl,
            winRate,
            activeCount: active.length
        });
    };

    useEffect(() => {
        fetchPositions();

        const channel = supabase
            .channel('paper_trading_updates')
            .on('postgres_changes', { event: '*', schema: 'public', table: 'paper_positions' }, () => {
                fetchPositions();
            })
            .subscribe();

        return () => {
            supabase.removeChannel(channel);
        };
    }, []);

    return (
        <div className="flex flex-col h-full bg-transparent p-6">
            <div className="flex justify-between items-start mb-8">
                <div className="flex flex-col gap-1">
                    <div className="flex items-center gap-2">
                        <div className="w-2 h-2 rounded-full bg-[#00ffa3] animate-pulse shadow-[0_0_10px_#00ffa3]"></div>
                        <h2 className="text-xs font-black text-[#00ffa3] uppercase tracking-[0.3em]">
                            Paper Engine
                        </h2>
                    </div>
                    <p className="text-[10px] text-gray-500 font-bold uppercase tracking-widest leading-none">Live Simulation Node</p>
                </div>
                <div className="text-right">
                    <p className="text-[9px] text-gray-600 font-black uppercase tracking-widest mb-1">Cumulative PnL</p>
                    <p className={`text-2xl font-black tracking-tighter ${stats.totalPnl >= 0 ? 'text-[#00ffa3]' : 'text-red-500'}`}>
                        {stats.totalPnl >= 0 ? '+' : ''}${stats.totalPnl.toFixed(2)}
                    </p>
                </div>
            </div>

            {/* ACTIVE TRADES */}
            <div className="mb-8">
                <div className="flex items-center justify-between mb-4 px-1">
                    <h3 className="text-[10px] font-black text-white/40 uppercase tracking-[0.2em] flex items-center gap-2">
                        Active Positions
                    </h3>
                    <span className="px-2 py-0.5 bg-white/5 rounded-full text-[9px] font-mono font-bold text-white/50 border border-white/5">
                        {stats.activeCount} OPEN
                    </span>
                </div>
                <div className="space-y-3">
                    {positions.filter(p => p.status === 'OPEN').length === 0 ? (
                        <div className="group relative py-8 px-4 border border-dashed border-white/10 rounded-3xl flex flex-col items-center justify-center gap-3 bg-white/[0.01] hover:bg-white/[0.02] transition-all">
                            <div className="w-8 h-8 rounded-full border border-white/10 flex items-center justify-center text-white/20 group-hover:text-white/40 group-hover:scale-110 transition-all">
                                <Activity size={16} />
                            </div>
                            <span className="text-[10px] text-white/20 font-black uppercase tracking-widest text-center px-4">
                                Monitoring market for entry conditions...
                            </span>
                        </div>
                    ) : (
                        positions.filter(p => p.status === 'OPEN').map(pos => (
                            <div key={pos.id} className="group relative p-4 bg-gradient-to-br from-white/[0.05] to-transparent rounded-2xl border border-white/5 hover:border-[#00ffa3]/30 transition-all overflow-hidden shadow-xl">
                                <div className="absolute top-0 right-0 p-2 opacity-10 group-hover:opacity-30 transition-all">
                                    <TrendingUp size={32} className="text-[#00ffa3]" />
                                </div>
                                <div className="flex justify-between items-start mb-3">
                                    <div>
                                        <h4 className="text-lg font-black tracking-tighter leading-none">{pos.symbol}</h4>
                                        <p className="text-[10px] text-[#00ffa3] font-mono font-bold uppercase mt-1">Status: Executing</p>
                                    </div>
                                    <div className="text-right">
                                        <p className="text-[9px] text-gray-500 font-bold uppercase tracking-widest">Entry</p>
                                        <p className="text-xs font-mono font-black text-white">${pos.entry_price.toLocaleString()}</p>
                                    </div>
                                </div>
                                <div className="w-full h-1 bg-white/5 rounded-full overflow-hidden">
                                    <div className="h-full bg-[#00ffa3] w-1/3 animate-progress-fast"></div>
                                </div>
                            </div>
                        ))
                    )}
                </div>
            </div>

            {/* RECENT HISTORY */}
            <div className="flex-1 flex flex-col min-h-0">
                <div className="flex items-center justify-between mb-4 px-1">
                    <h3 className="text-[10px] font-black text-white/40 uppercase tracking-[0.2em]">Execution Logs</h3>
                    <div className="flex items-center gap-2">
                        <span className="text-[10px] font-bold text-gray-500 uppercase tracking-widest">Win Rate:</span>
                        <span className="text-[10px] font-black tracking-widest text-[#00ffa3]">{stats.winRate.toFixed(0)}%</span>
                    </div>
                </div>
                <div className="flex-1 overflow-y-auto space-y-2 pr-2 custom-scrollbar-thin pb-4">
                    {positions.filter(p => p.status === 'CLOSED').length === 0 ? (
                        <div className="py-4 px-4 border border-dashed border-white/5 rounded-2xl flex items-center justify-center bg-white/[0.01]">
                            <span className="text-[9px] text-white/20 font-bold uppercase tracking-widest">Awaiting first settlement...</span>
                        </div>
                    ) : (
                        positions.filter(p => p.status === 'CLOSED').map(pos => (
                            <div key={pos.id} className="flex justify-between items-center p-3 bg-white/[0.02] hover:bg-white/[0.04] rounded-xl border border-white/5 transition-all group">
                                <div className="flex items-center gap-3">
                                    <div className={`w-1.5 h-1.5 rounded-full ${(pos.pnl || 0) >= 0 ? 'bg-[#00ffa3] shadow-[0_0_8px_#00ffa3]' : 'bg-red-500 shadow-[0_0_8px_red]'}`}></div>
                                    <div>
                                        <span className="font-black text-sm tracking-tight">{pos.symbol}</span>
                                        <p className="text-[9px] text-gray-500 font-bold uppercase tracking-widest leading-none mt-0.5">{pos.exit_reason}</p>
                                    </div>
                                </div>
                                <div className="text-right">
                                    <span className={`font-mono text-xs font-black ${(pos.pnl || 0) >= 0 ? 'text-[#00ffa3]' : 'text-red-500'}`}>
                                        {(pos.pnl || 0) >= 0 ? '+' : ''}${(pos.pnl || 0).toFixed(2)}
                                    </span>
                                </div>
                            </div>
                        ))
                    )}
                </div>
            </div>
        </div>
    );
}
