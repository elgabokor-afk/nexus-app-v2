
'use client';

import { useEffect, useState } from 'react';
import { supabase } from '@/lib/supabaseClient';
import { TrendingUp, RefreshCw, AlertCircle, CheckCircle } from 'lucide-react';

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
            .limit(20);

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
        <div className="bg-[#0a0a0c] border border-[#222] rounded-2xl p-6 shadow-xl">
            <div className="flex justify-between items-center mb-6">
                <div className="flex items-center gap-3">
                    <div className="p-2 bg-blue-500/10 rounded-lg border border-blue-500/20">
                        <RefreshCw className="text-blue-400" size={20} />
                    </div>
                    <div>
                        <h2 className="text-xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-blue-400 to-indigo-500">
                            Paper Trading Bot
                        </h2>
                        <p className="text-xs text-gray-500 font-mono">LIVE SIMULATION • $1000/TRADE</p>
                    </div>
                </div>
                <div className="text-right">
                    <p className="text-xs text-gray-400 font-mono mb-1">TOTAL PNL</p>
                    <p className={`text-xl font-mono font-bold ${stats.totalPnl >= 0 ? 'text-green-400' : 'text-red-400'}`}>
                        {stats.totalPnl >= 0 ? '+' : ''}${stats.totalPnl.toFixed(2)}
                    </p>
                </div>
            </div>

            {/* ACTIVE TRADES */}
            <div className="mb-6">
                <h3 className="text-sm font-bold text-gray-400 mb-3 flex items-center gap-2">
                    <span className="w-2 h-2 rounded-full bg-green-500 animate-pulse"></span>
                    ACTIVE POSITIONS ({stats.activeCount})
                </h3>
                <div className="space-y-2">
                    {positions.filter(p => p.status === 'OPEN').length === 0 ? (
                        <div className="text-sm text-gray-600 font-mono italic p-4 border border-dashed border-[#222] rounded-lg text-center">
                            Waiting for entry signals...
                        </div>
                    ) : (
                        positions.filter(p => p.status === 'OPEN').map(pos => (
                            <div key={pos.id} className="flex justify-between items-center p-3 bg-[#111] rounded-lg border border-[#222]">
                                <span className="font-bold font-mono">{pos.symbol}</span>
                                <span className="text-sm text-gray-400 font-mono">Entry: ${pos.entry_price.toFixed(2)}</span>
                                <span className="px-2 py-0.5 text-xs bg-blue-500/20 text-blue-400 rounded border border-blue-500/30">OPEN</span>
                            </div>
                        ))
                    )}
                </div>
            </div>

            {/* RECENT HISTORY */}
            <div>
                <h3 className="text-sm font-bold text-gray-400 mb-3">RECENT HISTORY (Win Rate: {stats.winRate.toFixed(0)}%)</h3>
                <div className="space-y-2 max-h-[200px] overflow-y-auto pr-2 custom-scrollbar">
                    {positions.filter(p => p.status === 'CLOSED').map(pos => (
                        <div key={pos.id} className="flex justify-between items-center p-3 bg-[#111] rounded-lg border border-[#222]">
                            <div className="flex items-center gap-2">
                                {(pos.pnl || 0) >= 0 ? <CheckCircle size={14} className="text-green-500" /> : <AlertCircle size={14} className="text-red-500" />}
                                <span className="font-bold font-mono text-sm">{pos.symbol}</span>
                            </div>
                            <span className="text-xs text-gray-500 font-mono uppercase">{pos.exit_reason}</span>
                            <span className={`font-mono text-sm ${(pos.pnl || 0) >= 0 ? 'text-green-400' : 'text-red-400'}`}>
                                {(pos.pnl || 0) >= 0 ? '+' : ''}${(pos.pnl || 0).toFixed(2)}
                            </span>
                        </div>
                    ))}
                </div>
            </div>
        </div>
    );
}
