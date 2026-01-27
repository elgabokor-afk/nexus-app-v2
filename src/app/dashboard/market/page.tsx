'use client';

import { useState, useEffect } from 'react';
import { ArrowUpRight, ArrowDownRight, Search, Zap, Globe, BarChart2 } from 'lucide-react';
import { LineChart, Line, ResponsiveContainer, YAxis } from 'recharts';

interface CMCData {
    id: number;
    name: string;
    symbol: string;
    cmc_rank: number;
    quote: {
        USD: {
            price: number;
            volume_24h: number;
            percent_change_24h: number;
            percent_change_7d: number;
            market_cap: number;
        }
    }
}

export default function MarketPage() {
    const [coins, setCoins] = useState<CMCData[]>([]);
    const [loading, setLoading] = useState(true);
    const [search, setSearch] = useState('');

    useEffect(() => {
        const fetchMarketData = async () => {
            try {
                // Internal Proxy to CoinMarketCap Pro API
                const res = await fetch('/api/market');
                if (!res.ok) throw new Error('API Error');
                const json = await res.json();
                if (json.data) {
                    setCoins(json.data);
                }
                setLoading(false);
            } catch (error) {
                console.error("CMC API Error:", error);
                setLoading(false);
            }
        };

        fetchMarketData();
        const interval = setInterval(fetchMarketData, 60000); // 1 min update
        return () => clearInterval(interval);
    }, []);

    const filteredCoins = coins.filter(c =>
        c.name.toLowerCase().includes(search.toLowerCase()) ||
        c.symbol.toLowerCase().includes(search.toLowerCase())
    );

    const formatCurrency = (val: number) => {
        return new Intl.NumberFormat('en-US', {
            style: 'currency',
            currency: 'USD',
            minimumFractionDigits: val < 1 ? 4 : 2,
            maximumFractionDigits: val < 1 ? 6 : 2,
        }).format(val);
    };

    const formatCompact = (val: number) => {
        return new Intl.NumberFormat('en-US', {
            notation: "compact",
            maximumFractionDigits: 1
        }).format(val);
    };

    const renderChange = (val: number) => {
        const isPos = val >= 0;
        return (
            <div className={`inline-flex items-center gap-1 font-bold text-xs ${isPos ? 'text-[#00ffa3]' : 'text-[#ff4d4d]'}`}>
                {isPos ? <ArrowUpRight size={14} /> : <ArrowDownRight size={14} />}
                {Math.abs(val).toFixed(2)}%
            </div>
        );
    };

    return (
        <div className="min-h-screen bg-[#050505] text-white p-6 lg:p-10 font-sans">

            {/* Header */}
            <div className="flex flex-col md:flex-row md:items-center justify-between gap-6 mb-8">
                <div>
                    <h1 className="text-3xl font-black tracking-tighter flex items-center gap-3">
                        <Globe className="text-[#00ffa3]" />
                        MARKET <span className="text-[#00ffa3]">OVERVIEW</span>
                    </h1>
                    <p className="text-gray-500 text-xs font-bold tracking-widest uppercase mt-1">
                        Powered by CoinMarketCap Pro
                    </p>
                </div>

                <div className="relative w-full md:w-96">
                    <Search className="absolute left-4 top-1/2 -translate-y-1/2 text-gray-500" size={18} />
                    <input
                        type="text"
                        placeholder="Search assets..."
                        value={search}
                        onChange={(e) => setSearch(e.target.value)}
                        className="w-full bg-white/[0.03] border border-white/10 rounded-2xl py-3 pl-12 pr-4 text-sm text-white focus:outline-none focus:border-[#00ffa3]/50 transition-all font-medium placeholder:text-gray-600"
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
                                <th className="p-6 text-[10px] font-black text-gray-500 uppercase tracking-widest text-center w-16">Rank</th>
                                <th className="p-6 text-[10px] font-black text-gray-500 uppercase tracking-widest">Asset</th>
                                <th className="p-6 text-[10px] font-black text-gray-500 uppercase tracking-widest text-right">Price</th>
                                <th className="p-6 text-[10px] font-black text-gray-500 uppercase tracking-widest text-right">24h %</th>
                                <th className="p-6 text-[10px] font-black text-gray-500 uppercase tracking-widest text-right hidden lg:table-cell">7d %</th>
                                <th className="p-6 text-[10px] font-black text-gray-500 uppercase tracking-widest text-right hidden xl:table-cell">Market Cap</th>
                                <th className="p-6 text-[10px] font-black text-gray-500 uppercase tracking-widest text-right hidden xl:table-cell">Volume (24h)</th>
                            </tr>
                        </thead>
                        <tbody>
                            {loading ? (
                                // Loading Skeletons
                                Array.from({ length: 10 }).map((_, i) => (
                                    <tr key={i} className="border-b border-white/5">
                                        <td className="p-6"><div className="h-4 w-8 bg-white/5 rounded animate-pulse mx-auto"></div></td>
                                        <td className="p-6"><div className="flex items-center gap-3"><div className="w-8 h-8 rounded-full bg-white/5 animate-pulse"></div><div className="h-4 w-24 bg-white/5 rounded animate-pulse"></div></div></td>
                                        <td className="p-6"><div className="h-4 w-20 bg-white/5 rounded animate-pulse ml-auto"></div></td>
                                        <td className="p-6"><div className="h-4 w-16 bg-white/5 rounded animate-pulse ml-auto"></div></td>
                                        <td className="p-6 hidden lg:table-cell"><div className="h-4 w-16 bg-white/5 rounded animate-pulse ml-auto"></div></td>
                                        <td className="p-6 hidden xl:table-cell"><div className="h-4 w-24 bg-white/5 rounded animate-pulse ml-auto"></div></td>
                                        <td className="p-6 hidden xl:table-cell"><div className="h-4 w-24 bg-white/5 rounded animate-pulse ml-auto"></div></td>
                                    </tr>
                                ))
                            ) : (
                                filteredCoins.map((coin) => {
                                    const quote = coin.quote.USD;
                                    const logoUrl = `https://s2.coinmarketcap.com/static/img/coins/64x64/${coin.id}.png`;

                                    return (
                                        <tr key={coin.id} className="border-b border-white/5 hover:bg-white/[0.02] transition-colors group">
                                            <td className="p-6 text-center text-xs text-gray-500 font-bold font-mono">
                                                {coin.cmc_rank}
                                            </td>
                                            <td className="p-6">
                                                <div className="flex items-center gap-4">
                                                    <img src={logoUrl} alt={coin.name} className="w-8 h-8 rounded-full grayscale group-hover:grayscale-0 transition-all duration-300" />
                                                    <div>
                                                        <span className="text-sm font-bold text-white block">{coin.name}</span>
                                                        <span className="text-[10px] font-black text-gray-600 uppercase tracking-wider">{coin.symbol}</span>
                                                    </div>
                                                </div>
                                            </td>
                                            <td className="p-6 text-right font-mono font-bold text-white tracking-tight">
                                                {formatCurrency(quote.price)}
                                            </td>
                                            <td className="p-6 text-right">
                                                {renderChange(quote.percent_change_24h)}
                                            </td>
                                            <td className="p-6 text-right hidden lg:table-cell">
                                                {renderChange(quote.percent_change_7d)}
                                            </td>
                                            <td className="p-6 text-right font-mono text-gray-400 text-xs hidden xl:table-cell">
                                                ${formatCompact(quote.market_cap)}
                                            </td>
                                            <td className="p-6 text-right font-mono text-gray-400 text-xs hidden xl:table-cell">
                                                ${formatCompact(quote.volume_24h)}
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
