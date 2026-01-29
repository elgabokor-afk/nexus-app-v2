"use client";

import { useEffect, useState } from 'react';
import { AreaChart, Area, XAxis, YAxis, Tooltip, ResponsiveContainer } from 'recharts';
import { supabase } from '@/lib/supabaseClient';
import { TrendingUp, TrendingDown, ShieldCheck } from 'lucide-react';

export default function VirtualPortfolio() {
    const [auditData, setAuditData] = useState<any[]>([]);
    const [cumulativePnL, setCumulativePnL] = useState<any[]>([]);
    const [totalWinRate, setTotalWinRate] = useState(0);
    const [netProfit, setNetProfit] = useState(0);

    useEffect(() => {
        const fetchAudit = async () => {
            const { data } = await supabase
                .from('signal_audit_history')
                .select('*')
                .order('id', { ascending: true }); // Chronological

            if (data) {
                setAuditData(data);

                // Calculate Cumulative PnL Curve
                let balance = 1000; // Starting with $1000
                const curve = data.map((d: any, i: number) => {
                    const pnlAmt = balance * (d.pnl_percent / 100);
                    balance += pnlAmt;
                    return {
                        id: i + 1,
                        balance: balance,
                        symbol: d.symbol,
                        outcome: d.outcome
                    };
                });
                setCumulativePnL(curve);
                setNetProfit(balance - 1000);

                // Win Rate
                const wins = data.filter((d: any) => d.outcome === 'WIN').length;
                setTotalWinRate((wins / data.length) * 100);
            }
        };

        fetchAudit();
    }, []);

    if (auditData.length === 0) return (
        <div className="w-full h-full flex flex-col items-center justify-center text-gray-700 bg-[#0e0e10] rounded-2xl border border-[#2f3336] p-8">
            <ShieldCheck size={48} className="mb-4 opacity-20" />
            <h3 className="text-xl font-bold">No Audit History Yet</h3>
            <p className="text-xs mt-2">The AI is gathering historical data...</p>
        </div>
    );

    return (
        <div className="flex flex-col h-full bg-[#0a0a0c] border border-[#2f3336] rounded-2xl p-4 md:p-6 relative overflow-hidden">
            {/* Background Glow */}
            <div className="absolute top-0 right-0 w-64 h-64 bg-[#00ffa3] blur-[100px] opacity-5 pointer-events-none"></div>

            <div className="flex items-center justify-between mb-6">
                <div>
                    <h2 className="text-lg font-black text-white uppercase tracking-tighter flex items-center gap-2">
                        <ShieldCheck size={20} className="text-[#00ffa3]" />
                        Virtual Portfolio Audit
                    </h2>
                    <p className="text-[10px] text-gray-500 font-bold uppercase tracking-widest mt-1">Starting Balance: $1,000</p>
                </div>
                <div className="text-right">
                    <span className={`text-2xl font-mono font-bold ${netProfit > 0 ? "text-[#00ffa3]" : "text-red-500"}`}>
                        {netProfit > 0 ? "+" : ""}${netProfit.toFixed(2)}
                    </span>
                    <p className="text-[10px] text-gray-500 font-bold uppercase tracking-widest mt-1">Net Hypothetical Profit</p>
                </div>
            </div>

            <div className="flex-1 min-h-[200px]">
                <ResponsiveContainer width="100%" height="100%">
                    <AreaChart data={cumulativePnL}>
                        <defs>
                            <linearGradient id="colorBal" x1="0" y1="0" x2="0" y2="1">
                                <stop offset="5%" stopColor="#00ffa3" stopOpacity={0.3} />
                                <stop offset="95%" stopColor="#00ffa3" stopOpacity={0} />
                            </linearGradient>
                        </defs>
                        <Tooltip
                            contentStyle={{ backgroundColor: '#111', borderColor: '#333' }}
                            itemStyle={{ color: '#fff' }}
                        />
                        <Area type="monotone" dataKey="balance" stroke="#00ffa3" strokeWidth={3} fillOpacity={1} fill="url(#colorBal)" />
                    </AreaChart>
                </ResponsiveContainer>
            </div>

            <div className="grid grid-cols-3 gap-4 mt-6">
                <div className="p-3 bg-[#111] rounded-lg border border-white/5">
                    <span className="text-[10px] text-gray-500 font-bold block">WIN RATE</span>
                    <span className="text-xl font-bold text-white">{totalWinRate.toFixed(1)}%</span>
                </div>
                <div className="p-3 bg-[#111] rounded-lg border border-white/5">
                    <span className="text-[10px] text-gray-500 font-bold block">TOTAL TRADES</span>
                    <span className="text-xl font-bold text-white">{auditData.length}</span>
                </div>
                <div className="p-3 bg-[#111] rounded-lg border border-white/5">
                    <span className="text-[10px] text-gray-500 font-bold block">AVG PNL</span>
                    <span className="text-xl font-bold text-[#00ffa3]">
                        {(cumulativePnL.length > 0 ? (cumulativePnL[cumulativePnL.length - 1].balance - 1000) / auditData.length : 0).toFixed(2)}%
                    </span>
                </div>
            </div>
        </div>
    );
}
