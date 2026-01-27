'use client';

import { useState, useEffect } from 'react';
import { ArrowUpRight, ArrowDownRight, Search, Zap, Globe, BarChart2 } from 'lucide-react';
import { LineChart, Line, ResponsiveContainer, YAxis } from 'recharts';

interface CoinData {
    id: string;
    symbol: string;
    name: string;
    image: string;
    current_price: number;
    market_cap: number;
    market_cap_rank: number;
    total_volume: number;
    price_change_percentage_24h: number;
    sparkline_in_7d: {
        price: number[];
    };
}

export default function MarketPage() {
    const [coins, setCoins] = useState<CoinData[]>([]);
    const [loading, setLoading] = useState(true);
    const [search, setSearch] = useState('');

    useEffect(() => {
        const fetchMarketData = async () => {
            try {
                // Free Tier CoinGecko API
                const url = 'https://api.coingecko.com/api/v3/coins/markets?vs_currency=usd&order=market_cap_desc&per_page=100&page=1&sparkline=true&price_change_percentage=24h';
                const res = await fetch(url);
                if (!res.ok) throw new Error('API Rate Limit or Error');
                const data = await res.json();
                setCoins(data);
                setLoading(false);
            } catch (error) {
                console.error("CoinGecko Error:", error);
                setLoading(false);
            }
        };

        fetchMarketData();
        const interval = setInterval(fetchMarketData, 60000); // Update every minute
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
                        Global Crypto Metrics & Trends
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
                                <th className="p-6 text-[10px] font-black text-gray-500 uppercase tracking-widest text-right">24h Change</th>
                                <th className="p-6 text-[10px] font-black text-gray-500 uppercase tracking-widest text-right hidden lg:table-cell">Market Cap</th>
                                <th className="p-6 text-[10px] font-black text-gray-500 uppercase tracking-widest text-right hidden xl:table-cell">Volume (24h)</th>
                                <th className="p-6 text-[10px] font-black text-gray-500 uppercase tracking-widest w-48 hidden md:table-cell">Last 7 Days</th>
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
                                        <td className="p-6 hidden lg:table-cell"><div className="h-4 w-24 bg-white/5 rounded animate-pulse ml-auto"></div></td>
                                        <td className="p-6 hidden xl:table-cell"><div className="h-4 w-24 bg-white/5 rounded animate-pulse ml-auto"></div></td>
                                        <td className="p-6 hidden md:table-cell"><div className="h-10 w-32 bg-white/5 rounded animate-pulse"></div></td>
                                    </tr>
                                ))
                            ) : (
                                filteredCoins.map((coin) => {
                                    const isPositive = coin.price_change_percentage_24h >= 0;
                                    const chartData = coin.sparkline_in_7d.price.map((val, i) => ({ i, val }));

                                    return (
                                        <tr key={coin.id} className="border-b border-white/5 hover:bg-white/[0.02] transition-colors group">
                                            <td className="p-6 text-center text-xs text-gray-500 font-bold font-mono">
                                                {coin.market_cap_rank}
                                            </td>
                                            <td className="p-6">
                                                <div className="flex items-center gap-4">
                                                    <img src={coin.image} alt={coin.name} className="w-8 h-8 rounded-full grayscale group-hover:grayscale-0 transition-all duration-300" />
                                                    <div>
                                                        <span className="text-sm font-bold text-white block">{coin.name}</span>
                                                        <span className="text-[10px] font-black text-gray-600 uppercase tracking-wider">{coin.symbol}</span>
                                                    </div>
                                                </div>
                                            </td>
                                            <td className="p-6 text-right font-mono font-bold text-white tracking-tight">
                                                {formatCurrency(coin.current_price)}
                                            </td>
                                            <td className="p-6 text-right">
                                                <div className={`inline-flex items-center gap-1 font-bold text-xs ${isPositive ? 'text-[#00ffa3]' : 'text-[#ff4d4d]'}`}>
                                                    {isPositive ? <ArrowUpRight size={14} /> : <ArrowDownRight size={14} />}
                                                    {Math.abs(coin.price_change_percentage_24h).toFixed(2)}%
                                                </div>
                                            </td>
                                            <td className="p-6 text-right font-mono text-gray-400 text-xs hidden lg:table-cell">
                                                ${formatCompact(coin.market_cap)}
                                            </td>
                                            <td className="p-6 text-right font-mono text-gray-400 text-xs hidden xl:table-cell">
                                                ${formatCompact(coin.total_volume)}
                                            </td>
                                            <td className="p-6 hidden md:table-cell">
                                                <div className="h-12 w-32">
                                                    <ResponsiveContainer width="100%" height="100%">
                                                        <LineChart data={chartData}>
                                                            <Line
                                                                type="monotone"
                                                                dataKey="val"
                                                                stroke={isPositive ? "#00ffa3" : "#ff4d4d"}
                                                                strokeWidth={2}
                                                                dot={false}
                                                                isAnimationActive={false}
                                                            />
                                                            <YAxis domain={['dataMin', 'dataMax']} hide />
                                                        </LineChart>
                                                    </ResponsiveContainer>
                                                </div>
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
