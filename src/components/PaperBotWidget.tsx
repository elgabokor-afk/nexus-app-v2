
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
    bot_stop_loss?: number;
    bot_take_profit?: number;
}

export default function PaperBotWidget() {
    const [positions, setPositions] = useState<PaperPosition[]>([]);
    const [wallet, setWallet] = useState({ equity: 10000, balance: 10000 });
    const [stats, setStats] = useState({ totalPnl: 0, winRate: 0, activeCount: 0 });
    const [prices, setPrices] = useState<Record<string, number>>({});

    const fetchPositions = async () => {
        const { data: walletData } = await supabase.from('bot_wallet').select('*').limit(1).single();
        if (walletData) setWallet(walletData);

        const { data } = await supabase.from('paper_positions').select('*').order('opened_at', { ascending: false }).limit(50);
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
        setStats({ totalPnl, winRate, activeCount: active.length });
    };

    // KRAKEN WEBSOCKET FOR LIVE PRICES
    useEffect(() => {
        const openSymbols = positions
            .filter(p => p.status === 'OPEN')
            .map(p => p.symbol.toUpperCase()) // Ensure format like BTC/USD
            .filter((v, i, a) => a.indexOf(v) === i); // Unique

        if (openSymbols.length === 0) return;

        const ws = new WebSocket('wss://ws.kraken.com');

        ws.onopen = () => {
            const payload = {
                event: 'subscribe',
                pair: openSymbols,
                subscription: { name: 'ticker' }
            };
            ws.send(JSON.stringify(payload));
        };

        ws.onmessage = (event) => {
            try {
                const data = JSON.parse(event.data);
                if (Array.isArray(data)) {
                    // Kraken array format: [channelID, { c: [price, vol], ... }, channelName, pair]
                    const ticker = data[1];
                    const pair = data[3];
                    if (ticker && ticker.c && pair) {
                        const currentPrice = parseFloat(ticker.c[0]);
                        setPrices(prev => ({ ...prev, [pair]: currentPrice }));
                    }
                }
            } catch (e) {
                // Ignore heartbeat/parsing errors
            }
        };

        return () => {
            ws.close();
        };
    }, [positions]); // Re-subscribe if positions change

    useEffect(() => {
        fetchPositions();
        const channel = supabase.channel('paper_trading_updates')
            .on('postgres_changes', { event: '*', schema: 'public', table: 'paper_positions' }, fetchPositions)
            .on('postgres_changes', { event: '*', schema: 'public', table: 'bot_wallet' }, fetchPositions)
            .subscribe();
        return () => { supabase.removeChannel(channel); };
    }, []);

    // CALCULATE UNREALIZED PnL
    const unrealizedPnl = positions
        .filter(p => p.status === 'OPEN')
        .reduce((acc, pos) => {
            const currentPrice = prices[pos.symbol.toUpperCase()] || pos.entry_price;
            let tradePnl = (currentPrice - pos.entry_price) * pos.quantity;
            // Invert for Shorts (Sell)
            if (pos.quantity < 0 || (pos.bot_take_profit && pos.bot_take_profit < pos.entry_price)) { // Simple heuristic since signal_type isn't always present in type
                tradePnl = (pos.entry_price - currentPrice) * Math.abs(pos.quantity);
            }
            return acc + tradePnl;
        }, 0);

    const totalEquity = wallet.balance + unrealizedPnl; // Balance is Cash. Equity is Cash + Unrealized.
    // Note: bot_wallet.equity in DB is usually settled equity. Visualizing live equity here.
    const displayEquity = totalEquity;
    const equityChange = displayEquity - 10000;
    const isProfit = equityChange >= 0;

    return (
        <div className="flex flex-col h-full bg-transparent overflow-y-auto custom-scrollbar">
            <div className="p-6">
                {/* WALLET HEADER */}
                <div className="flex justify-between items-start mb-8 bg-black/20 p-4 rounded-2xl border border-white/5 backdrop-blur-sm">
                    <div className="flex flex-col gap-1">
                        <div className="flex items-center gap-2">
                            <div className="w-2 h-2 rounded-full bg-[#00ffa3] animate-pulse shadow-[0_0_10px_#00ffa3]"></div>
                            <h2 className="text-xs font-black text-[#00ffa3] uppercase tracking-[0.3em]">
                                V3 Autonomous Fund
                            </h2>
                        </div>
                        <p className="text-[10px] text-gray-500 font-bold uppercase tracking-widest leading-none">Live Portfolio Logic</p>
                        <div className="mt-2 text-xs font-mono text-gray-400">
                            Cash: <span className="text-white">${wallet.balance.toLocaleString(undefined, { minimumFractionDigits: 2 })}</span>
                        </div>
                    </div>
                    <div className="text-right">
                        <p className="text-[9px] text-gray-600 font-black uppercase tracking-widest mb-1">Live Equity</p>
                        <p className="text-3xl font-black tracking-tighter text-white">
                            ${displayEquity.toLocaleString(undefined, { minimumFractionDigits: 2 })}
                        </p>
                        <div className="flex items-center justify-end gap-2">
                            <p className={`text-[10px] font-bold tracking-wider ${isProfit ? 'text-[#00ffa3]' : 'text-red-500'}`}>
                                {isProfit ? '+' : ''}{equityChange.toLocaleString(undefined, { minimumFractionDigits: 2 })}
                            </p>
                            {unrealizedPnl !== 0 && (
                                <span className={`text-[9px] font-mono px-1.5 rounded ${unrealizedPnl >= 0 ? 'bg-[#00ffa3]/20 text-[#00ffa3]' : 'bg-red-500/20 text-red-500'}`}>
                                    Floating: {unrealizedPnl >= 0 ? '+' : ''}${unrealizedPnl.toFixed(2)}
                                </span>
                            )}
                        </div>
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
                                <Activity size={16} className="text-white/20" />
                                <span className="text-[10px] text-white/20 font-black uppercase tracking-widest text-center px-4">
                                    Scanning for high probability setups...
                                </span>
                            </div>
                        ) : (
                            positions.filter(p => p.status === 'OPEN').map(pos => {
                                const livePrice = prices[pos.symbol.toUpperCase()] || pos.entry_price;
                                let pnl = (livePrice - pos.entry_price) * pos.quantity;
                                // Simple short detection (if TP is lower than entry)
                                if (pos.bot_take_profit && pos.bot_take_profit < pos.entry_price) {
                                    pnl = (pos.entry_price - livePrice) * Math.abs(pos.quantity);
                                }
                                const pnlPercent = (pnl / (pos.entry_price * pos.quantity)) * 100;
                                const isPosGreen = pnl >= 0;

                                return (
                                    <div key={pos.id} className={`group relative p-4 bg-gradient-to-br from-white/[0.05] to-transparent rounded-2xl border transition-all overflow-hidden shadow-xl ${isPosGreen ? 'border-[#00ffa3]/20 hover:border-[#00ffa3]/40' : 'border-red-500/20 hover:border-red-500/40'}`}>
                                        <div className="absolute top-0 right-0 p-2 opacity-10 group-hover:opacity-30 transition-all">
                                            <TrendingUp size={32} className={isPosGreen ? "text-[#00ffa3]" : "text-red-500"} />
                                        </div>
                                        <div className="flex justify-between items-start mb-3">
                                            <div>
                                                <h4 className="text-lg font-black tracking-tighter leading-none flex items-center gap-2">
                                                    {pos.symbol}
                                                    <span className={`text-[8px] px-1.5 py-0.5 rounded font-bold ${isPosGreen ? 'bg-[#00ffa3]/20 text-[#00ffa3]' : 'bg-red-500/20 text-red-500'}`}>
                                                        ${livePrice.toLocaleString()}
                                                    </span>
                                                </h4>
                                                <p className="text-[10px] text-gray-500 font-mono font-bold uppercase mt-1">
                                                    Size: ${(pos.entry_price * pos.quantity).toFixed(0)}
                                                </p>
                                            </div>
                                            <div className="text-right">
                                                <p className="text-[9px] text-gray-500 font-bold uppercase tracking-widest">Unrealized PnL</p>
                                                <p className={`text-base font-mono font-black ${isPosGreen ? 'text-[#00ffa3]' : 'text-red-500'}`}>
                                                    {isPosGreen ? '+' : ''}${pnl.toFixed(2)}
                                                </p>
                                                <p className={`text-[9px] font-bold ${isPosGreen ? 'text-[#00ffa3]' : 'text-red-500'}`}>
                                                    {isPosGreen ? '+' : ''}{pnlPercent.toFixed(2)}%
                                                </p>
                                            </div>
                                        </div>

                                        {/* Progress Bar relative to TP/SL could go here, for now just a separator */}
                                        <div className="w-full h-[1px] bg-white/5 my-2"></div>

                                        <div className="flex justify-between text-[9px] font-mono font-bold text-gray-500">
                                            <span>SL: ${pos.bot_stop_loss?.toFixed(2) || '---'}</span>
                                            <span className="text-[#00ffa3]">TP: ${pos.bot_take_profit?.toFixed(2) || '---'}</span>
                                        </div>
                                    </div>
                                );
                            })
                        )}
                    </div>
                </div>

                {/* RECENT HISTORY */}
                <div className="flex flex-col space-y-6">
                    <div className="flex items-center justify-between px-1">
                        <h3 className="text-[10px] font-black text-white/40 uppercase tracking-[0.2em]">Execution Logs</h3>
                        <div className="flex items-center gap-2">
                            <span className="text-[10px] font-bold text-gray-500 uppercase tracking-widest">Efficiency:</span>
                            <span className="text-[10px] font-black tracking-widest text-[#00ffa3]">{stats.winRate.toFixed(0)}%</span>
                        </div>
                    </div>

                    {positions.filter(p => p.status === 'CLOSED').length === 0 ? (
                        <div className="py-8 px-4 border border-dashed border-white/5 rounded-2xl flex items-center justify-center bg-white/[0.01]">
                            <span className="text-[9px] text-white/20 font-bold uppercase tracking-widest">Awaiting first settlement...</span>
                        </div>
                    ) : (
                        <div className="space-y-6">
                            {/* WINS SECTION */}
                            {positions.filter(p => p.status === 'CLOSED' && (p.pnl || 0) > 0).length > 0 && (
                                <div className="space-y-3">
                                    <div className="flex items-center gap-2 px-2">
                                        <div className="w-1 h-1 rounded-full bg-[#00ffa3]"></div>
                                        <span className="text-[9px] font-black text-[#00ffa3] uppercase tracking-widest">Settled Wins ({positions.filter(p => p.status === 'CLOSED' && (p.pnl || 0) > 0).length})</span>
                                    </div>
                                    <div className="space-y-2">
                                        {positions.filter(p => p.status === 'CLOSED' && (p.pnl || 0) > 0).map(pos => (
                                            <div key={pos.id} className="flex justify-between items-center p-3 bg-[#00ffa3]/[0.03] hover:bg-[#00ffa3]/[0.06] rounded-xl border border-[#00ffa3]/10 transition-all group">
                                                <div className="flex items-center gap-3">
                                                    <div className="w-1.5 h-1.5 rounded-full bg-[#00ffa3] shadow-[0_0_8px_#00ffa3]"></div>
                                                    <div>
                                                        <span className="font-black text-sm tracking-tight">{pos.symbol}</span>
                                                        <p className="text-[9px] text-gray-500 font-bold uppercase tracking-widest leading-none mt-0.5">{pos.exit_reason}</p>
                                                    </div>
                                                </div>
                                                <div className="text-right">
                                                    <span className="font-mono text-xs font-black text-[#00ffa3]">
                                                        +${(pos.pnl || 0).toFixed(2)}
                                                    </span>
                                                </div>
                                            </div>
                                        ))}
                                    </div>
                                </div>
                            )}

                            {/* LOSSES SECTION */}
                            {positions.filter(p => p.status === 'CLOSED' && (p.pnl || 0) <= 0).length > 0 && (
                                <div className="space-y-3 pb-4">
                                    <div className="flex items-center gap-2 px-2">
                                        <div className="w-1 h-1 rounded-full bg-red-500"></div>
                                        <span className="text-[9px] font-black text-red-500 uppercase tracking-widest">Settled Losses ({positions.filter(p => p.status === 'CLOSED' && (p.pnl || 0) <= 0).length})</span>
                                    </div>
                                    <div className="space-y-2">
                                        {positions.filter(p => p.status === 'CLOSED' && (p.pnl || 0) <= 0).map(pos => (
                                            <div key={pos.id} className="flex justify-between items-center p-3 bg-red-500/[0.03] hover:bg-red-500/[0.06] rounded-xl border border-red-500/10 transition-all group">
                                                <div className="flex items-center gap-3">
                                                    <div className="w-1.5 h-1.5 rounded-full bg-red-500 shadow-[0_0_8px_red]"></div>
                                                    <div>
                                                        <span className="font-black text-sm tracking-tight">{pos.symbol}</span>
                                                        <p className="text-[9px] text-gray-500 font-bold uppercase tracking-widest leading-none mt-0.5">{pos.exit_reason}</p>
                                                    </div>
                                                </div>
                                                <div className="text-right">
                                                    <span className="font-mono text-xs font-black text-red-500">
                                                        ${(pos.pnl || 0).toFixed(2)}
                                                    </span>
                                                </div>
                                            </div>
                                        ))}
                                    </div>
                                </div>
                            )}
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
}
