'use client';

import { useEffect, useState } from 'react';
import { supabase } from '@/lib/supabaseClient';
import { Gauge, TrendingUp, TrendingDown, Target, Zap } from 'lucide-react';
import Pusher from 'pusher-js';

interface AssetRanking {
    id: number;
    symbol: string;
    score: number;
    confidence: number;
    trend_status: string;
}

export default function PortfolioHub() {
    const [rankings, setRankings] = useState<AssetRanking[]>([]);
    const [loading, setLoading] = useState(true);

    const fetchRankings = async () => {
        const { data } = await supabase
            .from('ai_asset_rankings')
            .select('*')
            .order('score', { ascending: false });
        if (data) setRankings(data);
        setLoading(false);
    };

    // V3900: Listen to Pusher Events (No more WebSocket Bridge)
    useEffect(() => {
        const pusher = new Pusher(process.env.NEXT_PUBLIC_PUSHER_KEY!, {
            cluster: process.env.NEXT_PUBLIC_PUSHER_CLUSTER!,
            forceTLS: true,
        });

        const channel = pusher.subscribe('public-rankings');

        channel.bind('ranking-update', (newRank: AssetRanking) => {
            setRankings(prev => {
                // Upsert logic: Update if exists, add if new
                const exists = prev.find(r => r.symbol === newRank.symbol);
                let updatedList;
                if (exists) {
                    updatedList = prev.map(r => r.symbol === newRank.symbol ? { ...r, ...newRank } : r);
                } else {
                    updatedList = [...prev, newRank];
                }
                // Always keep sorted by Score
                return updatedList.sort((a, b) => b.score - a.score).slice(0, 20);
            });
        });

        return () => {
            pusher.unsubscribe('public-rankings');
            pusher.disconnect();
        };
    }, []);

    if (loading) return null;

    return (
        <div className="bg-black/40 p-4 rounded-3xl border border-white/5 backdrop-blur-md flex flex-col gap-4">
            <div className="flex items-center justify-between px-1">
                <div className="flex items-center gap-2">
                    <div className="p-2 bg-green-500/10 rounded-xl border border-green-500/20">
                        <Target size={18} className="text-green-400" />
                    </div>
                    <div>
                        <h3 className="text-xs font-black text-white uppercase tracking-widest">Target Ranking</h3>
                        <p className="text-[9px] text-gray-500 font-bold uppercase tracking-tighter">AI Top-20 Priority List</p>
                    </div>
                </div>
                <div className="flex items-center gap-1 bg-white/5 px-2 py-0.5 rounded-full">
                    <Zap size={10} className="text-yellow-400" />
                    <span className="text-[8px] font-mono text-gray-400 font-black">RECURSIVE V90</span>
                </div>
            </div>

            <div className="grid grid-cols-1 gap-1.5 overflow-y-auto max-h-[350px] custom-scrollbar pr-1">
                {rankings.map((rank, idx) => (
                    <div key={rank.symbol} className="flex items-center justify-between p-2 rounded-xl bg-white/[0.02] border border-white/5 hover:border-white/10 transition-all group">
                        <div className="flex items-center gap-3">
                            <span className="text-[10px] font-mono text-gray-600 w-4 font-black">#{idx + 1}</span>
                            <div className="flex flex-col">
                                <span className="text-[11px] font-black text-white group-hover:text-green-400 transition-colors uppercase italic">{rank.symbol.split('/')[0]}</span>
                                <div className="flex items-center gap-1.5">
                                    {rank.trend_status === 'BULLISH' ?
                                        <TrendingUp size={10} className="text-green-500" /> :
                                        <TrendingDown size={10} className="text-red-500" />
                                    }
                                    <span className={`text-[8px] font-bold uppercase ${rank.trend_status === 'BULLISH' ? 'text-green-500/60' : 'text-red-500/60'}`}>
                                        {rank.trend_status}
                                    </span>
                                </div>
                            </div>
                        </div>

                        <div className="flex items-center gap-4">
                            <div className="flex flex-col items-end">
                                <span className="text-[14px] font-black text-white tracking-tighter leading-none">{rank.score.toFixed(1)}</span>
                                <span className="text-[7px] text-gray-600 font-black tracking-widest uppercase">Score</span>
                            </div>
                            <div className="h-6 w-[2px] bg-white/5"></div>
                            <div className="flex flex-col items-end">
                                <span className="text-[10px] font-mono text-[#00ffa3] font-black italic">{(rank.confidence * 100).toFixed(0)}%</span>
                                <span className="text-[7px] text-gray-600 font-black tracking-widest uppercase italic">WinProb</span>
                            </div>
                        </div>
                    </div>
                ))}
            </div>
        </div>
    );
}
