'use client';

import { useEffect, useState } from 'react';
import { supabase } from '@/lib/supabaseClient';
import SignalCard from '@/components/SignalCard';
import { Zap } from 'lucide-react';

interface Signal {
    id: number;
    symbol: string;
    price: number;
    rsi: number;
    signal_type: string;
    confidence: number;
    timestamp: string;
}

import { ChartComponent } from '@/components/ChartComponent';

export default function Dashboard() {
    const [signals, setSignals] = useState<Signal[]>([]);
    const [loading, setLoading] = useState(true);

    // Fetch initial data
    const fetchSignals = async () => {
        const { data, error } = await supabase
            .from('market_signals')
            .select('*')
            .order('timestamp', { ascending: false })
            .limit(20);

        if (error) console.error('Error fetching signals:', error);
        else setSignals(data || []);
        setLoading(false);
    };

    useEffect(() => {
        fetchSignals();

        // Real-time Subscription
        const channel = supabase
            .channel('realtime signals')
            .on('postgres_changes', { event: 'INSERT', schema: 'public', table: 'market_signals' }, (payload) => {
                const newSignal = payload.new as Signal;
                setSignals((prev) => [newSignal, ...prev].slice(0, 50)); // Keep last 50
            })
            .subscribe();

        return () => {
            supabase.removeChannel(channel);
        };
    }, []);

    // Mock Data for the chart demonstration
    const chartData = [
        { time: '2023-12-22', value: 32.51 },
        { time: '2023-12-23', value: 31.11 },
        { time: '2023-12-24', value: 27.02 },
        { time: '2023-12-25', value: 27.32 },
        { time: '2023-12-26', value: 25.17 },
        { time: '2023-12-27', value: 28.89 },
        { time: '2023-12-28', value: 25.46 },
        { time: '2023-12-29', value: 23.92 },
        { time: '2023-12-30', value: 22.68 },
        { time: '2023-12-31', value: 22.67 },
    ];

    return (
        <div className="min-h-screen bg-[#050505] text-white font-sans selection:bg-[#00ffa3] selection:text-black">
            {/* HEADER */}
            <header className="fixed top-0 w-full h-16 bg-[#000]/80 backdrop-blur-md border-b border-[#222] z-50 flex items-center justify-between px-6">
                <div className="flex items-center gap-2">
                    <Zap className="text-[#00ffa3] fill-current" size={20} />
                    <span className="font-mono font-bold text-lg tracking-wider">
                        TRENDS<span className="text-[#00ffa3]">AI</span> v2
                    </span>
                </div>
                <div className="flex items-center gap-4">
                    <div className="hidden md:flex items-center gap-2 px-3 py-1 bg-[#111] rounded-full border border-[#333]">
                        <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse"></div>
                        <span className="text-xs text-gray-400 font-mono">SYSTEM ONLINE</span>
                    </div>
                    <a href="/" className="text-sm text-gray-500 hover:text-white transition-colors">Exit</a>
                </div>
            </header>

            {/* MAIN CONTENT */}
            <main className="pt-24 px-4 md:px-8 max-w-7xl mx-auto">
                <div className="flex justify-between items-end mb-8">
                    <div>
                        <h1 className="text-3xl font-bold mb-2">Live Market Scanner</h1>
                        <p className="text-gray-400">Monitoring 50+ High Volume Pairs via Binance API</p>
                    </div>
                </div>

                {/* MARKET OVERVIEW CHART */}
                <div className="mb-10 p-1 border border-[#222] rounded-2xl bg-[#0e0e12]">
                    <div className="p-4 border-b border-[#222] flex justify-between items-center">
                        <h3 className="text-sm font-bold text-gray-300">BTC/USDT TREND OVERVIEW</h3>
                        <span className="text-xs text-[#00ffa3]">LIVE FEED</span>
                    </div>
                    <div className="p-4">
                        <ChartComponent data={chartData} />
                    </div>
                </div>

                {/* SIGNALS GRID */}
                {loading ? (
                    <div className="flex justify-center items-center h-64 text-[#00ffa3] font-mono animate-pulse">
                        INITIALIZING NEURAL NET...
                    </div>
                ) : (
                    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                        {signals.map((signal) => (
                            <SignalCard key={signal.id} {...signal} />
                        ))}

                        {signals.length === 0 && (
                            <div className="col-span-full text-center py-20 text-gray-600 border border-dashed border-[#222] rounded-xl font-mono">
                                Searching for institutional patterns...
                            </div>
                        )}
                    </div>
                )}
            </main>
        </div>
    );
}
