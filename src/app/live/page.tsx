'use client';

import { useEffect, useState } from 'react';
import { supabase } from '@/lib/supabaseClient';
import { TrendingUp, Activity, ArrowRight } from 'lucide-react';

interface PaperPosition {
    id: number;
    symbol: string;
    entry_price: number;
    quantity: number;
    status: 'OPEN' | 'CLOSED';
    pnl: number | null;
    opened_at: string;
    bot_stop_loss?: number;
    bot_take_profit?: number;
    leverage?: number;
    liquidation_price?: number;
}

export default function LiveTradesPage() {
    const [positions, setPositions] = useState<PaperPosition[]>([]);
    const [prices, setPrices] = useState<Record<string, number>>({});
    const [loading, setLoading] = useState(true);

    const fetchPositions = async () => {
        try {
            const { data, error } = await supabase
                .from('paper_positions')
                .select('*')
                .eq('status', 'OPEN')
                .order('opened_at', { ascending: false });

            if (data) setPositions(data);
        } catch (e) {
            console.error("Error fetching trades", e);
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        fetchPositions();
        const interval = setInterval(fetchPositions, 10000); // 10s Poll

        // Subscription for real-time updates
        const channel = supabase.channel('public_trades')
            .on('postgres_changes', { event: '*', schema: 'public', table: 'paper_positions', filter: 'status=eq.OPEN' }, fetchPositions)
            .subscribe();

        return () => {
            clearInterval(interval);
            supabase.removeChannel(channel);
        };
    }, []);

    // KRAKEN WEBSOCKET FOR LIVE PRICES
    useEffect(() => {
        const openSymbols = positions
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
                    const pair = data[3];
                    if (ticker && ticker.c && pair) {
                        const currentPrice = parseFloat(ticker.c[0]);
                        setPrices(prev => ({ ...prev, [pair]: currentPrice }));
                    }
                }
            } catch (e) { }
        };

        return () => { ws.close(); };
    }, [positions]);

    return (
        <div className="min-h-screen bg-[#050505] text-white font-sans selection:bg-[#00ffa3]/30">
            {/* HERO SECTION */}
            <div className="relative pt-32 pb-20 px-6 border-b border-white/5 bg-[radial-gradient(ellipse_at_top,_var(--tw-gradient-stops))] from-blue-900/20 via-[#050505] to-[#050505]">
                <div className="max-w-6xl mx-auto text-center">
                    <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-blue-500/10 border border-blue-500/20 text-blue-400 text-[10px] font-bold uppercase tracking-widest mb-6 backdrop-blur">
                        <span className="w-1.5 h-1.5 rounded-full bg-blue-400 animate-pulse"></span>
                        Nexus Live Engine
                    </div>
                    <h1 className="text-5xl md:text-7xl font-black tracking-tighter mb-6 bg-gradient-to-b from-white to-white/40 bg-clip-text text-transparent">
                        Operativa Institucional <br />
                        <span className="text-[#00ffa3]">En Tiempo Real</span>
                    </h1>
                    <p className="text-gray-400 text-lg md:text-xl max-w-2xl mx-auto leading-relaxed mb-10">
                        Transparencia total. Observa cómo nuestro algoritmo autónomo gestiona el capital en los mercados de futuros, sin filtros ni retrasos.
                    </p>

                    <a href="/dashboard" className="inline-flex items-center gap-2 px-8 py-4 bg-[#00ffa3] hover:bg-[#00e692] text-black font-black uppercase tracking-wider rounded-xl transition-all hover:scale-105 shadow-[0_0_30px_rgba(0,255,163,0.3)]">
                        Acceder al Terminal <ArrowRight size={18} />
                    </a>
                </div>
            </div>

            {/* TRADES GRID */}
            <div className="max-w-6xl mx-auto px-6 py-20">
                <div className="flex items-center justify-between mb-8">
                    <h2 className="text-xl font-bold flex items-center gap-3">
                        <Activity className="text-[#00ffa3]" />
                        Operaciones Activas
                    </h2>
                    <span className="text-sm font-mono text-gray-500 flex items-center gap-2">
                        <span className="w-2 h-2 rounded-full bg-[#00ffa3] animate-pulse"></span>
                        LIVE FEED
                    </span>
                </div>

                {loading ? (
                    <div className="py-20 text-center text-gray-500 animate-pulse">
                        Cargando datos del motor...
                    </div>
                ) : positions.length === 0 ? (
                    <div className="py-20 px-6 border border-dashed border-white/10 rounded-3xl text-center bg-white/[0.02]">
                        <p className="text-gray-400 mb-2 font-medium">El escáner está buscando oportunidades de alta probabilidad...</p>
                        <p className="text-xs text-gray-600 uppercase tracking-widest">Sin posiciones abiertas</p>
                    </div>
                ) : (
                    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                        {positions.map((pos) => {
                            const livePrice = prices[pos.symbol.toUpperCase()] || pos.entry_price;
                            const isLong = pos.quantity >= 0;

                            // Calculate PnL Live
                            let pnl = (livePrice - pos.entry_price) * pos.quantity;
                            if (!isLong || (pos.bot_take_profit && pos.bot_take_profit < pos.entry_price)) {
                                // Short fix
                                pnl = (pos.entry_price - livePrice) * Math.abs(pos.quantity);
                            }

                            const isGreen = pnl >= 0;
                            const leverage = pos.leverage || 10;
                            const margin = (pos.entry_price * Math.abs(pos.quantity)) / leverage; // Approx margin if not in DB
                            const roe = margin > 0 ? (pnl / margin) * 100 : 0;

                            return (
                                <div key={pos.id} className={`group relative p-6 bg-white/[0.02] border rounded-3xl transition-all hover:-translate-y-1 overflow-hidden ${isGreen ? 'border-[#00ffa3]/20' : 'border-red-500/20'}`}>
                                    <div className={`absolute top-0 right-0 p-4 opacity-5 group-hover:opacity-10 transition-all`}>
                                        <TrendingUp size={100} className={isGreen ? "text-[#00ffa3]" : "text-red-500"} />
                                    </div>

                                    <div className="flex justify-between items-start mb-6 relative">
                                        <div>
                                            <div className="flex items-center gap-3 mb-2">
                                                <h3 className="text-2xl font-black tracking-tighter">{pos.symbol}</h3>
                                            </div>
                                            <div className="flex gap-2 mb-2">
                                                <span className={`px-2 py-1 rounded text-[10px] font-bold uppercase tracking-widest ${isLong ? 'bg-[#00ffa3]/10 text-[#00ffa3]' : 'bg-red-500/10 text-red-500'}`}>
                                                    {isLong ? 'Buy' : 'Sell'}
                                                </span>
                                                <span className="px-2 py-1 rounded text-[10px] font-black uppercase bg-white/10 text-white border border-white/10">
                                                    {pos.leverage || 10}x Lev
                                                </span>
                                            </div>
                                            <div className="inline-block bg-white/5 px-3 py-1.5 rounded-lg border border-white/10">
                                                <p className="text-[9px] text-gray-500 uppercase font-bold mb-0.5">Invested (Margin)</p>
                                                <p className="text-base font-black text-white font-mono">${margin.toFixed(2)}</p>
                                            </div>
                                        </div>
                                        <div className="text-right">
                                            <p className={`text-xl font-mono font-black ${isGreen ? 'text-[#00ffa3]' : 'text-red-500'}`}>
                                                {isGreen ? '+' : ''}{roe.toFixed(2)}%
                                            </p>
                                            <p className={`text-xs font-bold ${isGreen ? 'text-[#00ffa3]/70' : 'text-red-500/70'}`}>
                                                {isGreen ? '+' : ''}${pnl.toFixed(2)}
                                            </p>
                                        </div>
                                    </div>

                                    <div className="space-y-4 relative">
                                        <div className="flex justify-between items-end pb-4 border-b border-white/5">
                                            <span className="text-xs text-gray-500 font-bold uppercase tracking-wider">Entrada</span>
                                            <span className="font-mono text-xl font-bold">${pos.entry_price.toLocaleString()}</span>
                                        </div>

                                        <div className="grid grid-cols-2 gap-4">
                                            <div>
                                                <span className="block text-[10px] text-gray-500 font-bold uppercase tracking-wider mb-1">Take Profit</span>
                                                <span className="font-mono text-[#00ffa3] font-bold">
                                                    {pos.bot_take_profit ? `$${pos.bot_take_profit.toLocaleString()}` : 'OPEN'}
                                                </span>
                                            </div>
                                            <div className="text-right">
                                                <span className="block text-[10px] text-gray-500 font-bold uppercase tracking-wider mb-1">Stop Loss</span>
                                                <span className="font-mono text-red-500 font-bold">
                                                    {pos.bot_stop_loss ? `$${pos.bot_stop_loss.toLocaleString()}` : '---'}
                                                </span>
                                            </div>
                                        </div>

                                        <div className="pt-2 flex justify-between text-[10px] text-gray-600 font-mono">
                                            <span>Mark: ${livePrice.toLocaleString()}</span>
                                        </div>
                                    </div>
                                </div>
                            );
                        })}
                    </div>
                )}
            </div>

            <div className="text-center pb-20 px-6">
                <p className="text-xs text-gray-600 max-w-lg mx-auto leading-relaxed">
                    * Resultados de Paper Trading en entorno simulado v11.0. El rendimiento pasado no garantiza resultados futuros.
                    Nexus AI opera de forma autónoma basándose en parámetros de riesgo predefinidos.
                </p>
            </div>
        </div>
    );
}
