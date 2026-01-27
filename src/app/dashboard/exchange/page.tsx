'use client';

import { useState, useEffect } from 'react';
import { ArrowUpRight, ArrowDownRight, Search, Activity, BarChart2 } from 'lucide-react';

interface TickerData {
    symbol: string;
    lastPrice: string;
    priceChangePercent: string;
    quoteVolume: string; // 24h Volume in USDT
    count: number; // Trade count
}

export default function ExchangePage() {
    const [tickers, setTickers] = useState<TickerData[]>([]);
    const [loading, setLoading] = useState(true);
    const [search, setSearch] = useState('');

    useEffect(() => {
        const fetchTickerData = async () => {
            try {
                // Public Binance API (No Key Needed for Public Data)
                const res = await fetch('https://api.binance.com/api/v3/ticker/24hr');
                if (!res.ok) throw new Error('Binance API Error');
                const data: TickerData[] = await res.json();

                // Filter for USDT pairs only & Sort by Volume
                const usdtPairs = data
                    .filter(t => t.symbol.endsWith('USDT') && !t.symbol.includes('UP') && !t.symbol.includes('DOWN'))
                    .sort((a, b) => parseFloat(b.quoteVolume) - parseFloat(a.quoteVolume))
                    .slice(0, 100); // Top 100

                setTickers(usdtPairs);
                setLoading(false);
            } catch (error) {
                console.error("Binance API Error:", error);
                setLoading(false);
            }
        };

        fetchTickerData();
        const interval = setInterval(fetchTickerData, 5000); // Live Updates (5s)
        return () => clearInterval(interval);
    }, []);

    const filteredTickers = tickers.filter(t =>
        t.symbol.includes(search.toUpperCase())
    );

    const formatCurrency = (val: string) => {
        const num = parseFloat(val);
        return new Intl.NumberFormat('en-US', {
            style: 'currency',
            currency: 'USD',
            minimumFractionDigits: num < 1 ? 4 : 2,
            maximumFractionDigits: num < 1 ? 6 : 2,
        }).format(num);
    };

    const formatVolume = (val: string) => {
        const num = parseFloat(val);
        return new Intl.NumberFormat('en-US', {
            notation: "compact",
            maximumFractionDigits: 2
        }).format(num);
    };

    return (
        <div className="min-h-screen bg-[#050505] text-white p-6 lg:p-10 font-sans">

            {/* Header */}
            <div className="flex flex-col md:flex-row md:items-center justify-between gap-6 mb-8">
                <div>
                    <h1 className="text-3xl font-black tracking-tighter flex items-center gap-3">
                        <Activity className="text-[#00ffa3]" />
                        LIVE <span className="text-[#00ffa3]">EXCHANGE</span>
                    </h1>
                    <p className="text-gray-500 text-xs font-bold tracking-widest uppercase mt-1">
                        Top 100 Volume Assets (Binance Feed)
                    </p>
                </div>

                <div className="relative w-full md:w-96">
                    <Search className="absolute left-4 top-1/2 -translate-y-1/2 text-gray-500" size={18} />
                    <input
                        type="text"
                        placeholder="Search Pair (e.g. BTC)..."
                        value={search}
                        onChange={(e) => setSearch(e.target.value)}
                        className="w-full bg-white/[0.03] border border-white/10 rounded-2xl py-3 pl-12 pr-4 text-sm text-white focus:outline-none focus:border-[#00ffa3]/50 transition-all font-medium placeholder:text-gray-600 uppercase"
                    />
                </div>
            </div>

            {/* Table Container */}
            <div className="bg-[#0a0a0c] border border-white/5 rounded-[2.5rem] overflow-hidden shadow-2xl relative">
                {/* Gloss Effect */}
                <div className="absolute top-0 left-0 w-full h-1 bg-gradient-to-r from-transparent via-[#00ffa3]/20 to-transparent"></div>

                <div className="overflow-x-auto">
                    <table className="w-full text-left border-collapse">
                        <thead>
                            <tr className="border-b border-white/5 bg-white/[0.02]">
                                <th className="p-6 text-[10px] font-black text-gray-500 uppercase tracking-widest text-center w-16">#</th>
                                <th className="p-6 text-[10px] font-black text-gray-500 uppercase tracking-widest">Pair</th>
                                <th className="p-6 text-[10px] font-black text-gray-500 uppercase tracking-widest text-right">Price</th>
                                <th className="p-6 text-[10px] font-black text-gray-500 uppercase tracking-widest text-right">24h Change</th>
                                <th className="p-6 text-[10px] font-black text-gray-500 uppercase tracking-widest text-right hidden md:table-cell">24h Volume (USDT)</th>
                                <th className="p-6 text-[10px] font-black text-gray-500 uppercase tracking-widest text-right hidden lg:table-cell">Trades</th>
                            </tr>
                        </thead>
                        <tbody>
                            {loading ? (
                                // Loading Skeletons
                                Array.from({ length: 15 }).map((_, i) => (
                                    <tr key={i} className="border-b border-white/5">
                                        <td className="p-6"><div className="h-4 w-8 bg-white/5 rounded animate-pulse mx-auto"></div></td>
                                        <td className="p-6"><div className="h-4 w-24 bg-white/5 rounded animate-pulse"></div></td>
                                        <td className="p-6"><div className="h-4 w-20 bg-white/5 rounded animate-pulse ml-auto"></div></td>
                                        <td className="p-6"><div className="h-4 w-16 bg-white/5 rounded animate-pulse ml-auto"></div></td>
                                        <td className="p-6 hidden md:table-cell"><div className="h-4 w-24 bg-white/5 rounded animate-pulse ml-auto"></div></td>
                                        <td className="p-6 hidden lg:table-cell"><div className="h-4 w-16 bg-white/5 rounded animate-pulse ml-auto"></div></td>
                                    </tr>
                                ))
                            ) : (
                                filteredTickers.map((t, i) => {
                                    const change = parseFloat(t.priceChangePercent);
                                    const isPositive = change >= 0;
                                    const symbol = t.symbol.replace('USDT', ' / USDT');

                                    return (
                                        <tr key={t.symbol} className="border-b border-white/5 hover:bg-white/[0.02] transition-colors group">
                                            <td className="p-6 text-center text-xs text-gray-500 font-bold font-mono">
                                                {i + 1}
                                            </td>
                                            <td className="p-6">
                                                <div className="flex items-center gap-3">
                                                    <div className={`w-2 h-2 rounded-full ${isPositive ? 'bg-[#00ffa3]' : 'bg-[#ff4d4d]'}`}></div>
                                                    <span className="text-sm font-bold text-white font-mono">{symbol}</span>
                                                </div>
                                            </td>
                                            <td className="p-6 text-right font-mono font-bold text-white tracking-tight">
                                                {formatCurrency(t.lastPrice)}
                                            </td>
                                            <td className="p-6 text-right">
                                                <div className={`inline-flex items-center gap-1 font-bold text-xs ${isPositive ? 'text-[#00ffa3]' : 'text-[#ff4d4d]'}`}>
                                                    {isPositive ? <ArrowUpRight size={14} /> : <ArrowDownRight size={14} />}
                                                    {Math.abs(change).toFixed(2)}%
                                                </div>
                                            </td>
                                            <td className="p-6 text-right font-mono text-gray-400 text-xs hidden md:table-cell">
                                                ${formatVolume(t.quoteVolume)}
                                            </td>
                                            <td className="p-6 text-right font-mono text-gray-400 text-xs hidden lg:table-cell">
                                                {t.count.toLocaleString()}
                                            </td>
                                        </tr>
                                    );
                                })
                            )}
                        </tbody>
                    </table>
                </div>
            </div>
        </div>
    );
}
