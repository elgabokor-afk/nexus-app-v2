'use client';

import { useEffect, useState } from 'react';
import { supabase } from '@/lib/supabaseClient';
import { Brain, Cpu, Zap, Activity, MessageSquare } from 'lucide-react';

interface OracleInsight {
    id: number;
    timestamp: string;
    symbol: string;
    trend_status: string;
    ai_probability: number;
    reasoning: string;
    technical_context: any;
}

export default function OracleMonitor() {
    const [insights, setInsights] = useState<OracleInsight[]>([]);
    const [loading, setLoading] = useState(true);

    const fetchInsights = async () => {
        const { data } = await supabase
            .from('oracle_insights')
            .select('*')
            .order('timestamp', { ascending: false })
            .limit(10);
        if (data) setInsights(data);
        setLoading(false);
    };

    useEffect(() => {
        fetchInsights();

        const channel = supabase.channel('oracle_feed')
            .on(
                'postgres_changes',
                { event: 'INSERT', schema: 'public', table: 'oracle_insights' },
                (payload: any) => {
                    if (payload.new) {
                        setInsights(prev => [payload.new as OracleInsight, ...prev].slice(0, 10));
                    }
                }
            )
            .subscribe();

        return () => {
            supabase.removeChannel(channel);
        };
    }, []);

    return (
        <div className="flex flex-col gap-4 bg-black/40 p-4 rounded-3xl border border-white/5 backdrop-blur-md">
            <div className="flex items-center justify-between px-2">
                <div className="flex items-center gap-2">
                    <div className="p-2 bg-purple-500/10 rounded-xl border border-purple-500/20">
                        <Brain size={18} className="text-purple-400 animate-pulse" />
                    </div>
                    <div>
                        <h3 className="text-xs font-black text-white uppercase tracking-widest">Cosmos Oracle BLM</h3>
                        <p className="text-[9px] text-gray-500 font-bold uppercase tracking-tighter">1m Real-Time AI Thoughts</p>
                    </div>
                </div>
                <div className="flex items-center gap-1.5 bg-white/5 px-2 py-0.5 rounded-full border border-white/10">
                    <div className="w-1.5 h-1.5 rounded-full bg-purple-400 animate-pulse"></div>
                    <span className="text-[9px] font-mono text-purple-400 uppercase font-black">Online</span>
                </div>
            </div>

            <div className="flex flex-col gap-2 overflow-y-auto max-h-[300px] custom-scrollbar pr-1">
                {insights.length === 0 ? (
                    <div className="p-6 text-center opacity-20 flex flex-col items-center gap-2">
                        <Cpu size={32} />
                        <p className="text-[10px] font-mono">Awaiting Neural Link...</p>
                    </div>
                ) : (
                    insights.map(insight => (
                        <div key={insight.id} className="bg-white/[0.03] border border-white/5 p-3 rounded-2xl flex flex-col gap-2 group hover:border-purple-500/30 transition-all">
                            <div className="flex justify-between items-center">
                                <div className="flex items-center gap-2">
                                    <span className="text-[10px] font-black text-white">{insight.symbol}</span>
                                    <span className={`text-[8px] font-bold px-1.5 py-0.5 rounded uppercase ${insight.trend_status === 'BULLISH' ? 'bg-green-500/10 text-green-400' :
                                        insight.trend_status === 'BEARISH' ? 'bg-red-500/10 text-red-400' : 'text-gray-400'
                                        }`}>
                                        {insight.trend_status}
                                    </span>
                                    {insight.technical_context?.type === 'SCALP_SCAN' && (
                                        <span className="text-[7px] font-black bg-purple-500 text-white px-1.5 py-0.5 rounded-full animate-pulse">
                                            SCALP
                                        </span>
                                    )}
                                </div>
                                <span className="text-[9px] font-mono text-gray-600">
                                    {new Date(insight.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' })}
                                </span>
                            </div>

                            <div className="flex items-start gap-2">
                                <MessageSquare size={12} className="text-purple-500/50 mt-1 flex-shrink-0" />
                                <p className="text-[10px] leading-relaxed text-gray-300 font-medium italic">
                                    "{insight.reasoning}"
                                </p>
                            </div>

                            <div className="flex items-center justify-between mt-1 pt-2 border-t border-white/5">
                                <div className="flex items-center gap-3">
                                    <div className="flex items-center gap-1">
                                        <Activity size={10} className="text-gray-600" />
                                        <span className="text-[8px] font-mono text-gray-500">Prob: {(insight.ai_probability * 100).toFixed(1)}%</span>
                                    </div>
                                    <div className="flex items-center gap-1">
                                        <Zap size={10} className="text-gray-600" />
                                        <span className="text-[8px] font-mono text-gray-500">RSI: {insight.technical_context?.rsi?.toFixed(1) || '---'}</span>
                                    </div>
                                </div>
                                <div className="w-16 h-1 bg-white/5 rounded-full overflow-hidden">
                                    <div
                                        className={`h-full transition-all duration-1000 ${insight.ai_probability > 0.6 ? 'bg-green-500' :
                                            insight.ai_probability < 0.4 ? 'bg-red-500' : 'bg-purple-500'
                                            }`}
                                        style={{ width: `${insight.ai_probability * 100}%` }}
                                    ></div>
                                </div>
                            </div>
                        </div>
                    ))
                )}
            </div>

            <div className="pt-2 flex items-center justify-center border-t border-white/5">
                <p className="text-[8px] font-mono text-gray-600 uppercase tracking-widest">Integrated Bot Language Model (BLM)</p>
            </div>
        </div>
    );
}
