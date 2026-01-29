'use client';

import { useEffect, useState, useCallback } from 'react';
import { supabase } from '@/lib/supabaseClient';
import { TrendingUp, TrendingDown, Zap, Activity, AlertCircle, RefreshCw, Layers } from 'lucide-react';
import LearningCurve from './LearningCurve'; // V600
import { useLiveStream } from '@/hooks/useLiveStream'; // V1100
import Pusher from 'pusher-js'; // V2100

interface Position {
    id: number;
    symbol: string;
    entry_price: number;
    quantity: number;
    status: string;
    pnl?: number;
    closed_at?: string;
    exit_reason?: string;
    leverage?: number;
    initial_margin?: number;
    margin_mode?: string;
    bot_take_profit?: number;
    bot_stop_loss?: number;
    liquidation_price?: number;
    confidence_score?: number;
    rsi_entry?: number;
    atr_entry?: number;
    signal_type?: string;
}

interface Wallet {
    balance: number;
    equity: number;
}

export default function PaperBotWidget({
    onSelectSymbol,
    viewMode = 'widget'
}: {
    onSelectSymbol?: (symbol: string) => void,
    viewMode?: 'widget' | 'pro'
}) {
    const [positions, setPositions] = useState<Position[]>([]);
    const [wallet, setWallet] = useState<Wallet>({ balance: 0, equity: 0 });
    const [prices, setPrices] = useState<Record<string, number>>({});
    const [loading, setLoading] = useState(true);
    const [expandedId, setExpandedId] = useState<number | null>(null); // V530: Accordion State

    const fetchPositions = useCallback(async () => {
        const { data: posData } = await supabase
            .from('paper_positions')
            .select('*')
            .order('id', { ascending: false });

        const { data: walletData } = await supabase
            .from('bot_wallet')
            .select('*')
            .single();

        if (posData) setPositions(posData);
        if (walletData) setWallet(walletData);
        setLoading(false);
    }, []);

    const handleClosePosition = async (id: number) => {
        try {
            const { error } = await supabase
                .from('paper_positions')
                .update({
                    status: 'CLOSED',
                    exit_reason: 'MANUAL_CLOSE',
                    closed_at: new Date().toISOString()
                })
                .eq('id', id);

            if (error) throw error;
            fetchPositions();
        } catch (e) {
            console.error('Error closing position:', e);
            alert('Error closing position');
        }
    };

    // V1100: REMOVED Direct Kraken WS.
    // We now rely 100% on the Redis Bridge (useLiveStream) to receive 
    // unified price updates synced with the backend scanner.
    // This ensures "Mirror Mode" - what the bot sees is what you see.

    const { lastMessage, isConnected } = useLiveStream(['live_positions', 'live_prices']);

    useEffect(() => {
        if (!lastMessage) return;

        if (lastMessage.channel === 'live_positions') {
            const { type, data } = lastMessage.data;
            if (type === 'OPEN') {
                setPositions(prev => [data, ...prev]);
            } else if (type === 'CLOSED') {
                setPositions(prev => prev.map(p =>
                    p.id === data.id ? { ...p, status: 'CLOSED', ...data } : p
                ));
            }
        }

        if (lastMessage.channel === 'live_prices') {
            const { symbol, price } = lastMessage.data;
            setPrices(prev => ({ ...prev, [symbol]: price }));
        }
    }, [lastMessage]);

    useEffect(() => {
        fetchPositions();

        // V1500: Direct Supabase Realtime (Replaces WebSocket Bridge for DB Sync)
        const posChannel = supabase
            .channel('realtime_paper_positions')
            .on('postgres_changes', { event: '*', schema: 'public', table: 'paper_positions' }, (payload: any) => {
                if (payload.eventType === 'INSERT') {
                    setPositions(prev => [payload.new as Position, ...prev]);
                } else if (payload.eventType === 'UPDATE') {
                    setPositions(prev => prev.map(p =>
                        p.id === payload.new.id ? { ...p, ...payload.new } : p
                    ));
                } else if (payload.eventType === 'DELETE') {
                    setPositions(prev => prev.filter(p => p.id !== payload.old.id));
                }
            })
            .subscribe();

        // V2100: PUSHER LISTENER (The Real-Time "Pulse")
        // This receives the instant trade execution from the Python Bot

        const pusherKey = process.env.NEXT_PUBLIC_PUSHER_KEY;
        let pusherClient: any = null;

        if (pusherKey) {
            // @ts-ignore
            pusherClient = new Pusher(pusherKey, {
                cluster: process.env.NEXT_PUBLIC_PUSHER_CLUSTER!,
                forceTLS: true,
            });

            // V3800: Price Channel (Replaces WebSocket Bridge)
            const priceChannel = pusherClient.subscribe('public-price-feed');
            priceChannel.bind('price-update', (data: any) => {
                const { symbol, price } = data;
                setPrices(prev => ({ ...prev, [symbol]: price }));
            });

            const channel = pusherClient.subscribe('public-paper-positions');
            channel.bind('position-update', (event: any) => {
                const { type, data } = event;
                console.log("[PaperBot] Pusher Event:", type, data);

                if (type === 'OPEN') {
                    setPositions(prev => {
                        // Avoid duplicates
                        if (prev.find(p => p.id === data.id)) return prev;
                        return [data, ...prev];
                    });
                } else if (type === 'CLOSED') {
                    setPositions(prev => prev.map(p =>
                        p.id === data.id ? { ...p, status: 'CLOSED', ...data } : p
                    ));
                }
            });
        }

        const walletChannel = supabase
            .channel('realtime_bot_wallet')
            .on('postgres_changes', { event: 'UPDATE', schema: 'public', table: 'bot_wallet' }, (payload: any) => {
                setWallet(payload.new as Wallet);
            })
            .subscribe();

        // V1100: HA Polling is now just a background sync every 60s
        const interval = setInterval(fetchPositions, 60000);

        return () => {
            clearInterval(interval);
            supabase.removeChannel(posChannel);
            supabase.removeChannel(walletChannel);
        };
    }, [fetchPositions]);

    // V1500: DYNAMIC REAL-TIME CALCULATIONS
    const activePositions = positions.filter(p => p.status === 'OPEN');

    const totalUnrealizedPnl = activePositions.reduce((acc, pos) => {
        const livePrice = prices[pos.symbol.toUpperCase()] || prices[pos.symbol.toUpperCase().replace('/USDT', '/USD')] || pos.entry_price;
        let pnl = (livePrice - pos.entry_price) * pos.quantity;
        if (pos.quantity < 0 || (pos.bot_take_profit && pos.bot_take_profit < pos.entry_price)) {
            pnl = (pos.entry_price - livePrice) * Math.abs(pos.quantity);
        }
        return acc + pnl;
    }, 0);

    const usedMargin = activePositions.reduce((acc, pos) => {
        return acc + (pos.initial_margin || (pos.entry_price * Math.abs(pos.quantity) / (pos.leverage || 10)));
    }, 0);

    const dynamicEquity = wallet.balance + totalUnrealizedPnl;
    const dynamicAvailable = wallet.balance - usedMargin;

    const stats = {
        activeCount: activePositions.length,
        totalPnl: positions.filter(p => p.status === 'CLOSED').reduce((acc, p) => acc + (p.pnl || 0), 0) + totalUnrealizedPnl,
        winRate: (positions.filter(p => p.status === 'CLOSED' && (p.pnl || 0) > 0).length /
            (positions.filter(p => p.status === 'CLOSED').length || 1)) * 100
    };

    if (loading) return null;

    return (
        <div className="flex flex-col h-full">
            {/* V600: Learning Curve Monitor */}
            <div className="px-6 pt-6">
                <LearningCurve data={[]} />
            </div>

            {/* WALLET SUMMARY */}
            <div className="p-6 border-b border-white/5 bg-white/[0.01]">
                <div className="flex items-center justify-between mb-4 px-1">
                    <div className="flex items-center gap-2">
                        <div className={`w-2 h-2 rounded-full ${isConnected ? 'bg-[#00ffa3] animate-pulse shadow-[0_0_8px_#00ffa3]' : 'bg-red-500'}`}></div>
                        <span className="text-[10px] font-black text-white/40 uppercase tracking-widest">
                            {isConnected || Object.keys(prices).length > 0 ? 'Live Market Feed: Active' : 'Market Feed: Syncing...'}
                        </span>
                    </div>
                </div>
                <div className="grid grid-cols-2 gap-4">
                    <div className="p-4 rounded-3xl bg-black/40 border border-white/5">
                        <p className="text-[10px] font-black text-gray-500 uppercase tracking-widest mb-1">Available Margin</p>
                        <p className="text-xl font-black text-white font-mono">${dynamicAvailable.toLocaleString(undefined, { minimumFractionDigits: 2 })}</p>
                    </div>
                    <div className={`p-4 rounded-3xl border transition-colors duration-300 ${totalUnrealizedPnl >= 0 ? 'bg-[#00ffa3]/5 border-[#00ffa3]/20' : 'bg-red-500/5 border-red-500/20'}`}>
                        <p className={`text-[10px] font-black uppercase tracking-widest mb-1 ${totalUnrealizedPnl >= 0 ? 'text-[#00ffa3]/60' : 'text-red-500/60'}`}>Total Equity</p>
                        <p className={`text-xl font-black font-mono ${totalUnrealizedPnl >= 0 ? 'text-[#00ffa3]' : 'text-red-500'}`}>${dynamicEquity.toLocaleString(undefined, { minimumFractionDigits: 2 })}</p>
                    </div>
                </div>
            </div>

            {/* FULL LIST MODE (PRO) */}
            {viewMode === 'pro' && (
                <div className="mb-8 overflow-x-auto p-6">
                    <table className="w-full text-left border-collapse">
                        <thead className="bg-white/[0.02] border-b border-white/5 text-[9px] font-black text-gray-500 uppercase tracking-widest">
                            <tr>
                                <th className="p-3">Contract</th>
                                <th className="p-3">Side</th>
                                <th className="p-3 text-right">Notional</th>
                                <th className="p-3 text-right">Entry</th>
                                <th className="p-3 text-right">SL</th>
                                <th className="p-3 text-right">TP</th>
                                <th className="p-3 text-right">Mark</th>
                                <th className="p-3 text-right text-red-500/80">Liq.</th>
                                <th className="p-3 text-right">Margin</th>
                                <th className="p-3 text-center">Signal Context</th>
                                <th className="p-3 text-right">PnL (ROE %)</th>
                                <th className="p-3 text-right">Actions</th>
                            </tr>
                        </thead>
                        <tbody className="divide-y divide-white/5">
                            {positions.filter(p => p.status === 'OPEN').slice(0, 20).map(pos => {
                                const livePrice = prices[pos.symbol.toUpperCase()] || prices[pos.symbol.toUpperCase().replace('/USDT', '/USD')] || pos.entry_price;
                                const isStreaming = !!prices[pos.symbol.toUpperCase()];
                                let pnl = (livePrice - pos.entry_price) * pos.quantity;
                                if (pos.quantity < 0 || (pos.bot_take_profit && pos.bot_take_profit < pos.entry_price)) {
                                    pnl = (pos.entry_price - livePrice) * Math.abs(pos.quantity);
                                }
                                const margin = pos.initial_margin || (pos.entry_price * Math.abs(pos.quantity) / (pos.leverage || 10));
                                const roePercent = margin > 0 ? (pnl / margin) * 100 : 0;
                                const isPosGreen = pnl >= 0;

                                return (
                                    <tr key={pos.id} className="hover:bg-white/[0.02] transition-colors group">
                                        <td className="p-3">
                                            <div className="flex items-center gap-2">
                                                <span className="font-bold text-white text-xs font-mono">{pos.symbol}</span>
                                                <span className="text-[9px] px-1 py-0.5 rounded bg-white/10 text-gray-300 font-mono">
                                                    {pos.leverage || 10}x
                                                </span>
                                            </div>
                                        </td>
                                        <td className="p-3">
                                            <span className={`text-[10px] font-black uppercase ${pos.quantity >= 0 ? 'text-[#00ffa3]' : 'text-red-500'}`}>
                                                {pos.quantity >= 0 ? 'LONG' : 'SHORT'}
                                            </span>
                                        </td>
                                        <td className="p-3 text-right font-mono text-xs text-gray-300">
                                            ${(pos.entry_price * Math.abs(pos.quantity)).toFixed(0)}
                                        </td>
                                        <td className="p-3 text-right font-mono text-xs text-gray-400">
                                            ${pos.entry_price.toLocaleString()}
                                        </td>
                                        <td className="p-3 text-right font-mono text-xs text-red-500/80">
                                            ${pos.bot_stop_loss?.toLocaleString() || '---'}
                                        </td>
                                        <td className="p-3 text-right font-mono text-xs text-[#00ffa3]/80">
                                            ${pos.bot_take_profit?.toLocaleString() || '---'}
                                        </td>
                                        <td className={`p-3 text-right font-mono text-xs font-bold ${isPosGreen ? 'text-[#00ffa3]' : 'text-red-500'}`}>
                                            <div className="flex flex-col items-end">
                                                <span>${livePrice.toLocaleString()}</span>
                                                {isStreaming && <span className="text-[8px] animate-pulse text-[#00ffa3]">LIVE</span>}
                                            </div>
                                        </td>
                                        <td className="p-3 text-right font-mono text-xs text-orange-500">
                                            ${pos.liquidation_price?.toLocaleString() || '---'}
                                        </td>
                                        <td className="p-3 text-right font-mono text-xs text-gray-300">
                                            ${margin.toFixed(2)}
                                        </td>
                                        <td className="p-3 text-center">
                                            <div className="flex flex-col items-center">
                                                <span className="text-[9px] font-black uppercase text-gray-400 bg-white/5 px-1.5 py-0.5 rounded mb-1">
                                                    {pos.signal_type?.replace('ADOPTED_', '') || 'MANUAL'}
                                                </span>
                                                <div className="flex gap-2">
                                                    <span className="text-[9px] font-mono text-yellow-500">RSI: {Math.round(pos.rsi_entry || 50)}</span>
                                                    <span className="text-[9px] font-mono text-blue-400">Conf: {Math.round(pos.confidence_score || 0)}%</span>
                                                </div>
                                            </div>
                                        </td>
                                        <td className="p-3 text-right">
                                            <div className="flex flex-col items-end">
                                                <span className={`font-mono text-xs font-black ${isPosGreen ? 'text-[#00ffa3]' : 'text-red-500'}`}>
                                                    {isPosGreen ? '+' : ''}${pnl.toFixed(2)}
                                                </span>
                                                <span className={`text-[9px] font-bold ${isPosGreen ? 'text-[#00ffa3]' : 'text-red-500'}`}>
                                                    ({isPosGreen ? '+' : ''}{roePercent.toFixed(2)}%)
                                                </span>
                                            </div>
                                        </td>
                                        <td className="p-3 text-right">
                                            <button
                                                onClick={(e) => { e.stopPropagation(); handleClosePosition(pos.id); }}
                                                className="px-2 py-1 bg-white/5 hover:bg-white/10 text-gray-400 hover:text-white rounded text-[9px] font-bold uppercase transition-colors border border-white/5"
                                            >
                                                Close
                                            </button>
                                        </td>
                                    </tr>
                                );
                            })}
                        </tbody>
                    </table>
                </div>
            )}

            {/* WIDGET MODE (Dashboard Style) */}
            {viewMode === 'widget' && (
                <div className="px-6 py-6 flex-1 overflow-y-auto custom-scrollbar">
                    <div className="mb-8">
                        <div className="flex items-center justify-between mb-4 px-1">
                            <h3 className="text-[10px] font-black text-white/40 uppercase tracking-[0.2em] flex items-center gap-2">
                                <Activity size={10} className="text-[#00ffa3]" /> Active Positions
                            </h3>
                            <span className="px-2 py-0.5 bg-white/5 rounded-full text-[9px] font-mono font-bold text-white/50 border border-white/5">
                                {stats.activeCount} OPEN
                            </span>
                        </div>
                        <div className="space-y-4">
                            {positions.filter(p => p.status === 'OPEN').length === 0 ? (
                                <div className="group relative py-12 px-4 border border-dashed border-white/10 rounded-3xl flex flex-col items-center justify-center gap-4 bg-white/[0.01]">
                                    <RefreshCw size={24} className="text-white/10 animate-spin-slow" />
                                    <span className="text-[11px] text-white/30 font-black uppercase tracking-[0.2em] text-center max-w-[200px]">
                                        Monitoring 20+ Assets for AI Setups...
                                    </span>
                                </div>
                            ) : (
                                positions.filter(p => p.status === 'OPEN').slice(0, 20).map(pos => {
                                    const livePrice = prices[pos.symbol.toUpperCase()] || prices[pos.symbol.toUpperCase().replace('/USDT', '/USD')] || pos.entry_price;
                                    const isStreaming = !!prices[pos.symbol.toUpperCase()];
                                    let pnl = (livePrice - pos.entry_price) * pos.quantity;
                                    if (pos.quantity < 0 || (pos.bot_take_profit && pos.bot_take_profit < pos.entry_price)) {
                                        pnl = (pos.entry_price - livePrice) * Math.abs(pos.quantity);
                                    }
                                    const margin = pos.initial_margin || (pos.entry_price * Math.abs(pos.quantity) / (pos.leverage || 10));
                                    const notionalSize = pos.entry_price * Math.abs(pos.quantity);
                                    const roePercent = margin > 0 ? (pnl / margin) * 100 : 0;
                                    const isPosGreen = pnl >= 0;
                                    const liqPrice = pos.liquidation_price;
                                    const isLiqRisk = liqPrice ? Math.abs((livePrice - liqPrice) / livePrice) * 100 < 1.5 : false;

                                    // V530: Accordion State
                                    const isExpanded = expandedId === pos.id;

                                    return (
                                        <div
                                            key={pos.id}
                                            onClick={() => setExpandedId(isExpanded ? null : pos.id)}
                                            className={`group relative rounded-2xl border transition-all duration-300 overflow-hidden cursor-pointer active:scale-[0.99] animate-fade-in
                                                ${isPosGreen
                                                    ? 'bg-gradient-to-br from-[#00ffa3]/[0.02] to-transparent border-[#00ffa3]/20 hover:border-[#00ffa3]/50 hover:shadow-[0_0_20px_rgba(0,255,163,0.1)]'
                                                    : 'bg-gradient-to-br from-red-500/[0.02] to-transparent border-red-500/20 hover:border-red-500/50 hover:shadow-[0_0_20px_rgba(239,68,68,0.1)]'}
                                            `}
                                        >
                                            {/* Glowing Edge Gradient */}
                                            <div className={`absolute inset-0 opacity-0 group-hover:opacity-100 transition-opacity duration-500 pointer-events-none
                                                ${isPosGreen ? 'bg-[radial-gradient(circle_at_50%_0%,rgba(0,255,163,0.1),transparent_70%)]' : 'bg-[radial-gradient(circle_at_50%_0%,rgba(239,68,68,0.1),transparent_70%)]'}
                                            `}></div>

                                            {/* COMPACT ROW (Always Visible) */}
                                            <div className="p-4 flex justify-between items-center relative z-10">
                                                <div className="flex items-center gap-4">
                                                    <div className={`p-2.5 rounded-xl backdrop-blur-md shadow-inner transition-colors duration-300 ${isPosGreen ? 'bg-[#00ffa3]/10 text-[#00ffa3]' : 'bg-red-500/10 text-red-500'}`}>
                                                        <TrendingUp size={18} className={isPosGreen ? "text-[#00ffa3]" : "text-red-500"} />
                                                    </div>
                                                    <div>
                                                        <div className="flex items-center gap-2">
                                                            <h4 className="text-base font-black tracking-tight text-white">{pos.symbol}</h4>
                                                            <span className={`text-[9px] font-black px-1.5 py-0.5 rounded border ${isPosGreen ? 'bg-[#00ffa3]/10 text-[#00ffa3] border-[#00ffa3]/20' : 'bg-red-500/10 text-red-500 border-red-500/20'}`}>
                                                                {pos.signal_type?.includes('BUY') ? 'LONG' : 'SHORT'}
                                                            </span>
                                                        </div>
                                                        <div className="flex gap-3 mt-1.5">
                                                            <span className="text-[10px] font-bold text-gray-500 bg-white/5 px-1.5 rounded">{pos.leverage || 10}x</span>
                                                            <span className="text-[10px] font-mono text-gray-400 flex items-center gap-1">
                                                                <span className="w-1 h-1 rounded-full bg-gray-600"></span>
                                                                ${notionalSize.toLocaleString()}
                                                            </span>
                                                        </div>
                                                    </div>
                                                </div>

                                                <div className="flex items-center gap-6">
                                                    {/* Mini Sparkline or Context Metric */}
                                                    <div className="hidden sm:flex flex-col items-end">
                                                        <span className="text-[9px] font-black uppercase text-gray-600 tracking-wider">Entry</span>
                                                        <span className="text-xs font-mono text-gray-300">${pos.entry_price.toLocaleString()}</span>
                                                    </div>

                                                    <div className="flex flex-col items-end min-w-[80px]">
                                                        <span className={`text-lg font-black tracking-tight drop-shadow-lg ${isPosGreen ? 'text-[#00ffa3]' : 'text-red-500'}`}>
                                                            {isPosGreen ? '+' : ''}{roePercent.toFixed(2)}%
                                                        </span>
                                                        <span className={`text-[10px] font-mono font-bold ${isPosGreen ? 'text-[#00ffa3]/80' : 'text-red-500/80'}`}>
                                                            ${pnl.toFixed(2)}
                                                        </span>
                                                    </div>
                                                </div>
                                            </div>

                                            {/* EXPANDED DETAILS (Accordion) */}
                                            {isExpanded && (
                                                <div className="px-4 pb-4 pt-0 animate-in fade-in slide-in-from-top-2 duration-200">
                                                    <div className="h-px w-full bg-white/5 mb-3" />

                                                    {isLiqRisk && (
                                                        <div className="mb-3 p-2 bg-red-500/10 rounded-lg border border-red-500/20 flex items-center gap-2">
                                                            <AlertCircle size={12} className="text-red-500 animate-pulse" />
                                                            <span className="text-[10px] font-black text-red-500">LIQUIDATION RISK: ${liqPrice?.toLocaleString()}</span>
                                                        </div>
                                                    )}

                                                    <div className="grid grid-cols-3 gap-2 mb-3">
                                                        <div className="bg-black/20 p-2 rounded-xl border border-white/5">
                                                            <p className="text-[9px] text-gray-500 font-bold uppercase tracking-widest leading-none mb-1">Entry</p>
                                                            <p className="text-xs font-mono text-white font-black">${pos.entry_price.toLocaleString()}</p>
                                                        </div>
                                                        <div className="bg-black/20 p-2 rounded-xl border border-white/5">
                                                            <p className="text-[9px] text-gray-500 font-bold uppercase tracking-widest leading-none mb-1">Mark</p>
                                                            <p className={`text-xs font-mono font-black ${isPosGreen ? 'text-[#00ffa3]' : 'text-red-500'}`}>${livePrice.toLocaleString()}</p>
                                                        </div>
                                                        <div className="bg-black/20 p-2 rounded-xl border border-white/5 flex flex-col justify-center items-center">
                                                            <div className="flex gap-1 mb-1">
                                                                <span className="text-[9px] font-bold text-blue-400">{Math.round(pos.confidence_score || 0)}%</span>
                                                                <span className="text-[9px] font-bold text-yellow-500">RSI{Math.round(pos.rsi_entry || 0)}</span>
                                                            </div>
                                                            <span className="text-[8px] font-black uppercase text-gray-500">{pos.signal_type?.replace('ADOPTED_', '') || 'MANUAL'}</span>
                                                        </div>
                                                    </div>

                                                    <div className="flex gap-2">
                                                        <button
                                                            onClick={(e) => {
                                                                e.stopPropagation();
                                                                const newTp = prompt("New TP Price:", pos.bot_take_profit?.toString());
                                                                const newSl = prompt("New SL Price:", pos.bot_stop_loss?.toString());
                                                                if (newTp && newSl) {
                                                                    supabase.from('paper_positions').update({
                                                                        bot_take_profit: parseFloat(newTp),
                                                                        bot_stop_loss: parseFloat(newSl)
                                                                    }).eq('id', pos.id).then(() => fetchPositions());
                                                                }
                                                            }}
                                                            className="flex-1 py-2 bg-white/5 hover:bg-white/10 rounded-xl text-[9px] font-black uppercase tracking-widest transition-all border border-white/5 text-gray-400 hover:text-white"
                                                        >
                                                            Manage
                                                        </button>
                                                        <button
                                                            onClick={(e) => { e.stopPropagation(); handleClosePosition(pos.id); }}
                                                            className="flex-1 py-2 bg-red-500/10 hover:bg-red-500/20 rounded-xl text-[9px] font-black uppercase tracking-widest transition-all border border-red-500/10 text-red-500"
                                                        >
                                                            Close
                                                        </button>
                                                    </div>
                                                </div>
                                            )}
                                        </div>
                                    );
                                })
                            )}
                        </div>
                    </div>

                    {/* EXECUTION LOGS */}
                    <div className="flex flex-col space-y-4">
                        <div className="flex items-center justify-between px-1">
                            <h3 className="text-[10px] font-black text-white/40 uppercase tracking-[0.2em]">Execution Logs</h3>
                            <span className="text-[10px] font-black tracking-widest text-[#00ffa3]">{stats.winRate.toFixed(0)}% SUCCESS Rate</span>
                        </div>
                        <div className="space-y-2 max-h-[300px] overflow-y-auto custom-scrollbar pr-1">
                            {positions.filter(p => p.status === 'CLOSED').map(pos => (
                                <div key={pos.id} className="flex justify-between items-center p-3 bg-white/[0.02] hover:bg-white/[0.04] rounded-xl border border-white/5 transition-all">
                                    <div className="flex items-center gap-3">
                                        <div className={`w-1.5 h-1.5 rounded-full ${(pos.pnl || 0) > 0 ? 'bg-[#00ffa3] shadow-[0_0_8px_#00ffa3]' : 'bg-red-500'}`}></div>
                                        <div>
                                            <span className="font-black text-sm tracking-tight text-white">{pos.symbol}</span>
                                            <p className="text-[8px] text-gray-600 font-bold uppercase tracking-widest leading-none mt-0.5">{pos.exit_reason}</p>
                                        </div>
                                    </div>
                                    <span className={`font-mono text-xs font-black ${(pos.pnl || 0) > 0 ? 'text-[#00ffa3]' : 'text-red-500'}`}>
                                        {(pos.pnl || 0) > 0 ? '+' : ''}${(pos.pnl || 0).toFixed(2)}
                                    </span>
                                </div>
                            ))}
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
}
