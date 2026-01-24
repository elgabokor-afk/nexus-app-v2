'use client';

import { useEffect, useState, useCallback } from 'react';
import { supabase } from '@/lib/supabaseClient';
import { TrendingUp, TrendingDown, Zap, Activity, AlertCircle, RefreshCw, Layers } from 'lucide-react';

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

    useEffect(() => {
        const openSymbols = positions
            .filter(p => p.status === 'OPEN')
            .map(p => p.symbol.toUpperCase())
            .filter((v, i, a) => a.indexOf(v) === i);

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
                    const ticker = data[1];
                    let pair = data[3];

                    if (pair) {
                        pair = pair.toUpperCase().replace('XBT', 'BTC').replace('XDG', 'DOGE');
                    }

                    if (ticker && ticker.c && pair) {
                        const currentPrice = parseFloat(ticker.c[0]);
                        // Normalize the pair for matching (e.g., BTC/USD -> BTC/USDT)
                        const usdtPair = pair.includes('/USD') ? pair.replace('/USD', '/USDT') : pair;
                        setPrices(prev => ({
                            ...prev,
                            [pair]: currentPrice,
                            [usdtPair]: currentPrice
                        }));
                    }
                }
            } catch (e) { }
        };

        return () => {
            ws.close();
        };
    }, [positions]);

    useEffect(() => {
        fetchPositions();
        const interval = setInterval(fetchPositions, 2000);

        const channel = supabase.channel('paper_trading_updates')
            .on('postgres_changes', { event: '*', schema: 'public', table: 'paper_positions' }, fetchPositions)
            .on('postgres_changes', { event: '*', schema: 'public', table: 'bot_wallet' }, fetchPositions)
            .subscribe();

        return () => {
            clearInterval(interval);
            supabase.removeChannel(channel);
        };
    }, [fetchPositions]);

    const stats = {
        activeCount: positions.filter(p => p.status === 'OPEN').length,
        totalPnl: positions.filter(p => p.status === 'CLOSED').reduce((acc, p) => acc + (p.pnl || 0), 0),
        winRate: (positions.filter(p => p.status === 'CLOSED' && (p.pnl || 0) > 0).length /
            (positions.filter(p => p.status === 'CLOSED').length || 1)) * 100
    };

    if (loading) return null;

    return (
        <div className="flex flex-col h-full">
            {/* WALLET SUMMARY */}
            <div className="p-6 border-b border-white/5 bg-white/[0.01]">
                <div className="grid grid-cols-2 gap-4">
                    <div className="p-4 rounded-3xl bg-black/40 border border-white/5">
                        <p className="text-[10px] font-black text-gray-500 uppercase tracking-widest mb-1">Available Margin</p>
                        <p className="text-xl font-black text-white font-mono">${wallet.balance.toLocaleString(undefined, { minimumFractionDigits: 2 })}</p>
                    </div>
                    <div className="p-4 rounded-3xl bg-[#00ffa3]/5 border border-[#00ffa3]/10">
                        <p className="text-[10px] font-black text-[#00ffa3]/60 uppercase tracking-widest mb-1">Total Equity</p>
                        <p className="text-xl font-black text-[#00ffa3] font-mono">${wallet.equity.toLocaleString(undefined, { minimumFractionDigits: 2 })}</p>
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
                                const livePrice = prices[pos.symbol.toUpperCase()] || pos.entry_price;
                                let pnl = (livePrice - pos.entry_price) * pos.quantity;
                                if (pos.quantity < 0 || (pos.bot_take_profit && pos.bot_take_profit < pos.entry_price)) {
                                    pnl = (pos.entry_price - livePrice) * Math.abs(pos.quantity);
                                }
                                const margin = pos.initial_margin || (pos.entry_price * Math.abs(pos.quantity));
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
                                        <td className={`p-3 text-right font-mono text-xs font-bold ${isPosGreen ? 'text-[#00ffa3]' : 'text-red-500'}`}>
                                            ${livePrice.toLocaleString()}
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
                                            className={`group relative bg-gradient-to-br from-white/[0.05] to-transparent rounded-2xl border transition-all overflow-hidden shadow-xl cursor-pointer active:scale-[0.99] ${isPosGreen ? 'border-[#00ffa3]/20 hover:border-[#00ffa3]/40' : 'border-red-500/20 hover:border-red-500/40'}`}
                                        >
                                            {/* COMPACT ROW (Always Visible) */}
                                            <div className="p-4 flex justify-between items-center">
                                                <div className="flex items-center gap-3">
                                                    <div className={`p-2 rounded-xl ${isPosGreen ? 'bg-[#00ffa3]/10' : 'bg-red-500/10'}`}>
                                                        <TrendingUp size={16} className={isPosGreen ? "text-[#00ffa3]" : "text-red-500"} />
                                                    </div>
                                                    <div>
                                                        <div className="flex items-center gap-2">
                                                            <h4 className="text-sm font-black tracking-tight text-white">{pos.symbol}</h4>
                                                            <span className={`text-[9px] font-black px-1.5 py-0.5 rounded ${pos.quantity >= 0 ? 'bg-[#00ffa3]/10 text-[#00ffa3]' : 'bg-red-500/10 text-red-500'}`}>
                                                                {pos.quantity >= 0 ? 'LONG' : 'SHORT'}
                                                            </span>
                                                        </div>
                                                        <div className="flex gap-2 mt-1">
                                                            <span className="text-[9px] font-bold text-gray-500">{pos.leverage || 10}x</span>
                                                            <span className="text-[9px] font-mono text-gray-400">${notionalSize.toLocaleString()}</span>
                                                        </div>
                                                    </div>
                                                </div>

                                                <div className="flex items-center gap-4">
                                                    <div className="flex flex-col items-end">
                                                        <span className={`text-sm font-black tracking-tight ${isPosGreen ? 'text-[#00ffa3]' : 'text-red-500'}`}>
                                                            {isPosGreen ? '+' : ''}{roePercent.toFixed(2)}%
                                                        </span>
                                                        <span className={`text-[9px] font-mono font-bold ${isPosGreen ? 'text-[#00ffa3]/60' : 'text-red-500/60'}`}>
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
